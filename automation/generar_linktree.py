import json
from datetime import datetime, timedelta
import os

DATABASE_FILE = "base_de_datos_madrid.json"
OUTPUT_HTML = "index.html"

hoy_dt = datetime.now()
hoy_str = hoy_dt.strftime("%Y-%m-%d")

print(f"🌐 Generando Linktree interactivo con selector a partir de hoy: {hoy_str}")

if not os.path.exists(DATABASE_FILE):
    print(f"❌ No se encuentra la base de datos {DATABASE_FILE}")
    exit()

with open(DATABASE_FILE, "r", encoding="utf-8") as f:
    eventos = json.load(f)

# 1. Filtramos solo eventos de HOY en adelante
eventos_futuros = [e for e in eventos if e.get("fecha") >= hoy_str]

# 2. Obtenemos las fechas únicas ordenadas
fechas_unicas = sorted(list(set(e.get("fecha") for e in eventos_futuros)))

# 3. Generamos los botones de las pestañas (Tabs)
tabs_html = ""
for idx, fecha in enumerate(fechas_unicas):
    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    
    # Etiqueta amigable para la pestaña
    if fecha == hoy_str:
        label = "🔥 Hoy"
    elif fecha == (hoy_dt + timedelta(days=1)).strftime("%Y-%m-%d"):
        label = "🚀 Mañana"
    else:
        label = fecha_dt.strftime("%d %b")
        
    active_class = "active" if idx == 0 else ""
    tabs_html += f'<button class="tab-btn {active_class}" onclick="filterDate(\'{fecha}\', this)">{label}</button>\n'

# 4. Generamos las tarjetas de eventos
cards_html = ""
if not eventos_futuros:
    cards_html = '<div class="no-events">💤 No hay eventos próximos programados.</div>'
else:
    for e in eventos_futuros:
        fecha_dt = datetime.strptime(e['fecha'], "%Y-%m-%d")
        fecha_bonita = fecha_dt.strftime("%d %b")
        fecha_event = e['fecha']
        
        # Por defecto solo se muestran las de la primera fecha (Hoy)
        display_style = "flex" if fecha_event == fechas_unicas[0] else "none"
        
        cards_html += f"""
        <a href="{e['link_compra_rrpp']}" class="link-btn event-card" data-date="{fecha_event}" style="display: {display_style};" target="_blank">
            <span class="btn-emoji">🎟️</span>
            <div class="btn-text">
                <span class="btn-title">{e['titulo']}</span>
                <span class="btn-sub">{e['sala']} • {fecha_bonita} ({e['hora']}h)</span>
            </div>
        </a>
        """

# 5. Estructura HTML + CSS (Negro Absoluto y Centrado Físico Reforzado)
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
            background-color: #000000; /* 🔥 Negro puro */
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            padding: 40px 16px;
            min-height: 100vh;
            width: 100%;
        }}
        .profile-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            width: 100%;
            max-width: 580px;
            margin-bottom: 24px;
        }}
        .profile-pic-wrapper {{
            width: 96px;
            height: 96px;
            border-radius: 50%;
            background: linear-gradient(45deg, #fe2c55, #25f4ee);
            padding: 3px;
            margin: 0 auto 16px auto; /* 🎯 Centrado garantizado en bloque */
            display: block;
        }}
        .profile-pic-wrapper img {{
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
            background-color: #000000;
            display: block;
        }}
        h1 {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 6px;
            color: #ffffff;
        }}
        .bio {{
            font-size: 14px;
            color: #9ca3af;
            max-width: 400px;
            line-height: 1.4;
        }}
        
        /* Contenedor de Pestañas de Días */
        .tabs-wrapper {{
            display: flex;
            gap: 10px;
            margin-bottom: 24px;
            width: 100%;
            max-width: 580px;
            overflow-x: auto;
            padding-bottom: 4px;
            justify-content: center;
        }}
        .tab-btn {{
            background: #121214;
            border: 1px solid #27272a;
            color: #a1a1aa;
            padding: 8px 18px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s ease;
        }}
        .tab-btn.active {{
            background: #ffffff;
            color: #000000;
            border-color: #ffffff;
        }}

        .links-wrapper {{
            width: 100%;
            max-width: 580px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}
        .link-btn {{
            background: #121214;
            border: 1px solid #27272a;
            border-radius: 30px;
            padding: 14px 24px;
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
        .no-events {{
            text-align: center;
            color: #71717a;
            padding: 30px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="profile-container">
        <div class="profile-pic-wrapper">
            <img src="https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=150" alt="NextPlan">
        </div>
        <h1>@nextplanevents</h1>
        <p class="bio">📍 Tu cartelera oficial de Madrid. Listas GRATIS, entradas y reservados VIP.</p>
    </div>

    <!-- Pestañas para seleccionar el día -->
    <div class="tabs-wrapper">
        {tabs_html}
    </div>

    <!-- Lista Dinámica de Eventos -->
    <div class="links-wrapper">
        {cards_html}
    </div>

    <script>
        function filterDate(selectedDate, btnElement) {{
            // Cambiar estilo visual de los botones
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            btnElement.classList.add('active');
            
            // Mostrar solo las tarjetas del día seleccionado
            const cards = document.querySelectorAll('.event-card');
            cards.forEach(card => {{
                if (card.getAttribute('data-date') === selectedDate) {{
                    card.style.display = 'flex';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_completo)

print("🎯 ¡Linktree interactivo con selector de fechas generado con éxito!")