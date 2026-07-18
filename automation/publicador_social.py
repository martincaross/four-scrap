import json
import requests
from datetime import datetime, timedelta
import os
import time

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID_SOCIAL = os.getenv("TELEGRAM_CHAT_ID_SOCIAL") 
DATABASE_FILE = "base_de_datos_madrid.json"
MINUTOS_ESPACIADO = float(os.getenv("MINUTOS_ESPACIADO", 0))

fecha_objetivo = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
print(f"📆 [SOCIAL] Buscando eventos para: {fecha_objetivo}")

with open(DATABASE_FILE, "r", encoding="utf-8") as f:
    eventos = json.load(f)

eventos_filtrados = [e for e in eventos if e.get("fecha") == fecha_objetivo]

if not eventos_filtrados:
    print("💤 No hay eventos para el grupo de redes hoy.")
    exit()

with open("automation/templates/social_template.txt", "r", encoding="utf-8") as f:
    social_tmpl = f.read()

for index, evento in enumerate(eventos_filtrados):
    if index > 0 and MINUTOS_ESPACIADO > 0:
        print(f"⏳ Esperando {MINUTOS_ESPACIADO} minutos para las redes...")
        time.sleep(MINUTOS_ESPACIADO * 60)
        
    sala_clean = evento['sala'].replace(" ", "").replace("'", "").replace("|", "")
    
    msg_social = social_tmpl.format(
        titulo=evento['titulo'], descripcion=evento['descripcion'],
        hora=evento['hora'], edad=evento['edad'], vestimenta=evento['vestimenta'],
        sala=evento['sala'], sala_clean=sala_clean
    )
    
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(telegram_url, json={
        "chat_id": TELEGRAM_CHAT_ID_SOCIAL,
        "text": f"📸 *PACK INSTAGRAM / TIKTOK*\n\n{msg_social}\n\n🔗 *Descargar Flyer:* {evento['imagen']}",
        "parse_mode": "Markdown"
    })
    
    # CONTROL DE ERRORES REAL
    if response.status_code == 200:
        print(f"✅ Enviado pack de redes para: {evento['titulo']}")
    else:
        print(f"❌ Error en Telegram para {evento['titulo']}. Código: {response.status_code}. Respuesta: {response.text}")