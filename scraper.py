import requests
from bs4 import BeautifulSoup
import json
import urllib3
import os

# Silenciamos los avisos de certificado HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🔐 Leemos la API Key desde las variables de entorno de GitHub
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")

if not ZENROWS_API_KEY:
    print("❌ Error crítico: No se ha encontrado la variable de entorno ZENROWS_API_KEY.")
    exit(1)

zenrows_endpoint = "https://api.zenrows.com/v1/"

URLS_FILE = "urls.txt"
DATABASE_FILE = "base_de_datos_madrid.json"

# =========================================================================
# 📦 1. CARGAR BASE DE DATOS EXISTENTE
# =========================================================================
base_de_datos_eventos = []
ids_ya_guardados = set()

if os.path.exists(DATABASE_FILE):
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            base_de_datos_eventos = json.load(f)
            # Guardamos tanto el ID corto como la URL por si hay variantes
            ids_ya_guardados = {str(evento.get("id", "")) for evento in base_de_datos_eventos}
        print(f"📂 Base de datos detectada. Cargados {len(base_de_datos_eventos)} eventos históricos.")
    except Exception as e:
        print(f"⚠️ Alerta: El JSON de la base de datos estaba corrupto o vacío. Error: {e}")
        base_de_datos_eventos = []

# =========================================================================
# 📋 2. LEER LAS URLS A PROCESAR
# =========================================================================
if not os.path.exists(URLS_FILE):
    print(f"❌ Error: No se encuentra el archivo '{URLS_FILE}'. Ejecuta primero 'scraper_events.py'.")
    exit(1)

with open(URLS_FILE, "r", encoding="utf-8") as f:
    enlaces_rrpp = [line.strip() for line in f if line.strip() and not line.startswith("#")]

print(f"📋 Analizando lista de {len(enlaces_rrpp)} eventos frente a los guardados...")

# =========================================================================
# 🔄 3. BUCLE INTELIGENTE (SMART SKIP)
# =========================================================================
nuevos_agregados = 0

for index, url in enumerate(enlaces_rrpp):
    # Extraemos el ID único del enlace (ej: https://.../events/6YDG -> 6YDG)
    event_id = url.split("-")[-1].split("/")[-1]
    
    # Comprobamos si el ID o la URL completa ya están en la base de datos
    if event_id in ids_ya_guardados or url in ids_ya_guardados:
        print(f"⏩ [{index + 1}/{len(enlaces_rrpp)}] Saltando -> El evento [{event_id}] ya está indexado. (0 créditos)")
        continue
        
    print(f"\n✨ [{index + 1}/{len(enlaces_rrpp)}] ¡NUEVO EVENTO DETECTADO! [{event_id}]. Lanzando proxy...")
    
    params = {"apikey": ZENROWS_API_KEY, "url": url}
    
    try:
        response = requests.get(zenrows_endpoint, params=params, verify=False, timeout=30)
        
        if response.status_code == 404:
            print(f"⚠️ El evento [{event_id}] ya no existe en Fourvenues (404).")
            continue
            
        elif response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            texto_completo = soup.get_text()
            
            if "Event Cancelled" in texto_completo:
                print(f"⚠️ El evento [{event_id}] está cancelado. No se añade.")
                continue

            script_json_ld = soup.find("script", type="application/ld+json")
            data_main = json.loads(script_json_ld.string) if script_json_ld else {}
            
            meta_desc = soup.find("meta", attrs={"name": "description"})
            descripcion = meta_desc["content"] if meta_desc else "Sin descripción"
            
            vestimenta = "Smart / Arreglado" if "Smart" in texto_completo or "arreglado" in response.text else "Casual / Libre"
            edad = "+23" if "+23" in texto_completo else "+18"
            
            titulo_fiesta = data_main.get("name", "Evento de Fiesta")
            fecha = data_main.get("startDate", "2026-07-17").split("T")[0]
            hora_apertura = data_main.get("startDate", "18:00:00").split("T")[-1][:5]
            
            evento_estructurado = {
                "id": event_id,
                "titulo": titulo_fiesta,
                "imagen": data_main.get("image", "https://fourvenues.com/..."),
                "fecha": fecha,
                "hora": hora_apertura,
                "edad": edad,
                "vestimenta": vestimenta,
                "sala": data_main.get("location", {}).get("name", "Sala Madrid"),
                "direccion": data_main.get("location", {}).get("address", {}).get("streetAddress", "Madrid, España"),
                "link_compra_rrpp": url,
                "descripcion": descripcion
            }
            
            base_de_datos_eventos.append(evento_estructurado)
            ids_ya_guardados.add(event_id)
            nuevos_agregados += 1
            print(f"➕ Agregado con éxito a la cola: {titulo_fiesta}")
            
        else:
            print(f"⚠️ Fallo temporal en ZenRows para [{event_id}]. Estado: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Error al procesar {event_id}: {e}")

# =========================================================================
# 📅 4. ORDENADO CRONOLÓGICO SECTORIZADO (Primero Fecha, luego Hora)
# =========================================================================
print("\n📅 Ordenando cartelera por fecha y hora de apertura...")
base_de_datos_eventos.sort(key=lambda x: (x.get("fecha", "9999-12-31"), x.get("hora", "23:59")))

# =========================================================================
# 💾 5. GUARDAR LA BASE DE DATOS ACTUALIZADA
# =========================================================================
with open(DATABASE_FILE, "w", encoding="utf-8") as archivo:
    json.dump(base_de_datos_eventos, archivo, indent=4, ensure_ascii=False)

print(f"\n🏁 PROCESO COMPLETADO.")
print(f"Se han incorporado {nuevos_agregados} nuevos eventos.")
print(f"Archivo '{DATABASE_FILE}' sincronizado, ordenado y listo. Total: {len(base_de_datos_eventos)} eventos.")