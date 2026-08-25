import os
import json
import sys
import time
import argparse
import firebase_admin
from firebase_admin import credentials, firestore

def formatear_error_firestore(error: Exception) -> str:
    """Traduce y diagnostica errores comunes de Firestore para dar pistas claras de resolución."""
    err_str = str(error)
    if "Invalid database id %28default%29" in err_str or "Invalid database id (default)" in err_str:
        return (
            "🚨 DIAGNÓSTICO: Bug conocido de codificación en 'google-api-core' v2.35.0.\n"
            "   SOLUCIÓN: Añade 'google-api-core<=2.34.0' en 'requirements.txt' para evitar que se codifique '(default)' como '%28default%29'."
        )
    if "PermissionDenied" in err_str or "7 PERMISSION_DENIED" in err_str:
        return (
            "🚨 DIAGNÓSTICO: Permisos insuficientes en la cuenta de servicio de Firebase.\n"
            "   SOLUCIÓN: Revisa en Google Cloud Console que la Service Account tenga el rol 'Cloud Datastore User' o 'Firebase Admin'."
        )
    if "Unauthenticated" in err_str or "16 UNAUTHENTICATED" in err_str:
        return (
            "🚨 DIAGNÓSTICO: Clave de cuenta de servicio inválida o expirada.\n"
            "   SOLUCIÓN: Genera una nueva clave privada JSON en Firebase Console y actualiza el Secret FIREBASE_SERVICE_ACCOUNT."
        )
    return f"Detalles del error: {err_str}"


