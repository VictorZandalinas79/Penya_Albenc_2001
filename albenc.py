import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import dash.dependencies
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import calendar

# Inicializar la app
app = dash.Dash(__name__, suppress_callback_exceptions=True, 
                assets_folder='assets',
                assets_url_path='/assets/',
                meta_tags=[
                    {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"}
                ])
app.title = "Penya L'Albenc"

# Para Render
server = app.server

# Configurar la base de datos
def init_db():
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            tipo_servicio TEXT,
            tipo_comida TEXT,
            cocineros TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lista_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            objeto TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mantenimiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            año INTEGER,
            mantenimiento TEXT,
            cadafals TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            evento TEXT,
            tipo TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fiestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            cocineros TEXT,
            menu TEXT,
            adultos INTEGER DEFAULT 0,
            nombres_adultos TEXT DEFAULT '',
            niños INTEGER DEFAULT 0,
            nombres_niños TEXT DEFAULT '',
            programa TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Funciones de base de datos
def add_data(table, data):
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data.values()])
    
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.execute(query, list(data.values()))
    
    conn.commit()
    conn.close()

def get_data(table):
    conn = sqlite3.connect('penya_albenc.db')
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

def delete_data(table, id):
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def migrate_fiestas_table():
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    # Verificar si las columnas existen
    cursor.execute("PRAGMA table_info(fiestas)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'adultos' not in columns:
        cursor.execute('ALTER TABLE fiestas ADD COLUMN adultos INTEGER DEFAULT 0')
    if 'nombres_adultos' not in columns:
        cursor.execute('ALTER TABLE fiestas ADD COLUMN nombres_adultos TEXT DEFAULT ""')
    if 'niños' not in columns:
        cursor.execute('ALTER TABLE fiestas ADD COLUMN niños INTEGER DEFAULT 0')
    if 'nombres_niños' not in columns:
        cursor.execute('ALTER TABLE fiestas ADD COLUMN nombres_niños TEXT DEFAULT ""')
    if 'programa' not in columns:
        cursor.execute('ALTER TABLE fiestas ADD COLUMN programa TEXT DEFAULT ""')
    
    conn.commit()
    conn.close()

def update_mantenimiento_data():
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    datos_mantenimiento = [
        (2024, "David Vives\nFede", "Toni Vendrell\nFernando Cabrera"),
        (2025, "Antonio Vendrell\nFernando Cabrera", "Jesús Sánchez\nToni Millet"),
        (2026, "Jesús Sánchez\nToni Millet", "Ximo\nCarles"),
        (2027, "Ximo\nCarles", "Pascual\nRoberto"),
        (2028, "Pascual\nRoberto", "David Vives\nFede"),
    ]
    
    for año, mantenimiento, cadafals in datos_mantenimiento:
        cursor.execute("SELECT COUNT(*) FROM mantenimiento WHERE año = ?", (año,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO mantenimiento (año, mantenimiento, cadafals) VALUES (?, ?, ?)",
                         (año, mantenimiento, cadafals))
    
    conn.commit()
    conn.close()

def load_eventos_completos():
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    eventos = [
        # Eventos especiales
        ('2025-08-15', 'Fiesta del Pueblo', 'especial'),
        ('2025-12-25', 'Navidad', 'especial'),
        ('2026-01-01', 'Año Nuevo', 'especial'),
        # Mantenimiento
        ('2025-01-10', 'Revisión eléctrica', 'mantenimiento'),
        ('2025-06-15', 'Pintura exterior', 'mantenimiento'),
        ('2025-11-01', 'Revisión calefacción', 'mantenimiento'),
    ]
    
    for fecha, evento, tipo in eventos:
        cursor.execute("SELECT COUNT(*) FROM eventos WHERE fecha = ? AND evento = ?", (fecha, evento))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO eventos (fecha, evento, tipo) VALUES (?, ?, ?)",
                         (fecha, evento, tipo))
    
    conn.commit()
    conn.close()

def load_fiestas_agosto_2025():
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    # Verificar si ya existe la fiesta
    cursor.execute("SELECT COUNT(*) FROM fiestas WHERE fecha = ?", ('2025-08-16',))
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO fiestas (fecha, cocineros, menu, adultos, nombres_adultos, niños, nombres_niños, programa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2025-08-16',
            'Toni Vendrell\nFernando Cabrera',
            'Paella Valenciana\nEnsalada\nPostre: Helado',
            25,
            'Lista de adultos pendiente',
            8,
            'Lista de niños pendiente',
            '12:00 - Aperitivo\n14:00 - Comida\n17:00 - Sobremesa\n20:00 - Cena ligera'
        ))
    
    conn.commit()
    conn.close()

