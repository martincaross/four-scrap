import json
from datetime import datetime, timedelta
import os

DATABASE_FILE = "base_de_datos_madrid.json"
OUTPUT_HTML = "index.html"

# Fecha de hoy (22 de julio de 2026)
hoy_dt = datetime.now()
hoy_date = hoy_dt.date()
hoy_str = hoy_date.strftime("%Y-%m-%d")

print(f"🌐 Generando Linktree interactivo desde: {hoy_str}")

if not os.path.exists(DATABASE_FILE):
    print(f"❌ No se encuentra la base de datos {DATABASE_FILE}")
    exit()

with open(DATABASE_FILE, "r", encoding="utf-8") as f:
    eventos = json.load(f)

# =========================================================================
# 📦 1. PARSEO ROBUTOS Y FILTRADO POR FECHA REAL (No strings)
# =========================================================================
eventos_futuros = []

for e in eventos:
    f_raw = e.get("fecha", "")
    if not f_raw:
        continue
    
    # Intentamos parsear la fecha independientemente de su formato
    e_date = None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            e_date = datetime.strptime(str(f_raw).strip(), fmt).date()
            break
        except ValueError:
            pass
    
    # Solo nos quedamos con eventos de hoy en adelante
    if e_date and e_date >= hoy_date:
        e_copy = dict(e)
        e_copy["fecha_std"] = e_date.strftime("%Y-%m-%d")
        e_copy["date_obj"] = e_date
        eventos_futuros.append(e_copy)

# Ordenar eventos cronológicamente (Fecha primero, Hora después)
eventos_futuros.sort(key=lambda x: (x["date_obj"], x.get("hora", "23:59")))

# =========================================================================
# 📅 2. OBTENER DÍAS ÚNICOS
# =========================================================================
fechas_unicas = sorted(list(set(e["fecha_std"] for e in eventos_futuros)))

# Generamos botones de pestañas
tabs_html = ""
for idx, fecha in enumerate(fechas_unicas):
    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
    
    if fecha == hoy_str:
        label = "🔥 Hoy"
    elif fecha == (hoy_date + timedelta(days=1)).strftime("%Y-%m-%d"):
        label = "🚀 Mañana"
    else:
        label = fecha_dt.strftime("%d %b")
        
    active_class = "active" if idx == 0 else ""
    tabs_html += f'<button class="tab-btn {active_class}" onclick="filterDate(\'{fecha}\', this)">{label}</button>\n'

# =========================================================================
# 🎟️ 3. GENERAR TARJETAS DE EVENTOS
# =========================================================================
cards_html = ""
if not eventos_futuros:
    cards_html = '<div class="no-events">💤 No hay eventos próximos programados.</div>'
else:
    for e in eventos_futuros:
        fecha_dt = datetime.strptime(e['fecha_std'], "%Y-%m-%d")
        fecha_bonita = fecha_dt.strftime("%d %b")
        fecha_event = e['fecha_std']
        
        # Muestra por defecto los del primer día disponible
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

# =========================================================================
# 🎨 4. ESTRUCTURA HTML + CSS (Fix de Scroll y Negro Puro)
# =========================================================================
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
            background-color: #000000;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 32px 16px;
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
            margin-bottom: 20px;
        }}
        .profile-pic-wrapper {{
            width: 90px;
            height: 90px;
            border-radius: 50%;
            background: linear-gradient(45deg, #fe2c55, #25f4ee);
            padding: 3px;
            margin: 0 auto 14px auto;
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
            font-size: 13px;
            color: #9ca3af;
            max-width: 380px;
            line-height: 1.4;
        }}
        
        /* Contenedor de Pestañas con Scroll Móvil Corregido */
        .tabs-wrapper {{
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            width: 100%;
            max-width: 580px;
            overflow-x: auto;
            padding: 4px 4px 10px 4px;
            justify-content: flex-start; /* FIX: Evita que el scroll corte elementos a la izquierda */
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }}
        .tabs-wrapper::-webkit-scrollbar {{
            display: none;
        }}
        .tab-btn {{
            background: #121214;
            border: 1px solid #27272a;
            color: #a1a1aa;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s ease;
            flex-shrink: 0;
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
            gap: 12px;
        }}
        .link-btn {{
            background: #121214;
            border: 1px solid #27272a;
            border-radius: 24px;
            padding: 14px 20px;
            align-items: center;
            text-decoration: none;
            color: white;
            transition: transform 0.2s, background-color 0.2s;
        }}
        .link-btn:hover {{
            transform: scale(1.01);
            background: #18181b;
        }}
        .btn-emoji {{
            font-size: 22px;
            margin-right: 14px;
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
            margin-top: 2px;
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

    <div class="tabs-wrapper">
        {tabs_html}
    </div>

    <div class="links-wrapper">
        {cards_html}
    </div>

    <script>
        function filterDate(selectedDate, btnElement) {{
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            btnElement.classList.add('active');
            
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

print(f"🎯 ¡Linktree corregido! {len(eventos_futuros)} eventos organizados en {len(fechas_unicas)} días.")