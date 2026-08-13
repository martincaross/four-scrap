import requests
from bs4 import BeautifulSoup
import urllib3
import os
import sys

# Silenciamos los avisos de certificado HTTPS
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")
zenrows_endpoint = "https://api.zenrows.com/v1/"

# Las URLs de tu landing pública (hoy y próximos eventos)
URLS_OBJETIVO = [
    "https://site.fourvenues.com/es/nextplan",
    "https://site.fourvenues.com/es/nextplan/events"
]
OUTPUT_FILE = "urls.txt"

print("🕵️‍♂️ Iniciando rastreador de carteleras doble...")

if not ZENROWS_API_KEY:
    print("❌ Error crítico: no se encontró la variable de entorno ZENROWS_API_KEY.")
    sys.exit(1)

# Instrucciones en JS nativo para que ZenRows busque el botón y lo pulse
js_instructions = """
[
    {"wait_for": "app-root"},
    {"evaluate": "const btn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Cargar más')); if(btn) btn.click();"},
    {"wait": 2500},
    {"evaluate": "const btn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Cargar más')); if(btn) btn.click();"},
    {"wait": 2500},
    {"evaluate": "const btn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Cargar más')); if(btn) btn.click();"},
    {"wait": 2500},
    {"evaluate": "const btn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Cargar más')); if(btn) btn.click();"},
    {"wait": 2000},
    {"evaluate": "const btn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Cargar más')); if(btn) btn.click();"},
    {"wait": 2000},
    {"evaluate": "const btn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Cargar más')); if(btn) btn.click();"},
    {"wait": 2000},
    {"evaluate": "const btn = [...document.querySelectorAll('button')].find(b => b.textContent.includes('Cargar más')); if(btn) btn.click();"},
    {"wait": 2000}
]
"""

enlaces_limpios = []

for url in URLS_OBJETIVO:
    print(f"\n🔍 Analizando objetivo: {url}")
    params = {
        "apikey": ZENROWS_API_KEY,
        "url": url,
        "js_render": "true",           # Abre el navegador virtual
        "premium_proxy": "true",       # IP residencial premium para camuflar el bot
        "js_instructions": js_instructions
    }

    try:
        print("⏳ Conectando con ZenRows (desplegando botones de la web)...")
        response = requests.get(zenrows_endpoint, params=params, verify=False, timeout=60)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Rastreamos todos los links de la página desplegada
            for tag in soup.find_all("a", href=True):
                href = tag['href']
                
                # Filtramos: Solo nos interesan links que tengan la estructura de un evento
                if "/events/" in href:
                    # Si el enlace es relativo (/es/nextplan/events/...), lo volvemos absoluto
                    if href.startswith("/"):
                        href = "https://www.fourvenues.com" + href
                    
                    if href not in enlaces_limpios:
                        enlaces_limpios.append(href)
        else:
            print(f"❌ Error en el servidor de ZenRows para {url}. Código: {response.status_code}")

    except Exception as e:
        print(f"💥 Error al procesar {url}: {e}")

if enlaces_limpios:
    # Guardamos los enlaces pisando lo que hubiera antes en urls.txt
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in enlaces_limpios:
            f.write(f"{url}\n")
    
    print(f"\n🎯 ¡MISION CUMPLIDA!")
    print(f"Se han descubierto {len(enlaces_limpios)} eventos activos en total.")
    print(f"Lista combinada actualizada guardada en: '{OUTPUT_FILE}'")
else:
    print("\n⚠️ El proxy no detectó enlaces de eventos en ninguna de las páginas.")
    try:
        with open("debug_landing.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Se ha generado 'debug_landing.html' con el último intento para revisar qué ha visto el bot.")
    except NameError:
        pass