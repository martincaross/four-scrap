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
OUTPUT_FILE = "data/urls.txt"

print("🕵️‍♂️ Iniciando rastreador de carteleras doble...")

if not ZENROWS_API_KEY:
    print("❌ Error crítico: no se encontró la variable de entorno ZENROWS_API_KEY.")
    sys.exit(1)

# Instrucciones en JS nativo para que ZenRows busque el botón y lo pulse
js_instructions = """
[
    {"wait_for": "a[href*='/events/']"},
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

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configurar reintentos
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[ 500, 502, 503, 504 ])
session.mount('https://', HTTPAdapter(max_retries=retries))

enlaces_limpios = []
fallos_detectados = False

for url in URLS_OBJETIVO:
    print(f"\n🔍 Analizando objetivo: {url}")
    params = {
        "apikey": ZENROWS_API_KEY,
        "url": url,
        "js_render": "true",
        "premium_proxy": "true",
        "js_instructions": js_instructions
    }

    try:
        print("⏳ Conectando con ZenRows (desplegando botones de la web)...")
        # Aumentamos el timeout a 120s para prevenir cortes abruptos
        response = session.get(zenrows_endpoint, params=params, verify=False, timeout=120)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            enlaces_nuevos_pagina = 0
            for tag in soup.find_all("a", href=True):
                href = tag['href']
                if "/events/" in href:
                    if href.startswith("/"):
                        href = "https://www.fourvenues.com" + href
                    if href not in enlaces_limpios:
                        enlaces_limpios.append(href)
                        enlaces_nuevos_pagina += 1
            print(f"   ↳ {enlaces_nuevos_pagina} nuevos enlaces extraídos de esta página.")
        else:
            print(f"❌ Error en el servidor de ZenRows para {url}. Código: {response.status_code}")
            fallos_detectados = True

    except Exception as e:
        print(f"💥 Error al procesar {url}: {e}")
        fallos_detectados = True

if fallos_detectados:
    print("⚠️ Hubo fallos en al menos una página. Creando flag de scrapeo parcial.")
    with open("depuracion/PARTIAL_SCRAPE.flag", "w") as f:
        f.write("partial")

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
        with open("depuracion/debug_landing.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Se ha generado 'debug_landing.html' con el último intento para revisar qué ha visto el bot.")
    except NameError:
        pass
    
    # Si no obtuvimos absolutamente nada, salimos con error para detener las actions
    sys.exit(1)