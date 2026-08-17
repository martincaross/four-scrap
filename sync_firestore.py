import os
import json
import sys
import firebase_admin
from firebase_admin import credentials, firestore

def main():
    db_file = "base_de_datos_madrid.json"
    
    # 1. Verificación inicial
    if not os.path.exists(db_file):
        print(f"Error: El archivo {db_file} no existe.")
        sys.exit(1)
        
    try:
        with open(db_file, "r", encoding="utf-8") as f:
            eventos = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: El archivo {db_file} no contiene un JSON válido.")
        sys.exit(1)
        
    if not isinstance(eventos, list):
        print(f"Error: El archivo {db_file} no contiene una lista de eventos.")
        sys.exit(1)
        
    if len(eventos) == 0:
        print("Información: No hay eventos para sincronizar.")
        sys.exit(0)

    # 2. Autenticación segura
    service_account_info = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not service_account_info:
        print("Error: La variable de entorno FIREBASE_SERVICE_ACCOUNT no está definida.")
        sys.exit(1)
        
    try:
        cred_dict = json.loads(service_account_info)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Error al inicializar Firebase: {e}")
        sys.exit(1)
        
    db = firestore.client()
    collection_ref = db.collection("eventos")
    import argparse
    parser = argparse.ArgumentParser(description="Sincronizar eventos con Firestore")
    parser.add_argument("--wipe", action="store_true", help="Borra todos los eventos en la colección antes de sincronizar")
    args = parser.parse_args()

    # 3. Estructura y volcado en Firestore (Batch Writes)
    if args.wipe:
        print("⚠️ Flag --wipe detectado. Borrando todos los documentos existentes en 'eventos'...")
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
        print(f"✅ Se borraron {count} documentos antiguos.")

    print(f"Iniciando sincronización de {len(eventos)} eventos hacia Firestore...")
    
    total_eventos = len(eventos)
    eventos_procesados = 0
    batch_limit = 400
    
    # Recopilar todos los IDs que se van a subir para la limpieza posterior
    ids_activos = set()

    for i in range(0, total_eventos, batch_limit):
        batch = db.batch()
        lote_eventos = eventos[i:i + batch_limit]
        
        for evento in lote_eventos:
            if "id" not in evento:
                continue
                
            doc_id = str(evento["id"])
            ids_activos.add(doc_id)
            doc_ref = collection_ref.document(doc_id)
            
            # Usar set con merge=True para actualizar sin duplicar ni borrar campos extra
            batch.set(doc_ref, evento, merge=True)
            
        try:
            batch.commit()
            eventos_procesados += len(lote_eventos)
            print(f"Lote enviado: {eventos_procesados}/{total_eventos} eventos sincronizados.")
        except Exception as e:
            print(f"Error al enviar lote a Firestore: {e}")
            
    # 4. Limpieza de eventos caducados/eliminados
    if not args.wipe:
        print("🧹 Buscando eventos caducados o eliminados en Firestore para borrarlos...")
        docs = collection_ref.stream()
        delete_batch = db.batch()
        borrados = 0
        for doc in docs:
            if doc.id not in ids_activos:
                delete_batch.delete(doc.reference)
                borrados += 1
                if borrados % 400 == 0:
                    delete_batch.commit()
                    delete_batch = db.batch()
        if borrados % 400 != 0:
            delete_batch.commit()
        if borrados > 0:
            print(f"✅ Se eliminaron {borrados} eventos obsoletos de Firestore.")
        else:
            print("✨ No había eventos obsoletos que limpiar.")

    # 5. Trazabilidad y logs
    print(f"Sincronización completada exitosamente. Se sincronizaron {eventos_procesados} eventos activos.")

if __name__ == "__main__":
    main()
