import requests
from bs4 import BeautifulSoup
import urllib3
import os

# Silenciamos los avisos de certificado HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
zenrows_endpoint = "https://api.zenrows.com/v1/"

# La URL de tu landing pública con todas tus promotoras de Madrid
URL_GENERAL = "https://site.fourvenues.com/es/nextplan/events"
OUTPUT_FILE = "urls.txt"

print("🕵️‍♂️ Iniciando rastreador de carteleras...")
print(f"Objetivo: {URL_GENERAL}")

# Instrucciones en JS nativo para que ZenRows busque el botón y lo pulse
# Hacemos 2 intentos de clic separados por esperas para desplegar todo el mapa de fiestas
js_instructions = """
[
    {"wait_for": "app-root"},
    {"evaluate": "const btn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Cargar más')); if(btn) btn.click();"},
    {"wait": 3000},
    {"evaluate": "const btn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Cargar más')); if(btn) btn.click();"},
    {"wait": 2000}
]
"""

params = {
    "apikey": ZENROWS_API_KEY,
    "url": URL_GENERAL,
    "js_render": "true",           # Abre el navegador virtual
    "premium_proxy": "true",       # IP residencial premium para camuflar el bot
    "js_instructions": js_instructions
}

try:
    print("⏳ Conectando con ZenRows (desplegando botones de la web)...")
    response = requests.get(zenrows_endpoint, params=params, verify=False, timeout=60)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        enlaces_limpios = []
        
        # Rastreamos todos los links de la página desplegada
        for tag in soup.find_all("a", href=True):
            href = tag['href']
            
            # Filtramos: Solo nos interesan links que tengan la estructura de un evento
            if "/events/" in href and href not in enlaces_limpios:
                # Si el enlace es relativo (/es/nextplan/events/...), lo volvemos absoluto
                if href.startswith("/"):
                    href = "https://www.fourvenues.com" + href
                enlaces_limpios.append(href)
        
        if enlaces_limpios:
            # Guardamos los enlaces pisando lo que hubiera antes en urls.txt
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                for url in enlaces_limpios:
                    f.write(f"{url}\n")
            
            print(f"\n🎯 ¡MISION CUMPLIDA!")
            print(f"Se han descubierto {len(enlaces_limpios)} eventos activos de tus promotoras.")
            print(f"Lista actualizada guardada en: '{OUTPUT_FILE}'")
        else:
            print("⚠️ El proxy entró a la web pero no detectó enlaces de eventos en el HTML.")
            # Guardamos un archivo de debug por si acaso
            with open("debug_landing.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Se ha generado 'debug_landing.html' para revisar qué ha visto el bot.")

    else:
        print(f"❌ Error en el servidor de ZenRows. Código: {response.status_code}")

except Exception as e:
    print(f"💥 Error crítico en el proceso: {e}")