# Layout - Header moderno para móvil
header = html.Div([
    html.Div([
        html.Img(src="/assets/logo.png", className="mobile-logo"),
        html.H1("Penya L'Albenc", className="mobile-title"),
    ], className="mobile-header")
], className="header-container")

# Layout - Navegación inferior tipo app móvil
bottom_nav = html.Div([
    dcc.Link([
        html.I(className="fas fa-home nav-icon"),
        html.Span("Inicio", className="nav-text")
    ], href="/", className="nav-item", id="nav-home"),
    
    dcc.Link([
        html.I(className="fas fa-utensils nav-icon"),
        html.Span("Comidas", className="nav-text")
    ], href="/comidas", className="nav-item", id="nav-comidas"),
    
    dcc.Link([
        html.I(className="fas fa-shopping-cart nav-icon"),
        html.Span("Compra", className="nav-text")
    ], href="/lista-compra", className="nav-item", id="nav-compra"),
    
    dcc.Link([
        html.I(className="fas fa-tools nav-icon"),
        html.Span("Manten.", className="nav-text")
    ], href="/mantenimiento", className="nav-item", id="nav-manten"),
    
    dcc.Link([
        html.I(className="fas fa-glass-cheers nav-icon"),
        html.Span("Fiestas", className="nav-text")
    ], href="/fiestas", className="nav-item", id="nav-fiestas"),
], className="bottom-nav")

# Layout principal
content = html.Div(id="page-content", className="mobile-content")

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="confirm-action"),
    header,
    content,
    bottom_nav
], className="mobile-app")

# Callback para resaltar el item activo en la navegación
@app.callback(
    [Output(f"nav-{page}", "className") for page in ["home", "comidas", "compra", "manten", "fiestas"]],
    [Input("url", "pathname")]
)
def update_nav_active(pathname):
    nav_classes = ["nav-item"] * 5
    
    if pathname == "/":
        nav_classes[0] = "nav-item active"
    elif pathname == "/comidas":
        nav_classes[1] = "nav-item active"
    elif pathname == "/lista-compra":
        nav_classes[2] = "nav-item active"
    elif pathname == "/mantenimiento":
        nav_classes[3] = "nav-item active"
    elif pathname == "/fiestas":
        nav_classes[4] = "nav-item active"
    
    return nav_classes

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

