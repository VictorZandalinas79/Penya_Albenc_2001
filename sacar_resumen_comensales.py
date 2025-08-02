import csv
from collections import defaultdict
from io import StringIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def process_adults_individual(input_csv):
    """
    Procesar el CSV para obtener información individual de cada adulto
    """
    reader = csv.DictReader(StringIO(input_csv))
    
    # Diccionario para almacenar información de cada adulto
    adults_info = {}
    
    # Procesar cada entrada
    for row in reader:
        name = row['Nom i cognoms']
        age_group = row['Tria un...']
        
        # Solo procesar adultos
        if age_group != 'Adult':
            continue
            
        available_days = row['Tria els dies que estaras per a sopar'].split('\n')
        
        # Procesar días para cocinar (quinta columna)
        cook_days_column = list(row.values())[4] if len(row.values()) > 4 else ""
        cook_days = cook_days_column.split('\n') if cook_days_column else []
        
        # Limpiar y filtrar días vacíos
        eating_days = [day.strip() for day in available_days if day.strip()]
        cooking_days = [day.strip() for day in cook_days if day.strip()]
        
        # Almacenar información del adulto
        adults_info[name] = {
            'eating_days': eating_days,
            'cooking_days': cooking_days
        }
    
    return adults_info

def get_day_number(day_str):
    """
    Extraer el número del día para ordenar cronológicamente
    Ejemplo: "Dimarts 12 d'agost" -> 12
    """
    try:
        parts = day_str.split()
        return int(parts[1])
    except (IndexError, ValueError):
        return 0

def create_adults_individual_pdf(adults_info, filename='reporte_adultos_individual.pdf'):
    """
    Crear un PDF con la información individual de cada adulto
    """
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch, 
                          leftMargin=0.5*inch, rightMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=1,  # Centrado
        textColor=colors.darkblue
    )
    
    person_title_style = ParagraphStyle(
        'PersonTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        textColor=colors.darkgreen,
        leftIndent=10
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leftIndent=20,
        textColor=colors.black
    )
    
    # Título principal
    story.append(Paragraph("Reporte Individual - Adultos", title_style))
    story.append(Paragraph("Días de Comida y Cocina por Persona", styles['Heading3']))
    story.append(Spacer(1, 20))
    
    # Ordenar adultos alfabéticamente
    sorted_adults = sorted(adults_info.keys())
    
    for i, adult_name in enumerate(sorted_adults):
        info = adults_info[adult_name]
        
        # Nombre del adulto
        story.append(Paragraph(f"👤 {adult_name}", person_title_style))
        
        # Días que come (ordenados cronológicamente)
        eating_days = sorted(info['eating_days'], key=get_day_number)
        eating_text = f"<b>🍽️ Días que estará para cenar ({len(eating_days)} días):</b>"
        story.append(Paragraph(eating_text, section_style))
        
        if eating_days:
            for day in eating_days:
                story.append(Paragraph(f"• {day}", ParagraphStyle(
                    'DayStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    leftIndent=40,
                    spaceAfter=3
                )))
        else:
            story.append(Paragraph("• No hay días registrados", ParagraphStyle(
                'NoDaysStyle',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=40,
                spaceAfter=3,
                textColor=colors.grey
            )))
        
        story.append(Spacer(1, 10))
        
        # Días que cocina (ordenados cronológicamente)
        cooking_days = sorted(info['cooking_days'], key=get_day_number)
        cooking_text = f"<b>👨‍🍳 Días que cocinará ({len(cooking_days)} días):</b>"
        story.append(Paragraph(cooking_text, section_style))
        
        if cooking_days:
            for day in cooking_days:
                story.append(Paragraph(f"• {day}", ParagraphStyle(
                    'CookDayStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    leftIndent=40,
                    spaceAfter=3,
                    textColor=colors.darkred
                )))
        else:
            story.append(Paragraph("• No cocinará ningún día", ParagraphStyle(
                'NoCookStyle',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=40,
                spaceAfter=3,
                textColor=colors.grey
            )))
        
        # Separador entre personas (excepto la última)
        if i < len(sorted_adults) - 1:
            story.append(Spacer(1, 15))
            story.append(Paragraph("─" * 80, ParagraphStyle(
                'Separator',
                parent=styles['Normal'],
                fontSize=8,
                alignment=1,
                textColor=colors.lightgrey
            )))
            story.append(Spacer(1, 15))
    
    # Construir el PDF
    doc.build(story)
    print(f"PDF de reporte individual creado: {filename}")

