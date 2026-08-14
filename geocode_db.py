import json
import time
import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

DB_FILE = "base_de_datos_madrid.json"

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

    print(f"🔍 Iniciando geocodificación de {len(events)} eventos...")

    for event in events:
        direccion = event.get("direccion")
        
        # Saltamos si ya tiene coordenadas válidas
        if event.get("latitud") is not None and event.get("longitud") is not None:
            continue
            
        if not direccion:
            print(f"⚠️ Evento '{event.get('titulo')}' no tiene dirección. Saltando.")
            continue

        if direccion in cache:
            lat, lon = cache[direccion]
            if lat is not None:
                event["latitud"] = lat
                event["longitud"] = lon
                modificados += 1
            continue

        # Evitar el rate limiting de Nominatim (máx 1 req/s recomendado)
        time.sleep(1.2)

        try:
            print(f"📍 Geocodificando: {direccion}")
            location = geolocator.geocode(direccion, timeout=10)
            if location:
                lat, lon = location.latitude, location.longitude
                event["latitud"] = lat
                event["longitud"] = lon
                cache[direccion] = (lat, lon)
                modificados += 1
                print(f"   ✅ Éxito: {lat}, {lon}")
            else:
                print("   ❌ No se encontraron coordenadas.")
                cache[direccion] = (None, None)
        except GeocoderTimedOut:
            print("   ⏳ Timeout intentando geocodificar.")
            cache[direccion] = (None, None)
        except Exception as e:
            print(f"   💥 Error inesperado: {e}")
            cache[direccion] = (None, None)

    print(f"\n💾 Guardando {modificados} eventos actualizados...")
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

    print("✅ ¡Listo! base_de_datos_madrid.json ha sido actualizado con latitud y longitud.")

if __name__ == "__main__":
    main()