# Página de inicio modernizada
def create_home_page():
    comidas_df = get_data('comidas')
    lista_df = get_data('lista_compra')
    mantenimiento_df = get_data('mantenimiento')
    eventos_df = get_data('eventos')
    
    año_actual = datetime.now().year
    mantenimiento_actual = mantenimiento_df[mantenimiento_df['año'] == año_actual]
    
    return html.Div([
        # Hero Card
        html.Div([
            html.Div([
                html.Img(src="/assets/logo.png", className="hero-logo"),
                html.H2(f"Año {año_actual}", className="hero-year"),
            ], className="hero-header"),
            
            html.Div([
                html.Div([
                    html.H4("Mantenimiento", className="hero-label"),
                    html.P(mantenimiento_actual.iloc[0]['mantenimiento'] if len(mantenimiento_actual) > 0 else "Sin datos", 
                           className="hero-value")
                ], className="hero-section"),
                
                html.Div([
                    html.H4("Cadafals", className="hero-label"),
                    html.P(mantenimiento_actual.iloc[0]['cadafals'] if len(mantenimiento_actual) > 0 else "Sin datos", 
                           className="hero-value")
                ], className="hero-section"),
            ], className="hero-content")
        ], className="hero-card"),
        
        # Stats Cards
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-utensils stat-icon"),
                    html.H3(f"{len(comidas_df)}", className="stat-number"),
                    html.P("Comidas", className="stat-label")
                ], className="stat-content")
            ], className="stat-card stat-card-blue"),
            
            html.Div([
                html.Div([
                    html.I(className="fas fa-shopping-cart stat-icon"),
                    html.H3(f"{len(lista_df)}", className="stat-number"),
                    html.P("Lista compra", className="stat-label")
                ], className="stat-content")
            ], className="stat-card stat-card-green"),
            
            html.Div([
                html.Div([
                    html.I(className="fas fa-calendar stat-icon"),
                    html.H3(f"{len(eventos_df)}", className="stat-number"),
                    html.P("Eventos", className="stat-label")
                ], className="stat-content")
            ], className="stat-card stat-card-purple"),
            
            html.Div([
                html.Div([
                    html.I(className="fas fa-tools stat-icon"),
                    html.H3(f"{len(mantenimiento_df)}", className="stat-number"),
                    html.P("Años", className="stat-label")
                ], className="stat-content")
            ], className="stat-card stat-card-orange"),
        ], className="stats-grid"),
        
        # Sección de próximos eventos
        html.Div([
            html.H3("Próximos Eventos", className="section-header"),
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fas fa-calendar-day event-icon"),
                        html.Div([
                            html.H4("Fiesta del Pueblo", className="event-title"),
                            html.P("15 de Agosto, 2025", className="event-date")
                        ], className="event-info")
                    ], className="event-content")
                ], className="event-card"),
                
                html.Div([
                    html.Div([
                        html.I(className="fas fa-wrench event-icon"),
                        html.Div([
                            html.H4("Revisión Eléctrica", className="event-title"),
                            html.P("10 de Enero, 2025", className="event-date")
                        ], className="event-info")
                    ], className="event-content")
                ], className="event-card"),
            ], className="events-list")
        ], className="section")
    ], className="page-wrapper")

# Página de comidas modernizada
def create_comidas_page():
    comidas_df = get_data('comidas')
    
    return html.Div([
        html.Div([
            html.H2("Gestión de Comidas", className="page-header"),
            
            # Formulario moderno
            html.Div([
                html.Div([
                    html.Label("Fecha", className="form-label"),
                    dcc.DatePickerSingle(
                        id='comida-fecha',
                        date=date.today(),
                        display_format='DD/MM/YYYY',
                        className="date-picker"
                    ),
                ], className="form-field"),
                
                html.Div([
                    html.Label("Tipo de Servicio", className="form-label"),
                    dcc.Dropdown(
                        id='tipo-servicio',
                        options=[
                            {'label': '🍳 Desayuno', 'value': 'Desayuno'},
                            {'label': '🥘 Comida', 'value': 'Comida'},
                            {'label': '🌙 Cena', 'value': 'Cena'}
                        ],
                        className="dropdown"
                    ),
                ], className="form-field"),
                
                html.Div([
                    html.Label("Tipo de Comida", className="form-label"),
                    dcc.Input(
                        id='tipo-comida',
                        type='text',
                        placeholder='Ej: Paella, Barbacoa...',
                        className="input-field"
                    ),
                ], className="form-field"),
                
                html.Div([
                    html.Label("Cocineros", className="form-label"),
                    dcc.Input(
                        id='cocineros',
                        type='text',
                        placeholder='Nombres de los cocineros',
                        className="input-field"
                    ),
                ], className="form-field"),
                
                html.Button([
                    html.I(className="fas fa-plus btn-icon"),
                    "Añadir Comida"
                ], id='add-comida', className="btn-primary btn-block")
            ], className="form-card"),
            
            # Lista de comidas
            html.Div([
                html.H3("Comidas Programadas", className="section-subheader"),
                html.Div(id='comidas-list', className="items-list")
            ], className="list-section")
        ], className="page-container")
    ], className="page-wrapper")

# Página de lista de compra modernizada
def create_lista_compra_page():
    lista_df = get_data('lista_compra')
    
    return html.Div([
        html.Div([
            html.H2("Lista de Compra", className="page-header"),
            
            # Formulario para añadir
            html.Div([
                html.Div([
                    html.Label("Fecha", className="form-label"),
                    dcc.DatePickerSingle(
                        id='lista-fecha',
                        date=date.today(),
                        display_format='DD/MM/YYYY',
                        className="date-picker"
                    ),
                ], className="form-field"),
                
                html.Div([
                    html.Label("Artículo", className="form-label"),
                    dcc.Input(
                        id='objeto',
                        type='text',
                        placeholder='¿Qué necesitas comprar?',
                        className="input-field"
                    ),
                ], className="form-field"),
                
                html.Button([
                    html.I(className="fas fa-cart-plus btn-icon"),
                    "Añadir a la Lista"
                ], id='add-lista', className="btn-primary btn-block")
            ], className="form-card"),
            
            # Lista de items
            html.Div([
                html.H3("Artículos Pendientes", className="section-subheader"),
                html.Div(id='lista-items', className="items-list")
            ], className="list-section")
        ], className="page-container")
    ], className="page-wrapper")

