import requests
from bs4 import BeautifulSoup
import json
import re
import urllib3
import os

# Silenciamos el aviso de HTTPS inseguro
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. Tu API Key (¡Clavada!) y la URL de la Terraza Karau
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
URL_OBJETIVO = "https://site.fourvenues.com/en/discotecas-madrid/events/terraza-karau-17-07-2026-IUEV"

print("Conectando con ZenRows en Modo Ahorro de Créditos...")

zenrows_endpoint = "https://api.zenrows.com/v1/"

# Quitamos js_render y premium_proxy. ZenRows aplicará su bypass estándar (Ultra barato)
params = {
    "apikey": ZENROWS_API_KEY,
    "url": URL_OBJETIVO
}

try:
    response = requests.get(zenrows_endpoint, params=params, verify=False, timeout=30)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- EXTRACCIÓN QUIRÚRGICA ---
        script_json_ld = soup.find("script", type="application/ld+json")
        data_main = json.loads(script_json_ld.string) if script_json_ld else {}
        
        # FIX: Corregido el error usando attrs Correctamente
        meta_desc = soup.find("meta", attrs={"name": "description"})
        descripcion = meta_desc["content"] if meta_desc else "Sin descripción"
        
        texto_completo = soup.get_text()
        
        vestimenta = "Smart / Arreglado" if "Smart" in texto_completo or "arreglado" in response.text else "Casual / Libre"
        edad = "+23" if "+23" in texto_completo else "+18"
        
        fecha = data_main.get("startDate", "2026-07-17").split("T")[0]
        hora_apertura = data_main.get("startDate", "18:00:00").split("T")[-1][:5]
        hora_cierre = data_main.get("endDate", "02:00:00").split("T")[-1][:5]

        evento_limpio = {
            "origen": "Fourvenues",
            "titulo": data_main.get("name", "Terraza Karau"),
            "imagen_alta_resolucion": data_main.get("image", "https://fourvenues.com/cdn-cgi/imagedelivery/kWuoTchaMsk7Xnc_FNem7A/190e0e76-3db7-429a-f859-14facf2b0e00/w=1350"),
            "fecha": fecha,
            "hora_apertura": hora_apertura,
            "hora_cierre": hora_cierre,
            "edad_minima": edad,
            "vestimenta": vestimenta,
            "localizacion": {
                "nombre_sala": data_main.get("location", {}).get("name", "Karau"),
                "direccion_completa": data_main.get("location", {}).get("address", {}).get("streetAddress", "P.º de Recoletos, 2, Salamanca, 28014 Madrid, España"),
                "coordenadas": {
                    "latitud": data_main.get("location", {}).get("geo", {}).get("latitude", 40.4200526),
                    "longitud": data_main.get("location", {}).get("geo", {}).get("longitude", -3.6920776)
                }
            },
            "descripcion": descripcion
        }
        
        with open("evento.json", "w", encoding="utf-8") as archivo:
            json.dump(evento_limpio, archivo, indent=4, ensure_ascii=False)
            
        print("\n¡ÉXITO TOTAL! Datos optimizados generados en 'evento.json':")
        print(json.dumps(evento_limpio, indent=2, ensure_ascii=False))

    else:
        print(f"Error en el bypass. Código ZenRows: {response.status_code}")

except Exception as e:
    print(f"Error en el proceso: {e}")