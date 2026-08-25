import requests
import os
import sys

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8769199362")

WHATSAPP_SERVER_URL = os.getenv("WHATSAPP_SERVER_URL", "http://217.71.201.103:2785").rstrip("/")
WHATSAPP_SESSION_ID = os.getenv("WHATSAPP_SESSION_ID", "661a38c3-9b18-4c12-99c1-4ac3c13e3439")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "openwa_master_secret_key_prod_2026_abcdef123456")

PANEL_URL = f"{WHATSAPP_SERVER_URL}/sessions"


def enviar_alerta_telegram(mensaje: str):
    """Envía la alerta directa a tu chat privado de Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_ADMIN_CHAT_ID:
        print("⚠️ [Alerta] Falta TELEGRAM_TOKEN o TELEGRAM_ADMIN_CHAT_ID para enviar notificación.")
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
            print(f"✅ Alerta enviada a Telegram privado ({TELEGRAM_ADMIN_CHAT_ID}) con éxito.")
        else:
            print(f"❌ Error al enviar alerta a Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción al enviar alerta a Telegram: {e}")


def verificar_salud():
    print(f"🔍 Comprobando sesiones en {WHATSAPP_SERVER_URL}...")
    url = f"{WHATSAPP_SERVER_URL}/api/sessions"
    headers = {}
    if WHATSAPP_API_KEY:
        headers["X-Api-Key"] = WHATSAPP_API_KEY

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except Exception as e:
        msg = (
            f"🚨 *ALERTA NEXT PLAN - SERVIDOR WHATSAPP INACCESIBLE*\n\n"
            f"❌ No se pudo conectar al servidor de OpenWA en `{WHATSAPP_SERVER_URL}`.\n"
            f"*Error de red:* `{e}`\n\n"
            f"🔗 *Panel:* {PANEL_URL}"
        )
        print(f"❌ Fallo de conexión: {e}")
        enviar_alerta_telegram(msg)
        sys.exit(1)

    if response.status_code != 200:
        msg = (
            f"🚨 *ALERTA NEXT PLAN - ERROR EN SERVIDOR WHATSAPP*\n\n"
            f"⚠️ El endpoint de sesiones respondió con código *{response.status_code}*.\n"
            f"*Detalle:* `{response.text}`\n\n"
            f"🔗 *Accede al panel para revisarla:* {PANEL_URL}"
        )
        print(f"❌ Error al consultar sesiones: {response.status_code} - {response.text}")
        enviar_alerta_telegram(msg)
        sys.exit(1)

    try:
        sesiones = response.json()
    except Exception:
        sesiones = []

    if not sesiones:
        msg = (
            f"🚨 *ALERTA NEXT PLAN - NO HAY SESIONES ACTIVAS*\n\n"
            f"⚠️ No se encontró ninguna sesión configurada en el servidor de WhatsApp.\n\n"
            f"📱 *Solución:* Entra al panel y crea/inicia una sesión:\n"
            f"👉 {PANEL_URL}"
        )
        print("❌ No se encontraron sesiones.")
        enviar_alerta_telegram(msg)
        sys.exit(1)

    # Buscamos la sesión objetivo por ID o por nombre ("mingle")
    sesion_objetivo = None
    for s in sesiones:
        if s.get("id") == WHATSAPP_SESSION_ID or s.get("name") in (WHATSAPP_SESSION_ID, "mingle"):
            sesion_objetivo = s
            break
    
    # Si no coincide exactamente, tomamos la primera sesión disponible
    if not sesion_objetivo:
        sesion_objetivo = sesiones[0]

    nombre = sesion_objetivo.get("name", "desconocida")
    status = sesion_objetivo.get("status", "unknown")
    engine_loaded = sesion_objetivo.get("engineLoaded", False)
    phone = sesion_objetivo.get("phone", "Sin número")

    print(f"ℹ️ Sesión: {nombre} ({phone}) | Estado: {status} | Motor cargado: {engine_loaded}")

    if status == "ready" and engine_loaded:
        print("✅ Sesión de WhatsApp activa, saludable y lista para el goteo de hoy.")
        sys.exit(0)
    else:
        msg = (
            f"🚨 *ALERTA NEXT PLAN - WHATSAPP DESCONECTADO*\n\n"
            f"⚠️ La sesión *{nombre}* no está lista para los envíos de hoy.\n"
            f"📊 *Estado actual:* `{status}` (Motor: `{engine_loaded}`)\n\n"
            f"📱 *Solución rápida desde tu móvil:*\n"
            f"1. Abre el panel: {PANEL_URL}\n"
            f"2. Si está en *Iniciando/Bloqueada*, pulsa *Detener* y luego *Iniciar*.\n"
            f"3. Si pide código QR, vuelve a escanearlo."
        )
        enviar_alerta_telegram(msg)
        sys.exit(1)


if __name__ == "__main__":
    verificar_salud()
