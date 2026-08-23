import json
import requests
import os

WHATSAPP_SERVER_URL = os.getenv("WHATSAPP_SERVER_URL", "http://217.71.201.103:2785").rstrip("/")
WHATSAPP_SESSION_ID = os.getenv("WHATSAPP_SESSION_ID", "59d30296-ead4-4b08-bd20-02328dbff003")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "openwa_master_secret_key_prod_2026_abcdef123456")
WHATSAPP_CHAT_ID = os.getenv("WHATSAPP_CHAT_ID", "120363408786329052@g.us")

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, ".."))

DATABASE_FILE = os.path.join(root_dir, "data/base_de_datos_madrid.json")
TEMPLATE_FILE = os.path.join(script_dir, "templates/chat_template.txt")

with open(DATABASE_FILE, "r", encoding="utf-8") as f:
    eventos = json.load(f)

evento = eventos[0]

with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
    chat_tmpl = f.read()

msg_chat = chat_tmpl.format(
    titulo=evento.get('titulo', ''),
    descripcion=evento.get('descripcion', ''),
    hora=evento.get('hora', ''),
    edad=evento.get('edad', ''),
    vestimenta=evento.get('vestimenta', ''),
    sala=evento.get('sala', ''),
    link_compra_rrpp=evento.get('link_compra_rrpp', '')
)

url = f"{WHATSAPP_SERVER_URL}/api/sessions/{WHATSAPP_SESSION_ID}/messages/send-text"
headers = {"Content-Type": "application/json", "X-Api-Key": WHATSAPP_API_KEY}
payload = {"chatId": WHATSAPP_CHAT_ID, "text": msg_chat}

response = requests.post(url, json=payload, headers=headers, timeout=15)
print(f"Status: {response.status_code} - Response: {response.text}")
