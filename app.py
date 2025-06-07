import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from datetime import datetime, date
import calendar

# Inicializar la app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
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

# Funciones auxiliares para filtros
def buscar_comidas_por_filtros(fecha=None, tipo_comida=None):
    """Buscar comidas por fecha y/o tipo de comida"""
    conn = sqlite3.connect('penya_albenc.db')
    
    query = "SELECT * FROM comidas WHERE 1=1"
    params = []
    
    if fecha:
        query += " AND fecha = ?"
        params.append(fecha)
    
    if tipo_comida:
        query += " AND tipo_comida LIKE ?"
        params.append(f"%{tipo_comida}%")
    
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

# Funciones avanzadas para gestión de cocineros (actualizada)
def get_comida_cocineros(comida_id):
    """Obtener la lista de cocineros de una comida específica"""
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    cursor.execute("SELECT cocineros FROM comidas WHERE id = ?", (comida_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return [nombre.strip() for nombre in result[0].split(',')]
    return []

def intercambiar_cocineros(id1, cocinero1, id2, cocinero2):
    """Intercambiar cocineros entre dos comidas usando IDs"""
    try:
        # Obtener las listas actuales de cocineros
        cocineros1 = get_comida_cocineros(id1)
        cocineros2 = get_comida_cocineros(id2)
        
        # Verificar que los cocineros existen en sus respectivas listas
        if cocinero1 not in cocineros1:
            return f"❌ {cocinero1} no está en la comida ID {id1}"
        if cocinero2 not in cocineros2:
            return f"❌ {cocinero2} no está en la comida ID {id2}"
        
        # Realizar el intercambio
        cocineros1[cocineros1.index(cocinero1)] = cocinero2
        cocineros2[cocineros2.index(cocinero2)] = cocinero1
        
        # Actualizar en la base de datos
        update_data('comidas', id1, 'cocineros', ', '.join(cocineros1))
        update_data('comidas', id2, 'cocineros', ', '.join(cocineros2))
        
        return f"✅ Intercambio exitoso: {cocinero1} ↔ {cocinero2}"
    except Exception as e:
        return f"❌ Error en el intercambio: {str(e)}"

def agregar_cocinero(comida_id, nuevo_cocinero):
    """Agregar un cocinero a una comida existente usando ID"""
    try:
        cocineros = get_comida_cocineros(comida_id)
        
        if nuevo_cocinero in cocineros:
            return f"⚠️ {nuevo_cocinero} ya está en esta comida"
        
        cocineros.append(nuevo_cocinero)
        update_data('comidas', comida_id, 'cocineros', ', '.join(cocineros))
        
        return f"✅ {nuevo_cocinero} agregado a la comida ID {comida_id}"
    except Exception as e:
        return f"❌ Error al agregar cocinero: {str(e)}"

def eliminar_cocinero(comida_id, cocinero_eliminar):
    """Eliminar un cocinero específico de una comida usando ID"""
    try:
        cocineros = get_comida_cocineros(comida_id)
        
        if cocinero_eliminar not in cocineros:
            return f"⚠️ {cocinero_eliminar} no está en esta comida"
        
        cocineros.remove(cocinero_eliminar)
        
        if not cocineros:
            return f"⚠️ No se puede eliminar el último cocinero de la comida"
        
        update_data('comidas', comida_id, 'cocineros', ', '.join(cocineros))
        
        return f"✅ {cocinero_eliminar} eliminado de la comida ID {comida_id}"
    except Exception as e:
        return f"❌ Error al eliminar cocinero: {str(e)}"

def buscar_comida_por_filtros(fecha, tipo_comida):
    """Buscar una comida específica por fecha y tipo"""
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, cocineros FROM comidas WHERE fecha = ? AND tipo_comida = ?", (fecha, tipo_comida))
    result = cursor.fetchone()
    conn.close()
    return result

def intercambiar_cocineros_por_filtros(fecha1, tipo1, cocinero1, fecha2, tipo2, cocinero2):
    """Intercambiar cocineros usando filtros de fecha y tipo"""
    try:
        # Buscar las comidas
        comida1 = buscar_comida_por_filtros(fecha1, tipo1)
        comida2 = buscar_comida_por_filtros(fecha2, tipo2)
        
        if not comida1:
            return f"❌ No se encontró comida el {fecha1} de tipo '{tipo1}'"
        if not comida2:
            return f"❌ No se encontró comida el {fecha2} de tipo '{tipo2}'"
        
        id1, _ = comida1
        id2, _ = comida2
        
        # Realizar el intercambio usando las IDs encontradas
        return intercambiar_cocineros(id1, cocinero1, id2, cocinero2)
    except Exception as e:
        return f"❌ Error en el intercambio: {str(e)}"

def agregar_cocinero_por_filtros(fecha, tipo_comida, nuevo_cocinero):
    """Agregar cocinero usando filtros"""
    try:
        comida = buscar_comida_por_filtros(fecha, tipo_comida)
        if not comida:
            return f"❌ No se encontró comida el {fecha} de tipo '{tipo_comida}'"
        
        comida_id, _ = comida
        return agregar_cocinero(comida_id, nuevo_cocinero)
    except Exception as e:
        return f"❌ Error al agregar cocinero: {str(e)}"

def eliminar_cocinero_por_filtros(fecha, tipo_comida, cocinero_eliminar):
    """Eliminar cocinero usando filtros"""
    try:
        comida = buscar_comida_por_filtros(fecha, tipo_comida)
        if not comida:
            return f"❌ No se encontró comida el {fecha} de tipo '{tipo_comida}'"
        
        comida_id, _ = comida
        return eliminar_cocinero(comida_id, cocinero_eliminar)
    except Exception as e:
        return f"❌ Error al eliminar cocinero: {str(e)}"

def actualizar_cocineros_por_filtros(fecha, tipo_comida, nuevos_cocineros):
    """Actualizar cocineros usando filtros"""
    try:
        comida = buscar_comida_por_filtros(fecha, tipo_comida)
        if not comida:
            return f"❌ No se encontró comida el {fecha} de tipo '{tipo_comida}'"
        
        comida_id, _ = comida
        update_data('comidas', comida_id, 'cocineros', nuevos_cocineros)
        return f"✅ Cocineros actualizados para {tipo_comida} del {fecha}! 👨‍🍳"
    except Exception as e:
        return f"❌ Error al actualizar: {str(e)}"

# Estilos CSS
# Estilos CSS
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "18rem",
    "padding": "2rem 1rem",
    "background": "linear-gradient(180deg, #2E7D32 0%, #1976D2 100%)",
    "color": "white",
    "box-shadow": "2px 0 5px rgba(0,0,0,0.1)"
}

CONTENT_STYLE = {
    "margin-left": "20rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "background": "#FAFAFA",
    "min-height": "100vh"
}

# CSS adicional para mejorar la apariencia
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                background: linear-gradient(135deg, #E8F5E8 0%, #E3F2FD 100%);
            }
            
            .nav-link:hover {
                background: rgba(255,255,255,0.2) !important;
                transform: translateX(5px);
            }
            
            .summary-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
                transition: all 0.3s ease;
            }
            
            /* Estilos para las tablas */
            .dash-table-container {
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                background: white;
            }
            
            /* Animaciones suaves */
            .fade-in {
                animation: fadeIn 0.5s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            /* Estilos para botones */
            button:hover {
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
                transition: all 0.2s ease !important;
            }
            
            /* Calendario personalizado */
            table {
                border-radius: 12px !important;
                overflow: hidden !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
            }
            
            /* Inputs y dropdowns */
            .Select-control, input[type="text"], input[type="number"] {
                border-radius: 6px !important;
                border: 2px solid #E0E0E0 !important;
                transition: border-color 0.3s ease !important;
            }
            
            .Select-control:focus, input[type="text"]:focus, input[type="number"]:focus {
                border-color: #4CAF50 !important;
                box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
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

# Layout del sidebar mejorado
sidebar = html.Div([
    html.Div([
        html.H2("🏠 Penya L'Albenc", 
               style={"font-size": "1.8rem", "margin-bottom": "10px", "text-align": "center"}),
        html.P("📍 Gestión de grupo", 
               style={"font-size": "0.9rem", "opacity": "0.8", "text-align": "center", "margin-bottom": "20px"})
    ]),
    html.Hr(style={"border-color": "rgba(255,255,255,0.3)", "margin": "20px 0"}),
    dcc.Location(id="url"),
    html.Nav([
        dcc.Link([
            html.Div([
                html.Span("🏠", style={"font-size": "1.2rem", "margin-right": "10px"}),
                html.Span("Inicio")
            ], style={"display": "flex", "align-items": "center"})
        ], href="/", className="nav-link", 
           style={
               "color": "white", "text-decoration": "none", "padding": "12px 15px", 
               "display": "block", "border-radius": "8px", "margin": "5px 0",
               "transition": "all 0.3s", "background": "rgba(255,255,255,0.1)"
           }),
        
        dcc.Link([
            html.Div([
                html.Span("🍽️", style={"font-size": "1.2rem", "margin-right": "10px"}),
                html.Span("Comidas")
            ], style={"display": "flex", "align-items": "center"})
        ], href="/comidas", className="nav-link",
           style={
               "color": "white", "text-decoration": "none", "padding": "12px 15px", 
               "display": "block", "border-radius": "8px", "margin": "5px 0",
               "transition": "all 0.3s"
           }),
        
        dcc.Link([
            html.Div([
                html.Span("🛒", style={"font-size": "1.2rem", "margin-right": "10px"}),
                html.Span("Lista de Compra")
            ], style={"display": "flex", "align-items": "center"})
        ], href="/lista-compra", className="nav-link",
           style={
               "color": "white", "text-decoration": "none", "padding": "12px 15px", 
               "display": "block", "border-radius": "8px", "margin": "5px 0",
               "transition": "all 0.3s"
           }),
        
        dcc.Link([
            html.Div([
                html.Span("🔧", style={"font-size": "1.2rem", "margin-right": "10px"}),
                html.Span("Mantenimiento")
            ], style={"display": "flex", "align-items": "center"})
        ], href="/mantenimiento", className="nav-link",
           style={
               "color": "white", "text-decoration": "none", "padding": "12px 15px", 
               "display": "block", "border-radius": "8px", "margin": "5px 0",
               "transition": "all 0.3s"
           }),
        
        dcc.Link([
            html.Div([
                html.Span("🎉", style={"font-size": "1.2rem", "margin-right": "10px"}),
                html.Span("Fiestas")
            ], style={"display": "flex", "align-items": "center"})
        ], href="/fiestas", className="nav-link",
           style={
               "color": "white", "text-decoration": "none", "padding": "12px 15px", 
               "display": "block", "border-radius": "8px", "margin": "5px 0",
               "transition": "all 0.3s"
           }),
    ], style={"margin-top": "20px"}),
    
    # Footer del sidebar
    html.Div([
        html.Hr(style={"border-color": "rgba(255,255,255,0.3)", "margin": "30px 0 20px 0"}),
        html.P("💚 Versión 2.0", 
               style={"font-size": "0.8rem", "opacity": "0.7", "text-align": "center", "margin": "0"})
    ], style={"position": "absolute", "bottom": "20px", "left": "1rem", "right": "1rem"})
], style=SIDEBAR_STYLE)

# Layout principal
content = html.Div(id="page-content", style=CONTENT_STYLE)

# Layout de la app
app.layout = html.Div([
    dcc.Store(id="confirm-action"),
    sidebar,
    content
])

# Callback para las páginas
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/comidas":
        return create_comidas_page()
    elif pathname == "/lista-compra":
        return create_lista_compra_page()
    elif pathname == "/mantenimiento":
        return create_mantenimiento_page()
    elif pathname == "/fiestas":
        return create_fiestas_page()
    else:
        return create_home_page()

# Página de inicio
def create_home_page():
    # Obtener datos para resumen
    comidas_df = get_data('comidas')
    lista_df = get_data('lista_compra')
    mantenimiento_df = get_data('mantenimiento')
    eventos_df = get_data('eventos')
    
    # Últimos elementos añadidos
    ultima_comida = comidas_df.tail(1) if len(comidas_df) > 0 else pd.DataFrame()
    ultima_lista = lista_df.tail(1) if len(lista_df) > 0 else pd.DataFrame()
    ultimo_mantenimiento = mantenimiento_df.tail(1) if len(mantenimiento_df) > 0 else pd.DataFrame()
    
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
        html.H1("Bienvenido a Penya L'Albenc", style={"color": "#2E7D32", "margin-bottom": "30px"}),
        
        # Resumen con contadores
        html.Div([
            html.H3("Resumen General", style={"color": "#1976D2", "margin-bottom": "20px"}),
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
            ], style={"display": "flex", "justify-content": "space-around", "flex-wrap": "wrap"}),
        ]),
        
        # Últimas actividades
        html.Div([
            html.H3("🔥 Últimas Actividades", style={"color": "#1976D2", "margin": "30px 0 20px 0"}),
            html.Div([
                # Última comida
                html.Div([
                    html.H5("🍽️ Última Comida", style={"color": "#4CAF50", "margin-bottom": "10px"}),
                    html.P(f"📅 {ultima_comida.iloc[0]['fecha'] if len(ultima_comida) > 0 else 'Ninguna'}", 
                           style={"margin": "5px 0"}),
                    html.P(f"🥘 {ultima_comida.iloc[0]['tipo_comida'] if len(ultima_comida) > 0 else 'N/A'}", 
                           style={"margin": "5px 0"}),
                    html.P(f"👨‍🍳 {ultima_comida.iloc[0]['cocineros'] if len(ultima_comida) > 0 else 'N/A'}", 
                           style={"margin": "5px 0", "font-size": "0.9rem"})
                ], style={
                    "background": "#F1F8E9", "padding": "20px", "margin": "10px", 
                    "border-radius": "8px", "border-left": "4px solid #4CAF50"
                }),
                
                # Último item lista
                html.Div([
                    html.H5("🛒 Último Item Lista", style={"color": "#2196F3", "margin-bottom": "10px"}),
                    html.P(f"📅 {ultima_lista.iloc[0]['fecha'] if len(ultima_lista) > 0 else 'Ninguna'}", 
                           style={"margin": "5px 0"}),
                    html.P(f"📦 {ultima_lista.iloc[0]['objeto'] if len(ultima_lista) > 0 else 'N/A'}", 
                           style={"margin": "5px 0"})
                ], style={
                    "background": "#E8F4FD", "padding": "20px", "margin": "10px", 
                    "border-radius": "8px", "border-left": "4px solid #2196F3"
                }),
                
                # Último mantenimiento
                html.Div([
                    html.H5("🔧 Último Mantenimiento", style={"color": "#FF9800", "margin-bottom": "10px"}),
                    html.P(f"📅 {ultimo_mantenimiento.iloc[0]['año'] if len(ultimo_mantenimiento) > 0 else 'Ninguno'}", 
                           style={"margin": "5px 0"}),
                    html.P(f"🔨 {ultimo_mantenimiento.iloc[0]['mantenimiento'] if len(ultimo_mantenimiento) > 0 else 'N/A'}", 
                           style={"margin": "5px 0", "font-size": "0.9rem"})
                ], style={
                    "background": "#FFF8E1", "padding": "20px", "margin": "10px", 
                    "border-radius": "8px", "border-left": "4px solid #FF9800"
                }),
            ], style={"display": "flex", "justify-content": "space-around", "flex-wrap": "wrap"})
        ]),
        
        # Calendario mejorado
        html.Div([
            html.H3("📅 Calendario de Eventos", style={"color": "#1976D2", "margin": "30px 0 15px 0"}),
            html.P("🔴 Días con comidas/cenas | 🔵 Hoy", style={"color": "#666", "margin-bottom": "15px"}),
            calendar_table
        ], style={"margin-top": "30px"})
    ])

