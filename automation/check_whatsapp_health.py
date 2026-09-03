import requests
import os
import sys
import time
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    TZ_MADRID = ZoneInfo("Europe/Madrid")
except Exception:
    TZ_MADRID = None

# Cargar .env local si existe (para desarrollo sin exponer credenciales en git)
def _cargar_env_local():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v

_cargar_env_local()

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID") or "8769199362"

WHATSAPP_SERVER_URL = (os.getenv("WHATSAPP_SERVER_URL") or "").rstrip("/")
WHATSAPP_SESSION_ID = os.getenv("WHATSAPP_SESSION_ID")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY")

PANEL_URL = f"{WHATSAPP_SERVER_URL}/dashboard" if WHATSAPP_SERVER_URL else "Panel WhatsApp"


def enviar_telegram(mensaje: str):
    """Envía un mensaje directo a tu chat privado de Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_ADMIN_CHAT_ID:
        print("⚠️ [Telegram] Falta TELEGRAM_TOKEN o TELEGRAM_ADMIN_CHAT_ID para enviar notificación.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_ADMIN_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print(f"✅ Notificación enviada a Telegram privado ({TELEGRAM_ADMIN_CHAT_ID}).")
        else:
            print(f"❌ Error al enviar a Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción al enviar a Telegram: {e}")


def probar_motor_activo(session_id: str, headers: dict) -> bool:
    """Realiza una petición real al motor Chromium (Keep-Alive activo)."""
    url = f"{WHATSAPP_SERVER_URL}/api/sessions/{session_id}/chats?limit=1"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def intentar_auto_reinicio(session_id: str, headers: dict) -> bool:
    """Intenta auto-recuperar un Chromium congelado mediante ciclo stop -> start."""
    print(f"🔄 Intentando auto-recuperación de la sesión '{session_id}'...")
    try:
        requests.post(f"{WHATSAPP_SERVER_URL}/api/sessions/{session_id}/stop", headers=headers, timeout=10)
        time.sleep(3)
        start_resp = requests.post(f"{WHATSAPP_SERVER_URL}/api/sessions/{session_id}/start", headers=headers, timeout=15)
        if start_resp.status_code in (200, 201):
            time.sleep(5)
            return probar_motor_activo(session_id, headers)
    except Exception as e:
        print(f"⚠️ Fallo durante auto-reinicio: {e}")
    return False


def verificar_salud():
    hora_actual = datetime.now(TZ_MADRID).strftime("%H:%M:%S") if TZ_MADRID else datetime.now().strftime("%H:%M:%S")
    print(f"🔍 [{hora_actual} (Madrid)] Comprobando salud activa de WhatsApp en {WHATSAPP_SERVER_URL}...")
    
    url = f"{WHATSAPP_SERVER_URL}/api/sessions"
    headers = {"Content-Type": "application/json"}
    if WHATSAPP_API_KEY:
        headers["X-Api-Key"] = WHATSAPP_API_KEY

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except Exception as e:
        msg = (
            f"🚨 *ALERTA NEXT PLAN - SERVIDOR WHATSAPP INACCESIBLE*\n\n"
            f"❌ No se pudo conectar con `{WHATSAPP_SERVER_URL}`.\n"
            f"*Error de red:* `{e}`\n\n"
            f"🔗 *Panel:* {PANEL_URL}"
        )
        print(f"❌ Fallo de conexión: {e}")
        enviar_telegram(msg)
        sys.exit(1)

    if response.status_code != 200:
        msg = (
            f"🚨 *ALERTA NEXT PLAN - ERROR EN SERVIDOR WHATSAPP*\n\n"
            f"⚠️ El servidor respondió con código *{response.status_code}*.\n"
            f"*Detalle:* `{response.text}`\n\n"
            f"🔗 *Panel:* {PANEL_URL}"
        )
        print(f"❌ Error HTTP {response.status_code}: {response.text}")
        enviar_telegram(msg)
        sys.exit(1)

    try:
        sesiones = response.json()
    except Exception:
        sesiones = []

    if not sesiones:
        msg = (
            f"🚨 *ALERTA NEXT PLAN - NO HAY SESIONES ACTIVAS*\n\n"
            f"⚠️ No se encontró ninguna sesión configurada en el servidor.\n\n"
            f"📱 *Solución:* Entra al panel y crea la sesión `mingle`:\n"
            f"👉 {PANEL_URL}"
        )
        print("❌ No se encontraron sesiones.")
        enviar_telegram(msg)
        sys.exit(1)

    # Buscar la sesión objetivo
    sesion_objetivo = None
    for s in sesiones:
        if s.get("id") == WHATSAPP_SESSION_ID or s.get("name") in (WHATSAPP_SESSION_ID, "mingle"):
            sesion_objetivo = s
            break
    if not sesion_objetivo:
        sesion_objetivo = sesiones[0]

    sid = sesion_objetivo.get("id") or sesion_objetivo.get("name")
    nombre = sesion_objetivo.get("name", "desconocida")
    status = sesion_objetivo.get("status", "unknown")
    phone = sesion_objetivo.get("phone", "Sin número")

    print(f"ℹ️ Sesión detectada: {nombre} ({phone}) | Estado reportado: {status}")

    # 1. Si la sesión está reportada como ready, probamos el motor real
    if status == "ready":
        motor_responde = probar_motor_activo(sid, headers)
        if motor_responde:
            print("✅ Motor Chromium activo y respondiendo correctamente.")
            msg_ok = f"🟢 w-sync: {nombre} [ok] • {hora_actual}"
            enviar_telegram(msg_ok)
            sys.exit(0)
        else:
            print("⚠️ Sesión en 'ready' pero Chromium congelado. Probando auto-reinicio...")
            recuperado = intentar_auto_reinicio(sid, headers)
            if recuperado:
                msg_recuperado = f"🟡 w-sync: {nombre} [reboot ok] • {hora_actual}"
                print("✅ Sesión recuperada automáticamente.")
                enviar_telegram(msg_recuperado)
                sys.exit(0)

    # 2. Si el estado es fallido o no respondió al auto-reinicio
    msg_alerta = f"🔴 w-sync: {nombre} [{status}] • {hora_actual}\n{PANEL_URL}"
    print("❌ Sesión no operativa. Enviando alerta a Telegram.")
    enviar_telegram(msg_alerta)
    sys.exit(1)


if __name__ == "__main__":
    verificar_salud()
