import json
import os
import shutil
from datetime import datetime, timedelta

DATABASE_FILE = "base_de_datos_madrid.json"
BACKUP_DIR = "backups"

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

hoy_str = datetime.now().strftime("%Y-%m-%d")

if os.path.exists(DATABASE_FILE):
    backup_file = os.path.join(BACKUP_DIR, f"base_de_datos_madrid_original.json")
    shutil.copy(DATABASE_FILE, backup_file)
    print(f"✅ Copia de seguridad original creada en {backup_file}")
    
    with open(DATABASE_FILE, "r", encoding="utf-8") as f:
        eventos = json.load(f)
        
    eventos_reparados = []
    
    for evento in eventos:
        fecha = evento.get("fecha", "1970-01-01")
        hora = evento.get("hora", "23:59")
        
        # Reparar madrugada
        if hora < "06:00":
            try:
                dt_fecha = datetime.strptime(fecha, "%Y-%m-%d")
                fecha = (dt_fecha - timedelta(days=1)).strftime("%Y-%m-%d")
                evento["fecha"] = fecha
            except:
                pass
                
        # Mantener solo los de hoy o futuros
        if fecha >= hoy_str:
            eventos_reparados.append(evento)
            
    # Ordenar
    def sort_key(x):
        f = x.get("fecha", "9999-12-31")
        h = x.get("hora", "23:59")
        h_ord = f"{int(h[:2]) + 24}:{h[3:]}" if h < "06:00" else h
        return (f, h_ord)
        
    eventos_reparados.sort(key=sort_key)
    
    with open(DATABASE_FILE, "w", encoding="utf-8") as f:
        json.dump(eventos_reparados, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Base de datos reparada. Se eliminaron los pasados. Total actual: {len(eventos_reparados)}")
else:
    print("❌ No se encontró base de datos para reparar.")
