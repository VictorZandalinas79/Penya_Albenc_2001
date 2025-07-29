import csv
from collections import defaultdict
from io import StringIO
import os


def process_festes_csv(input_csv):
    # Leer el CSV original
    reader = csv.DictReader(StringIO(input_csv))
    
    # Estructuras para almacenar los datos
    days_adults = defaultdict(list)
    days_children = defaultdict(list)
    
    # Procesar cada entrada
    for row in reader:
        name = row['Nom i cognoms']
        age_group = row['Tria un...']
        available_days = row['Tria els dies que estaras per a sopar'].split('\n')
        
        for day in available_days:
            day = day.strip()
            if not day:
                continue
                
            if age_group == 'Adult':
                days_adults[day].append(name)
            elif age_group == 'Xiquet':
                days_children[day].append(name)
    
    # Ordenar los días cronológicamente (necesitamos extraer la fecha numérica)
    def get_day_number(day_str):
        # Ejemplo: "Dimarts 12 d'agost" -> extraer 12
        parts = day_str.split()
        return int(parts[1])
    
    sorted_days = sorted(days_adults.keys(), key=get_day_number)
    
    # Preparar el CSV de salida
    output = StringIO()
    writer = csv.writer(output)
    
    # Escribir encabezados
    writer.writerow(['Dia', 'Adults (noms)', 'Adults (quantitat)', 'Xiquets (noms)', 'Xiquets (quantitat)'])
    
    # Escribir datos para cada día
    for day in sorted_days:
        adults = days_adults.get(day, [])
        children = days_children.get(day, [])
        
        writer.writerow([
            day,
            ', '.join(adults),
            len(adults),
            ', '.join(children),
            len(children)
        ])
    
    return output.getvalue()

# Ejemplo de uso (deberías reemplazar esto con la lectura real del archivo)
with open('Festes_20252025-07-28_12_25_30.csv', mode='r', encoding='utf-8') as file:
    input_csv = file.read()

output_csv = process_festes_csv(input_csv)

# Guardar el resultado en un nuevo archivo CSV
with open('assistencia_per_dia.csv', mode='w', encoding='utf-8') as file:
    file.write(output_csv)

print("Archivo procesado correctamente. Resultado guardado en 'assistencia_per_dia.csv'")