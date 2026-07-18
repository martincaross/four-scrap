import json
import csv
import os

# Nombre de tus archivos
archivo_json = "base_de_datos_madrid.json"
archivo_csv = "eventos_madrid.csv"

print("🔄 Iniciando conversión de JSON a formato Excel (CSV)...")

# 1. Comprobar si el JSON existe
if not os.path.exists(archivo_json):
    print(f"❌ Error: No encuentro el archivo '{archivo_json}'. Asegúrate de estar en la carpeta correcta.")
    exit()

try:
    # 2. Leer los datos del JSON
    with open(archivo_json, "r", encoding="utf-8") as f:
        eventos = json.load(f)
    
    # 3. Definir el orden de las columnas que queremos en el Excel
    columnas = [
        "id", "titulo", "sala", "fecha", "hora", 
        "edad", "vestimenta", "direccion", 
        "link_compra_rrpp", "imagen", "descripcion"
    ]
    
    # 4. Escribir el archivo CSV formateado para Excel
    with open(archivo_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        
        # Escribimos los títulos de las columnas arriba
        writer.writeheader()
        
        # Volcamos cada evento en una fila
        for evento in eventos:
            # Filtramos el diccionario para que solo tenga las columnas que queremos
            fila = {col: evento.get(col, "") for col in columnas}
            writer.writerow(fila)
            
    print(f"🎯 ¡ÉXITO TOTAL! Archivo '{archivo_csv}' generado con {len(eventos)} filas.")
    print("Ya puedes descargarlo de tu Codespace y abrirlo directamente con Excel o Numbers.")

except Exception as e:
    print(f"💥 Hubo un problema al transformar el archivo: {e}")