# Página de mantenimiento modernizada
def create_mantenimiento_page():
    mantenimiento_df = get_data('mantenimiento')
    
    return html.Div([
        html.Div([
            html.H2("Plan de Mantenimiento", className="page-header"),
            
            # Tarjetas de años
            html.Div([
                html.Div([
                    html.Div([
                        html.H3(f"Año {row['año']}", className="year-title"),
                        html.Div([
                            html.Div([
                                html.H4("Mantenimiento", className="maint-label"),
                                html.P(row['mantenimiento'], className="maint-names")
                            ], className="maint-section"),
                            html.Div([
                                html.H4("Cadafals", className="maint-label"),
                                html.P(row['cadafals'], className="maint-names")
                            ], className="maint-section")
                        ], className="maint-content")
                    ], className="year-card-content")
                ], className=f"year-card {'year-card-current' if row['año'] == datetime.now().year else ''}")
                for _, row in mantenimiento_df.iterrows()
            ], className="years-grid")
        ], className="page-container")
    ], className="page-wrapper")

# Página de fiestas modernizada
def create_fiestas_page():
    fiestas_df = get_data('fiestas')
    
    return html.Div([
        html.Div([
            html.H2("Gestión de Fiestas", className="page-header"),
            
            # Formulario para añadir fiesta
            html.Div([
                html.Div([
                    html.Label("Fecha", className="form-label"),
                    dcc.DatePickerSingle(
                        id='fiesta-fecha',
                        date=date.today(),
                        display_format='DD/MM/YYYY',
                        className="date-picker"
                    ),
                ], className="form-field"),
                
                html.Div([
                    html.Label("Cocineros", className="form-label"),
                    dcc.Textarea(
                        id='fiesta-cocineros',
                        placeholder='Nombres de los cocineros',
                        className="textarea-field"
                    ),
                ], className="form-field"),
                
                html.Div([
                    html.Label("Menú", className="form-label"),
                    dcc.Textarea(
                        id='fiesta-menu',
                        placeholder='Describe el menú de la fiesta',
                        className="textarea-field"
                    ),
                ], className="form-field"),
                
                html.Div([
                    html.Div([
                        html.Label("Adultos", className="form-label"),
                        dcc.Input(
                            id='fiesta-adultos',
                            type='number',
                            value=0,
                            className="input-field"
                        ),
                    ], className="form-field-half"),
                    
                    html.Div([
                        html.Label("Niños", className="form-label"),
                        dcc.Input(
                            id='fiesta-ninos',
                            type='number',
                            value=0,
                            className="input-field"
                        ),
                    ], className="form-field-half"),
                ], className="form-row"),
                
                html.Button([
                    html.I(className="fas fa-calendar-plus btn-icon"),
                    "Crear Fiesta"
                ], id='add-fiesta', className="btn-primary btn-block")
            ], className="form-card"),
            
            # Lista de fiestas
            html.Div([
                html.H3("Fiestas Programadas", className="section-subheader"),
                html.Div(id='fiestas-list', className="items-list")
            ], className="list-section")
        ], className="page-container")
    ], className="page-wrapper")