def create_summary_table_pdf(adults_info, filename='resumen_adultos_tabla.pdf'):
    """
    Crear un PDF con una tabla resumen de todos los adultos
    """
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch, 
                          leftMargin=0.5*inch, rightMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=1,
        textColor=colors.darkblue
    )
    
    story.append(Paragraph("Resumen de Adultos - Tabla", title_style))
    story.append(Spacer(1, 20))
    
    # Preparar datos para la tabla
    table_data = [['Nombre', 'Días de Cena', 'Días de Cocina', 'Total Cenas', 'Total Cocinas']]
    
    # Ordenar adultos alfabéticamente
    sorted_adults = sorted(adults_info.keys())
    
    for adult_name in sorted_adults:
        info = adults_info[adult_name]
        
        # Formatear días de cena
        eating_days_text = '\n'.join(info['eating_days'][:3])  # Máximo 3 días por celda
        if len(info['eating_days']) > 3:
            eating_days_text += f"\n... y {len(info['eating_days']) - 3} más"
        
        # Formatear días de cocina
        cooking_days_text = '\n'.join(info['cooking_days'][:3])  # Máximo 3 días por celda
        if len(info['cooking_days']) > 3:
            cooking_days_text += f"\n... y {len(info['cooking_days']) - 3} más"
        
        table_data.append([
            adult_name,
            eating_days_text if eating_days_text.strip() else 'Ninguno',
            cooking_days_text if cooking_days_text.strip() else 'Ninguno',
            str(len(info['eating_days'])),
            str(len(info['cooking_days']))
        ])
    
    # Crear la tabla
    table = Table(table_data, colWidths=[2*inch, 2.5*inch, 2.5*inch, 0.8*inch, 0.8*inch])
    
    # Estilo de la tabla
    table.setStyle(TableStyle([
        # Encabezados
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # Cuerpo de la tabla
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 1), (4, -1), 'CENTER'),  # Centrar columnas de totales
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        
        # Bordes
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        
        # Alternar colores de fila
        ('BACKGROUND', (0, 2), (-1, -1), colors.lightgrey),
        ('BACKGROUND', (0, 1), (-1, 1), colors.beige),
    ]))
    
    # Aplicar color alternado a las filas
    for i in range(2, len(table_data), 2):
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, i), (-1, i), colors.lightgrey),
        ]))
    
    story.append(table)
    
    # Construir el PDF
    doc.build(story)
    print(f"PDF de tabla resumen creado: {filename}")

def print_console_summary(adults_info):
    """
    Mostrar resumen en consola
    """
    print("\n" + "="*60)
    print("RESUMEN DE ADULTOS - DÍAS DE COMIDA Y COCINA")
    print("="*60)
    
    sorted_adults = sorted(adults_info.keys())
    
    for adult_name in sorted_adults:
        info = adults_info[adult_name]
        
        print(f"\n👤 {adult_name}")
        print(f"   🍽️  Días de cena ({len(info['eating_days'])}): {', '.join(info['eating_days']) if info['eating_days'] else 'Ninguno'}")
        print(f"   👨‍🍳 Días de cocina ({len(info['cooking_days'])}): {', '.join(info['cooking_days']) if info['cooking_days'] else 'Ninguno'}")
    
    print(f"\n📊 Total de adultos procesados: {len(sorted_adults)}")

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
    
    # Procesar información de adultos
    adults_info = process_adults_individual(input_csv)
    
    if not adults_info:
        print("No se encontraron adultos en el archivo CSV")
        return
    
    # Crear PDFs
    create_adults_individual_pdf(adults_info)
    create_summary_table_pdf(adults_info)
    
    # Mostrar resumen en consola
    print_console_summary(adults_info)
    
    print(f"\n✅ Proceso completado. Se generaron 2 PDFs:")
    print("   - reporte_adultos_individual.pdf (detalle por persona)")
    print("   - resumen_adultos_tabla.pdf (tabla resumen)")

if __name__ == "__main__":
    main()