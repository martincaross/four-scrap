import requests
from bs4 import BeautifulSoup
import json
import re

# URL específica del evento Terraza Karau (17-07-2026)
url = "https://site.fourvenues.com/en/discotecas-madrid/events/terraza-karau-17-07-2026-IUEV"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Iniciando la extracción de datos...")
response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 1. Extraer datos de los Metatags nativos (Título e Imagen base)
    meta_title = soup.find("meta", property="og:title")
    meta_image = soup.find("meta", property="og:image")
    meta_desc = soup.find("meta", property="og:description")
    
    titulo = meta_title["content"] if meta_title else "No encontrado"
    imagen_url = meta_image["content"] if meta_image else "No encontrada"
    descripcion = meta_desc["content"] if meta_desc else ""
    
    # 2. Buscar imágenes de alta resolución (w=1350) en el código fuente
    # Buscamos en todas las etiquetas <img> o textos que contengan la firma w=1350
    imagenes_encontradas = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "w=1350" in src:
            imagenes_encontradas.append(src)
            
    # Si encontramos la de alta resolución, usamos esa como prioritaria
    if imagenes_encontradas:
        imagen_url = imagenes_encontradas[0]

    # 3. Extraer Hora y Edad mediante búsquedas inteligentes en el texto estructurado
    # (Fourvenues suele poner la edad como "+18", "Edad: +18" o en la descripción)
    texto_pagina = soup.get_text()
    
    # Regex para buscar formatos de hora comunes (Ej: 23:00, 18:30, 20:00)
    horas = re.findall(r'\b\d{2}:\d{2}\b', texto_pagina)
    hora_evento = horas[0] if horas else "Verificar en link (No detectada)"
    
    # Regex para buscar restricciones de edad comunes (+18, +21, >18)
    edad_match = re.search(r'(?:\+|>|Edad\s*:\s*\+?)\s*(18|21|16)', texto_pagina, re.IGNORECASE)
    edad_minima = f"+{edad_match.group(1)}" if edad_match else "No especificada (revisar descripción)"

    # Estructuramos el archivo JSON final
    datos_evento = {
        "origen": "Fourvenues",
        "url_fuente": url,
        "titulo": titulo,
        "hora": hora_evento,
        "edad_minima": edad_minima,
        "imagen_optimizada": imagen_url,
        "detalles_adicionales": descripcion.strip()
    }
    
    # Guardamos los resultados en un archivo físico de texto JSON
    with open("evento.json", "w", encoding="utf-8") as archivo:
        json.dump(datos_evento, archivo, indent=4, ensure_ascii=False)
        
    print("¡Extracción completada con éxito! Archivo 'evento.json' generado.")
else:
    print(f"Error crítico al acceder a la web. Estado: {response.status_code}")