def main():
    parser = argparse.ArgumentParser(description="Sincronizar eventos con Firestore")
    parser.add_argument("--wipe", action="store_true", help="Borra todos los eventos en la colección antes de sincronizar")
    args = parser.parse_args()

    db_file = "data/base_de_datos_madrid.json"
    
    # 1. Verificación inicial de fichero local
    if not os.path.exists(db_file):
        print(f"❌ Error: El archivo local '{db_file}' no existe.")
        sys.exit(1)
        
    try:
        with open(db_file, "r", encoding="utf-8") as f:
            eventos = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: El archivo '{db_file}' no contiene un JSON válido: {e}")
        sys.exit(1)
        
    if not isinstance(eventos, list):
        print(f"❌ Error: El archivo '{db_file}' debe contener una lista de eventos.")
        sys.exit(1)
        
    if len(eventos) == 0:
        print("ℹ️ Información: No hay eventos para sincronizar en la base de datos.")
        sys.exit(0)

    # 2. Autenticación y configuración segura con Firebase
    service_account_info = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not service_account_info:
        print("❌ Error: La variable de entorno FIREBASE_SERVICE_ACCOUNT no está definida.")
        sys.exit(1)
        
    try:
        cred_dict = json.loads(service_account_info)
        project_id = cred_dict.get("project_id", "desconocido")
        print(f"🔐 Inicializando Firebase Admin SDK para el proyecto: '{project_id}'...")
        
        # Evitar re-inicializar si ya existía una app activa
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
    except json.JSONDecodeError:
        print("❌ Error: El contenido de FIREBASE_SERVICE_ACCOUNT no es un JSON válido.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error al inicializar Firebase Admin: {e}")
        print(formatear_error_firestore(e))
        sys.exit(1)
        
    try:
        db = firestore.client()
        collection_ref = db.collection("eventos")
    except Exception as e:
        print(f"❌ Error al obtener el cliente de Firestore: {e}")
        print(formatear_error_firestore(e))
        sys.exit(1)

    # 3. Limpieza previa si se solicitó flag --wipe
    if args.wipe:
        print("⚠️ Flag --wipe detectado. Procediendo a vaciar la colección 'eventos'...")
        try:
            docs = collection_ref.stream()
            delete_batch = db.batch()
            count = 0
            for doc in docs:
                delete_batch.delete(doc.reference)
                count += 1
                if count % 400 == 0:
                    delete_batch.commit()
                    delete_batch = db.batch()
            if count % 400 != 0:
                delete_batch.commit()
            print(f"✅ Se borraron {count} documentos antiguos (--wipe).")
        except Exception as e:
            print(f"❌ Error durante el vaciado (--wipe): {e}")
            print(formatear_error_firestore(e))
            sys.exit(1)

    # 4. Volcado de eventos por lotes (Batch Writes con reintentos y tolerancia a fallos)
    total_eventos = len(eventos)
    print(f"🚀 Iniciando sincronización de {total_eventos} eventos hacia Firestore...")
    
    eventos_procesados = 0
    batch_limit = 400
    ids_activos = set()
    lotes_fallidos = 0

    for i in range(0, total_eventos, batch_limit):
        batch = db.batch()
        lote_eventos = eventos[i:i + batch_limit]
        
        for evento in lote_eventos:
            if "id" not in evento:
                continue
                
            doc_id = str(evento["id"])
            ids_activos.add(doc_id)
            doc_ref = collection_ref.document(doc_id)
            
            # Usar set con merge=True para actualizar o insertar sin sobreescribir datos ajenos
            batch.set(doc_ref, evento, merge=True)
            
        # Reintentos con backoff exponencial para cada lote
        exito_lote = False
        max_reintentos = 3
        for intento in range(1, max_reintentos + 1):
            try:
                batch.commit()
                eventos_procesados += len(lote_eventos)
                print(f"  📦 Lote {i // batch_limit + 1}: {eventos_procesados}/{total_eventos} eventos sincronizados.")
                exito_lote = True
                break
            except Exception as e:
                print(f"  ⚠️ Intento {intento}/{max_reintentos} fallido en lote {i // batch_limit + 1}: {e}")
                if intento == max_reintentos:
                    print(f"❌ Error definitivo en el lote {i // batch_limit + 1}.")
                    print(formatear_error_firestore(e))
                    lotes_fallidos += 1
                else:
                    time.sleep(2 ** intento)

    # Si hubo lotes fallidos, abortamos de forma segura sin realizar borrado de obsoletos
    if lotes_fallidos > 0:
        print(f"\n❌ Abortando sincronización: {lotes_fallidos} lote(s) fallaron durante la subida.")
        print("Se cancela la fase de depuración de eventos obsoletos para evitar pérdidas accidentales.")
        sys.exit(1)

    # 5. Limpieza segura de eventos caducados/eliminados
    if not args.wipe:
        print("\n🧹 Buscando eventos caducados o eliminados en Firestore para depuración...")
        try:
            docs = list(collection_ref.stream())
            docs_a_borrar = [doc for doc in docs if doc.id not in ids_activos]
            
            if len(docs_a_borrar) > 30:
                print(f"⚠️ ¡ALERTA DE SEGURIDAD! Se intentaban borrar {len(docs_a_borrar)} eventos de golpe.")
                print("   Para proteger la base de datos de anomalías del scraper, se cancela la depuración automática.")
                print("   Si es intencionado, ejecuta el workflow con el flag 'wipe_db: true'.")
            elif len(docs_a_borrar) > 0:
                delete_batch = db.batch()
                borrados = 0
                for doc in docs_a_borrar:
                    delete_batch.delete(doc.reference)
                    borrados += 1
                    if borrados % 400 == 0:
                        delete_batch.commit()
                        delete_batch = db.batch()
                if borrados % 400 != 0:
                    delete_batch.commit()
                print(f"✅ Se eliminaron {borrados} eventos obsoletos de Firestore.")
            else:
                print("✨ No hay eventos obsoletos que limpiar. La base de datos está perfectamente sincronizada.")
        except Exception as e:
            print(f"⚠️ Error durante la verificación de obsoletos: {e}")
            print(formatear_error_firestore(e))
            sys.exit(1)

    # 6. Finalización exitosa
    print(f"\n🎉 Sincronización completada exitosamente. Total de eventos activos en Firestore: {len(ids_activos)}.")

if __name__ == "__main__":
    main()
