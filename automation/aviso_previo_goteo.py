import json
import os
import sys
from datetime import datetime
import requests

try:
    from zoneinfo import ZoneInfo
    TZ_MADRID = ZoneInfo("Europe/Madrid")
except Exception:
    TZ_MADRID = None


def _cargar_env_local():
    """Carga el .env local si existe (desarrollo local sin exponer tokens en git)."""
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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

WHATSAPP_SERVER_URL = (os.getenv("WHATSAPP_SERVER_URL") or "").rstrip("/")
WHATSAPP_SESSION_ID = os.getenv("WHATSAPP_SESSION_ID")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY")

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, ".."))
DATABASE_FILE = os.path.join(root_dir, "data/base_de_datos_madrid.json")


def enviar_telegram(mensaje: str) -> bool:
    """Envía la alerta al chat privado del administrador de Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_ADMIN_CHAT_ID:
        print("⚠️ [Telegram] Falta TELEGRAM_TOKEN o TELEGRAM_ADMIN_CHAT_ID.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_ADMIN_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print(f"✅ Notificación enviada a Telegram privado ({TELEGRAM_ADMIN_CHAT_ID}).")
            return True
        else:
            print(f"❌ Error al enviar a Telegram: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Excepción al enviar a Telegram: {e}")
        return False


def comprobar_estado_whatsapp() -> tuple[str, str]:
    """Consulta rápidamente el estado de la sesión de WhatsApp en OpenWA."""
    if not WHATSAPP_SERVER_URL:
        return "desconocido", "Servidor no configurado"

    headers = {"Content-Type": "application/json"}
    if WHATSAPP_API_KEY:
        headers["X-Api-Key"] = WHATSAPP_API_KEY

    try:
        resp = requests.get(f"{WHATSAPP_SERVER_URL}/api/sessions", headers=headers, timeout=8)
        if resp.status_code != 200:
            return "error", f"HTTP {resp.status_code}"
        sesiones = resp.json()
        for s in sesiones:
            if s.get("name") == "mingle" and s.get("status") == "ready":
                return "ready", s.get("phone", "")
        for s in sesiones:
            if s.get("status") == "ready":
                return "ready", s.get("phone", "")
        if sesiones:
            s0 = sesiones[0]
            return s0.get("status", "unknown"), s0.get("name", "")
        return "sin_sesiones", "No hay sesiones creadas"
    except Exception as e:
        return "error_red", str(e)


def generar_y_enviar_aviso_previo():
    """Genera la lista con los nombres de eventos de hoy y la envía a Telegram."""
    hora_actual = datetime.now(TZ_MADRID).strftime("%H:%M") if TZ_MADRID else datetime.now().strftime("%H:%M")
    fecha_hoy = datetime.now(TZ_MADRID).strftime("%Y-%m-%d") if TZ_MADRID else datetime.now().strftime("%Y-%m-%d")

    print(f"🔍 [{hora_actual} Madrid] Generando previa de eventos para la fecha: {fecha_hoy}...")

    if not os.path.exists(DATABASE_FILE):
        msg_error = (
            f"⚠️ *PREVIA GOTEO DIARIO (13:00h)*\n\n"
            f"❌ No se encontró el archivo de base de datos en `{DATABASE_FILE}`."
        )
        print(f"❌ Base de datos no encontrada en: {DATABASE_FILE}")
        enviar_telegram(msg_error)
        return

    with open(DATABASE_FILE, "r", encoding="utf-8") as f:
        eventos = json.load(f)

    eventos_hoy = [e for e in eventos if e.get("fecha") == fecha_hoy]
    total = len(eventos_hoy)
    nombres = [e.get("titulo", "Sin título").strip() for e in eventos_hoy]

    # Comprobamos WhatsApp en paralelo
    wa_status, wa_info = comprobar_estado_whatsapp()
    if wa_status == "ready":
        wa_line = "🟢 *WhatsApp:* Sesión `mingle` activa y lista para el goteo."
    else:
        wa_line = f"⚠️ *WhatsApp:* Estado `{wa_status}` ({wa_info}). Revisa el panel antes de las 13:00h."

    if total > 0:
        lista_nombres = "\n".join(f"{i}. {n}" for i, n in enumerate(nombres, 1))
        mensaje = (
            f"📋 *PREVIA GOTEO DIARIO (13:00h)*\n\n"
            f"🎯 *Total eventos programados hoy:* {total}\n\n"
            f"{lista_nombres}\n\n"
            f"{wa_line}\n"
            f"⏰ *Inicio del goteo:* 13:00h (espaciado 15 min)."
        )
    else:
        mensaje = (
            f"📋 *PREVIA GOTEO DIARIO (13:00h)*\n\n"
            f"💤 *Hoy no hay eventos programados en cartelera para el goteo.*\n\n"
            f"{wa_line}"
        )

    print("\n--- MENSAJE PREVIA GENERADO ---")
    print(mensaje)
    print("--------------------------------\n")

    enviado = enviar_telegram(mensaje)
    if enviado:
        print("✅ Previa enviada con éxito al chat privado de Telegram.")
    else:
        print("ℹ️ Ejecución completada localmente (sin envío de red si no hay token).")


if __name__ == "__main__":
    generar_y_enviar_aviso_previo()
