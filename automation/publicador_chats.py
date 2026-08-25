import json
import requests
from datetime import datetime
import os
import time
import sys

# ==========================================
# CONFIGURACIÓN
# ==========================================

# Telegram (Intacto tal cual funcionaba)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID_CHATS = os.getenv("TELEGRAM_CHAT_ID_CHATS")
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "true").lower() in ("true", "1", "yes")

# WhatsApp Server (OpenWA Gateway en VPS)
WHATSAPP_SERVER_URL = os.getenv("WHATSAPP_SERVER_URL", "http://217.71.201.103:2785").rstrip("/")
WHATSAPP_SESSION_ID = os.getenv("WHATSAPP_SESSION_ID", "661a38c3-9b18-4c12-99c1-4ac3c13e3439")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "openwa_master_secret_key_prod_2026_abcdef123456")
# Grupo: Next Night Plan 🌙
WHATSAPP_CHAT_ID_CHATS = os.getenv("WHATSAPP_CHAT_ID_CHATS", "120363408786329052@g.us")
WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "true").lower() in ("true", "1", "yes")

# Rutas y tiempos
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, ".."))

DATABASE_FILE = os.path.join(root_dir, "data/base_de_datos_madrid.json")
TEMPLATE_FILE = os.path.join(script_dir, "templates/chat_template.txt")

# Espaciado configurable en segundos o minutos
if os.getenv("ESPACIADO_SEGUNDOS") is not None:
    SEGUNDOS_ESPACIADO = float(os.getenv("ESPACIADO_SEGUNDOS"))
else:
    SEGUNDOS_ESPACIADO = float(os.getenv("MINUTOS_ESPACIADO", 0)) * 60


# ==========================================
# FUNCIONES DE ENVÍO
# ==========================================

def enviar_telegram(msg_chat: str, evento_titulo: str) -> bool:
    """Envía el mensaje exacto a Telegram con la configuración original intacta."""
    if not TELEGRAM_ENABLED:
        return False

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID_CHATS:
        print(f"⚠️ [Telegram] Omitido para '{evento_titulo}': falta TELEGRAM_TOKEN o TELEGRAM_CHAT_ID_CHATS")
        return False
    
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID_CHATS,
        "text": msg_chat,  # 👈 Solo enviamos la plantilla limpia
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(telegram_url, json=payload, timeout=15)
        if response.status_code == 200:
            print(f"✅ [Telegram] Enviado pack de chat para: {evento_titulo}")
            return True
        else:
            print(f"❌ Error en Telegram para {evento_titulo}. Código: {response.status_code}. Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Excepción en Telegram para {evento_titulo}: {e}")
        return False


def obtener_sesion_activa_id() -> str:
    """Resuelve dinámicamente el ID de la sesión activa de OpenWA."""
    try:
        headers = {"X-Api-Key": WHATSAPP_API_KEY} if WHATSAPP_API_KEY else {}
        resp = requests.get(f"{WHATSAPP_SERVER_URL}/api/sessions", headers=headers, timeout=5)
        if resp.status_code == 200:
            sesiones = resp.json()
            for s in sesiones:
                if s.get("id") == WHATSAPP_SESSION_ID or s.get("name") in (WHATSAPP_SESSION_ID, "mingle"):
                    if s.get("status") == "ready":
                        return s.get("id") or s.get("name")
            for s in sesiones:
                if s.get("status") == "ready":
                    return s.get("id") or s.get("name")
    except Exception:
        pass
    return WHATSAPP_SESSION_ID

SESSION_ACTIVA_ID = obtener_sesion_activa_id()


def enviar_whatsapp(msg_chat: str, evento_titulo: str) -> bool:
    """Envía el mensaje al grupo de WhatsApp (Next Night Plan 🌙) a través de OpenWA."""
    if not WHATSAPP_ENABLED:
        return False
        
    if not WHATSAPP_CHAT_ID_CHATS:
        print(f"⚠️ [WhatsApp] Omitido para '{evento_titulo}': falta WHATSAPP_CHAT_ID_CHATS")
        return False

    url = f"{WHATSAPP_SERVER_URL}/api/sessions/{SESSION_ACTIVA_ID}/messages/send-text"
    headers = {"Content-Type": "application/json"}
    if WHATSAPP_API_KEY:
        headers["X-Api-Key"] = WHATSAPP_API_KEY
        
    payload = {
        "chatId": WHATSAPP_CHAT_ID_CHATS,
        "text": msg_chat,
        "linkPreview": False
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code in (200, 201):
            print(f"✅ [WhatsApp] Enviado a grupo 'Next Night Plan 🌙' para: {evento_titulo}")
            return True
        else:
            print(f"❌ Error en WhatsApp para {evento_titulo}. Código: {response.status_code}. Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Excepción en WhatsApp para {evento_titulo}: {e}")
        return False


# ==========================================
# FLUJO PRINCIPAL
# ==========================================

fecha_objetivo = datetime.now().strftime("%Y-%m-%d")
print(f"📆 [CHATS] Buscando eventos para: {fecha_objetivo}")

if not os.path.exists(DATABASE_FILE):
    print(f"❌ No se encontró el archivo de base de datos en: {DATABASE_FILE}")
    sys.exit(1)

with open(DATABASE_FILE, "r", encoding="utf-8") as f:
    eventos = json.load(f)

eventos_filtrados = [e for e in eventos if e.get("fecha") == fecha_objetivo]

if not eventos_filtrados:
    print("💤 No hay eventos para el grupo de chats hoy.")
    sys.exit(0)

if not os.path.exists(TEMPLATE_FILE):
    print(f"❌ No se encontró la plantilla de chat en: {TEMPLATE_FILE}")
    sys.exit(1)

with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
    chat_tmpl = f.read()

print(f"🎯 Total eventos encontrados para hoy: {len(eventos_filtrados)}")

for index, evento in enumerate(eventos_filtrados):
    if index > 0 and SEGUNDOS_ESPACIADO > 0:
        print(f"⏳ Esperando {int(SEGUNDOS_ESPACIADO)} segundos para el siguiente chat...")
        time.sleep(SEGUNDOS_ESPACIADO)
        
    # Formateamos el mensaje directo sin cabeceras añadidas (exactamente igual que antes)
    msg_chat = chat_tmpl.format(
        titulo=evento.get('titulo', ''),
        descripcion=evento.get('descripcion', ''),
        hora=evento.get('hora', ''),
        edad=evento.get('edad', ''),
        vestimenta=evento.get('vestimenta', ''),
        sala=evento.get('sala', ''),
        link_compra_rrpp=evento.get('link_compra_rrpp', '')
    )
    
    titulo_evento = evento.get('titulo', 'Sin título')
    
    # 1. Enviar a Telegram (mismo payload, headers y formato)
    enviar_telegram(msg_chat, titulo_evento)
    
    # 2. Enviar a WhatsApp
    enviar_whatsapp(msg_chat, titulo_evento)