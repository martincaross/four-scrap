import requests
from bs4 import BeautifulSoup
import json

# 1. Configuración de ZenRows y URL
ZENROWS_API_KEY = "01925db639fc974ce575b4013b48825ec1787b68"
URL_OBJETIVO = "https://site.fourvenues.com/en/discotecas-madrid/events/terraza-karau-17-07-2026-IUEV"

# Solicitamos la página a través de ZenRows de forma segura
proxies = {"http": f"http://{ZENROWS_API_KEY}@proxy.zenrows.com:8001"}
print("Conectando con el escudo de ZenRows...")

try:
    # Hacemos la petición (ZenRows se encarga de saltarse Cloudflare)
    response = requests.get(URL_OBJETIVO, proxies=proxies, verify=False, timeout=30)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- EXTRACCIÓN QUIRÚRGICA ---
        
        # 1. Extraer los datos estructurados principales (ld+json)
        script_json_ld = soup.find("script", type="application/ld+json")
        data_main = json.loads(script_json_ld.string) if script_json_ld else {}
        
        # 2. Extraer metatags para la descripción
        meta_desc = soup.find("meta", name="description")
        descripcion = meta_desc["content"] if meta_desc else "Sin descripción"
        
        # 3. Extraer vestimenta (viene dentro del megajson de Angular 'ng-state')
        # Buscamos la palabra "dressCode" de forma segura en el texto del script
        script_ng = soup.find("script", id="ng-state")
        vestimenta = "No especificado"
        if script_ng:
            if "dressCode\":\"arreglado\"" in script_ng.text or "Smart" in response.text:
                vestimenta = "Smart / Arreglado"
            elif "casual" in script_ng.text:
                vestimenta = "Casual"

        # Mapeamos todo a nuestro formato limpio para tu App
        evento_limpio = {
            "origen": "Fourvenues",
            "titulo": data_main.get("name", "No encontrado"),
            "imagen_alta_resolucion": data_main.get("image", "No encontrada"),
            "fecha_inicio": data_main.get("startDate", "").split("T")[0],
            "hora_apertura": data_main.get("startDate", "").split("T")[1][:5] if "T" in data_main.get("startDate", "") else "No encontrada",
            "hora_cierre": data_main.get("endDate", "").split("T")[1][:5] if "T" in data_main.get("endDate", "") else "No encontrada",
            "edad_minima": f"+{data_main.get('typicalAgeRange', '').replace('-', '')}" if data_main.get('typicalAgeRange') else "No especificada",
            "vestimenta": vestimenta,
            "localizacion": {
                "nombre_sala": data_main.get("location", {}).get("name", "No encontrado"),
                "direccion_completa": data_main.get("location", {}).get("address", {}).get("streetAddress", "No encontrada"),
                "coordenadas": {
                    "latitud": data_main.get("location", {}).get("geo", {}).get("latitude"),
                    "longitud": data_main.get("location", {}).get("geo", {}).get("longitude")
                }
            },
            "descripcion_comercial": descripcion
        }
        
        # Guardamos el resultado en el archivo json definitivo
        with open("evento.json", "w", encoding="utf-8") as archivo:
            json.dump(evento_limpio, archivo, indent=4, ensure_ascii=False)
            
        print("¡ÉXITO TOTAL! Los datos requeridos están en 'evento.json'.")
        print(json.dumps(evento_limpio, indent=2, ensure_ascii=False))

    else:
        print(f"Error en ZenRows. Código de estado: {response.status_code}")

except Exception as e:
    print(f"Error en el proceso de scraping: {e}")