# Página de comidas
def create_comidas_page():
    comidas_df = get_data('comidas')
    tipos_comida = get_tipos_comida()
    
    return html.Div([
        html.H1("🍽️ Gestión de Comidas", style={"color": "#2E7D32", "margin-bottom": "30px"}),
        
        # Tabla de comidas PRIMERO
        html.H3("📋 Lista de Comidas", style={"color": "#2E7D32", "margin": "20px 0 15px 0"}),
        dash_table.DataTable(
            id='tabla-comidas',
            data=comidas_df.to_dict('records'),
            columns=[
                {"name": "🆔 ID", "id": "id", "type": "numeric", "editable": False},
                {"name": "📅 Fecha", "id": "fecha", "type": "datetime", "editable": True},
                {"name": "🍽️ Servicio", "id": "tipo_servicio", "type": "text", "editable": True},
                {"name": "🥘 Tipo Comida", "id": "tipo_comida", "type": "text", "editable": True},
                {"name": "👨‍🍳 Cocineros", "id": "cocineros", "type": "text", "editable": True}
            ],
            row_deletable=True,
            editable=True,
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontFamily': 'Arial, sans-serif'
            },
            style_header={
                'backgroundColor': '#4CAF50',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#F8F9FA'
                },
                {
                    'if': {'column_id': 'cocineros'},
                    'backgroundColor': '#E8F5E8',
                    'color': '#2E7D32'
                }
            ],
            sort_action="native",
            filter_action="native",
            page_size=15
        ),
        
        # Formulario para agregar DESPUÉS de la tabla
        html.Div([
            html.H3("➕ Agregar Nueva Comida", style={"color": "#4CAF50"}),
            html.Div([
                html.Div([
                    html.Label("📅 Fecha:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.DatePickerSingle(
                        id='comida-fecha',
                        date=date.today(),
                        display_format='DD/MM/YYYY',
                        style={"width": "100%"}
                    )
                ], style={"margin": "10px"}),
                
                html.Div([
                    html.Label("🍽️ Tipo de Servicio:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Dropdown(
                        id='comida-servicio',
                        options=[
                            {'label': '🌅 Comida', 'value': 'Comida'},
                            {'label': '🌙 Cena', 'value': 'Cena'},
                            {'label': '🌅🌙 Comida y Cena', 'value': 'Comida y Cena'}
                        ],
                        placeholder="Selecciona tipo de servicio",
                        style={"width": "100%"}
                    )
                ], style={"margin": "10px"}),
                
                html.Div([
                    html.Label("🥘 Tipo de Comida:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='comida-tipo', 
                        placeholder="Ej: Comida Normal, Sant Antoni, etc.", 
                        type='text',
                        style={"width": "100%", "padding": "8px"}
                    )
                ], style={"margin": "10px"}),
                
                html.Div([
                    html.Label("👨‍🍳 Cocineros:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='comida-cocineros', 
                        placeholder="Separados por comas: Juan, María, Pedro", 
                        type='text',
                        style={"width": "100%", "padding": "8px"}
                    )
                ], style={"margin": "10px"}),
                
                html.Button('✅ Agregar Comida', id='btn-add-comida', n_clicks=0,
                           style={
                               "background": "linear-gradient(45deg, #4CAF50, #45a049)", 
                               "color": "white", "border": "none", "padding": "12px 24px",
                               "border-radius": "8px", "font-weight": "bold", "cursor": "pointer",
                               "margin": "10px"
                           })
            ], style={"background": "#F8F9FA", "padding": "20px", "border-radius": "12px", "margin": "20px 0"})
        ]),
        
        # Panel avanzado de gestión de cocineros (actualizado con filtros de fecha y tipo)
        html.Div([
            html.H3("🔄 Gestión Avanzada de Cocineros", style={"color": "#1976D2", "margin-bottom": "20px"}),
            html.P("💡 Tip: Usa la fecha y tipo de comida para identificar las comidas en lugar de ID", 
                   style={"color": "#666", "font-style": "italic", "margin-bottom": "20px"}),
            
            # Herramientas de gestión
            html.Div([
                # Editar cocineros por fecha y tipo
                html.Div([
                    html.H5("✏️ Editar Cocineros", style={"color": "#2196F3", "margin-bottom": "10px"}),
                    html.Div([
                        html.Div([
                            dcc.DatePickerSingle(
                                id='edit-fecha',
                                placeholder="Fecha de la comida",
                                display_format='DD/MM/YYYY',
                                style={"width": "140px"}
                            )
                        ], style={"margin": "5px"}),
                        html.Div([
                            dcc.Dropdown(
                                id='edit-tipo',
                                options=tipos_comida,
                                placeholder="Tipo de comida",
                                style={"width": "180px"}
                            )
                        ], style={"margin": "5px"}),
                        html.Div([
                            dcc.Input(
                                id='edit-cocineros-filtro',
                                type='text',
                                placeholder="Nuevos cocineros (separados por comas)",
                                style={"padding": "8px", "width": "300px"}
                            )
                        ], style={"margin": "5px"}),
                        html.Button('💾 Actualizar', id='btn-edit-cocineros-filtro', n_clicks=0,
                                   style={
                                       "background": "#2196F3", "color": "white", "border": "none",
                                       "padding": "8px 16px", "border-radius": "6px", "margin": "5px", "cursor": "pointer"
                                   })
                    ], style={"display": "flex", "align-items": "center", "gap": "5px", "flex-wrap": "wrap"})
                ], style={"background": "#E3F2FD", "padding": "15px", "border-radius": "8px", "margin": "10px"}),
                
                # Intercambiar cocineros por fecha y tipo
                html.Div([
                    html.H5("🔄 Intercambiar Cocineros", style={"color": "#FF9800", "margin-bottom": "10px"}),
                    html.Div([
                        # Primera comida
                        html.Div([
                            html.Label("Comida 1:", style={"font-weight": "bold", "color": "#FF9800"}),
                            dcc.DatePickerSingle(
                                id='intercambio-fecha1',
                                placeholder="Fecha 1",
                                display_format='DD/MM/YYYY',
                                style={"width": "120px", "margin": "2px"}
                            ),
                            dcc.Dropdown(
                                id='intercambio-tipo1',
                                options=tipos_comida,
                                placeholder="Tipo 1",
                                style={"width": "140px", "margin": "2px"}
                            ),
                            dcc.Input(
                                id='intercambio-cocinero1',
                                type='text',
                                placeholder="Cocinero 1",
                                style={"padding": "6px", "width": "120px", "margin": "2px"}
                            )
                        ], style={"display": "flex", "flex-direction": "column", "gap": "5px", "margin": "5px"}),
                        
                        html.Span("↔️", style={"margin": "0 10px", "font-size": "24px", "align-self": "center"}),
                        
                        # Segunda comida
                        html.Div([
                            html.Label("Comida 2:", style={"font-weight": "bold", "color": "#FF9800"}),
                            dcc.DatePickerSingle(
                                id='intercambio-fecha2',
                                placeholder="Fecha 2",
                                display_format='DD/MM/YYYY',
                                style={"width": "120px", "margin": "2px"}
                            ),
                            dcc.Dropdown(
                                id='intercambio-tipo2',
                                options=tipos_comida,
                                placeholder="Tipo 2",
                                style={"width": "140px", "margin": "2px"}
                            ),
                            dcc.Input(
                                id='intercambio-cocinero2',
                                type='text',
                                placeholder="Cocinero 2",
                                style={"padding": "6px", "width": "120px", "margin": "2px"}
                            )
                        ], style={"display": "flex", "flex-direction": "column", "gap": "5px", "margin": "5px"}),
                        
                        html.Button('🔄 Intercambiar', id='btn-intercambiar-filtro', n_clicks=0,
                                   style={
                                       "background": "#FF9800", "color": "white", "border": "none",
                                       "padding": "12px 20px", "border-radius": "6px", "margin": "10px", 
                                       "cursor": "pointer", "align-self": "center"
                                   })
                    ], style={"display": "flex", "align-items": "start", "gap": "10px", "flex-wrap": "wrap"})
                ], style={"background": "#FFF3E0", "padding": "15px", "border-radius": "8px", "margin": "10px"}),
                
                # Agregar/Eliminar cocinero específico por fecha y tipo
                html.Div([
                    html.H5("➕➖ Agregar/Eliminar Cocinero", style={"color": "#4CAF50", "margin-bottom": "10px"}),
                    html.Div([
                        dcc.DatePickerSingle(
                            id='manage-fecha',
                            placeholder="Fecha de la comida",
                            display_format='DD/MM/YYYY',
                            style={"width": "140px"}
                        ),
                        dcc.Dropdown(
                            id='manage-tipo',
                            options=tipos_comida,
                            placeholder="Tipo de comida",
                            style={"width": "180px"}
                        ),
                        dcc.Input(
                            id='manage-cocinero-filtro',
                            type='text',
                            placeholder="Nombre del cocinero",
                            style={"padding": "8px", "width": "200px"}
                        ),
                        html.Button('➕ Agregar', id='btn-add-cocinero-filtro', n_clicks=0,
                                   style={
                                       "background": "#4CAF50", "color": "white", "border": "none",
                                       "padding": "8px 16px", "border-radius": "6px", "margin": "5px", "cursor": "pointer"
                                   }),
                        html.Button('➖ Eliminar', id='btn-remove-cocinero-filtro', n_clicks=0,
                                   style={
                                       "background": "#F44336", "color": "white", "border": "none",
                                       "padding": "8px 16px", "border-radius": "6px", "margin": "5px", "cursor": "pointer"
                                   })
                    ], style={"display": "flex", "align-items": "center", "gap": "5px", "flex-wrap": "wrap"})
                ], style={"background": "#E8F5E8", "padding": "15px", "border-radius": "8px", "margin": "10px"}),
                
            ], style={"margin": "20px 0"})
        ], style={"background": "#F5F5F5", "padding": "20px", "border-radius": "12px", "margin": "20px 0"}),
        
        # Mensajes y confirmaciones
        html.Div(id='comida-output', style={"margin": "20px 0", "padding": "10px"})
    ])

