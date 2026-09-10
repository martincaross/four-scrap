import json
import os
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    hoy_date = datetime.now(ZoneInfo("Europe/Madrid")).date()
except Exception:
    hoy_date = datetime.now().date()

DATABASE_FILE = "data/base_de_datos_madrid.json"
OLD_DATABASE_FILE = "data/base_de_datos_madrid_old.json"

def main():
    print("🚨 Iniciando rutina de FALLBACK: Limpieza de eventos pasados.")
    
    if not os.path.exists(DATABASE_FILE):
        print(f"❌ No se encontró la base de datos local {DATABASE_FILE}. Fallback abortado.")
        return

    # Leer eventos activos actuales
    with open(DATABASE_FILE, "r", encoding="utf-8") as f:
        eventos = json.load(f)

    # Leer eventos antiguos
    eventos_old = []
    if os.path.exists(OLD_DATABASE_FILE):
        with open(OLD_DATABASE_FILE, "r", encoding="utf-8") as f:
            eventos_old = json.load(f)

    eventos_mantenidos = []
    eventos_caducados = []

    for e in eventos:
        f_raw = e.get("fecha", "")
        if not f_raw:
            eventos_caducados.append(e)
            continue
        
        # Parsear fecha
        e_date = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                e_date = datetime.strptime(str(f_raw).strip(), fmt).date()
                break
            except ValueError:
                pass
        
        # Si la fecha es válida y >= hoy, se mantiene. Si no, a caducados.
        if e_date and e_date >= hoy_date:
            eventos_mantenidos.append(e)
        else:
            eventos_caducados.append(e)

    # Actualizar listas
    print(f"🧹 Eventos mantenidos (activos): {len(eventos_mantenidos)}")
    print(f"🗑️  Eventos caducados (pasados a old): {len(eventos_caducados)}")

    # Guardar base de datos limpia
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(eventos_mantenidos, f, indent=4, ensure_ascii=False)
        
    # Anexar a la base antigua y guardarla
    if eventos_caducados:
        eventos_old.extend(eventos_caducados)
        # Limpiar duplicados en old por si acaso
        seen_ids = set()
        clean_old = []
        for eo in eventos_old:
            e_id = eo.get("id")
            if e_id not in seen_ids:
                seen_ids.add(e_id)
                clean_old.append(eo)
                
        with open(OLD_DATABASE_FILE, "w", encoding="utf-8") as f:
            json.dump(clean_old, f, indent=4, ensure_ascii=False)

    print("✅ Fallback completado con éxito. Base de datos lista para el pipeline.")

if __name__ == "__main__":
    main()
