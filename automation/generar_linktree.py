import json
from datetime import datetime
import os

DATABASE_FILE = "base_de_datos_madrid.json"
OUTPUT_HTML = "index.html"

# Obtenemos la fecha de hoy en formato AAAA-MM-DD
hoy = datetime.now().strftime("%Y-%m-%d")

print(f"🌐 Generando Linktree para los eventos exclusivos de hoy: {hoy}")

if not os.path.exists(DATABASE_FILE):
    print(f"❌ No se encuentra la base de datos {DATABASE_FILE}")
    exit()

with open(DATABASE_FILE, "r", encoding="utf-8") as f:
    eventos = json.load(f)

# 🚨 FILTRO CORREGIDO: Filtramos de forma estricta SOLO los eventos de HOY
eventos_hoy = [e for e in eventos if e.get("fecha") == hoy]

botones_html = ""

if not eventos_hoy:
    # Mensaje elegante por si un día no hay fiestas registradas hoy
    botones_html = """
    <div style="text-align: center; color: #9ca3af; padding: 20px; font-size: 15px;">
        💤 No hay eventos programados para el día de hoy. ¡Vuelve mañana para nuevos planazos!
    </div>
    """
else:
    for e in eventos_hoy:
        fecha_dt = datetime.strptime(e['fecha'], "%Y-%m-%d")
        fecha_bonita = fecha_dt.strftime("%d %b")
        
        botones_html += f"""
        <a href="{e['link_compra_rrpp']}" class="link-btn" target="_blank">
            <span class="btn-emoji">🎟️</span>
            <div class="btn-text">
                <span class="btn-title">{e['titulo']}</span>
                <span class="btn-sub">{e['sala']} • {fecha_bonita} ({e['hora']}h)</span>
            </div>
        </a>
        """

# CÓDIGO HTML + CSS CORREGIDO (Centrado estricto y Negro Puro)
html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NextPlan Events - Madrid</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        body {{
            background: #000000; /* 🔥 Negro más oscuro absoluto */
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
            min-height: 100vh;
        }}
        .profile-container {{
            display: flex;
            flex-direction: column;
            align-items: center; /* 🎯 Centrado horizontal de todo el bloque */
            text-align: center;
            margin-bottom: 32px;
            width: 100%;
        }}
        .profile-pic-wrapper {{
            width: 96px;
            height: 96px;
            border-radius: 50%;
            background: linear-gradient(45deg, #fe2c55, #25f4ee);
            padding: 3px;
            margin-bottom: 16px;
            display: flex;
            justify-content: center; /* 🎯 Centrado horizontal interno de la foto */
            align-items: center;     /* 🎯 Centrado vertical interno de la foto */
        }}
        .profile-pic-wrapper img {{
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
            background: #000000;
        }}
        h1 {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #ffffff;
        }}
        .bio {{
            font-size: 14px;
            color: #9ca3af;
            max-width: 400px;
            line-height: 1.4;
        }}
        .links-wrapper {{
            width: 100%;
            max-width: 580px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .link-btn {{
            background: #121214;
            border: 1px solid #27272a;
            border-radius: 30px;
            padding: 14px 24px;
            display: flex;
            align-items: center;
            text-decoration: none;
            color: white;
            transition: transform 0.2s, background-color 0.2s, border-color 0.2s;
        }}
        .link-btn:hover {{
            transform: scale(1.015);
            background: #18181b;
            border-color: #3f3f46;
        }}
        .btn-emoji {{
            font-size: 22px;
            margin-right: 16px;
        }}
        .btn-text {{
            display: flex;
            flex-direction: column;
            text-align: left;
        }}
        .btn-title {{
            font-size: 15px;
            font-weight: 600;
            color: #ffffff;
        }}
        .btn-sub {{
            font-size: 12px;
            color: #a1a1aa;
            margin-top: 3px;
        }}
    </style>
</head>
<body>
    <div class="profile-container">
        <div class="profile-pic-wrapper">
            <img src="https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=150" alt="NextPlan">
        </div>
        <h1>@nextplanevents</h1>
        <p class="bio">📍 Tu cartelera oficial de Madrid. Listas GRATIS, entradas y reservados VIP para el día de hoy.</p>
    </div>

    <div class="links-wrapper">
        {botones_html}
    </div>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_completo)

print("🎯 ¡index.html actualizado con diseño premium e idéntico a Linktree!")