# Página de lista de compra
def create_lista_compra_page():
    lista_df = get_data('lista_compra')
    
    return html.Div([
        html.H1("🛒 Lista de Compra", style={"color": "#2E7D32", "margin-bottom": "30px"}),
        
        # Tabla de lista PRIMERO
        html.H3("📋 Lista de Compras", style={"color": "#2E7D32", "margin": "20px 0 15px 0"}),
        dash_table.DataTable(
            id='tabla-lista',
            data=lista_df.to_dict('records'),
            columns=[
                {"name": "🆔 ID", "id": "id", "type": "numeric", "editable": False},
                {"name": "📅 Fecha", "id": "fecha", "type": "datetime", "editable": True},
                {"name": "📦 Objeto", "id": "objeto", "type": "text", "editable": True}
            ],
            row_deletable=True,
            editable=True,
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontFamily': 'Arial, sans-serif'
            },
            style_header={
                'backgroundColor': '#2196F3',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#F8F9FA'
                },
                {
                    'if': {'column_id': 'objeto'},
                    'backgroundColor': '#E3F2FD',
                    'color': '#1976D2'
                }
            ],
            sort_action="native",
            filter_action="native",
            page_size=15
        ),
        
        # Formulario para agregar DESPUÉS de la tabla
        html.Div([
            html.H3("➕ Agregar Nuevo Item", style={"color": "#2196F3"}),
            html.Div([
                html.Div([
                    html.Label("📅 Fecha:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.DatePickerSingle(
                        id='lista-fecha',
                        date=date.today(),
                        display_format='DD/MM/YYYY',
                        style={"width": "100%"}
                    )
                ], style={"margin": "10px", "flex": "1"}),
                
                html.Div([
                    html.Label("📦 Objeto a Comprar:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='lista-objeto', 
                        placeholder="Ej: Tomates, Pan, Aceite...", 
                        type='text',
                        style={"width": "100%", "padding": "8px"}
                    )
                ], style={"margin": "10px", "flex": "2"}),
                
                html.Button('✅ Agregar Item', id='btn-add-lista', n_clicks=0,
                           style={
                               "background": "linear-gradient(45deg, #2196F3, #1976D2)", 
                               "color": "white", "border": "none", "padding": "12px 24px",
                               "border-radius": "8px", "font-weight": "bold", "cursor": "pointer",
                               "margin": "10px", "align-self": "end"
                           })
            ], style={"display": "flex", "align-items": "end", "gap": "10px"})
        ], style={"background": "#F8F9FA", "padding": "20px", "border-radius": "12px", "margin": "20px 0"}),
        
        html.Div(id='lista-output', style={"margin": "20px 0", "padding": "10px"})
    ])

