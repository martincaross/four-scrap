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
    """Comprueba de forma no destructiva que el motor y la API responden correctamente."""
    try:
        # 1. Comprobar estado del motor en la sesión
        url_session = f"{WHATSAPP_SERVER_URL}/api/sessions/{session_id}"
        resp_session = requests.get(url_session, headers=headers, timeout=10)
        if resp_session.status_code != 200:
            return False
        data = resp_session.json()
        if data.get("status") != "ready" or not data.get("engineLoaded"):
            return False

        # 2. Comprobar que la capa de mensajes responde
        url_msgs = f"{WHATSAPP_SERVER_URL}/api/sessions/{session_id}/messages?limit=1"
        resp_msgs = requests.get(url_msgs, headers=headers, timeout=10)
        return resp_msgs.status_code == 200
    except Exception as e:
        print(f"⚠️ Excepción en probe de motor: {e}")
        return False


def intentar_auto_arranque(session_id: str, headers: dict) -> bool:
    """Intenta arrancar limpiamente una sesión detenida o desconectada (p. ej. tras reinicio del VPS)."""
    print(f"🔄 Intentando arranque limpio de la sesión '{session_id}'...")
    try:
        start_resp = requests.post(f"{WHATSAPP_SERVER_URL}/api/sessions/{session_id}/start", headers=headers, timeout=25)
        if start_resp.status_code in (200, 201):
            time.sleep(5)
            return probar_motor_activo(session_id, headers)
    except Exception as e:
        print(f"⚠️ Fallo durante auto-arranque: {e}")
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

    # 1. Resolución dinámica robusta de la sesión objetivo (prioriza nombre 'mingle')
    sesion_objetivo = None
    for s in sesiones:
        if s.get("name") == "mingle" and s.get("status") == "ready":
            sesion_objetivo = s
            break
    if not sesion_objetivo:
        for s in sesiones:
            if s.get("name") == "mingle":
                sesion_objetivo = s
                break
    if not sesion_objetivo:
        for s in sesiones:
            if s.get("id") == WHATSAPP_SESSION_ID:
                sesion_objetivo = s
                break
    if not sesion_objetivo:
        for s in sesiones:
            if s.get("status") == "ready":
                sesion_objetivo = s
                break
    if not sesion_objetivo:
        sesion_objetivo = sesiones[0]

    sid = sesion_objetivo.get("id")
    nombre = sesion_objetivo.get("name", "desconocida")
    status = sesion_objetivo.get("status", "unknown")
    phone = sesion_objetivo.get("phone", "Sin número")

    print(f"ℹ️ Sesión detectada: {nombre} ({sid}) ({phone}) | Estado reportado: {status}")

    # 2. Si la sesión está en 'ready', validamos que el motor responda
    if status == "ready":
        if probar_motor_activo(sid, headers):
            print("✅ Motor Chromium activo y respondiendo correctamente.")
            msg_ok = f"🟢 w-sync: {nombre} [ok] • {hora_actual}"
            enviar_telegram(msg_ok)
            sys.exit(0)
        else:
            print("⚠️ Sesión reportada en 'ready' pero no respondió a las pruebas.")

    # 3. Si la sesión está detenida o desconectada (ej. tras reinicio VPS), auto-arrancamos limpiamente
    if status in ("stopped", "disconnected"):
        print(f"ℹ️ Sesión '{nombre}' en estado '{status}'. Intentando auto-arranque pasivo...")
        if intentar_auto_arranque(sid, headers):
            msg_recuperado = f"🟡 w-sync: {nombre} [auto-start ok] • {hora_actual}"
            print("✅ Sesión auto-arrancada con éxito sin intervención manual.")
            enviar_telegram(msg_recuperado)
            sys.exit(0)

    # 4. Si el estado es qr_ready, failed o no arrancó, avisamos con enlace al panel
    msg_alerta = f"🔴 w-sync: {nombre} [{status}] • {hora_actual}\n{PANEL_URL}"
    print(f"❌ Sesión no operativa [{status}]. Enviando alerta a Telegram.")
    enviar_telegram(msg_alerta)
    sys.exit(1)


if __name__ == "__main__":
    verificar_salud()
