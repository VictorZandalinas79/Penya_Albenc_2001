import csv
from collections import defaultdict
from io import StringIO
import os
<<<<<<< HEAD
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
=======

>>>>>>> e93812b7752819badd8563c55f763cc423373247

def process_festes_csv(input_csv):
    # Leer el CSV original
    reader = csv.DictReader(StringIO(input_csv))
    
    # Estructuras para almacenar los datos
    days_adults = defaultdict(list)
    days_children = defaultdict(list)
<<<<<<< HEAD
    days_cooks = defaultdict(list)  # Nueva estructura para cocineros
=======
>>>>>>> e93812b7752819badd8563c55f763cc423373247
    
    # Procesar cada entrada
    for row in reader:
        name = row['Nom i cognoms']
        age_group = row['Tria un...']
        available_days = row['Tria els dies que estaras per a sopar'].split('\n')
        
<<<<<<< HEAD
        # Procesar días para cocinar (quinta columna)
        cook_days_column = list(row.values())[4] if len(row.values()) > 4 else ""
        cook_days = cook_days_column.split('\n') if cook_days_column else []
        
        # Procesar días de asistencia
=======
>>>>>>> e93812b7752819badd8563c55f763cc423373247
        for day in available_days:
            day = day.strip()
            if not day:
                continue
<<<<<<< HEAD
                        
=======
                
>>>>>>> e93812b7752819badd8563c55f763cc423373247
            if age_group == 'Adult':
                days_adults[day].append(name)
            elif age_group == 'Xiquet':
                days_children[day].append(name)
<<<<<<< HEAD
        
        # Procesar días para cocinar (solo adultos pueden cocinar)
        if age_group == 'Adult':
            for day in cook_days:
                day = day.strip()
                if day:
                    days_cooks[day].append(name)
    
    # Ordenar los días cronológicamente
    def get_day_number(day_str):
=======
    
    # Ordenar los días cronológicamente (necesitamos extraer la fecha numérica)
    def get_day_number(day_str):
        # Ejemplo: "Dimarts 12 d'agost" -> extraer 12
>>>>>>> e93812b7752819badd8563c55f763cc423373247
        parts = day_str.split()
        return int(parts[1])
    
    sorted_days = sorted(days_adults.keys(), key=get_day_number)
    
<<<<<<< HEAD
    # Preparar el CSV de salida para asistencia
=======
    # Preparar el CSV de salida
>>>>>>> e93812b7752819badd8563c55f763cc423373247
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
    
<<<<<<< HEAD
    return output.getvalue(), days_cooks, sorted_days, days_adults, days_children