# Página de mantenimiento
def create_mantenimiento_page():
    mant_df = get_data('mantenimiento')
    
    return html.Div([
        html.H1("🔧 Mantenimiento", style={"color": "#2E7D32", "margin-bottom": "30px"}),
        
        # Tabla de mantenimiento PRIMERO
        html.H3("📋 Tareas de Mantenimiento", style={"color": "#2E7D32", "margin": "20px 0 15px 0"}),
        dash_table.DataTable(
            id='tabla-mant',
            data=mant_df.to_dict('records'),
            columns=[
                {"name": "🆔 ID", "id": "id", "type": "numeric", "editable": False},
                {"name": "📅 Año", "id": "año", "type": "numeric", "editable": True},
                {"name": "🔨 Mantenimiento", "id": "mantenimiento", "type": "text", "editable": True},
                {"name": "🏗️ Cadafals", "id": "cadafals", "type": "text", "editable": True}
            ],
            row_deletable=True,
            editable=True,
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontFamily': 'Arial, sans-serif'
            },
            style_header={
                'backgroundColor': '#FF9800',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#F8F9FA'
                },
                {
                    'if': {'column_id': 'mantenimiento'},
                    'backgroundColor': '#FFF3E0',
                    'color': '#E65100'
                },
                {
                    'if': {'column_id': 'cadafals'},
                    'backgroundColor': '#FFF8E1',
                    'color': '#F57C00'
                }
            ],
            sort_action="native",
            filter_action="native",
            page_size=15
        ),
        
        # Formulario para agregar DESPUÉS de la tabla
        html.Div([
            html.H3("➕ Agregar Tarea de Mantenimiento", style={"color": "#FF9800"}),
            html.Div([
                html.Div([
                    html.Label("📅 Año:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='mant-año', 
                        placeholder="2025", 
                        type='number', 
                        value=datetime.now().year,
                        style={"width": "100%", "padding": "8px"}
                    )
                ], style={"margin": "10px", "flex": "1"}),
                
                html.Div([
                    html.Label("🔨 Mantenimiento:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='mant-mantenimiento', 
                        placeholder="Descripción del mantenimiento", 
                        type='text',
                        style={"width": "100%", "padding": "8px"}
                    )
                ], style={"margin": "10px", "flex": "2"}),
                
                html.Div([
                    html.Label("🏗️ Cadafals:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='mant-cadafals', 
                        placeholder="Responsables de cadafals", 
                        type='text',
                        style={"width": "100%", "padding": "8px"}
                    )
                ], style={"margin": "10px", "flex": "2"}),
                
                html.Button('✅ Agregar Tarea', id='btn-add-mant', n_clicks=0,
                           style={
                               "background": "linear-gradient(45deg, #FF9800, #F57C00)", 
                               "color": "white", "border": "none", "padding": "12px 24px",
                               "border-radius": "8px", "font-weight": "bold", "cursor": "pointer",
                               "margin": "10px", "align-self": "end"
                           })
            ], style={"display": "flex", "align-items": "end", "gap": "10px"})
        ], style={"background": "#F8F9FA", "padding": "20px", "border-radius": "12px", "margin": "20px 0"}),
        
        html.Div(id='mant-output', style={"margin": "20px 0", "padding": "10px"})
    ])

