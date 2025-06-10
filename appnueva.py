import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table, ALL
import dash.dependencies
import dash_bootstrap_components as dbc  # ← NUEVO IMPORT
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import calendar

# Inicializar la app con Bootstrap
app = dash.Dash(__name__, 
                suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP])  # ← CAMBIO AQUÍ
app.title = "Penya L'Albenc"

# Para Render
server = app.server

# Configurar la base de datos
def init_db():
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    # Tabla de comidas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            tipo_servicio TEXT,
            tipo_comida TEXT,
            cocineros TEXT
        )
    ''')
    
    # Tabla de lista de compra
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lista_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            objeto TEXT
        )
    ''')
    
    # Tabla de mantenimiento
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mantenimiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            año INTEGER,
            mantenimiento TEXT,
            cadafals TEXT
        )
    ''')
    
    # Tabla de eventos para el calendario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            evento TEXT,
            tipo TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Funciones de base de datos
def get_data(table):
    conn = sqlite3.connect('penya_albenc.db')
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

def add_data(table, data):
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    if table == 'comidas':
        cursor.execute("INSERT INTO comidas (fecha, tipo_servicio, tipo_comida, cocineros) VALUES (?, ?, ?, ?)", data)
    elif table == 'lista_compra':
        cursor.execute("INSERT INTO lista_compra (fecha, objeto) VALUES (?, ?)", data)
    elif table == 'mantenimiento':
        cursor.execute("INSERT INTO mantenimiento (año, mantenimiento, cadafals) VALUES (?, ?, ?)", data)
    elif table == 'eventos':
        cursor.execute("INSERT INTO eventos (fecha, evento, tipo) VALUES (?, ?, ?)", data)
    
    conn.commit()
    conn.close()

def update_data(table, id_record, field, new_value):
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {table} SET {field} = ? WHERE id = ?", (new_value, id_record))
    conn.commit()
    conn.close()

def delete_data(table, id_record):
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (id_record,))
    conn.commit()
    conn.close()

# ===== NUEVAS FUNCIONES PARA CARDS MODERNAS =====

def create_comida_card(row, show_actions=True):
    """Crear card moderna para una comida"""
    # Formatear fecha
    try:
        fecha_obj = datetime.strptime(row['fecha'], '%Y-%m-%d')
        fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
    except:
        fecha_formateada = row['fecha']
    
    # Crear acciones si están habilitadas
    actions = []
    if show_actions:
        actions = [
            html.Button("✏️ Editar", 
                       id={'type': 'edit-comida', 'index': row['id']}, 
                       className="btn-icon btn-edit",
                       n_clicks=0),
            html.Button("🗑️ Eliminar", 
                       id={'type': 'delete-comida', 'index': row['id']}, 
                       className="btn-icon btn-delete",
                       n_clicks=0)
        ]
    
    return html.Div([
        # Header de la card
        html.Div([
            html.H4(f"🍽️ {row['tipo_comida']}", className="card-title"),
        ], className="card-header"),
        
        # Información de la comida
        html.Div([
            html.Div([
                html.Span("📅 ", className="card-info-label"),
                html.Span(fecha_formateada, className="card-info-value")
            ], className="card-info-item"),
            
            html.Div([
                html.Span("🍽️ ", className="card-info-label"),
                html.Span(row['tipo_servicio'], className="card-info-value")
            ], className="card-info-item"),
            
            html.Div([
                html.Span("👨‍🍳 ", className="card-info-label"),
                html.Span(row['cocineros'], className="card-info-value")
            ], className="card-info-item"),
        ], className="card-info"),
        
        # Acciones
        html.Div(actions, className="card-actions") if actions else html.Div()
        
    ], className="data-card", style={"border-left-color": "#4CAF50"})

def create_comidas_cards_container(comidas_df):
    """Crear contenedor con todas las cards de comidas"""
    if len(comidas_df) == 0:
        return html.Div([
            html.Div("📭", style={"font-size": "3rem", "margin-bottom": "10px"}),
            html.H4("No hay comidas registradas"),
            html.P("Agrega la primera comida usando el formulario de abajo")
        ], className="no-data")
    
    # Ordenar por fecha
    comidas_sorted = comidas_df.sort_values('fecha')
    
    cards = []
    for _, row in comidas_sorted.iterrows():
        cards.append(create_comida_card(row))
    
    return html.Div([
        html.Div(f"📊 Total: {len(comidas_df)} comidas registradas", 
                style={"text-align": "center", "margin-bottom": "15px", 
                       "font-weight": "bold", "color": "#2E7D32"}),
        html.Div(cards, style={"max-height": "500px", "overflow-y": "auto", 
                              "padding-right": "10px"})
    ])

def create_lista_card(row, show_actions=True):
    """Crear card moderna para lista de compra"""
    # Formatear fecha
    try:
        fecha_obj = datetime.strptime(row['fecha'], '%Y-%m-%d')
        fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
    except:
        fecha_formateada = row['fecha']
    
    # Crear acciones si están habilitadas
    actions = []
    if show_actions:
        actions = [
            html.Button("✏️ Editar", 
                       id={'type': 'edit-lista', 'index': row['id']}, 
                       className="btn-icon btn-edit",
                       n_clicks=0),
            html.Button("🗑️ Eliminar", 
                       id={'type': 'delete-lista', 'index': row['id']}, 
                       className="btn-icon btn-delete",
                       n_clicks=0)
        ]
    
    return html.Div([
        # Header de la card
        html.Div([
            html.H4(f"🛒 {row['objeto']}", className="card-title"),
        ], className="card-header"),
        
        # Información del item
        html.Div([
            html.Div([
                html.Span("📅 ", className="card-info-label"),
                html.Span(fecha_formateada, className="card-info-value")
            ], className="card-info-item"),
            
            html.Div([
                html.Span("📦 ", className="card-info-label"),
                html.Span(row['objeto'], className="card-info-value")
            ], className="card-info-item"),
        ], className="card-info"),
        
        # Acciones
        html.Div(actions, className="card-actions") if actions else html.Div()
        
    ], className="data-card", style={"border-left-color": "#2196F3"})

def create_lista_cards_container(lista_df):
    """Crear contenedor con todas las cards de lista"""
    if len(lista_df) == 0:
        return html.Div([
            html.Div("🛒", style={"font-size": "3rem", "margin-bottom": "10px"}),
            html.H4("No hay items en la lista"),
            html.P("Agrega el primer item usando el formulario de abajo")
        ], className="no-data")
    
    # Ordenar por fecha (más recientes primero)
    lista_sorted = lista_df.sort_values('fecha', ascending=False)
    
    cards = []
    for _, row in lista_sorted.iterrows():
        cards.append(create_lista_card(row))
    
    return html.Div([
        html.Div(f"📊 Total: {len(lista_df)} items en lista", 
                style={"text-align": "center", "margin-bottom": "15px", 
                       "font-weight": "bold", "color": "#2196F3"}),
        html.Div(cards, style={"max-height": "500px", "overflow-y": "auto", 
                              "padding-right": "10px"})
    ])

def create_mant_card(row, show_actions=True):
    """Crear card moderna para mantenimiento"""
    
    # Crear acciones si están habilitadas
    actions = []
    if show_actions:
        actions = [
            html.Button("✏️ Editar", 
                       id={'type': 'edit-mant', 'index': row['id']}, 
                       className="btn-icon btn-edit",
                       n_clicks=0),
            html.Button("🗑️ Eliminar", 
                       id={'type': 'delete-mant', 'index': row['id']}, 
                       className="btn-icon btn-delete",
                       n_clicks=0)
        ]
    
    return html.Div([
        # Header de la card
        html.Div([
            html.H4(f"🔧 Año {row['año']}", className="card-title"),
        ], className="card-header"),
        
        # Información del mantenimiento
        html.Div([
            html.Div([
                html.Span("📅 ", className="card-info-label"),
                html.Span(f"Año {row['año']}", className="card-info-value")
            ], className="card-info-item"),
            
            html.Div([
                html.Span("🔨 ", className="card-info-label"),
                html.Span(row['mantenimiento'], className="card-info-value")
            ], className="card-info-item"),
            
            html.Div([
                html.Span("🏗️ ", className="card-info-label"),
                html.Span(row['cadafals'], className="card-info-value")
            ], className="card-info-item"),
        ], className="card-info"),
        
        # Acciones
        html.Div(actions, className="card-actions") if actions else html.Div()
        
    ], className="data-card", style={"border-left-color": "#FF9800"})

def create_mant_cards_container(mant_df):
    """Crear contenedor con todas las cards de mantenimiento"""
    if len(mant_df) == 0:
        return html.Div([
            html.Div("🔧", style={"font-size": "3rem", "margin-bottom": "10px"}),
            html.H4("No hay tareas de mantenimiento"),
            html.P("Agrega la primera tarea usando el formulario de abajo")
        ], className="no-data")
    
    # Ordenar por año
    mant_sorted = mant_df.sort_values('año')
    
    cards = []
    for _, row in mant_sorted.iterrows():
        cards.append(create_mant_card(row))
    
    return html.Div([
        html.Div(f"📊 Total: {len(mant_df)} tareas programadas", 
                style={"text-align": "center", "margin-bottom": "15px", 
                       "font-weight": "bold", "color": "#FF9800"}),
        html.Div(cards, style={"max-height": "500px", "overflow-y": "auto", 
                              "padding-right": "10px"})
    ])

# CSS responsive y diseño mobile-first
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {%favicon%}
        {%css%}
        <style>
            * {
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #E8F5E8 0%, #E3F2FD 100%);
                min-height: 100vh;
            }
            
            /* Header responsive */
            .header-container {
                background: linear-gradient(90deg, #2E7D32 0%, #1976D2 100%);
                color: white;
                padding: 1rem;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .header-container h1 {
                margin: 0;
                font-size: 1.8rem;
            }
            
            @media (max-width: 768px) {
                .header-container h1 {
                    font-size: 1.4rem;
                }
            }
            
            /* Contenedor principal responsive */
            .main-container {
                padding: 1rem;
                max-width: 100%;
                margin: 0 auto;
            }
            
            @media (min-width: 1200px) {
                .main-container {
                    max-width: 1200px;
                    padding: 2rem;
                }
            }
            
            /* Estilos para las pestañas */
            .dash-tab-content {
                padding: 1rem !important;
                background: white !important;
                border-radius: 0 0 8px 8px !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            }
            
            .tab-container .tab {
                background: #f5f5f5 !important;
                border: 1px solid #ddd !important;
                color: #666 !important;
                padding: 12px 16px !important;
                font-weight: 500 !important;
                border-radius: 8px 8px 0 0 !important;
                margin-right: 2px !important;
                transition: all 0.3s ease !important;
            }
            
            .tab-container .tab:hover {
                background: #e8f5e8 !important;
                color: #2E7D32 !important;
            }
            
            .tab-container .tab--selected {
                background: linear-gradient(45deg, #4CAF50, #2E7D32) !important;
                color: white !important;
                border-bottom: none !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
            }
            
            /* Responsive tabs en móvil */
            @media (max-width: 768px) {
                .tab-container {
                    overflow-x: auto !important;
                    white-space: nowrap !important;
                }
                
                .tab-container .tab {
                    display: inline-block !important;
                    min-width: 120px !important;
                    text-align: center !important;
                    font-size: 0.9rem !important;
                    padding: 10px 12px !important;
                }
            }
            
            /* ===== NUEVOS ESTILOS PARA CARDS MODERNAS ===== */
            .data-card {
                background: white;
                border-radius: 12px;
                padding: 16px;
                margin: 10px 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border-left: 4px solid #4CAF50;
                transition: all 0.3s ease;
                position: relative;
            }

            .data-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }

            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 12px;
                flex-wrap: wrap;
            }

            .card-title {
                color: #2E7D32;
                margin: 0;
                font-size: 1.1rem;
                font-weight: 600;
            }

            .card-actions {
                display: flex;
                gap: 8px;
                margin-top: 12px;
                flex-wrap: wrap;
            }

            .card-info {
                display: grid;
                gap: 8px;
            }

            .card-info-item {
                display: flex;
                align-items: center;
                margin: 0;
                padding: 4px 0;
                border-bottom: 1px solid #f0f0f0;
                font-size: 0.95rem;
            }

            .card-info-item:last-child {
                border-bottom: none;
            }

            .card-info-label {
                font-weight: 600;
                min-width: 80px;
                color: #555;
            }

            .card-info-value {
                color: #333;
                word-break: break-word;
            }

            .btn-icon {
                padding: 6px 12px !important;
                border-radius: 6px !important;
                border: none !important;
                cursor: pointer !important;
                font-size: 0.85rem !important;
                transition: all 0.3s ease !important;
                min-width: auto !important;
            }

            .btn-edit {
                background: #2196F3 !important;
                color: white !important;
            }

            .btn-edit:hover {
                background: #1976D2 !important;
            }

            .btn-delete {
                background: #f44336 !important;
                color: white !important;
            }

            .btn-delete:hover {
                background: #d32f2f !important;
            }

            .no-data {
                text-align: center;
                color: #666;
                padding: 40px 20px;
                background: #f9f9f9;
                border-radius: 8px;
                margin: 20px 0;
            }

            /* Responsive para móviles */
            @media (max-width: 768px) {
                .data-card {
                    padding: 12px;
                    margin: 8px 0;
                }
                
                .card-header {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .card-actions {
                    width: 100%;
                    justify-content: center;
                }
                
                .btn-icon {
                    flex: 1;
                    text-align: center;
                }
                
                .card-info-item {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 4px;
                }
                
                .card-info-label {
                    min-width: auto;
                    font-size: 0.8rem;
                }
            }
            
            /* Cards responsive */
            .summary-card {
                transition: all 0.3s ease !important;
            }
            
            .summary-card:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
            }
            
            /* Grid responsive */
            .grid-container {
                display: grid;
                gap: 1rem;
                grid-template-columns: 1fr;
            }
            
            @media (min-width: 768px) {
                .grid-container {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            
            @media (min-width: 1024px) {
                .grid-container {
                    grid-template-columns: repeat(3, 1fr);
                }
            }
            
            @media (min-width: 1200px) {
                .grid-container {
                    grid-template-columns: repeat(4, 1fr);
                }
            }
            
            /* Formularios responsive */
            .form-container {
                background: white;
                padding: 1.5rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 1rem 0;
            }
            
            .form-row {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
                margin: 1rem 0;
            }
            
            .form-item {
                flex: 1;
                min-width: 200px;
            }
            
            @media (max-width: 768px) {
                .form-item {
                    min-width: 100%;
                }
                
                .form-container {
                    padding: 1rem;
                }
            }
            
            /* Botones responsive */
            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                display: inline-block;
                text-align: center;
                min-width: 120px;
            }
            
            .btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            
            @media (max-width: 768px) {
                .btn {
                    width: 100%;
                    margin: 5px 0;
                }
            }
            
            /* Inputs y dropdowns responsive */
            .Select-control, input[type="text"], input[type="number"], .DateInput_input {
                border-radius: 6px !important;
                border: 2px solid #E0E0E0 !important;
                transition: border-color 0.3s ease !important;
                padding: 8px 12px !important;
                width: 100% !important;
            }
            
            .Select-control:focus, input[type="text"]:focus, input[type="number"]:focus {
                border-color: #4CAF50 !important;
                box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
                outline: none !important;
            }
            
            /* Animaciones */
            .fade-in {
                animation: fadeIn 0.5s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            /* Scrollbar personalizado */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #4CAF50;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #2E7D32;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Funciones auxiliares para filtros (SIN CAMBIOS)
def buscar_comidas_por_año_tipo(año=None, tipo_comida=None):
    """Buscar comidas por año y/o tipo de comida"""
    conn = sqlite3.connect('penya_albenc.db')
    
    query = "SELECT * FROM comidas WHERE 1=1"
    params = []
    
    if año:
        query += " AND strftime('%Y', fecha) = ?"
        params.append(str(año))
    
    if tipo_comida:
        query += " AND tipo_comida = ?"
        params.append(tipo_comida)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_tipos_comida():
    """Obtener lista única de tipos de comida"""
    comidas_df = get_data('comidas')
    if len(comidas_df) > 0:
        tipos = comidas_df['tipo_comida'].unique().tolist()
        return [{'label': tipo, 'value': tipo} for tipo in tipos]
    return []

def get_años_disponibles():
    """Obtener lista de años disponibles en comidas"""
    comidas_df = get_data('comidas')
    if len(comidas_df) > 0:
        años = sorted(list(set([int(fecha.split('-')[0]) for fecha in comidas_df['fecha']])))
        return [{'label': str(año), 'value': año} for año in años]
    return []

def get_cocineros_options():
    """Obtener lista única de cocineros desde las comidas existentes"""
    try:
        comidas_df = get_data('comidas')
        if len(comidas_df) == 0:
            return []
        
        # Extraer todos los cocineros únicos
        cocineros_set = set()
        for cocineros_str in comidas_df['cocineros'].dropna():
            # Separar por comas y limpiar espacios
            cocineros = [c.strip() for c in str(cocineros_str).split(',')]
            cocineros_set.update(cocineros)
        
        # Remover strings vacíos
        cocineros_list = sorted([c for c in cocineros_set if c])
        
        return [{'label': cocinero, 'value': cocinero} for cocinero in cocineros_list]
    except Exception as e:
        print(f"Error obteniendo cocineros: {e}")
        return []

def buscar_comidas_por_año_tipo_completas(año, tipo_comida):
    """Buscar todas las comidas de un año y tipo específico"""
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, fecha, cocineros FROM comidas 
        WHERE strftime('%Y', fecha) = ? AND tipo_comida = ?
        ORDER BY fecha
    """, (str(año), tipo_comida))
    results = cursor.fetchall()
    conn.close()
    return results

def intercambiar_cocineros_especifico(año1, tipo1, cocinero1, año2, tipo2, cocinero2):
    """Intercambiar cocineros específicos entre diferentes año/tipo"""
    try:
        # Buscar comidas del primer grupo
        comidas1 = buscar_comidas_por_año_tipo_completas(año1, tipo1)
        if not comidas1:
            return f"❌ No se encontraron comidas en {año1} de tipo '{tipo1}'"
        
        # Buscar comidas del segundo grupo
        comidas2 = buscar_comidas_por_año_tipo_completas(año2, tipo2)
        if not comidas2:
            return f"❌ No se encontraron comidas en {año2} de tipo '{tipo2}'"
        
        cambios_realizados = 0
        
        # Intercambiar en el primer grupo: cocinero1 → cocinero2
        for comida_id, fecha, cocineros_str in comidas1:
            cocineros = [c.strip() for c in cocineros_str.split(',')]
            if cocinero1 in cocineros:
                cocineros[cocineros.index(cocinero1)] = cocinero2
                nueva_lista = ', '.join(cocineros)
                update_data('comidas', comida_id, 'cocineros', nueva_lista)
                cambios_realizados += 1
        
        # Intercambiar en el segundo grupo: cocinero2 → cocinero1
        for comida_id, fecha, cocineros_str in comidas2:
            cocineros = [c.strip() for c in cocineros_str.split(',')]
            if cocinero2 in cocineros:
                cocineros[cocineros.index(cocinero2)] = cocinero1
                nueva_lista = ', '.join(cocineros)
                update_data('comidas', comida_id, 'cocineros', nueva_lista)
                cambios_realizados += 1
        
        if cambios_realizados > 0:
            return f"✅ Intercambio exitoso: {cocinero1} ({tipo1} {año1}) ↔ {cocinero2} ({tipo2} {año2}) en {cambios_realizados} comidas"
        else:
            return f"⚠️ No se encontraron los cocineros especificados en sus respectivos grupos"
    except Exception as e:
        return f"❌ Error en el intercambio: {str(e)}"

def cambiar_cocinero_en_año_tipo(año, tipo_comida, cocinero_antiguo, cocinero_nuevo):
    """Cambiar un cocinero por otro en todas las comidas de un año y tipo"""
    try:
        comidas = buscar_comidas_por_año_tipo_completas(año, tipo_comida)
        if not comidas:
            return f"❌ No se encontraron comidas en {año} de tipo '{tipo_comida}'"
        
        cambios_realizados = 0
        for comida_id, fecha, cocineros_str in comidas:
            cocineros = [c.strip() for c in cocineros_str.split(',')]
            if cocinero_antiguo in cocineros:
                cocineros[cocineros.index(cocinero_antiguo)] = cocinero_nuevo
                nueva_lista = ', '.join(cocineros)
                update_data('comidas', comida_id, 'cocineros', nueva_lista)
                cambios_realizados += 1
        
        if cambios_realizados > 0:
            return f"✅ {cocinero_antiguo} → {cocinero_nuevo} en {cambios_realizados} comidas de {tipo_comida} ({año})"
        else:
            return f"⚠️ {cocinero_antiguo} no encontrado en comidas de {tipo_comida} ({año})"
    except Exception as e:
        return f"❌ Error en el cambio: {str(e)}"

def agregar_cocinero_en_año_tipo(año, tipo_comida, nuevo_cocinero):
    """Agregar un cocinero a todas las comidas de un año y tipo"""
    try:
        comidas = buscar_comidas_por_año_tipo_completas(año, tipo_comida)
        if not comidas:
            return f"❌ No se encontraron comidas en {año} de tipo '{tipo_comida}'"
        
        cambios_realizados = 0
        for comida_id, fecha, cocineros_str in comidas:
            cocineros = [c.strip() for c in cocineros_str.split(',')]
            if nuevo_cocinero not in cocineros:
                cocineros.append(nuevo_cocinero)
                nueva_lista = ', '.join(cocineros)
                update_data('comidas', comida_id, 'cocineros', nueva_lista)
                cambios_realizados += 1
        
        if cambios_realizados > 0:
            return f"✅ {nuevo_cocinero} agregado a {cambios_realizados} comidas de {tipo_comida} ({año})"
        else:
            return f"⚠️ {nuevo_cocinero} ya está en todas las comidas de {tipo_comida} ({año})"
    except Exception as e:
        return f"❌ Error al agregar: {str(e)}"

def eliminar_cocinero_en_año_tipo(año, tipo_comida, cocinero_eliminar):
    """Eliminar un cocinero de todas las comidas de un año y tipo"""
    try:
        comidas = buscar_comidas_por_año_tipo_completas(año, tipo_comida)
        if not comidas:
            return f"❌ No se encontraron comidas en {año} de tipo '{tipo_comida}'"
        
        cambios_realizados = 0
        for comida_id, fecha, cocineros_str in comidas:
            cocineros = [c.strip() for c in cocineros_str.split(',')]
            if cocinero_eliminar in cocineros and len(cocineros) > 1:
                cocineros.remove(cocinero_eliminar)
                nueva_lista = ', '.join(cocineros)
                update_data('comidas', comida_id, 'cocineros', nueva_lista)
                cambios_realizados += 1
        
        if cambios_realizados > 0:
            return f"✅ {cocinero_eliminar} eliminado de {cambios_realizados} comidas de {tipo_comida} ({año})"
        else:
            return f"⚠️ No se pudo eliminar {cocinero_eliminar} (no encontrado o es el único cocinero)"
    except Exception as e:
        return f"❌ Error al eliminar: {str(e)}"

def get_proximos_eventos(limit=5):
    """Obtener los próximos eventos ordenados por fecha"""
    try:
        conn = sqlite3.connect('penya_albenc.db')
        query = """
        SELECT fecha, tipo_comida, tipo_servicio, cocineros
        FROM comidas 
        WHERE fecha >= date('now')
        ORDER BY fecha ASC
        LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=[limit])
        conn.close()
        return df
    except Exception as e:
        print(f"Error obteniendo próximos eventos: {e}")
        return pd.DataFrame()

# Layout principal con pestañas
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🏠 Penya L'Albenc", style={"margin": "0", "color": "white"}),
        html.P("📍 Gestión de grupo", style={"margin": "5px 0 0 0", "opacity": "0.9"})
    ], className="header-container"),
    
    # Contenido principal con pestañas
    html.Div([
        dcc.Tabs(
            id="main-tabs",
            value="inicio",
            children=[
                dcc.Tab(
                    label="🏠 Inicio",
                    value="inicio",
                    className="tab",
                    selected_className="tab--selected"
                ),
                dcc.Tab(
                    label="🍽️ Comidas",
                    value="comidas",
                    className="tab",
                    selected_className="tab--selected"
                ),
                dcc.Tab(
                    label="🛒 Lista Compra",
                    value="lista-compra",
                    className="tab",
                    selected_className="tab--selected"
                ),
                dcc.Tab(
                    label="🔧 Mantenimiento",
                    value="mantenimiento",
                    className="tab",
                    selected_className="tab--selected"
                ),
                dcc.Tab(
                    label="🎉 Fiestas",
                    value="fiestas",
                    className="tab",
                    selected_className="tab--selected"
                )
            ],
            className="tab-container"
        ),
        
        # Contenido de las pestañas
        html.Div(id="tab-content")
    ], className="main-container")
])

# Callback para cambiar el contenido según la pestaña seleccionada
@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value")
)
def render_tab_content(active_tab):
    if active_tab == "comidas":
        return create_comidas_tab()
    elif active_tab == "lista-compra":
        return create_lista_compra_tab()
    elif active_tab == "mantenimiento":
        return create_mantenimiento_tab()
    elif active_tab == "fiestas":
        return create_fiestas_tab()
    else:
        return create_inicio_tab()

# Contenido de la pestaña Inicio (SIN CAMBIOS)
def create_inicio_tab():
    # Obtener datos para resumen
    comidas_df = get_data('comidas')
    lista_df = get_data('lista_compra')
    mantenimiento_df = get_data('mantenimiento')
    eventos_df = get_data('eventos')
    
    # Crear calendario mejorado con eventos
    today = datetime.now()
    cal = calendar.monthcalendar(today.year, today.month)
    month_name = calendar.month_name[today.month]
    
    # Obtener eventos del mes actual
    eventos_mes = eventos_df[eventos_df['fecha'].str.contains(f"{today.year}-{today.month:02d}")] if len(eventos_df) > 0 else pd.DataFrame()
    dias_con_eventos = []
    if len(eventos_mes) > 0:
        dias_con_eventos = [int(fecha.split('-')[2]) for fecha in eventos_mes['fecha'].tolist()]
    
    # Crear calendario con eventos marcados
    calendar_rows = []
    for week in cal:
        week_cells = []
        for day in week:
            if day == 0:
                week_cells.append(html.Td("", style={"padding": "10px", "border": "1px solid #ddd"}))
            else:
                cell_style = {
                    "padding": "10px", 
                    "border": "1px solid #ddd",
                    "text-align": "center",
                    "cursor": "pointer"
                }
                
                if day == today.day:
                    cell_style["background"] = "#2196F3"
                    cell_style["color"] = "white"
                    cell_style["font-weight"] = "bold"
                elif day in dias_con_eventos:
                    cell_style["background"] = "#FF5722"
                    cell_style["color"] = "white"
                    cell_style["font-weight"] = "bold"
                else:
                    cell_style["background"] = "white"
                
                week_cells.append(html.Td(str(day), style=cell_style))
        calendar_rows.append(html.Tr(week_cells))
    
    calendar_table = html.Table([
        html.Thead([
            html.Tr([html.Th(f"{month_name} {today.year}", colSpan=7, 
                           style={"text-align": "center", "background": "#4CAF50", "color": "white", "padding": "15px"})])
        ]),
        html.Thead([
            html.Tr([html.Th(day, style={"background": "#E8F5E8", "padding": "8px", "text-align": "center"}) 
                    for day in ['L', 'M', 'X', 'J', 'V', 'S', 'D']])
        ]),
        html.Tbody(calendar_rows)
    ], style={"border-collapse": "collapse", "width": "100%", "margin": "20px 0"})
    
    return html.Div([
        html.H2("Bienvenido a Penya L'Albenc", style={"color": "#2E7D32", "margin-bottom": "30px", "text-align": "center"}),
        
        # Resumen con contadores
        html.Div([
            html.H3("Resumen General", style={"color": "#1976D2", "margin-bottom": "20px", "text-align": "center"}),
            html.Div([
                html.Div([
                    html.H4(f"{len(comidas_df)}", style={"color": "#4CAF50", "margin": "0", "font-size": "2rem"}),
                    html.P("Comidas planificadas", style={"margin": "5px 0"})
                ], className="summary-card", style={
                    "background": "linear-gradient(135deg, #E8F5E8 0%, #C8E6C9 100%)", 
                    "padding": "25px", "margin": "10px", "border-radius": "12px",
                    "box-shadow": "0 4px 6px rgba(0,0,0,0.1)", "text-align": "center"
                }),
                
                html.Div([
                    html.H4(f"{len(lista_df)}", style={"color": "#2196F3", "margin": "0", "font-size": "2rem"}),
                    html.P("Items en lista", style={"margin": "5px 0"})
                ], className="summary-card", style={
                    "background": "linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)", 
                    "padding": "25px", "margin": "10px", "border-radius": "12px",
                    "box-shadow": "0 4px 6px rgba(0,0,0,0.1)", "text-align": "center"
                }),
                
                html.Div([
                    html.H4(f"{len(mantenimiento_df)}", style={"color": "#FF9800", "margin": "0", "font-size": "2rem"}),
                    html.P("Tareas mantenimiento", style={"margin": "5px 0"})
                ], className="summary-card", style={
                    "background": "linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%)", 
                    "padding": "25px", "margin": "10px", "border-radius": "12px",
                    "box-shadow": "0 4px 6px rgba(0,0,0,0.1)", "text-align": "center"
                }),
                
                html.Div([
                    html.H4(f"{len(eventos_df)}", style={"color": "#9C27B0", "margin": "0", "font-size": "2rem"}),
                    html.P("Eventos programados", style={"margin": "5px 0"})
                ], className="summary-card", style={
                    "background": "linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%)", 
                    "padding": "25px", "margin": "10px", "border-radius": "12px",
                    "box-shadow": "0 4px 6px rgba(0,0,0,0.1)", "text-align": "center"
                }),
            ], className="grid-container"),
        ]),
        
        # Próximos eventos
        html.Div([
            html.H3("🔥 Próximos Eventos", style={"color": "#1976D2", "margin": "30px 0 20px 0", "text-align": "center"}),
            html.Div(id="proximos-eventos-container-tabs")
        ], style={"margin-top": "30px"}),
        
        # Calendario
        html.Div([
            html.H3("📅 Calendario del Mes", style={"color": "#1976D2", "margin": "30px 0 20px 0", "text-align": "center"}),
            html.Div([calendar_table], style={"overflow-x": "auto"})
        ], style={"margin-top": "30px"})
    ], className="fade-in")

# Contenido de la pestaña Comidas (ACTUALIZADA CON CARDS)
def create_comidas_tab():
    tipos_comida = get_tipos_comida()
    años_disponibles = get_años_disponibles()
    cocineros_options = get_cocineros_options()
    
    return html.Div([
        html.H2("🍽️ Gestión de Comidas", style={"color": "#2E7D32", "margin-bottom": "30px", "text-align": "center"}),
        
        # Cards de comidas (REEMPLAZA LA TABLA)
        html.Div([
            html.H3("📋 Lista de Comidas", style={"color": "#2E7D32", "margin": "20px 0 15px 0"}),
            html.Div(id='comidas-cards-container')
        ], className="form-container"),
        
        # Formulario para agregar comida (SIN CAMBIOS)
        html.Div([
            html.H3("➕ Agregar Nueva Comida", style={"color": "#4CAF50", "text-align": "center"}),
            html.Div([
                html.Div([
                    html.Label("📅 Fecha:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.DatePickerSingle(
                        id='comida-fecha-tabs',
                        date=date.today(),
                        display_format='DD/MM/YYYY',
                        style={"width": "100%"}
                    )
                ], className="form-item"),
                
                html.Div([
                    html.Label("🍽️ Tipo de Servicio:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Dropdown(
                        id='comida-servicio-tabs',
                        options=[
                            {'label': '🌅 Comida', 'value': 'Comida'},
                            {'label': '🌙 Cena', 'value': 'Cena'},
                            {'label': '🌅🌙 Comida y Cena', 'value': 'Comida y Cena'}
                        ],
                        placeholder="Selecciona tipo de servicio"
                    )
                ], className="form-item"),
                
                html.Div([
                    html.Label("🥘 Tipo de Comida:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='comida-tipo-tabs', 
                        placeholder="Ej: Comida Normal, Sant Antoni, etc.", 
                        type='text',
                        style={"width": "100%", "padding": "8px"}
                    )
                ], className="form-item"),
                
                html.Div([
                    html.Label("👨‍🍳 Cocineros:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Dropdown(
                        id='comida-cocineros-selector-tabs',
                        options=cocineros_options,
                        placeholder="Selecciona cocineros (múltiple)",
                        multi=True
                    )
                ], className="form-item"),
            ], className="form-row"),
            
            html.Button('✅ Agregar Comida', id='btn-add-comida-tabs', n_clicks=0,
                       className="btn", style={
                           "background": "linear-gradient(45deg, #4CAF50, #45a049)", 
                           "color": "white", "margin": "20px auto", "display": "block"
                       })
        ], className="form-container"),
        
        # Panel avanzado de gestión de cocineros (SIN CAMBIOS)
        html.Div([
            html.H3("🔄 Gestión Avanzada de Cocineros", style={"color": "#1976D2", "margin-bottom": "20px", "text-align": "center"}),
            html.P("💡 Selecciona año y tipo de comida para modificar cocineros en TODAS las comidas de esa categoría", 
                   style={"color": "#666", "font-style": "italic", "margin-bottom": "20px", "text-align": "center"}),
            
            # Filtros principales
            html.Div([
                html.H4("🎯 Seleccionar Comidas a Modificar", style={"color": "#9C27B0", "margin-bottom": "15px", "text-align": "center"}),
                html.Div([
                    html.Div([
                        html.Label("📅 Año:", style={"font-weight": "bold", "color": "#9C27B0"}),
                        dcc.Dropdown(
                            id='filter-año-tabs',
                            options=años_disponibles,
                            placeholder="Selecciona el año"
                        )
                    ], className="form-item"),
                    
                    html.Div([
                        html.Label("🥘 Tipo de Comida:", style={"font-weight": "bold", "color": "#9C27B0"}),
                        dcc.Dropdown(
                            id='filter-tipo-tabs',
                            options=tipos_comida,
                            placeholder="Selecciona el tipo"
                        )
                    ], className="form-item"),
                ], className="form-row")
            ], style={"background": "#F3E5F5", "padding": "15px", "border-radius": "8px", "margin": "15px 0"}),
            
            # Operaciones disponibles
            html.Div([
                # Cambiar cocinero por otro
                html.Div([
                    html.H4("🔄 Cambiar Cocinero", style={"color": "#FF9800", "margin-bottom": "10px", "text-align": "center"}),
                    html.Div([
                        html.Div([
                            dcc.Dropdown(
                                id='cambiar-cocinero-antiguo-tabs',
                                options=cocineros_options,
                                placeholder="Cocinero actual"
                            )
                        ], className="form-item"),
                        html.Div([
                            dcc.Dropdown(
                                id='cambiar-cocinero-nuevo-tabs',
                                options=cocineros_options,
                                placeholder="Cocinero nuevo"
                            )
                        ], className="form-item"),
                    ], className="form-row"),
                    html.Button('🔄 Cambiar', id='btn-cambiar-cocinero-tabs', n_clicks=0,
                               className="btn", style={"background": "#FF9800", "color": "white", "margin": "10px auto", "display": "block"})
                ], style={"background": "#FFF3E0", "padding": "15px", "border-radius": "8px", "margin": "10px 0"}),
                
                # Agregar cocinero
                html.Div([
                    html.H4("➕ Agregar Cocinero", style={"color": "#4CAF50", "margin-bottom": "10px", "text-align": "center"}),
                    html.Div([
                        dcc.Dropdown(
                            id='agregar-cocinero-tabs',
                            options=cocineros_options,
                            placeholder="Selecciona cocinero a agregar"
                        )
                    ], className="form-item"),
                    html.Button('➕ Agregar', id='btn-agregar-cocinero-tabs', n_clicks=0,
                               className="btn", style={"background": "#4CAF50", "color": "white", "margin": "10px auto", "display": "block"})
                ], style={"background": "#E8F5E8", "padding": "15px", "border-radius": "8px", "margin": "10px 0"}),
                
                # Eliminar cocinero
                html.Div([
                    html.H4("➖ Eliminar Cocinero", style={"color": "#F44336", "margin-bottom": "10px", "text-align": "center"}),
                    html.Div([
                        dcc.Dropdown(
                            id='eliminar-cocinero-tabs',
                            options=cocineros_options,
                            placeholder="Selecciona cocinero a eliminar"
                        )
                    ], className="form-item"),
                    html.Button('➖ Eliminar', id='btn-eliminar-cocinero-tabs', n_clicks=0,
                               className="btn", style={"background": "#F44336", "color": "white", "margin": "10px auto", "display": "block"})
                ], style={"background": "#FFEBEE", "padding": "15px", "border-radius": "8px", "margin": "10px 0"}),
            ])
        ], className="form-container"),
        
        # Componentes de confirmación (NUEVOS)
        dcc.ConfirmDialog(
            id='confirm-delete-comida',
            message='¿Estás seguro de que quieres eliminar esta comida?',
        ),
        
        dcc.Store(id='selected-comida-id', data=None),
        
        # Mensajes y confirmaciones
        html.Div(id='comida-output-tabs', style={"margin": "20px 0", "padding": "10px", "text-align": "center"})
    ], className="fade-in")

# Contenido de la pestaña Lista de Compra (ACTUALIZADA CON CARDS)
def create_lista_compra_tab():
    return html.Div([
        html.H2("🛒 Lista de Compra", style={"color": "#2E7D32", "margin-bottom": "30px", "text-align": "center"}),
        
        # Cards de lista (REEMPLAZA LA TABLA)
        html.Div([
            html.H3("📋 Lista de Compras", style={"color": "#2E7D32", "margin": "20px 0 15px 0"}),
            html.Div(id='lista-cards-container')
        ], className="form-container"),
        
        # Formulario para agregar (SIN CAMBIOS)
        html.Div([
            html.H3("➕ Agregar Nuevo Item", style={"color": "#2196F3", "text-align": "center"}),
            html.Div([
                html.Div([
                    html.Label("📅 Fecha:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.DatePickerSingle(
                        id='lista-fecha-tabs',
                        date=date.today(),
                        display_format='DD/MM/YYYY'
                    )
                ], className="form-item"),
                
                html.Div([
                    html.Label("📦 Objeto a Comprar:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='lista-objeto-tabs', 
                        placeholder="Ej: Tomates, Pan, Aceite...", 
                        type='text',
                        style={"width": "100%", "padding": "8px"}
                    )
                ], className="form-item"),
            ], className="form-row"),
            
            html.Button('✅ Agregar Item', id='btn-add-lista-tabs', n_clicks=0,
                       className="btn", style={
                           "background": "linear-gradient(45deg, #2196F3, #1976D2)", 
                           "color": "white", "margin": "20px auto", "display": "block"
                       })
        ], className="form-container"),
        
        # Componentes de confirmación (NUEVOS)
        dcc.ConfirmDialog(
            id='confirm-delete-lista',
            message='¿Estás seguro de que quieres eliminar este item de la lista?',
        ),
        
        dcc.Store(id='selected-lista-id', data=None),
        
        html.Div(id='lista-output-tabs', style={"margin": "20px 0", "padding": "10px", "text-align": "center"})
    ], className="fade-in")

# Contenido de la pestaña Mantenimiento (ACTUALIZADA CON CARDS)
def create_mantenimiento_tab():
    return html.Div([
        html.H2("🔧 Mantenimiento", style={"color": "#2E7D32", "margin-bottom": "30px", "text-align": "center"}),
        
        # Cards de mantenimiento (REEMPLAZA LA TABLA)
        html.Div([
            html.H3("📋 Tareas de Mantenimiento", style={"color": "#2E7D32", "margin": "20px 0 15px 0"}),
            html.Div(id='mant-cards-container')
        ], className="form-container"),
        
        # Formulario para agregar (SIN CAMBIOS)
        html.Div([
            html.H3("➕ Agregar Tarea de Mantenimiento", style={"color": "#FF9800", "text-align": "center"}),
            html.Div([
                html.Div([
                    html.Label("📅 Año:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='mant-año-tabs', 
                        placeholder="2025", 
                        type='number', 
                        value=datetime.now().year,
                        style={"width": "100%", "padding": "8px"}
                    )
                ], className="form-item"),
                
                html.Div([
                    html.Label("🔨 Mantenimiento:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='mant-mantenimiento-tabs', 
                        placeholder="Descripción del mantenimiento", 
                        type='text',
                        style={"width": "100%", "padding": "8px"}
                    )
                ], className="form-item"),
                
                html.Div([
                    html.Label("🏗️ Cadafals:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='mant-cadafals-tabs', 
                        placeholder="Responsables de cadafals", 
                        type='text',
                        style={"width": "100%", "padding": "8px"}
                    )
                ], className="form-item"),
            ], className="form-row"),
            
            html.Button('✅ Agregar Tarea', id='btn-add-mant-tabs', n_clicks=0,
                       className="btn", style={
                           "background": "linear-gradient(45deg, #FF9800, #F57C00)", 
                           "color": "white", "margin": "20px auto", "display": "block"
                       })
        ], className="form-container"),
        
        # Componentes de confirmación (NUEVOS)
        dcc.ConfirmDialog(
            id='confirm-delete-mant',
            message='¿Estás seguro de que quieres eliminar esta tarea?',
        ),
        
        dcc.Store(id='selected-mant-id', data=None),
        
        html.Div(id='mant-output-tabs', style={"margin": "20px 0", "padding": "10px", "text-align": "center"})
    ], className="fade-in")

# Contenido de la pestaña Fiestas (SIN CAMBIOS)
def create_fiestas_tab():
    return html.Div([
        html.H2("🎉 Fiestas", style={"color": "#2E7D32", "margin-bottom": "30px", "text-align": "center"}),
        
        # Contenido temporal
        html.Div([
            html.Div([
                html.H3("🚧 En Construcción", style={"color": "#9C27B0", "text-align": "center"}),
                html.P("Esta sección estará disponible en próximas actualizaciones.", 
                       style={"font-size": "18px", "color": "#666", "text-align": "center"}),
                html.P("Aquí podrás gestionar:", style={"margin-top": "20px", "font-weight": "bold", "text-align": "center"}),
                html.Ul([
                    html.Li("🎭 Eventos especiales y fiestas"),
                    html.Li("🎪 Organización de actividades"),
                    html.Li("🎨 Decoraciones y temáticas"),
                    html.Li("🎵 Música y entretenimiento"),
                    html.Li("📸 Galería de fotos"),
                ], style={"color": "#555", "margin": "20px 0", "text-align": "left", "max-width": "400px", "margin": "20px auto"})
            ], className="form-container", style={"text-align": "center"}),
            
            # Próximas fiestas
            html.Div([
                html.H4("🎊 Próximos Eventos Especiales", style={"color": "#1976D2", "text-align": "center"}),
                html.Div([
                    html.Div([
                        html.H5("🎭 Sant Antoni", style={"color": "#FF5722"}),
                        html.P("📅 Enero - Cena especial"),
                        html.P("🍽️ Tradición gastronómica")
                    ], style={"background": "#FFF3E0", "padding": "15px", "margin": "10px", "border-radius": "8px", "text-align": "center"}),
                    
                    html.Div([
                        html.H5("🌸 Brena St Vicent", style={"color": "#4CAF50"}),
                        html.P("📅 Mayo - Comida y Cena"),
                        html.P("🌺 Celebración primaveral")
                    ], style={"background": "#E8F5E8", "padding": "15px", "margin": "10px", "border-radius": "8px", "text-align": "center"}),
                    
                    html.Div([
                        html.H5("🎪 Fira Magdalena", style={"color": "#9C27B0"}),
                        html.P("📅 Julio - Gran celebración"),
                        html.P("🎉 Evento principal del año")
                    ], style={"background": "#F3E5F5", "padding": "15px", "margin": "10px", "border-radius": "8px", "text-align": "center"}),
                ], className="grid-container")
            ], style={"margin-top": "30px"})
        ])
    ], className="fade-in")

# ===== CALLBACKS ACTUALIZADOS PARA CARDS =====

# Callback para actualizar cards de comidas
@app.callback(
    Output('comidas-cards-container', 'children'),
    [Input('btn-add-comida-tabs', 'n_clicks'),
     Input('btn-cambiar-cocinero-tabs', 'n_clicks'),
     Input('btn-agregar-cocinero-tabs', 'n_clicks'),
     Input('btn-eliminar-cocinero-tabs', 'n_clicks'),
     Input('confirm-delete-comida', 'submit_n_clicks'),
     Input('main-tabs', 'value')]
)
def update_comidas_cards(n_add, n_cambiar, n_agregar, n_eliminar, n_delete_confirm, active_tab):
    if active_tab != 'comidas':
        return []
    
    comidas_df = get_data('comidas')
    return create_comidas_cards_container(comidas_df)

# Callback para actualizar cards de lista
@app.callback(
    Output('lista-cards-container', 'children'),
    [Input('btn-add-lista-tabs', 'n_clicks'),
     Input('confirm-delete-lista', 'submit_n_clicks'),
     Input('main-tabs', 'value')]
)
def update_lista_cards(n_add, n_delete_confirm, active_tab):
    if active_tab != 'lista-compra':
        return []
    
    lista_df = get_data('lista_compra')
    return create_lista_cards_container(lista_df)

# Callback para actualizar cards de mantenimiento
@app.callback(
    Output('mant-cards-container', 'children'),
    [Input('btn-add-mant-tabs', 'n_clicks'),
     Input('confirm-delete-mant', 'submit_n_clicks'),
     Input('main-tabs', 'value')]
)
def update_mant_cards(n_add, n_delete_confirm, active_tab):
    if active_tab != 'mantenimiento':
        return []
    
    mant_df = get_data('mantenimiento')
    return create_mant_cards_container(mant_df)

# Callbacks para manejar confirmaciones de eliminación - COMIDAS
@app.callback(
    [Output('confirm-delete-comida', 'displayed'),
     Output('selected-comida-id', 'data')],
    [Input({'type': 'delete-comida', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def show_delete_confirmation_comida(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered:
        return False, None
    
    # Obtener qué botón fue presionado
    for i, n_clicks in enumerate(n_clicks_list):
        if n_clicks and n_clicks > 0:
            button_id = ctx.triggered[0]['prop_id']
            import json
            button_data = json.loads(button_id.split('.')[0])
            return True, button_data['index']
    
    return False, None

# Callback para confirmar eliminación de comida
@app.callback(
    Output('comida-output-tabs', 'children', allow_duplicate=True),
    [Input('confirm-delete-comida', 'submit_n_clicks')],
    [State('selected-comida-id', 'data')],
    prevent_initial_call=True
)
def delete_comida_confirmed(submit_n_clicks, selected_id):
    if submit_n_clicks and selected_id:
        delete_data('comidas', selected_id)
        return html.Div("🗑️ Comida eliminada exitosamente!", 
                       style={"color": "red", "font-weight": "bold"})
    return ""

# Callbacks para manejar confirmaciones de eliminación - LISTA
@app.callback(
    [Output('confirm-delete-lista', 'displayed'),
     Output('selected-lista-id', 'data')],
    [Input({'type': 'delete-lista', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def show_delete_confirmation_lista(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered:
        return False, None
    
    for i, n_clicks in enumerate(n_clicks_list):
        if n_clicks and n_clicks > 0:
            button_id = ctx.triggered[0]['prop_id']
            import json
            button_data = json.loads(button_id.split('.')[0])
            return True, button_data['index']
    
    return False, None

# Callback para confirmar eliminación de lista
@app.callback(
    Output('lista-output-tabs', 'children', allow_duplicate=True),
    [Input('confirm-delete-lista', 'submit_n_clicks')],
    [State('selected-lista-id', 'data')],
    prevent_initial_call=True
)
def delete_lista_confirmed(submit_n_clicks, selected_id):
    if submit_n_clicks and selected_id:
        delete_data('lista_compra', selected_id)
        return html.Div("🗑️ Item eliminado exitosamente!", 
                       style={"color": "red", "font-weight": "bold"})
    return ""

# Callbacks para manejar confirmaciones de eliminación - MANTENIMIENTO
@app.callback(
    [Output('confirm-delete-mant', 'displayed'),
     Output('selected-mant-id', 'data')],
    [Input({'type': 'delete-mant', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def show_delete_confirmation_mant(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered:
        return False, None
    
    for i, n_clicks in enumerate(n_clicks_list):
        if n_clicks and n_clicks > 0:
            button_id = ctx.triggered[0]['prop_id']
            import json
            button_data = json.loads(button_id.split('.')[0])
            return True, button_data['index']
    
    return False, None

# Callback para confirmar eliminación de mantenimiento
@app.callback(
    Output('mant-output-tabs', 'children', allow_duplicate=True),
    [Input('confirm-delete-mant', 'submit_n_clicks')],
    [State('selected-mant-id', 'data')],
    prevent_initial_call=True
)
def delete_mant_confirmed(submit_n_clicks, selected_id):
    if submit_n_clicks and selected_id:
        delete_data('mantenimiento', selected_id)
        return html.Div("🗑️ Tarea eliminada exitosamente!", 
                       style={"color": "red", "font-weight": "bold"})
    return ""

# Callbacks para agregar datos (ACTUALIZADOS)
@app.callback(
    Output('comida-output-tabs', 'children'),
    [Input('btn-add-comida-tabs', 'n_clicks'), 
     Input('btn-cambiar-cocinero-tabs', 'n_clicks'),
     Input('btn-agregar-cocinero-tabs', 'n_clicks'),
     Input('btn-eliminar-cocinero-tabs', 'n_clicks')],
    [State('comida-fecha-tabs', 'date'), State('comida-servicio-tabs', 'value'),
     State('comida-tipo-tabs', 'value'), State('comida-cocineros-selector-tabs', 'value'),
     State('filter-año-tabs', 'value'), State('filter-tipo-tabs', 'value'),
     State('cambiar-cocinero-antiguo-tabs', 'value'), State('cambiar-cocinero-nuevo-tabs', 'value'),
     State('agregar-cocinero-tabs', 'value'), State('eliminar-cocinero-tabs', 'value')],
    prevent_initial_call=True
)
def handle_comidas_actions(n_add, n_cambiar, n_agregar, n_eliminar,
                          fecha, servicio, tipo, cocineros_lista, 
                          filter_año, filter_tipo, cocinero_antiguo, cocinero_nuevo,
                          nuevo_cocinero, cocinero_eliminar):
    ctx = callback_context
    
    if not ctx.triggered:
        return ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Agregar nueva comida
    if trigger_id == 'btn-add-comida-tabs' and n_add > 0:
        if fecha and servicio and tipo and cocineros_lista:
            cocineros_str = ', '.join(cocineros_lista)
            add_data('comidas', (fecha, servicio, tipo, cocineros_str))
            add_data('eventos', (fecha, tipo, servicio))
            return html.Div("✅ Comida agregada exitosamente! 🎉", 
                           style={"color": "green", "font-weight": "bold"})
        else:
            return html.Div("⚠️ Por favor completa todos los campos.", 
                           style={"color": "orange", "font-weight": "bold"})
    
    # Cambiar cocinero
    elif trigger_id == 'btn-cambiar-cocinero-tabs' and n_cambiar > 0:
        if filter_año and filter_tipo and cocinero_antiguo and cocinero_nuevo:
            resultado = cambiar_cocinero_en_año_tipo(filter_año, filter_tipo, cocinero_antiguo, cocinero_nuevo)
            return html.Div(f"🔄 {resultado}", 
                           style={"color": "blue", "font-weight": "bold"})
        else:
            return html.Div("⚠️ Selecciona año, tipo y ambos cocineros.", 
                           style={"color": "orange", "font-weight": "bold"})
    
    # Agregar cocinero
    elif trigger_id == 'btn-agregar-cocinero-tabs' and n_agregar > 0:
        if filter_año and filter_tipo and nuevo_cocinero:
            resultado = agregar_cocinero_en_año_tipo(filter_año, filter_tipo, nuevo_cocinero)
            return html.Div(f"➕ {resultado}", 
                           style={"color": "green", "font-weight": "bold"})
        else:
            return html.Div("⚠️ Selecciona año, tipo y cocinero.", 
                           style={"color": "orange", "font-weight": "bold"})
    
    # Eliminar cocinero
    elif trigger_id == 'btn-eliminar-cocinero-tabs' and n_eliminar > 0:
        if filter_año and filter_tipo and cocinero_eliminar:
            resultado = eliminar_cocinero_en_año_tipo(filter_año, filter_tipo, cocinero_eliminar)
            return html.Div(f"➖ {resultado}", 
                           style={"color": "red", "font-weight": "bold"})
        else:
            return html.Div("⚠️ Selecciona año, tipo y cocinero.", 
                           style={"color": "orange", "font-weight": "bold"})
    
    return ""

# Callback para agregar lista
@app.callback(
    Output('lista-output-tabs', 'children'),
    [Input('btn-add-lista-tabs', 'n_clicks')],
    [State('lista-fecha-tabs', 'date'), State('lista-objeto-tabs', 'value')],
    prevent_initial_call=True
)
def handle_lista_add(n_clicks, fecha, objeto):
    if n_clicks > 0:
        if fecha and objeto:
            add_data('lista_compra', (fecha, objeto))
            return html.Div("✅ Item agregado exitosamente! 🛒", 
                           style={"color": "green", "font-weight": "bold"})
        else:
            return html.Div("⚠️ Por favor completa todos los campos.", 
                           style={"color": "orange", "font-weight": "bold"})
    return ""

# Callback para agregar mantenimiento
@app.callback(
    Output('mant-output-tabs', 'children'),
    [Input('btn-add-mant-tabs', 'n_clicks')],
    [State('mant-año-tabs', 'value'), State('mant-mantenimiento-tabs', 'value'),
     State('mant-cadafals-tabs', 'value')],
    prevent_initial_call=True
)
def handle_mant_add(n_clicks, año, mantenimiento, cadafals):
    if n_clicks > 0:
        if año and mantenimiento and cadafals:
            add_data('mantenimiento', (año, mantenimiento, cadafals))
            return html.Div("✅ Tarea agregada exitosamente! 🔧", 
                           style={"color": "green", "font-weight": "bold"})
        else:
            return html.Div("⚠️ Por favor completa todos los campos.", 
                           style={"color": "orange", "font-weight": "bold"})
    return ""

# Callback para actualizar opciones dinámicamente
@app.callback(
    [Output('filter-tipo-tabs', 'options'),
     Output('comida-cocineros-selector-tabs', 'options'),
     Output('cambiar-cocinero-antiguo-tabs', 'options'),
     Output('cambiar-cocinero-nuevo-tabs', 'options'),
     Output('agregar-cocinero-tabs', 'options'),
     Output('eliminar-cocinero-tabs', 'options')],
    [Input('btn-add-comida-tabs', 'n_clicks'),
     Input('main-tabs', 'value')],
    prevent_initial_call=True
)
def update_filter_options_tabs(n_clicks, active_tab):
    tipos = get_tipos_comida()
    cocineros = get_cocineros_options()
    return tipos, cocineros, cocineros, cocineros, cocineros, cocineros

# Callback para próximos eventos en la pestaña inicio
@app.callback(
    Output('proximos-eventos-container-tabs', 'children'),
    [Input('main-tabs', 'value')]
)
def update_proximos_eventos_tabs(active_tab):
    if active_tab != 'inicio':
        return []
    
    proximos_df = get_proximos_eventos(5)
    
    if len(proximos_df) == 0:
        return [html.P("No hay eventos próximos", style={"text-align": "center", "color": "#666"})]
    
    eventos_cards = []
    for _, evento in proximos_df.iterrows():
        # Formatear fecha a D-M-A
        try:
            fecha_obj = datetime.strptime(evento['fecha'], '%Y-%m-%d')
            fecha_formateada = fecha_obj.strftime('%d-%m-%Y')
        except:
            fecha_formateada = evento['fecha']
        
        card = html.Div([
            html.H4(f"🎉 {evento['tipo_comida']}", style={"color": "#FF5722", "margin-bottom": "8px"}),
            html.P(f"📅 {fecha_formateada}", style={"margin": "5px 0", "font-weight": "bold"}),
            html.P(f"🍽️ {evento['tipo_servicio']}", style={"margin": "5px 0"}),
            html.P(f"👨‍🍳 {evento['cocineros']}", style={"margin": "5px 0", "font-size": "0.9rem", "color": "#666"})
        ], style={
            "background": "linear-gradient(135deg, #FFF3E0 0%, #FFCC80 100%)",
            "padding": "15px", "margin": "10px", "border-radius": "8px",
            "border-left": "4px solid #FF9800", "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
            "flex": "1", "min-width": "280px"
        })
        eventos_cards.append(card)
    
    return html.Div(eventos_cards, style={"display": "flex", "flex-wrap": "wrap", "gap": "10px"})

# ===== FUNCIONES DE CARGA DE DATOS (SIN CAMBIOS) =====

def load_initial_data():
    """Cargar datos iniciales si la base de datos está vacía"""
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    # Verificar si ya hay datos
    cursor.execute("SELECT COUNT(*) FROM comidas")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Datos de comidas (muestra - puedes agregar más desde el archivo que subiste)
    comidas_data = [
        ('2025-01-18', 'Cena', 'Sant Antoni', 'Lluis, Alonso, Raul A., David'),
        ('2025-05-03', 'Comida y Cena', 'Brena St Vicent', 'Xisco, Serafin, Alfonso, Raul M.'),
        ('2025-05-31', 'Comida', 'Penya Taurina', 'Juan Fernando, Victor M., Diego'),
        ('2025-07-19', 'Comida y Cena', 'Fira Magdalena', 'Juan Ramon, Victor Z., Miguel A., Oscar'),
        ('2026-01-17', 'Cena', 'Sant Antoni', 'Serafin, Juan Fernando, Oscar, Alfonso'),
    ]
    
    # Datos completos de mantenimiento (2025-2045)
    mantenimiento_data = [
        (2025, 'David, Juan Fernando', 'David, Juan Fernando, Diego, Miguel A.'),
        (2026, 'Diego, Miguel A.', 'Diego, Miguel A., Xisco, Serafin'),
        (2027, 'Xisco, Serafin', 'Xisco, Serafin, Juan Ramon, Oscar'),
        (2028, 'Juan Ramon, Oscar', 'Juan Ramon, Oscar, Alfonso, Victor Z.'),
        (2029, 'Alfonso, Victor Z.', 'Alfonso, Victor Z., David, Victor M.'),
        (2030, 'David, Victor M.', 'David, Victor M., Xisco, Alonso'),
        (2031, 'Xisco, Alonso', 'Xisco, Alonso, Serafin, Raul M.'),
        (2032, 'Serafin, Raul M.', 'Serafin, Raul M., Alfonso, Raul A.'),
        (2033, 'Alfonso, Raul A.', 'Alfonso, Raul A., Miguel A., Juan Fernando'),
        (2034, 'Miguel A., Juan Fernando', 'Miguel A., Juan Fernando, Oscar, Diego'),
        (2035, 'Oscar, Diego', 'Oscar, Diego, Juan Ramon, Victor M.'),
        (2036, 'Juan Ramon, Victor M.', 'Juan Ramon, Victor M., David, Victor Z.'),
        (2037, 'David, Victor Z.', 'David, Victor Z., Xisco, Raul M.'),
        (2038, 'Xisco, Raul M.', 'Xisco, Raul M., Serafin, Alonso'),
        (2039, 'Serafin, Alonso', 'Serafin, Alonso, Alfonso, Raul A.'),
        (2040, 'Alfonso, Raul A.', 'Alfonso, Juan Fernando, Miguel A., Raul A.'),
        (2041, 'Miguel A., Juan Fernando', 'Miguel A., Juan Fernando, Oscar, Victor M.'),
        (2042, 'Oscar, Victor M.', 'Oscar, Victor M., Alfonso, Diego'),
        (2043, 'Alfonso, Diego', 'Alfonso, Diego, Juan Ramon, Alonso'),
        (2044, 'Juan Ramon, Alonso', 'Juan Ramon, Alonso, Miguel A., Victor Z.'),
        (2045, 'Miguel A., Victor Z.', 'Miguel A., Victor Z., Serafin, Juan Fernando'),
    ]
    
    # Insertar datos
    for data in comidas_data:
        cursor.execute("INSERT INTO comidas (fecha, tipo_servicio, tipo_comida, cocineros) VALUES (?, ?, ?, ?)", data)
        # Crear evento en calendario
        cursor.execute("INSERT INTO eventos (fecha, evento, tipo) VALUES (?, ?, ?)", (data[0], data[2], data[1]))
    
    for data in mantenimiento_data:
        cursor.execute("INSERT INTO mantenimiento (año, mantenimiento, cadafals) VALUES (?, ?, ?)", data)
    
    conn.commit()
    conn.close()
    
    # Inicializar cocineros únicos desde las comidas cargadas
    inicializar_cocineros_desde_comidas()

def load_eventos_completos():
    """Cargar todos los eventos de la tabla completa 2025-2045"""
    import calendar
    from datetime import datetime, timedelta
    
    def get_tercer_sabado_enero(año):
        """Obtener el tercer sábado de enero"""
        primer_dia = datetime(año, 1, 1)
        dias_hasta_sabado = (5 - primer_dia.weekday()) % 7  # 5 = sábado
        primer_sabado = primer_dia + timedelta(days=dias_hasta_sabado)
        tercer_sabado = primer_sabado + timedelta(days=14)  # +2 semanas
        return tercer_sabado.strftime('%Y-%m-%d')
    
    def get_sabado_cercano_28_abril(año):
        """Obtener el sábado más cercano al 28 de abril"""
        abril_28 = datetime(año, 4, 28)
        dias_hasta_sabado = (5 - abril_28.weekday()) % 7
        if dias_hasta_sabado <= 3:  # Si está a 3 días o menos, usar ese sábado
            sabado = abril_28 + timedelta(days=dias_hasta_sabado)
        else:  # Si no, usar el sábado anterior
            sabado = abril_28 - timedelta(days=abril_28.weekday() + 2)
        return sabado.strftime('%Y-%m-%d')
    
    def get_tercer_sabado_julio(año):
        """Obtener el tercer sábado de julio"""
        primer_dia = datetime(año, 7, 1)
        dias_hasta_sabado = (5 - primer_dia.weekday()) % 7
        primer_sabado = primer_dia + timedelta(days=dias_hasta_sabado)
        tercer_sabado = primer_sabado + timedelta(days=14)
        return tercer_sabado.strftime('%Y-%m-%d')
    
    def get_ultimo_sabado_mayo(año):
        """Obtener el último sábado de mayo"""
        # Último día de mayo
        ultimo_dia = datetime(año, 5, 31)
        # Encontrar el último sábado
        dias_desde_sabado = (ultimo_dia.weekday() + 2) % 7  # +2 porque sábado es 5
        ultimo_sabado = ultimo_dia - timedelta(days=dias_desde_sabado)
        return ultimo_sabado.strftime('%Y-%m-%d')
    
    # Datos completos de la tabla
    eventos_data = {
        2025: {
            'sant_antoni': 'Lluis, Alonso, Raul A., David',
            'brena_st_vicent': 'Xisco, Serafin, Alfonso, Raul M.',
            'fira_magdalena': 'Juan Ramon, Victor Z., Miguel A., Oscar',
            'penya_taurina': 'Juan Fernando, Victor M., Diego'
        },
        2026: {
            'sant_antoni': 'Serafin, Juan Fernando, Oscar, Alfonso',
            'brena_st_vicent': 'Alonso, Victor M., Juan Ramon, Miguel A.',
            'fira_magdalena': 'Xisco, David, Diego, Raul A.',
            'penya_taurina': 'Victor Z., Lluis, Raul M.'
        },
        2027: {
            'sant_antoni': 'Raul A., Diego, Alonso, Victor Z.',
            'brena_st_vicent': 'Lluis, David, Oscar, Serafin',
            'fira_magdalena': 'Juan Fernando, Victor M., Alfonso, Juan Ramon',
            'penya_taurina': 'Xisco, Miguel A., Raul M.'
        },
        2028: {
            'sant_antoni': 'Juan Fernando, Serafin, Alfonso, David',
            'brena_st_vicent': 'Xisco, Diego, Victor Z., Juan Ramon',
            'fira_magdalena': 'Raul M., Oscar, Miguel A., Raul A.',
            'penya_taurina': 'Victor M., Alonso, Lluis'
        },
        2029: {
            'sant_antoni': 'Victor M., Raul A., Xisco, Miguel A.',
            'brena_st_vicent': 'Alonso, Lluis, Juan Fernando, Serafin',
            'fira_magdalena': 'Victor Z., Diego, Juan Ramon, David',
            'penya_taurina': 'Oscar, Raul M., Alfonso'
        },
        2030: {
            'sant_antoni': 'Juan Fernando, Alonso, Diego, Victor Z.',
            'brena_st_vicent': 'Raul A., Oscar, David, Alfonso',
            'fira_magdalena': 'Serafin, Miguel A., Victor M., Lluis',
            'penya_taurina': 'Xisco, Juan Ramon, Raul M.'
        },
        2031: {
            'sant_antoni': 'Victor M., Juan Ramon, Oscar, David',
            'brena_st_vicent': 'Raul M., Alonso, Lluis, Xisco',
            'fira_magdalena': 'Diego, Raul A., Juan Fernando, Victor Z.',
            'penya_taurina': 'Alfonso, Serafin, Miguel A.'
        },
        2032: {
            'sant_antoni': 'Victor Z., Raul M., Serafin, Juan Fernando',
            'brena_st_vicent': 'Victor M., Raul A., Diego, Alfonso',
            'fira_magdalena': 'Juan Ramon, Oscar, Lluis, Miguel A.',
            'penya_taurina': 'David, Xisco, Alonso'
        },
        2033: {
            'sant_antoni': 'Alfonso, Miguel A., Victor M., David',
            'brena_st_vicent': 'Xisco, Lluis, Alonso, Victor Z.',
            'fira_magdalena': 'Raul M., Juan Fernando, Serafin, Raul A.',
            'penya_taurina': 'Diego, Juan Ramon, Oscar'
        },
        2034: {
            'sant_antoni': 'Raul A., Lluis, Diego, Juan Fernando',
            'brena_st_vicent': 'Alfonso, Victor M., David, Serafin',
            'fira_magdalena': 'Juan Ramon, Oscar, Xisco, Victor Z.',
            'penya_taurina': 'Raul M., Miguel A., Alonso'
        },
        2035: {
            'sant_antoni': 'Juan Ramon, Alonso, Xisco, David',
            'brena_st_vicent': 'Raul A., Lluis, Diego, Victor Z.',
            'fira_magdalena': 'Victor M., Alfonso, Juan Fernando, Miguel A.',
            'penya_taurina': 'Raul M., Oscar, Serafin'
        },
        2036: {
            'sant_antoni': 'Victor Z., Diego, Raul A., Raul M.',
            'brena_st_vicent': 'Juan Fernando, Alfonso, David, Oscar',
            'fira_magdalena': 'Serafin, Lluis, Xisco, Juan Ramon',
            'penya_taurina': 'Alonso, Victor M., Miguel A.'
        },
        2037: {
            'sant_antoni': 'Alfonso, Victor M., Miguel A., Xisco',
            'brena_st_vicent': 'Alonso, Raul M., Raul A., Lluis',
            'fira_magdalena': 'Diego, Victor Z., David, Juan Fernando',
            'penya_taurina': 'Oscar, Serafin, Juan Ramon'
        },
        2038: {
            'sant_antoni': 'Raul A., Raul M., Juan Fernando, David',
            'brena_st_vicent': 'Victor Z., Juan Ramon, Diego, Victor M.',
            'fira_magdalena': 'Alonso, Oscar, Xisco, Alfonso',
            'penya_taurina': 'Miguel A., Serafin, Lluis'
        },
        2039: {
            'sant_antoni': 'Oscar, Serafin, Juan Ramon, Alfonso',
            'brena_st_vicent': 'Raul M., Lluis, Alonso, Juan Fernando',
            'fira_magdalena': 'Victor M., Raul A., Diego, Miguel A.',
            'penya_taurina': 'Victor Z., David, Xisco'
        },
        2040: {
            'sant_antoni': 'Xisco, Raul M., David, Victor Z.',
            'brena_st_vicent': 'Alfonso, Victor M., Diego, Oscar',
            'fira_magdalena': 'Serafin, Lluis, Alonso, Juan Fernando',
            'penya_taurina': 'Miguel A., Raul A., Juan Ramon'
        },
        2041: {
            'sant_antoni': 'Serafin, Miguel A., Alonso, Raul A.',
            'brena_st_vicent': 'Lluis, Raul M., Juan Ramon, David',
            'fira_magdalena': 'Diego, Xisco, Victor Z., Victor M.',
            'penya_taurina': 'Oscar, Juan Fernando, Alfonso'
        },
        2042: {
            'sant_antoni': 'Lluis, Raul M., Juan Ramon, Oscar',
            'brena_st_vicent': 'Alonso, Miguel A., Raul A., Xisco',
            'fira_magdalena': 'Alfonso, Juan Fernando, Serafin, David',
            'penya_taurina': 'Victor M., Victor Z., Diego'
        },
        2043: {
            'sant_antoni': 'Alfonso, Xisco, Victor M., Juan Fernando',
            'brena_st_vicent': 'Victor Z., Diego, Juan Ramon, David',
            'fira_magdalena': 'Raul M., Alonso, Lluis, Miguel A.',
            'penya_taurina': 'Serafin, Raul A., Oscar'
        },
        2044: {
            'sant_antoni': 'Diego, Miguel A., Serafin, Oscar',
            'brena_st_vicent': 'Juan Fernando, Alfonso, Alonso, Raul A.',
            'fira_magdalena': 'Victor M., Xisco, Victor Z., David',
            'penya_taurina': 'Lluis, Juan Ramon, Raul M.'
        },
        2045: {
            'sant_antoni': 'Victor M., Alonso, Alfonso, Raul A.',
            'brena_st_vicent': 'Xisco, Diego, Raul M., Serafin',
            'fira_magdalena': 'Oscar, Miguel A., Juan Ramon, Juan Fernando',
            'penya_taurina': 'Lluis, David, Victor Z.'
        }
    }
    
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    # BORRAR todos los datos existentes
    cursor.execute("DELETE FROM comidas")
    cursor.execute("DELETE FROM eventos")
    
    # Insertar nuevos datos
    for año, eventos in eventos_data.items():
        # Sant Antoni - tercer sábado de enero
        fecha_sant_antoni = get_tercer_sabado_enero(año)
        cursor.execute("INSERT INTO comidas (fecha, tipo_servicio, tipo_comida, cocineros) VALUES (?, ?, ?, ?)",
                      (fecha_sant_antoni, 'Cena', 'Sant Antoni', eventos['sant_antoni']))
        cursor.execute("INSERT INTO eventos (fecha, evento, tipo) VALUES (?, ?, ?)",
                      (fecha_sant_antoni, 'Sant Antoni', 'Cena'))
        
        # Brena St Vicent - sábado cercano al 28 de abril
        fecha_brena = get_sabado_cercano_28_abril(año)
        cursor.execute("INSERT INTO comidas (fecha, tipo_servicio, tipo_comida, cocineros) VALUES (?, ?, ?, ?)",
                      (fecha_brena, 'Comida y Cena', 'Brena St Vicent', eventos['brena_st_vicent']))
        cursor.execute("INSERT INTO eventos (fecha, evento, tipo) VALUES (?, ?, ?)",
                      (fecha_brena, 'Brena St Vicent', 'Comida y Cena'))
        
        # Fira Magdalena - tercer sábado de julio
        fecha_fira = get_tercer_sabado_julio(año)
        cursor.execute("INSERT INTO comidas (fecha, tipo_servicio, tipo_comida, cocineros) VALUES (?, ?, ?, ?)",
                      (fecha_fira, 'Comida y Cena', 'Fira Magdalena', eventos['fira_magdalena']))
        cursor.execute("INSERT INTO eventos (fecha, evento, tipo) VALUES (?, ?, ?)",
                      (fecha_fira, 'Fira Magdalena', 'Comida y Cena'))
        
        # Penya Taurina - último sábado de mayo
        fecha_penya = get_ultimo_sabado_mayo(año)
        cursor.execute("INSERT INTO comidas (fecha, tipo_servicio, tipo_comida, cocineros) VALUES (?, ?, ?, ?)",
                      (fecha_penya, 'Comida', 'Penya Taurina', eventos['penya_taurina']))
        cursor.execute("INSERT INTO eventos (fecha, evento, tipo) VALUES (?, ?, ?)",
                      (fecha_penya, 'Penya Taurina', 'Comida'))
    
    conn.commit()
    conn.close()
    print("✅ Eventos completos 2025-2045 cargados exitosamente!")

def update_mantenimiento_data():
    """Función para actualizar solo los datos de mantenimiento (útil para actualizaciones)"""
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    # Limpiar datos existentes de mantenimiento
    cursor.execute("DELETE FROM mantenimiento")
    
    # Datos completos de mantenimiento (2025-2045)
    mantenimiento_data = [
        (2025, 'David, Juan Fernando', 'David, Juan Fernando, Diego, Miguel A.'),
        (2026, 'Diego, Miguel A.', 'Diego, Miguel A., Xisco, Serafin'),
        (2027, 'Xisco, Serafin', 'Xisco, Serafin, Juan Ramon, Oscar'),
        (2028, 'Juan Ramon, Oscar', 'Juan Ramon, Oscar, Alfonso, Victor Z.'),
        (2029, 'Alfonso, Victor Z.', 'Alfonso, Victor Z., David, Victor M.'),
        (2030, 'David, Victor M.', 'David, Victor M., Xisco, Alonso'),
        (2031, 'Xisco, Alonso', 'Xisco, Alonso, Serafin, Raul M.'),
        (2032, 'Serafin, Raul M.', 'Serafin, Raul M., Alfonso, Raul A.'),
        (2033, 'Alfonso, Raul A.', 'Alfonso, Raul A., Miguel A., Juan Fernando'),
        (2034, 'Miguel A., Juan Fernando', 'Miguel A., Juan Fernando, Oscar, Diego'),
        (2035, 'Oscar, Diego', 'Oscar, Diego, Juan Ramon, Victor M.'),
        (2036, 'Juan Ramon, Victor M.', 'Juan Ramon, Victor M., David, Victor Z.'),
        (2037, 'David, Victor Z.', 'David, Victor Z., Xisco, Raul M.'),
        (2038, 'Xisco, Raul M.', 'Xisco, Raul M., Serafin, Alonso'),
        (2039, 'Serafin, Alonso', 'Serafin, Alonso, Alfonso, Raul A.'),
        (2040, 'Alfonso, Raul A.', 'Alfonso, Juan Fernando, Miguel A., Raul A.'),
        (2041, 'Miguel A., Juan Fernando', 'Miguel A., Juan Fernando, Oscar, Victor M.'),
        (2042, 'Oscar, Victor M.', 'Oscar, Victor M., Alfonso, Diego'),
        (2043, 'Alfonso, Diego', 'Alfonso, Diego, Juan Ramon, Alonso'),
        (2044, 'Juan Ramon, Alonso', 'Juan Ramon, Alonso, Miguel A., Victor Z.'),
        (2045, 'Miguel A., Victor Z.', 'Miguel A., Victor Z., Serafin, Juan Fernando'),
    ]
    
    # Insertar datos actualizados
    for data in mantenimiento_data:
        cursor.execute("INSERT INTO mantenimiento (año, mantenimiento, cadafals) VALUES (?, ?, ?)", data)
    
    conn.commit()
    conn.close()
    print("✅ Datos de mantenimiento actualizados correctamente!")

def limpiar_eventos_antiguos():
    """Eliminar eventos que tengan más de un mes de antigüedad"""
    try:
        conn = sqlite3.connect('penya_albenc.db')
        cursor = conn.cursor()
        
        # Fecha límite: hace un mes
        fecha_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Eliminar comidas antiguas
        cursor.execute("DELETE FROM comidas WHERE fecha < ?", (fecha_limite,))
        comidas_eliminadas = cursor.rowcount
        
        # Eliminar eventos antiguos
        cursor.execute("DELETE FROM eventos WHERE fecha < ?", (fecha_limite,))
        eventos_eliminados = cursor.rowcount
        
        # No eliminamos mantenimiento porque son tareas anuales
        
        conn.commit()
        conn.close()
        
        if comidas_eliminadas > 0 or eventos_eliminados > 0:
            print(f"🧹 Limpieza automática: {comidas_eliminadas} comidas y {eventos_eliminados} eventos eliminados")
        
        return f"✅ Limpieza completada: {comidas_eliminadas} comidas y {eventos_eliminados} eventos eliminados"
    except Exception as e:
        return f"❌ Error en limpieza: {str(e)}"

def inicializar_cocineros_desde_comidas():
    """Función auxiliar para inicializar cocineros (ya no es necesaria con get_cocineros_options)"""
    pass

# ===== INICIALIZACIÓN Y EJECUCIÓN =====

# Inicializar la base de datos y cargar datos
init_db()
load_eventos_completos()

# Ejecutar limpieza automática al iniciar
print("🚀 Iniciando aplicación Penya L'Albenc...")
resultado_limpieza = limpiar_eventos_antiguos()
print(f"🧹 {resultado_limpieza}")

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Servidor iniciado en puerto {port}")
    print("📊 Base de datos inicializada correctamente")
    print("📱 Diseño responsive activado - Compatible con móviles")
    print("✨ ¡Aplicación lista para usar!")
    print("🎉 CARDS MODERNAS ACTIVADAS - Perfectas para móviles!")
    
    app.run_server(debug=debug, host='0.0.0.0', port=port)