def create_cooking_pdf(days_cooks, sorted_days, days_adults, days_children, filename='cocineros_por_dia.pdf'):
    """
    Crear un PDF horizontal con cuadrados por día (5 arriba, 5 abajo)
    """
    doc = SimpleDocTemplate(filename, pagesize=landscape(A4), topMargin=0.2*inch, bottomMargin=0.2*inch, leftMargin=0.3*inch, rightMargin=0.3*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para títulos
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=15,
        alignment=1,  # Centrado
        textColor=colors.darkblue
    )
    
    # Título principal
    story.append(Paragraph("Cocineros y Comensales por Día", title_style))
    story.append(Spacer(1, 10))
    
    # Preparar datos para la tabla de cuadrados
    # Dividir los días en grupos de 5 para hacer 2 filas
    days_chunks = [sorted_days[i:i+5] for i in range(0, len(sorted_days), 5)]
    
    # Si hay más de 10 días, tomar solo los primeros 10
    if len(days_chunks) > 2:
        days_chunks = days_chunks[:2]
    
    # Completar con días vacíos si es necesario
    while len(days_chunks) < 2:
        days_chunks.append([])
    
    while len(days_chunks[0]) < 5:
        days_chunks[0].append("")
    while len(days_chunks[1]) < 5:
        days_chunks[1].append("")
    
    # Crear la tabla principal (2 filas x 5 columnas)
    table_data = []
    
    for row_idx, days_row in enumerate(days_chunks):
        row_data = []
        
        for day in days_row:
            if day:  # Día válido
                cooks = days_cooks.get(day, [])
                adults = days_adults.get(day, [])
                children = days_children.get(day, [])
                
                # Crear el contenido del cuadrado
                day_title = f"<b>{day}</b>"
                
                # Sección de cocineros
                cook_quantity = f"<b>Cocineros: {len(cooks)}</b>"
                
                if cooks:
                    cooks_list = "<br/>".join([f"• {cook}" for cook in cooks])
                    cook_section = f"{cook_quantity}<br/>{cooks_list}"
                else:
                    cook_section = f"{cook_quantity}<br/><i>Sin cocineros</i>"
                
                # Sección de comensales
                comensales_info = f"<br/><br/><b>--- COMENSALES ---</b><br/>"
                comensales_info += f"<b>Adultos: {len(adults)} | Niños: {len(children)}</b>"
                
                # Contenido completo de la celda
                cell_content = f"{day_title}<br/>{cook_section}{comensales_info}"
                
                cell_paragraph = Paragraph(cell_content, ParagraphStyle(
                    'CellStyle',
                    parent=styles['Normal'],
                    fontSize=8,
                    alignment=1,  # Centrado
                    spaceAfter=2,
                    leftIndent=3,
                    rightIndent=3
                ))
                
                row_data.append(cell_paragraph)
            else:
                # Celda vacía
                row_data.append("")
        
        table_data.append(row_data)
    
    # Crear la tabla
    col_width = 2.2*inch
    row_height = 3.5*inch  # Aumentado para que quepa toda la información
    
    table = Table(table_data, colWidths=[col_width]*5, rowHeights=[row_height]*2)
    
    # Estilo de la tabla
    table.setStyle(TableStyle([
        # Bordes y grid
        ('GRID', (0, 0), (-1, -1), 2, colors.black),
        
        # Fondo de las celdas
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        
        # Alineación
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        
        # Bordes más gruesos para separar bien los cuadrados
        ('LINEWIDTH', (0, 0), (-1, -1), 1.5),
    ]))
    
    story.append(table)
    
    # Construir el PDF
    doc.build(story)
    print(f"PDF de cocineros y comensales creado en formato horizontal: {filename}")

def main():
    # Leer el archivo CSV
    try:
        with open('Festes.csv', mode='r', encoding='utf-8') as file:
            input_csv = file.read()
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'Festes.csv'")
        return
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return
    
    # Procesar el CSV
    output_csv, days_cooks, sorted_days, days_adults, days_children = process_festes_csv(input_csv)
    
    # Guardar el CSV de asistencia
    with open('assistencia_per_dia.csv', mode='w', encoding='utf-8') as file:
        file.write(output_csv)
    print("Archivo de asistencia procesado correctamente. Resultado guardado en 'assistencia_per_dia.csv'")
    
    # Crear el PDF de cocineros y comensales
    create_cooking_pdf(days_cooks, sorted_days, days_adults, days_children)
    
    # Mostrar resumen de cocineros por día
    print("\n=== RESUMEN DE COCINEROS POR DÍA ===")
    for day in sorted_days:
        adults = days_adults.get(day, [])
        children = days_children.get(day, [])
        cooks = days_cooks.get(day, [])
        
        print(f"\n{day}:")
        print(f"  Cocineros ({len(cooks)}): {', '.join(cooks) if cooks else 'Sin cocineros'}")
        print(f"  Comensales - Adultos: {len(adults)}, Niños: {len(children)}")

if __name__ == "__main__":
    main()
=======
    return output.getvalue()

# Ejemplo de uso (deberías reemplazar esto con la lectura real del archivo)
with open('Festes_20252025-07-28_12_25_30.csv', mode='r', encoding='utf-8') as file:
    input_csv = file.read()

output_csv = process_festes_csv(input_csv)

# Guardar el resultado en un nuevo archivo CSV
with open('assistencia_per_dia.csv', mode='w', encoding='utf-8') as file:
    file.write(output_csv)

print("Archivo procesado correctamente. Resultado guardado en 'assistencia_per_dia.csv'")
>>>>>>> e93812b7752819badd8563c55f763cc423373247
