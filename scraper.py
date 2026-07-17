import requests
from bs4 import BeautifulSoup
import json
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ZENROWS_API_KEY = "ba529a43017963c1e75c046c7a86af6d4457b79a"
zenrows_endpoint = "https://api.zenrows.com/v1/"

# Archivos del sistema
URLS_FILE = "urls.txt"
DATABASE_FILE = "base_de_datos_madrid.json"

# 1. Comprobamos si existe el archivo de enlaces externos
if not os.path.exists(URLS_FILE):
    print(f"❌ Error: No se encuentra el archivo '{URLS_FILE}'. Créalo antes de ejecutar.")
    exit()

# 2. Leer los enlaces del archivo txt limpiando espacios y saltos de línea
with open(URLS_FILE, "r", encoding="utf-8") as f:
    enlaces_rrpp = [line.strip() for line in f if line.strip() and not line.startswith("#")]

base_de_datos_eventos = []

print(f"🚀 Cargados {len(enlaces_rrpp)} enlaces desde '{URLS_FILE}'. Iniciando escaneo...")

for index, url in enumerate(enlaces_rrpp):
    print(f"\n🔄 [{index + 1}/{len(enlaces_rrpp)}] Verificando: {url}")
    
    params = {"apikey": ZENROWS_API_KEY, "url": url}
    
    try:
        response = requests.get(zenrows_endpoint, params=params, verify=False, timeout=30)
        
        # --- 🚨 CONTROL DE COMPROBACIÓN: EVENTO BORRADO O CANCELADO ---
        if response.status_code == 404:
            print(f"⚠️¡AVISO CRÍTICO! El evento ha sido BORRADO por el organizador (404 Not Found). Saltando...")
            continue  # Salta al siguiente enlace sin meterlo en la base de datos
            
        elif response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Comprobación secundaria: ver si en el texto de la página dice que está cancelado o finalizado
            texto_completo = soup.get_text()
            if "Event Cancelled" in texto_completo or "The event you are trying to access has been cancelled" in texto_completo:
                print(f"⚠️ El link existe pero Fourvenues indica que está CANCELADO. Saltando...")
                continue

            # Extracción de metadatos estructurados
            script_json_ld = soup.find("script", type="application/ld+json")
            data_main = json.loads(script_json_ld.string) if script_json_ld else {}
            
            meta_desc = soup.find("meta", attrs={"name": "description"})
            descripcion = meta_desc["content"] if meta_desc else "Sin descripción"
            
            vestimenta = "Smart / Arreglado" if "Smart" in texto_completo or "arreglado" in response.text else "Casual / Libre"
            edad = "+23" if "+23" in texto_completo else "+18"
            
            # Corrección de campos vacíos o por defecto
            titulo_fiesta = data_main.get("name", "Evento sin título")
            fecha = data_main.get("startDate", "2026-07-17").split("T")[0]
            hora_apertura = data_main.get("startDate", "18:00:00").split("T")[-1][:5]
            
            event_id = url.split("-")[-1]
            
            # Estructuración limpia del objeto
            evento_estructurado = {
                "id": event_id,
                "titulo": titulo_fiesta,
                "imagen": data_main.get("image", "https://fourvenues.com/cdn-cgi/imagedelivery/kWuoTchaMsk7Xnc_FNem7A/190e0e76-3db7-429a-f859-14facf2b0e00/w=1350"),
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
            print(f"✅ Procesado e indexado con éxito: {titulo_fiesta}")
            
        else:
            print(f"⚠️ Código de respuesta inesperado de ZenRows: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Error al procesar el enlace: {e}")

# 3. Guardar la lista completa en tu archivo JSON maestro
with open(DATABASE_FILE, "w", encoding="utf-8") as archivo:
    json.dump(base_de_datos_eventos, archivo, indent=4, ensure_ascii=False)

print(f"\n BÚNKER DE DATOS ACTUALIZADO.")
print(f"El archivo '{DATABASE_FILE}' contiene ahora {len(base_de_datos_eventos)} eventos listos para tu App móvil.")