# Página de fiestas (mejorada)
def create_fiestas_page():
    return html.Div([
        html.H1("🎉 Fiestas", style={"color": "#2E7D32", "margin-bottom": "30px"}),
        
        # Contenido temporal
        html.Div([
            html.Div([
                html.H3("🚧 En Construcción", style={"color": "#9C27B0", "text-align": "center"}),
                html.P("Esta sección estará disponible en próximas actualizaciones.", 
                       style={"font-size": "18px", "color": "#666", "text-align": "center"}),
                html.P("Aquí podrás gestionar:", style={"margin-top": "20px", "font-weight": "bold"}),
                html.Ul([
                    html.Li("🎭 Eventos especiales y fiestas"),
                    html.Li("🎪 Organización de actividades"),
                    html.Li("🎨 Decoraciones y temáticas"),
                    html.Li("🎵 Música y entretenimiento"),
                    html.Li("📸 Galería de fotos"),
                ], style={"color": "#555", "margin": "20px 0"})
            ], style={
                "background": "linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%)",
                "padding": "40px", "border-radius": "15px", "text-align": "center",
                "box-shadow": "0 4px 6px rgba(0,0,0,0.1)", "margin": "20px 0"
            }),
            
            # Próximas fiestas (basadas en eventos existentes)
            html.Div([
                html.H4("🎊 Próximos Eventos Especiales", style={"color": "#1976D2"}),
                html.Div([
                    html.Div([
                        html.H5("🎭 Sant Antoni", style={"color": "#FF5722"}),
                        html.P("📅 Enero - Cena especial"),
                        html.P("🍽️ Tradición gastronómica")
                    ], style={"background": "#FFF3E0", "padding": "15px", "margin": "10px", "border-radius": "8px"}),
                    
                    html.Div([
                        html.H5("🌸 Brena St Vicent", style={"color": "#4CAF50"}),
                        html.P("📅 Mayo - Comida y Cena"),
                        html.P("🌺 Celebración primaveral")
                    ], style={"background": "#E8F5E8", "padding": "15px", "margin": "10px", "border-radius": "8px"}),
                    
                    html.Div([
                        html.H5("🎪 Fira Magdalena", style={"color": "#9C27B0"}),
                        html.P("📅 Julio - Gran celebración"),
                        html.P("🎉 Evento principal del año")
                    ], style={"background": "#F3E5F5", "padding": "15px", "margin": "10px", "border-radius": "8px"}),
                ], style={"display": "flex", "justify-content": "space-around", "flex-wrap": "wrap"})
            ], style={"margin-top": "30px"})
        ])
    ])

