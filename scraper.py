from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import re

url = "https://site.fourvenues.com/en/discotecas-madrid/events/terraza-karau-17-07-2026-IUEV"

print("Iniciando extracción avanzada imitando a Google Chrome...")

try:
    # 'impersonate="chrome"' clona la huella TLS exacta de un Chrome real
    response = requests.get(url, impersonate="chrome", timeout=15)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Extraer datos de los Metatags nativos
        meta_title = soup.find("meta", property="og:title")
        meta_image = soup.find("meta", property="og:image")
        meta_desc = soup.find("meta", property="og:description")
        
        titulo = meta_title["content"] if meta_title else "No encontrado"
        imagen_url = meta_image["content"] if meta_image else "No encontrada"
        descripcion = meta_desc["content"] if meta_desc else ""
        
        # 2. Buscar imágenes de alta resolución (w=1350)
        imagenes_encontradas = []
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if "w=1350" in src:
                imagenes_encontradas.append(src)
                
        if imagenes_encontradas:
            imagen_url = imagenes_encontradas[0]

        # 3. Extraer Hora y Edad en el texto
        texto_pagina = soup.get_text()
        
        horas = re.findall(r'\b\d{2}:\d{2}\b', texto_pagina)
        hora_evento = horas[0] if horas else "Verificar en link"
        
        edad_match = re.search(r'(?:\+|>|Edad\s*:\s*\+?)\s*(18|21|16)', texto_pagina, re.IGNORECASE)
        edad_minima = f"+{edad_match.group(1)}" if edad_match else "+18"

        datos_evento = {
            "origen": "Fourvenues",
            "url_fuente": url,
            "titulo": titulo,
            "hora": hora_evento,
            "edad_minima": edad_minima,
            "imagen_optimizada": imagen_url,
            "detalles_adicionales": descripcion.strip()
        }
        
        with open("evento.json", "w", encoding="utf-8") as archivo:
            json.dump(datos_evento, archivo, indent=4, ensure_ascii=False)
            
        print("¡Extracción completada con éxito! Archivo 'evento.json' generado.")
        
    else:
        print(f"Error crítico. Estado: {response.status_code}")
        print("Si sigue dando 403, Cloudflare está bloqueando el rango de IPs de GitHub por completo.")

except Exception as e:
    print(f"Ocurrió un error en la petición: {e}")