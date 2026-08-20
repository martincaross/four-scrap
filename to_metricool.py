#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
to_metricool.py
----------------
Módulo de salida para redes sociales (Marketing Automation).
Sube vídeos y recursos multimedia a Firebase Storage y genera archivos CSV
compatibles con la importación masiva (Bulk CSV Upload) de Metricool.

Cabeceras oficiales de Metricool:
    Date, Time, Text, Image/Video URL, Link, Pinterest board

Configuración del entorno:
    1. FIREBASE_SERVICE_ACCOUNT:
       - Contenido JSON de la cuenta de servicio o ruta a 'serviceAccountKey.json'.
    2. FIREBASE_STORAGE_BUCKET:
       - Nombre del bucket de Firebase Storage (ej: 'mi-proyecto.appspot.com' o 'mi-proyecto.firebasestorage.app').
"""

import os
import sys
import csv
import json
import logging
import mimetypes
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, storage
except ImportError:
    firebase_admin = None
    credentials = None
    storage = None

# Configuración de logs para el pipeline
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ToMetricool")


def init_firebase_storage(
    storage_bucket: Optional[str] = None,
    service_account_info: Optional[str] = None
) -> Any:
    """
    Inicializa la conexión con Firebase Admin SDK habilitando Firebase Storage.
    
    Args:
        storage_bucket: Nombre del bucket (ej: 'proyecto.appspot.com'). Si es None,
                        se obtiene de la variable de entorno FIREBASE_STORAGE_BUCKET.
        service_account_info: JSON string o ruta al archivo de credenciales. Si es None,
                              se obtiene de FIREBASE_SERVICE_ACCOUNT.
    
    Returns:
        bucket: Instancia del bucket de Firebase Storage listo para operar.
    """
    if firebase_admin is None:
        raise ImportError(
            "El paquete 'firebase-admin' no está instalado. "
            "Instálalo ejecutando: pip install firebase-admin"
        )

    # 1. Resolver el nombre del bucket de Storage (por defecto el de mingle si no se especifica)
    bucket_name = (
        storage_bucket
        or os.environ.get("FIREBASE_STORAGE_BUCKET")
        or "mingle-495e0.firebasestorage.app"
    )

    # 2. Inicializar la app de Firebase si no está creada
    if not firebase_admin._apps:
        sa_raw = service_account_info or os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        
        # Búsqueda automática de archivo JSON de credenciales local si no hay variable de entorno
        if not sa_raw:
            for file in os.listdir("."):
                if file.endswith(".json") and ("firebase-adminsdk" in file or "serviceAccount" in file or "credentials" in file):
                    sa_raw = file
                    logger.info(f"🔍 Clave de servicio local detectada automáticamente: {file}")
                    break

        if not sa_raw:
            logger.warning(
                "FIREBASE_SERVICE_ACCOUNT no está definida y no se encontró clave local. "
                "Intentando usar Default Application Credentials..."
            )
            cred = credentials.ApplicationDefault()
        else:
            try:
                # Comprobar si es una ruta a archivo o un string JSON
                if os.path.isfile(sa_raw):
                    cred = credentials.Certificate(sa_raw)
                else:
                    cred_dict = json.loads(sa_raw)
                    cred = credentials.Certificate(cred_dict)
            except Exception as e:
                logger.error(f"Error al cargar credenciales de Firebase: {e}")
                raise

        firebase_admin.initialize_app(cred, {
            'storageBucket': bucket_name
        })
        logger.info(f"✅ Firebase Admin inicializado con bucket: {bucket_name}")
    
    # 3. Obtener y retornar referencia al bucket
    try:
        bucket = storage.bucket(bucket_name)
        return bucket
    except Exception as e:
        logger.error(f"Error al obtener el bucket '{bucket_name}': {e}")
        raise


def upload_to_storage(
    local_file_path: str,
    destination_blob_name: Optional[str] = None,
    storage_bucket: Optional[str] = None
) -> str:
    """
    Sube un archivo local (vídeo mp4, imagen, etc.) a Firebase Storage y genera
    su URL pública de descarga accesible para Metricool.

    Args:
        local_file_path: Ruta local del archivo a subir.
        destination_blob_name: Ruta destino dentro del bucket (opcional).
        storage_bucket: Nombre del bucket (opcional si ya está configurado en el entorno).

    Returns:
        str: URL pública de descarga del archivo en Firebase Storage.
    """
    try:
        # Validación de existencia del archivo local
        if not os.path.exists(local_file_path):
            raise FileNotFoundError(f"El archivo local '{local_file_path}' no existe.")

        # Determinar nombre del blob si no se proporcionó
        if not destination_blob_name:
            file_name = os.path.basename(local_file_path)
            destination_blob_name = f"marketing_media/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"

        logger.info(f"📤 Iniciando subida de '{local_file_path}' -> '{destination_blob_name}'...")

        # Conectar con el bucket
        bucket = init_firebase_storage(storage_bucket=storage_bucket)
        blob = bucket.blob(destination_blob_name)

        # Detectar el tipo MIME (por defecto video/mp4 si es .mp4)
        content_type, _ = mimetypes.guess_type(local_file_path)
        if not content_type:
            if local_file_path.lower().endswith(".mp4"):
                content_type = "video/mp4"
            else:
                content_type = "application/octet-stream"

        # Subir archivo al bucket
        blob.upload_from_filename(local_file_path, content_type=content_type)
        logger.info(f"📦 Archivo subido con éxito (ContentType: {content_type}).")

        # Hacer el archivo público para que Metricool pueda descargarlo e importarlo
        try:
            blob.make_public()
            public_url = blob.public_url
        except Exception as perm_err:
            # Fallback en caso de buckets con Uniform Bucket-Level Access donde se usa la URL estándar
            logger.warning(
                f"No se pudo invocar make_public() directamente ({perm_err}). "
                "Generando URL canónica de Google Storage."
            )
            bucket_clean = bucket.name.replace(".appspot.com", "")
            public_url = f"https://storage.googleapis.com/{bucket.name}/{destination_blob_name}"

        logger.info(f"🔗 URL pública generada: {public_url}")
        return public_url

    except Exception as e:
        logger.error(f"❌ Error al subir '{local_file_path}' a Firebase Storage: {e}")
        raise


def generate_metricool_csv(
    lista_posts: List[Dict[str, Any]],
    output_filename: str = "metricool.csv",
    base_date: Optional[datetime] = None
) -> str:
    """
    Genera un archivo CSV con el formato exacto de importación masiva de Metricool.

    Cabeceras exactas de Metricool:
        Date, Time, Text, Image/Video URL, Link, Pinterest board

    Lógica de programación de fechas:
        - Primer post: Mañana a las 19:00
        - Segundo post: Pasado mañana a las 19:00
        - Siguientes posts: +1 día secuencial a las 19:00
        - Formato Date: DD/MM/YYYY
        - Formato Time: HH:MM

    Args:
        lista_posts: Lista de diccionarios con la información de cada post.
                     Campos soportados:
                     - 'text' / 'Text' / 'texto': Texto o copia del post.
                     - 'media_url' / 'Image/Video URL' / 'url': URL del vídeo o imagen.
                     - 'link' / 'Link': Enlace web de destino (opcional).
                     - 'pinterest_board' / 'Pinterest board': Tablero de Pinterest (opcional).
                     - 'date' / 'Date': (Opcional) Sobrescribir fecha calculada.
                     - 'time' / 'Time': (Opcional) Sobrescribir hora calculada.
        output_filename: Nombre o ruta del archivo CSV de salida.
        base_date: Fecha base de referencia (por defecto datetime.now()).

    Returns:
        str: Ruta absoluta del archivo CSV generado.
    """
    try:
        if not lista_posts:
            logger.warning("⚠️ La lista de posts está vacía. Se creará un CSV solo con cabeceras.")

        # Cabeceras requeridas por la plantilla oficial de Metricool
        fieldnames = [
            "Date",
            "Time",
            "Text",
            "Image/Video URL",
            "Link",
            "Pinterest board"
        ]

        if base_date is None:
            base_date = datetime.now()

        # Asegurar directorio de salida si se especifica una ruta con carpetas
        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        rows_to_write = []

        for index, post in enumerate(lista_posts):
            # 1. Cálculo de fecha secuencial (Post 0 = Mañana, Post 1 = Pasado mañana, etc.)
            default_datetime = base_date + timedelta(days=(index + 1))
            default_date_str = default_datetime.strftime("%d/%m/%Y")  # DD/MM/YYYY
            default_time_str = "19:00"  # 19:00 HH:MM

            # Permitir sobrescritura manual si el post ya trae 'Date' o 'Time'
            date_val = post.get("Date") or post.get("date") or default_date_str
            time_val = post.get("Time") or post.get("time") or default_time_str

            # 2. Extracción flexible de campos
            text_val = (
                post.get("Text")
                or post.get("text")
                or post.get("texto")
                or post.get("copy")
                or ""
            )

            media_val = (
                post.get("Image/Video URL")
                or post.get("media_url")
                or post.get("image_url")
                or post.get("video_url")
                or post.get("url")
                or ""
            )

            link_val = (
                post.get("Link")
                or post.get("link")
                or post.get("url_evento")
                or ""
            )

            pinterest_val = (
                post.get("Pinterest board")
                or post.get("pinterest_board")
                or post.get("board")
                or ""
            )

            rows_to_write.append({
                "Date": str(date_val).strip(),
                "Time": str(time_val).strip(),
                "Text": str(text_val),
                "Image/Video URL": str(media_val).strip(),
                "Link": str(link_val).strip(),
                "Pinterest board": str(pinterest_val).strip()
            })

        # 3. Escritura del archivo CSV con delimitador de coma y codificación UTF-8
        with open(output_filename, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=",",
                quoting=csv.QUOTE_MINIMAL
            )
            writer.writeheader()
            for row in rows_to_write:
                writer.writerow(row)

        abs_path = os.path.abspath(output_filename)
        logger.info(f"✅ Archivo CSV generado correctamente: {abs_path} ({len(rows_to_write)} posts)")
        return abs_path

    except Exception as e:
        logger.error(f"❌ Error al generar el archivo CSV de Metricool: {e}")
        raise


# =====================================================================
# BLOQUE DE EJECUCIÓN / PRUEBAS MOCK
# =====================================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 PROBANDO MÓDULO DE SALIDA PARA METRICOOL (to_metricool.py)")
    print("=" * 60)

    # 1. Crear un archivo de vídeo simulado (mock MP4) para la prueba local
    mock_video_path = "temp_mock_video.mp4"
    try:
        with open(mock_video_path, "wb") as f:
            # Cabecera básica de contenedor MP4 / datos binarios de prueba
            f.write(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom<MOCK_VIDEO_DATA>")
        print(f"🎬 Vídeo de prueba creado: '{mock_video_path}'")

        # 2. Intentar subida a Firebase Storage
        video_url = ""
        try:
            print("🔑 Probando subida real a Firebase Storage...")
            video_url = upload_to_storage(mock_video_path, "tests/marketing_demo.mp4")
            print(f"✅ Subida exitosa. URL pública: {video_url}")
        except Exception as upload_err:
            print(f"⚠️ No se pudo completar la subida real ({upload_err}). Usando URL simulada.")
            video_url = "https://storage.googleapis.com/mingle-495e0.firebasestorage.app/marketing_media/demo_reel_2026.mp4"

        # 3. Definir lista de posts "mock" de prueba para el pipeline de marketing
        posts_demo = [
            {
                "text": "🔥 ¡Este fin de semana reventamos la noche en Madrid! No te quedes sin tu entrada. #MadridFiesta #NocheMadrid",
                "media_url": video_url,
                "link": "https://fourvenues.com/es/evento/demo-party-1",
                "pinterest_board": ""
            },
            {
                "text": "🎧 Line-up exclusivo con los mejores DJs de la capital. Consigue tus pases con consumición incluida. 🍹🕺",
                "media_url": video_url,
                "link": "https://fourvenues.com/es/evento/demo-party-2",
                "pinterest_board": "Madrid Nightlife"
            },
            {
                "text": "✨ Domingo de tardeo con la mejor música y ambientazo. ¡Reserva tu mesa VIP antes de que se agoten! 🍾",
                "media_url": video_url,
                "link": "https://fourvenues.com/es/evento/demo-party-3",
                "pinterest_board": "Madrid Nightlife"
            }
        ]

        # 4. Generar el archivo CSV de Metricool
        csv_salida = "metricool_test.csv"
        csv_path = generate_metricool_csv(posts_demo, output_filename=csv_salida)

        # 5. Mostrar el contenido generado para verificar cabeceras y fechas
        print("\n📄 VISTA PREVIA DEL CSV GENERADO:")
        print("-" * 60)
        with open(csv_path, "r", encoding="utf-8") as f:
            print(f.read())
        print("-" * 60)
        print("✅ Prueba completada con éxito. El CSV cumple con el estándar de Metricool.\n")

    finally:
        # Limpieza de archivo temporal mock
        if os.path.exists(mock_video_path):
            os.remove(mock_video_path)
            print(f"🧹 Archivo temporal '{mock_video_path}' eliminado.")