# Callbacks para comidas (actualizado con filtros por fecha y tipo)
@app.callback(
    [Output('tabla-comidas', 'data'), Output('comida-output', 'children')],
    [Input('btn-add-comida', 'n_clicks'), 
     Input('btn-edit-cocineros-filtro', 'n_clicks'),
     Input('btn-intercambiar-filtro', 'n_clicks'),
     Input('btn-add-cocinero-filtro', 'n_clicks'),
     Input('btn-remove-cocinero-filtro', 'n_clicks'),
     Input('tabla-comidas', 'data_previous'),
     Input('tabla-comidas', 'data')],
    [State('comida-fecha', 'date'), State('comida-servicio', 'value'),
     State('comida-tipo', 'value'), State('comida-cocineros', 'value'),
     State('edit-fecha', 'date'), State('edit-tipo', 'value'), State('edit-cocineros-filtro', 'value'),
     State('intercambio-fecha1', 'date'), State('intercambio-tipo1', 'value'), State('intercambio-cocinero1', 'value'),
     State('intercambio-fecha2', 'date'), State('intercambio-tipo2', 'value'), State('intercambio-cocinero2', 'value'),
     State('manage-fecha', 'date'), State('manage-tipo', 'value'), State('manage-cocinero-filtro', 'value')],
    prevent_initial_call=True
)
def update_comidas_con_filtros(n_add, n_edit, n_intercambio, n_add_cocinero, n_remove_cocinero,
                               previous_data, current_data, fecha, servicio, tipo, cocineros, 
                               edit_fecha, edit_tipo, edit_cocineros_nuevos,
                               int_fecha1, int_tipo1, int_cocinero1, int_fecha2, int_tipo2, int_cocinero2,
                               manage_fecha, manage_tipo, manage_cocinero):
    ctx = callback_context
    
    if not ctx.triggered:
        try:
            return get_data('comidas').to_dict('records'), ""
        except:
            return [], ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Agregar nueva comida
    if trigger_id == 'btn-add-comida' and n_add > 0:
        if fecha and servicio and tipo and cocineros:
            add_data('comidas', (fecha, servicio, tipo, cocineros))
            add_data('eventos', (fecha, tipo, servicio))
            return get_data('comidas').to_dict('records'), f"✅ Comida agregada exitosamente! 🎉"
        else:
            return get_data('comidas').to_dict('records'), "⚠️ Por favor completa todos los campos."
    
    # Editar cocineros por fecha y tipo
    elif trigger_id == 'btn-edit-cocineros-filtro' and n_edit > 0:
        if edit_fecha and edit_tipo and edit_cocineros_nuevos:
            resultado = actualizar_cocineros_por_filtros(edit_fecha, edit_tipo, edit_cocineros_nuevos)
            return get_data('comidas').to_dict('records'), f"✏️ {resultado}"
        else:
            return get_data('comidas').to_dict('records'), "⚠️ Proporciona la fecha, tipo de comida y nuevos cocineros."
    
    # Intercambiar cocineros por fecha y tipo
    elif trigger_id == 'btn-intercambiar-filtro' and n_intercambio > 0:
        if int_fecha1 and int_tipo1 and int_cocinero1 and int_fecha2 and int_tipo2 and int_cocinero2:
            resultado = intercambiar_cocineros_por_filtros(
                int_fecha1, int_tipo1, int_cocinero1.strip(), 
                int_fecha2, int_tipo2, int_cocinero2.strip()
            )
            return get_data('comidas').to_dict('records'), f"🔄 {resultado}"
        else:
            return get_data('comidas').to_dict('records'), "⚠️ Completa todos los campos para el intercambio."
    
    # Agregar cocinero por fecha y tipo
    elif trigger_id == 'btn-add-cocinero-filtro' and n_add_cocinero > 0:
        if manage_fecha and manage_tipo and manage_cocinero:
            resultado = agregar_cocinero_por_filtros(manage_fecha, manage_tipo, manage_cocinero.strip())
            return get_data('comidas').to_dict('records'), f"➕ {resultado}"
        else:
            return get_data('comidas').to_dict('records'), "⚠️ Proporciona la fecha, tipo de comida y nombre del cocinero."
    
    # Eliminar cocinero por fecha y tipo
    elif trigger_id == 'btn-remove-cocinero-filtro' and n_remove_cocinero > 0:
        if manage_fecha and manage_tipo and manage_cocinero:
            resultado = eliminar_cocinero_por_filtros(manage_fecha, manage_tipo, manage_cocinero.strip())
            return get_data('comidas').to_dict('records'), f"➖ {resultado}"
        else:
            return get_data('comidas').to_dict('records'), "⚠️ Proporciona la fecha, tipo de comida y nombre del cocinero."
    
    # Detectar edición directa en la tabla
    elif trigger_id == 'tabla-comidas' and previous_data is not None and current_data is not None:
        if len(current_data) < len(previous_data):
            # Fila eliminada
            current_ids = [row['id'] for row in current_data]
            deleted_id = None
            for row in previous_data:
                if row['id'] not in current_ids:
                    deleted_id = row['id']
                    break
            
            if deleted_id:
                delete_data('comidas', deleted_id)
                return get_data('comidas').to_dict('records'), f"🗑️ Comida eliminada exitosamente!"
        
        elif len(current_data) == len(previous_data):
            # Posible edición de celda
            for i, (prev_row, curr_row) in enumerate(zip(previous_data, current_data)):
                for key in prev_row.keys():
                    if prev_row[key] != curr_row[key]:
                        update_data('comidas', curr_row['id'], key, curr_row[key])
                        return get_data('comidas').to_dict('records'), f"✏️ Campo '{key}' actualizado!"
    
    try:
        return get_data('comidas').to_dict('records'), ""
    except:
        return [], ""