# Callbacks para añadir datos
@app.callback(
    Output('comidas-list', 'children'),
    [Input('add-comida', 'n_clicks'),
     Input('url', 'pathname')],
    [State('comida-fecha', 'date'),
     State('tipo-servicio', 'value'),
     State('tipo-comida', 'value'),
     State('cocineros', 'value')]
)
def manage_comidas(n_clicks, pathname, fecha, tipo_servicio, tipo_comida, cocineros):
    if n_clicks and all([fecha, tipo_servicio, tipo_comida, cocineros]):
        add_data('comidas', {
            'fecha': fecha,
            'tipo_servicio': tipo_servicio,
            'tipo_comida': tipo_comida,
            'cocineros': cocineros
        })
    
    comidas_df = get_data('comidas')
    
    return [
        html.Div([
            html.Div([
                html.Div([
                    html.H4(f"{row['tipo_servicio']}: {row['tipo_comida']}", className="item-title"),
                    html.P(f"👨‍🍳 {row['cocineros']}", className="item-subtitle"),
                    html.P(f"📅 {row['fecha']}", className="item-date")
                ], className="item-info"),
                html.Button([
                    html.I(className="fas fa-trash")
                ], className="btn-delete", id={'type': 'delete-comida', 'index': row['id']})
            ], className="item-content")
        ], className="item-card")
        for _, row in comidas_df.iterrows()
    ]

@app.callback(
    Output('lista-items', 'children'),
    [Input('add-lista', 'n_clicks'),
     Input('url', 'pathname')],
    [State('lista-fecha', 'date'),
     State('objeto', 'value')]
)
def manage_lista(n_clicks, pathname, fecha, objeto):
    if n_clicks and all([fecha, objeto]):
        add_data('lista_compra', {
            'fecha': fecha,
            'objeto': objeto
        })
    
    lista_df = get_data('lista_compra')
    
    return [
        html.Div([
            html.Div([
                html.Div([
                    html.H4(row['objeto'], className="item-title"),
                    html.P(f"📅 {row['fecha']}", className="item-date")
                ], className="item-info"),
                html.Button([
                    html.I(className="fas fa-check")
                ], className="btn-check", id={'type': 'delete-lista', 'index': row['id']})
            ], className="item-content")
        ], className="item-card")
        for _, row in lista_df.iterrows()
    ]

@app.callback(
    Output('fiestas-list', 'children'),
    [Input('add-fiesta', 'n_clicks'),
     Input('url', 'pathname')],
    [State('fiesta-fecha', 'date'),
     State('fiesta-cocineros', 'value'),
     State('fiesta-menu', 'value'),
     State('fiesta-adultos', 'value'),
     State('fiesta-ninos', 'value')]
)
def manage_fiestas(n_clicks, pathname, fecha, cocineros, menu, adultos, ninos):
    if n_clicks and all([fecha, cocineros, menu]):
        add_data('fiestas', {
            'fecha': fecha,
            'cocineros': cocineros,
            'menu': menu,
            'adultos': adultos or 0,
            'niños': ninos or 0,
            'nombres_adultos': '',
            'nombres_niños': '',
            'programa': ''
        })
    
    fiestas_df = get_data('fiestas')
    
    return [
        html.Div([
            html.Div([
                html.Div([
                    html.H4(f"Fiesta - {row['fecha']}", className="item-title"),
                    html.P(f"👨‍🍳 {row['cocineros']}", className="item-subtitle"),
                    html.P(f"🍽️ {row['menu']}", className="item-text"),
                    html.P(f"👥 {row['adultos']} adultos, {row['niños']} niños", className="item-info-text")
                ], className="item-info"),
                html.Button([
                    html.I(className="fas fa-trash")
                ], className="btn-delete", id={'type': 'delete-fiesta', 'index': row['id']})
            ], className="item-content")
        ], className="fiesta-card")
        for _, row in fiestas_df.iterrows()
    ]

# Callbacks para eliminar (genérico)
@app.callback(
    Output('confirm-action', 'data'),
    [Input({'type': 'delete-comida', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'delete-lista', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'delete-fiesta', 'index': dash.dependencies.ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def delete_items(comida_clicks, lista_clicks, fiesta_clicks):
    ctx = callback_context
    
    if not ctx.triggered:
        return None
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_data = eval(button_id)
    
    if button_data['type'] == 'delete-comida':
        delete_data('comidas', button_data['index'])
    elif button_data['type'] == 'delete-lista':
        delete_data('lista_compra', button_data['index'])
    elif button_data['type'] == 'delete-fiesta':
        delete_data('fiestas', button_data['index'])
    
    return "deleted"

# Inicializar la base de datos
init_db()
migrate_fiestas_table()
update_mantenimiento_data()
load_eventos_completos()
load_fiestas_agosto_2025()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    app.run_server(debug=debug, host='0.0.0.0', port=port)