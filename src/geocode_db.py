import json
import time
import os
import unicodedata
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

DB_FILE = "data/base_de_datos_madrid.json"
ERROR_LOG = "depuracion/errores_geocodificacion.txt"

# Diccionario de fallback para mapear ciudades conocidas a sus provincias correspondientes
# Todo en minúsculas y sin tildes para facilitar el matching.
CITY_PROVINCE_MAP = {
    "tarifa": "cadiz",
    "jerez": "cadiz",
    "jerez de la frontera": "cadiz",
    "marbella": "malaga",
    "ibiza": "illes balears",
    "eivissa": "illes balears",
    "san antonio": "illes balears",
    "gijon": "asturias",
    "vigo": "pontevedra",
    "cartagena": "murcia",
    "elche": "alicante",
    "sabadell": "barcelona",
    "terrassa": "barcelona",
    "badalona": "barcelona",
    "hospitalet": "barcelona",
    "alcala de henares": "madrid",
    "leganes": "madrid",
    "getafe": "madrid",
    "alcorcon": "madrid",
    "mostoles": "madrid",
    "fuenlabrada": "madrid",
    "madrid": "madrid",
    "barcelona": "barcelona",
    "valencia": "valencia",
    "sevilla": "sevilla"
}

def normalize_text(text):
    if not text:
        return "desconocido"
    # Convertir a string si no lo es, minúsculas, quitar tildes y diacríticos
    text = str(text).lower().strip()
    text = ''.join((c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn'))
    return text

def infer_province_from_address(direccion):
    norm_dir = normalize_text(direccion)
    for city, province in CITY_PROVINCE_MAP.items():
        if city in norm_dir:
            return city, province
    return "desconocido", "desconocido"

def main():
    if not os.path.exists(DB_FILE):
        print(f"Error: {DB_FILE} no encontrado.")
        return

    with open(DB_FILE, "r", encoding="utf-8") as f:
        events = json.load(f)

    # Inicializar el geocoder de OpenStreetMap
    geolocator = Nominatim(user_agent="mingle_geocoder_script")
    
    # Caché temporal para no preguntar por la misma dirección dos veces
    cache = {}

    modificados = 0
    errores = []

    print(f"🔍 Iniciando geocodificación y reestructuración de {len(events)} eventos...")

    # Anulaciones manuales para direcciones enrevesadas (hipódromo)
    MANUAL_COORDS_MAP = {
        "hipodromo": (40.4578, -3.7533, "madrid", "madrid", "comunidad de madrid", "es"),
        "hipódromo": (40.4578, -3.7533, "madrid", "madrid", "comunidad de madrid", "es")
    }

    for event in events:
        # Migración de la estructura antigua a la nueva
        if "ubicacion" not in event:
            direccion = event.pop("direccion", "Dirección desconocida")
            latitud = event.pop("latitud", None)
            longitud = event.pop("longitud", None)
            event["ubicacion"] = {
                "direccion": direccion,
                "ciudad": "desconocido",
                "provincia": "desconocido",
                "comunidad": "desconocido",
                "pais": "es",
                "latitud": latitud,
                "longitud": longitud
            }
            modificados += 1

        ubicacion = event["ubicacion"]
        direccion = ubicacion.get("direccion")
        
        # Saltamos si ya tiene coordenadas válidas y campos de territorio distintos a desconocido
        if ubicacion.get("latitud") is not None and ubicacion.get("longitud") is not None and ubicacion.get("ciudad") != "desconocido" and ubicacion.get("provincia") != "desconocido":
            continue
            
        if not direccion or direccion == "Dirección desconocida":
            print(f"⚠️ Evento '{event.get('titulo')}' no tiene dirección. Saltando.")
            continue

        dir_lower = (direccion + " " + event.get("sala", "")).lower()
        manual_match = None
        for key, vals in MANUAL_COORDS_MAP.items():
            if key in dir_lower:
                manual_match = vals
                break
                
        if manual_match:
            new_data = {
                "latitud": manual_match[0],
                "longitud": manual_match[1],
                "ciudad": manual_match[2],
                "provincia": manual_match[3],
                "comunidad": manual_match[4],
                "pais": manual_match[5]
            }
            ubicacion.update(new_data)
            modificados += 1
            print(f"   🎯 Éxito (Manual Override): {new_data['ciudad']}, {new_data['provincia']}")
            continue

        if direccion in cache:
            cached_data = cache[direccion]
            ubicacion.update(cached_data)
            modificados += 1
            continue

        # Evitar el rate limiting de Nominatim (máx 1 req/s recomendado)
        time.sleep(1.2)

        try:
            print(f"📍 Geocodificando: {direccion}")
            location = geolocator.geocode(direccion, timeout=10, addressdetails=True)
            if location:
                raw = location.raw.get("address", {})
                
                lat = location.latitude
                lon = location.longitude
                
                # Extraer y normalizar
                ciudad_raw = raw.get("city", raw.get("town", raw.get("village", raw.get("municipality", ""))))
                provincia_raw = raw.get("province", raw.get("county", ""))
                comunidad_raw = raw.get("state", raw.get("region", ""))
                pais_raw = raw.get("country_code", "es")
                
                ciudad = normalize_text(ciudad_raw)
                provincia = normalize_text(provincia_raw)
                comunidad = normalize_text(comunidad_raw)
                pais = normalize_text(pais_raw)
                
                # Validar con diccionario si Nominatim no devuelve provincia o si es dudoso
                if ciudad == "desconocido" or provincia == "desconocido":
                    inf_city, inf_prov = infer_province_from_address(direccion)
                    if ciudad == "desconocido": ciudad = inf_city
                    if provincia == "desconocido": provincia = inf_prov
                else:
                    # Sobrescribir con el diccionario si la ciudad está mapeada explícitamente para evitar errores (Ej. Tarifa es Cádiz)
                    if ciudad in CITY_PROVINCE_MAP:
                        provincia = CITY_PROVINCE_MAP[ciudad]

                new_data = {
                    "latitud": lat,
                    "longitud": lon,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "comunidad": comunidad,
                    "pais": pais
                }
                
                ubicacion.update(new_data)
                cache[direccion] = new_data
                modificados += 1
                print(f"   ✅ Éxito: {ciudad}, {provincia}")
            else:
                print("   ❌ No se encontraron coordenadas.")
                inf_city, inf_prov = infer_province_from_address(direccion)
                new_data = {
                    "ciudad": inf_city,
                    "provincia": inf_prov,
                    "comunidad": "desconocido",
                    "pais": "es"
                }
                ubicacion.update(new_data)
                cache[direccion] = new_data
                errores.append(f"{event.get('id', 'ID')} - {event.get('titulo', 'Titulo')}: {direccion}")
        except GeocoderTimedOut:
            print("   ⏳ Timeout intentando geocodificar.")
            errores.append(f"TIMEOUT - {event.get('id')} - {event.get('titulo')}: {direccion}")
        except Exception as e:
            print(f"   💥 Error inesperado: {e}")
            errores.append(f"ERROR: {e} - {event.get('id')} - {event.get('titulo')}: {direccion}")

    print(f"\n💾 Guardando {modificados} eventos actualizados...")
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
        
    if errores:
        print(f"⚠️ Hubo {len(errores)} direcciones que fallaron o no se encontraron. Revisa {ERROR_LOG}.")
        with open(ERROR_LOG, "w", encoding="utf-8") as f:
            for error in errores:
                f.write(error + "\n")

    print("✅ ¡Listo! base_de_datos_madrid.json ha sido actualizado con la nueva estructura de ubicación.")

if __name__ == "__main__":
    main()