# Callback para actualizar opciones de tipo de comida dinámicamente
@app.callback(
    [Output('edit-tipo', 'options'),
     Output('intercambio-tipo1', 'options'),
     Output('intercambio-tipo2', 'options'),
     Output('manage-tipo', 'options')],
    [Input('tabla-comidas', 'data')],
    prevent_initial_call=True
)
def update_tipo_options(data):
    tipos = get_tipos_comida()
    return tipos, tipos, tipos, tipos

# Callbacks para lista de compra (con protección)
@app.callback(
    [Output('tabla-lista', 'data'), Output('lista-output', 'children')],
    [Input('btn-add-lista', 'n_clicks'), 
     Input('tabla-lista', 'data_previous'),
     Input('tabla-lista', 'data')],
    [State('lista-fecha', 'date'), State('lista-objeto', 'value')],
    prevent_initial_call=True
)
def update_lista(n_clicks, previous_data, current_data, fecha, objeto):
    ctx = callback_context
    
    if not ctx.triggered:
        try:
            return get_data('lista_compra').to_dict('records'), ""
        except:
            return [], ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'btn-add-lista' and n_clicks > 0:
        if fecha and objeto:
            add_data('lista_compra', (fecha, objeto))
            return get_data('lista_compra').to_dict('records'), f"✅ Item agregado exitosamente! 🛒"
        else:
            return get_data('lista_compra').to_dict('records'), "⚠️ Por favor completa todos los campos."
    
    elif trigger_id == 'tabla-lista' and previous_data is not None and current_data is not None:
        if len(current_data) < len(previous_data):
            # Fila eliminada
            current_ids = [row['id'] for row in current_data]
            deleted_id = None
            for row in previous_data:
                if row['id'] not in current_ids:
                    deleted_id = row['id']
                    break
            
            if deleted_id:
                delete_data('lista_compra', deleted_id)
                return get_data('lista_compra').to_dict('records'), f"🗑️ Item eliminado exitosamente!"
        
        elif len(current_data) == len(previous_data):
            # Posible edición de celda
            for i, (prev_row, curr_row) in enumerate(zip(previous_data, current_data)):
                for key in prev_row.keys():
                    if prev_row[key] != curr_row[key]:
                        update_data('lista_compra', curr_row['id'], key, curr_row[key])
                        return get_data('lista_compra').to_dict('records'), f"✏️ Campo '{key}' actualizado!"
    
    try:
        return get_data('lista_compra').to_dict('records'), ""
    except:
        return [], ""

