import json
from datetime import datetime
import os

DATABASE_FILE = "base_de_datos_madrid.json"
OUTPUT_HTML = "index.html"

# Obtenemos la fecha de hoy para ocultar los eventos que ya han pasado
hoy = datetime.now().strftime("%Y-%m-%d")

print(f"🌐 Generando Linktree clon para la cartelera del día: {hoy}")

if not os.path.exists(DATABASE_FILE):
    print(f"❌ No se encuentra la base de datos {DATABASE_FILE}")
    exit()

with open(DATABASE_FILE, "r", encoding="utf-8") as f:
    eventos = json.load(f)

# Filtramos: Solo mostrar eventos de hoy en adelante
eventos_activos = [e for e in eventos if e.get("fecha") >= hoy]

# Construimos los botones dinámicamente
botones_html = ""
for e in eventos_activos:
    # Formateamos la fecha para que quede bonita en el botón (ej: 19 Jul)
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

# Estructura e IDÉNTICO DISEÑO a Linktree (Minimalista, premium y responsive)
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
            background: #0d0e12;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
            min-height: 100vh;
        }}
        .profile-container {{
            text-align: center;
            margin-bottom: 32px;
        }}
        .profile-pic {{
            width: 96px;
            height: 96px;
            border-radius: 50%;
            background: linear-gradient(45deg, #fe2c55, #25f4ee);
            padding: 3px;
            margin-bottom: 16px;
        }}
        .profile-pic img {{
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
            background: #000;
        }}
        h1 {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .bio {{
            font-size: 14px;
            color: #9ca3af;
            max-width: 600px;
        }}
        .links-wrapper {{
            width: 100%;
            max-width: 580px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .link-btn {{
            background: #1f2937;
            border: 1px solid #374151;
            border-radius: 30px;
            padding: 14px 24px;
            display: flex;
            align-items: center;
            text-decoration: none;
            color: white;
            transition: transform 0.2s, background-color 0.2s;
        }}
        .link-btn:hover {{
            transform: scale(1.02);
            background: #374151;
        }}
        .btn-emoji {{
            font-size: 24px;
            margin-right: 16px;
        }}
        .btn-text {{
            display: flex;
            flex-direction: column;
        }}
        .btn-title {{
            font-size: 16px;
            font-weight: 600;
        }}
        .btn-sub {{
            font-size: 12px;
            color: #9ca3af;
            margin-top: 2px;
        }}
    </style>
</head>
<body>
    <div class="profile-container">
        <div class="profile-pic">
            <!-- Puedes cambiar esta URL por el logo oficial de vuestra app -->
            <img src="https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=150" alt="NextPlan">
        </div>
        <h1>@nextplanevents</h1>
        <p class="bio">📍 Tu cartelera oficial de Madrid. Listas GRATIS, entradas y reservados VIP.</p>
    </div>

    <div class="links-wrapper">
        {botones_html}
    </div>
</body>
</html>
"""

# Guardamos el archivo HTML definitivo en la raíz del repositorio
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_completo)

print("🎯 ¡index.html generado con éxito listo para GitHub Pages!")