# Callbacks para mantenimiento (con protección)
@app.callback(
    [Output('tabla-mant', 'data'), Output('mant-output', 'children')],
    [Input('btn-add-mant', 'n_clicks'), 
     Input('tabla-mant', 'data_previous'),
     Input('tabla-mant', 'data')],
    [State('mant-año', 'value'), State('mant-mantenimiento', 'value'),
     State('mant-cadafals', 'value')],
    prevent_initial_call=True
)
def update_mant(n_clicks, previous_data, current_data, año, mantenimiento, cadafals):
    ctx = callback_context
    
    if not ctx.triggered:
        try:
            return get_data('mantenimiento').to_dict('records'), ""
        except:
            return [], ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'btn-add-mant' and n_clicks > 0:
        if año and mantenimiento and cadafals:
            add_data('mantenimiento', (año, mantenimiento, cadafals))
            return get_data('mantenimiento').to_dict('records'), f"✅ Tarea agregada exitosamente! 🔧"
        else:
            return get_data('mantenimiento').to_dict('records'), "⚠️ Por favor completa todos los campos."
    
    elif trigger_id == 'tabla-mant' and previous_data is not None and current_data is not None:
        if len(current_data) < len(previous_data):
            # Fila eliminada
            current_ids = [row['id'] for row in current_data]
            deleted_id = None
            for row in previous_data:
                if row['id'] not in current_ids:
                    deleted_id = row['id']
                    break
            
            if deleted_id:
                delete_data('mantenimiento', deleted_id)
                return get_data('mantenimiento').to_dict('records'), f"🗑️ Tarea eliminada exitosamente!"
        
        elif len(current_data) == len(previous_data):
            # Posible edición de celda
            for i, (prev_row, curr_row) in enumerate(zip(previous_data, current_data)):
                for key in prev_row.keys():
                    if prev_row[key] != curr_row[key]:
                        update_data('mantenimiento', curr_row['id'], key, curr_row[key])
                        return get_data('mantenimiento').to_dict('records'), f"✏️ Campo '{key}' actualizado!"
    
    try:
        return get_data('mantenimiento').to_dict('records'), ""
    except:
        return [], ""

# Inicializar la base de datos y cargar datos
init_db()
load_initial_data()

# Si quieres actualizar solo los datos de mantenimiento, descomenta la siguiente línea:
# update_mantenimiento_data()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run_server(debug=debug, host='0.0.0.0', port=port)