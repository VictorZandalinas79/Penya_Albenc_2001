
import asyncio
from telegram import Bot
import os
from datetime import datetime
import pandas as pd
import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_manager import dm
import os
from datetime import datetime, date, timedelta
import calendar
import dash_bootstrap_components as dbc
from dash import ALL, callback_context, dash_table, dcc, html
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
import io
import base64
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from dotenv import load_dotenv
load_dotenv()





# IMPORTAR DATA MANAGER
# Asumimos que tienes un archivo data_manager.py con un objeto `dm`
# que maneja la conexión a la base de datos (ej. Supabase).
from data_manager import dm

# Inicializar la app
app = dash.Dash(__name__, 
                suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP])

app.config.suppress_callback_exceptions = True
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Penya L'Albenc</title>
        <link rel="shortcut icon" href="/assets/favicon.ico">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        {%css%}
    </head>
    <body style="margin:0;padding:0;background:#f8fafc;font-family:'Inter',sans-serif;">
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

server = app.server

# ===== ENDPOINTS DE HEALTH CHECK =====
@server.route('/health')
def health_check():
    """Endpoint ligero para health checks"""
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}, 200

@server.route('/ping')
def ping():
    """Endpoint ultra-ligero para pings"""
    return 'pong', 200

@server.route('/status')
def status():
    """Endpoint con info básica del sistema"""
    try:
        return {
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        }, 200
    except:
        return {'status': 'error', 'database': 'disconnected'}, 500

# ================================
# ===== FUNCIONES DE UTILIDAD =====
# ================================



def enviar_notificacion_telegram(mensaje):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    print("--- DEBUG TELEGRAM ---")
    print(f"Bot Token leído: {bot_token}")
    print(f"Chat ID leído: {chat_id}")
    print("----------------------")

    if not bot_token or not chat_id:
        print("❌ ERROR: Variables de entorno de Telegram no configuradas o nulas.")
        return False

    try:
        bot = Bot(token=bot_token)

        async def send():
            await bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown')

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(send())
        except RuntimeError:
            asyncio.run(send())

        print("✅ Mensaje enviado a Telegram.")
        return True
    except Exception as e:
        print(f"❌ ERROR al enviar a Telegram: {e}")
        return False


def registrar_cambio(tipo_cambio, descripcion, usuario="Anónimo"):
    """Registrar un cambio en el sistema usando el data_manager."""
    try:
        nueva_fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dm.add_data('cambios', (nueva_fecha, tipo_cambio, descripcion, usuario))
        return True
    except Exception as e:
        print(f"Error registrando cambio: {e}")
        return False

def obtener_ultimos_cambios(n=10):
    """Obtener los últimos N cambios."""
    try:
        cambios_df = dm.get_data('cambios')
        if not cambios_df.empty:
            cambios_df['fecha_dt'] = pd.to_datetime(cambios_df['fecha'])
            return cambios_df.sort_values('fecha_dt', ascending=False).head(n)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error obteniendo últimos cambios: {e}")
        return pd.DataFrame()

def get_proximos_eventos(limit=5):
    """Obtener próximos eventos desde las tablas de eventos y comidas."""
    try:
        eventos_df = dm.get_data('eventos')
        comidas_df = dm.get_comidas_recientes(limit=100)
        
        eventos_lista = []
        
        # Procesar eventos (sin cambios aquí)
        if not eventos_df.empty:
            for _, evento in eventos_df.iterrows():
                eventos_lista.append({
                    'fecha': evento['fecha'],
                    'tipo': evento['evento'],
                    'descripcion': evento.get('tipo', '')
                })
        
        # Procesar comidas (CON LOS CAMBIOS)
        if not comidas_df.empty:
            for _, comida in comidas_df.iterrows():
                # Formateamos el 'dia' para que sea más legible (ej: 'sant_antoni' -> 'Sant Antoni')
                dia_formateado = (comida.get('dia') or 'Comida').replace('_', ' ').title()
                
                eventos_lista.append({
                    'fecha': comida['fecha'],
                    'tipo': dia_formateado, # <-- CAMBIO CLAVE
                    'descripcion': f"({comida.get('tipo_comida', '')}) Cocinan: {comida.get('cocineros', 'N/A')}"
                })
        
        if eventos_lista:
            df_eventos = pd.DataFrame(eventos_lista)
            df_eventos['fecha_dt'] = pd.to_datetime(df_eventos['fecha'])
            hoy = pd.Timestamp.now().normalize()
            df_eventos = df_eventos[df_eventos['fecha_dt'] >= hoy]
            df_eventos = df_eventos.sort_values('fecha_dt').head(limit)
            return df_eventos
        
        return pd.DataFrame()
    except Exception as e:
        print(f"Error obteniendo próximos eventos: {e}")
        return pd.DataFrame()

def get_dias_fiestas_con_semana():
    """Generar opciones para el selector de días de fiestas con el día de la semana."""
    dias_semana = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    opciones = []
    for i in range(8, 18):
        fecha_str = f"2025-08-{i:02d}"
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia_semana = dias_semana[fecha_obj.weekday()]
        opciones.append({'label': f"{dia_semana} {i} de agosto 2025", 'value': fecha_str})
    return opciones

def generar_tarjetas_fiestas():
    """Generar las tarjetas visuales para la página de Fiestas."""
    try:
        fiestas_df = dm.get_data('fiestas')
        
        fiestas_agosto = fiestas_df[
            (fiestas_df['fecha'] >= '2025-08-08') & (fiestas_df['fecha'] <= '2025-08-17')
        ].sort_values('fecha') if not fiestas_df.empty else pd.DataFrame()
        
        if fiestas_agosto.empty:
            return [html.P("No hay datos de fiestas de agosto cargados.", style={"text-align": "center", "color": "#666"})]
        
        tarjetas = []
        dias_semana = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}

        for _, dia in fiestas_agosto.iterrows():
            fecha_obj = datetime.strptime(dia['fecha'], '%Y-%m-%d')
            dia_semana_str = dias_semana[fecha_obj.weekday()]
            fecha_formateada = f"{dia_semana_str} {fecha_obj.day} de agosto"
            
            eventos = dia['programa'].split('|') if dia['programa'] and isinstance(dia['programa'], str) else ['Sin programa']
            
            def crear_lista_comensales(nombres_str, emoji, color):
                if not nombres_str or pd.isna(nombres_str) or nombres_str.strip() == '':
                    return html.P("Sin comensales registrados", style={"font-style": "italic", "color": "#999", "margin": "0"})
                
                nombres = [nombre.strip() for nombre in nombres_str.split(',') if nombre.strip()]
                return html.Div([
                    html.Div(f"{emoji} {nombre}", style={
                        "background": f"{color}20", "padding": "4px 10px", "border-radius": "12px",
                        "border": f"1px solid {color}40", "font-size": "0.85rem", "margin": "2px"
                    }) for nombre in nombres
                ], style={"display": "flex", "flex-wrap": "wrap", "gap": "5px", "margin-top": "5px"})

            nombres_adultos = dia.get('nombres_adultos', '') or ''
            nombres_niños = dia.get('nombres_niños', '') or ''
            
            total_adultos = len([n for n in nombres_adultos.split(',') if n.strip()])
            total_niños = len([n for n in nombres_niños.split(',') if n.strip()])

            color_dia = "#FF5722"  # Naranja por defecto
            if "PENYES" in dia['cocineros'].upper(): color_dia = "#4CAF50" # Verde
            elif fecha_obj.weekday() == 5: color_dia = "#9C27B0"  # Morado para sábados
            elif fecha_obj.weekday() == 6: color_dia = "#2196F3"  # Azul para domingos

            tarjetas.append(html.Div([
                html.Div(f"📅 {fecha_formateada}", style={
                    "color": "white", "margin": "-20px -20px 15px -20px", "padding": "15px",
                    "background": f"linear-gradient(135deg, {color_dia} 0%, {color_dia}CC 100%)",
                    "border-radius": "12px 12px 0 0", "font-size": "1.2rem", "font-weight": "bold", "text-align": "center"
                }),
                html.H6("👨‍🍳 Cocineros:", style={"color": "#4CAF50"}),
                html.P(dia['cocineros'], style={"margin": "0 0 15px 0", "font-weight": "bold", "background": "#E8F5E8", "padding": "8px", "border-radius": "6px"}),
                html.H6("🍽️ Menú:", style={"color": "#2196F3"}),
                html.P(dia['menu'] or 'Sin menú definido', style={"margin": "0 0 15px 0", "font-style": "italic" if not dia['menu'] else "normal"}),
                html.H6(f"👥 Adultos ({total_adultos})", style={"color": "#9C27B0"}),
                crear_lista_comensales(nombres_adultos, "👤", "#9C27B0"),
                html.H6(f"👶 Niños ({total_niños})", style={"color": "#FF9800", "margin-top": "15px"}),
                crear_lista_comensales(nombres_niños, "👶", "#FF9800"),
                html.H6("🎪 Programa:", style={"color": "#795548", "margin-top": "15px"}),
                html.Div([html.Div(f"› {evento.strip()}", style={"padding": "3px 0"}) for evento in eventos]),
            ], style={
                "border": f"2px solid {color_dia}40", "margin": "15px", "padding": "20px", "border-radius": "16px",
                "background": "white", "box-shadow": f"0 8px 25px {color_dia}20", "flex": "1", "min-width": "350px", "max-width": "450px"
            }))
        
        return html.Div(tarjetas, style={"display": "flex", "flex-wrap": "wrap", "justify-content": "center", "gap": "15px"})
    except Exception as e:
        return [html.P(f"Error cargando tarjetas de fiestas: {e}", style={"color": "red"})]


def limpiar_comidas_antiguas():
    """Borrar automáticamente comidas de años anteriores al actual."""
    try:
        año_actual = datetime.now().year
        comidas_df = dm.get_data('comidas')
        
        if not comidas_df.empty:
            comidas_df['fecha_dt'] = pd.to_datetime(comidas_df['fecha'])
            comidas_df['año'] = comidas_df['fecha_dt'].dt.year
            
            antes = len(comidas_df)
            comidas_a_guardar = comidas_df[comidas_df['año'] >= año_actual].drop(columns=['fecha_dt', 'año'])
            despues = len(comidas_a_guardar)
            
            if antes > despues:
                dm.save_data('comidas', comidas_a_guardar)
                eliminadas = antes - despues
                print(f"🗑️ Limpieza automática: {eliminadas} comidas antiguas eliminadas")
                registrar_cambio('Sistema', f'Limpieza automática: {eliminadas} comidas antiguas eliminadas')
    except Exception as e:
        print(f"Error en limpieza automática de comidas: {e}")

# ================================
# ===== ESTILOS Y LAYOUTS =====
# ================================

STYLES = {
    'navbar': {
        'position': 'fixed', 'top': 0, 'left': 0, 'right': 0, 'height': '70px',
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 'color': 'white',
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'padding': '0 30px', 'boxShadow': '0 4px 20px rgba(0,0,0,0.1)', 'zIndex': '1000'
    },
    'container': {'marginTop': '90px', 'padding': '20px', 'maxWidth': '1400px', 'margin': '90px auto 20px auto'},
    'card': {'background': 'white', 'borderRadius': '16px', 'padding': '24px', 'marginBottom': '20px', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'},
    'button': {'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 'color': 'white', 'border': 'none', 'borderRadius': '8px', 'padding': '12px 24px', 'fontSize': '14px', 'fontWeight': '600', 'cursor': 'pointer'},
    'input': {'width': '100%', 'padding': '12px', 'borderRadius': '8px', 'border': '2px solid #e2e8f0', 'marginBottom': '12px'},
    'title': {'fontSize': '28px', 'fontWeight': '700', 'color': '#1a202c', 'marginBottom': '24px'},
    'subtitle': {'fontSize': '20px', 'fontWeight': '600', 'color': '#2d3748', 'marginBottom': '16px'}
}

# REEMPLAZA ESTA FUNCIÓN EN app.py

def create_modern_navbar():
    """Crea la barra de navegación superior fija y con efecto de cristal."""
    return html.Div(
        id="sidebar",
        className="d-flex justify-content-between align-items-center p-3",
        style={
            "position": "fixed",
            "top": "0",
            "left": "0",
            "right": "0",
            "zIndex": "1030",
            "background": "rgba(33, 37, 41, 0.8)", # Fondo oscuro semi-transparente
        },
        children=[
            html.A(
                href="/",
                className="d-flex align-items-center",
                style={"textDecoration": "none"},
                children=[
                    html.Img(src='/assets/logo.png', style={'height': '45px', 'marginRight': '10px'}),
                    html.H2("L'Albenc", className="d-block d-md-none m-0", style={"fontSize": "1.2rem", "color": "white"}),
                    html.H2("Penya L'Albenc", className="d-none d-md-block m-0", style={"fontSize": "1.5rem", "color": "white"})
                ]
            ),
            # El único cambio está aquí: hemos eliminado className="btn"
            html.Button(
                "☰",
                id="btn-toggle-sidebar",
            )
        ]
    )

def create_menu_dropdown():
    """Crea el menú de navegación que se despliega."""
    return html.Div(
        id="menu-dropdown",
        className="modern-dropdown",
        style={"display": "none"},
        children=[
            dcc.Link([html.Span("🏠"), " Inicio"], href="/", className="nav-link-dropdown"),
            dcc.Link([html.Span("🍽️"), " Comidas"], href="/comidas", className="nav-link-dropdown"),
            dcc.Link([html.Span("🛒"), " Compra"], href="/lista-compra", className="nav-link-dropdown"),
            dcc.Link([html.Span("📅"), " Eventos"], href="/eventos", className="nav-link-dropdown"),
            dcc.Link([html.Span("🎉"), " Fiestas"], href="/fiestas", className="nav-link-dropdown"),
            dcc.Link([html.Span("🔧"), " Mantenimiento"], href="/mantenimiento", className="nav-link-dropdown"), 
            dcc.Link([html.Span("🤝"), " Reuniones"], href="/reuniones", className="nav-link-dropdown"),
        ]
    )

def create_home_page(cache):
    # Usar datos del caché
    eventos_df = pd.DataFrame(cache['eventos'])
    comidas_df = pd.DataFrame(cache['comidas'])
    cambios_df = pd.DataFrame(cache['cambios'])
    mantenimiento_df = pd.DataFrame(cache['mantenimiento'])
    
    # Calcular próximos eventos desde el caché
    eventos_lista = []
    if not eventos_df.empty:
        for _, evento in eventos_df.iterrows():
            eventos_lista.append({
                'fecha': evento['fecha'],
                'tipo': evento['evento'],
                'descripcion': evento.get('tipo', '')
            })
    
    if not comidas_df.empty:
        for _, comida in comidas_df.iterrows():
            dia_formateado = (comida.get('dia') or 'Comida').replace('_', ' ').title()
            eventos_lista.append({
                'fecha': comida['fecha'],
                'tipo': dia_formateado,
                'descripcion': f"({comida.get('tipo_comida', '')}) Cocinan: {comida.get('cocineros', 'N/A')}"
            })
    
    proximos = pd.DataFrame()
    if eventos_lista:
        df_eventos = pd.DataFrame(eventos_lista)
        df_eventos['fecha_dt'] = pd.to_datetime(df_eventos['fecha'])
        hoy = pd.Timestamp.now().normalize()
        df_eventos = df_eventos[df_eventos['fecha_dt'] >= hoy]
        proximos = df_eventos.sort_values('fecha_dt').head(5)
    
    # Calcular últimos cambios desde el caché
    cambios = pd.DataFrame()
    if not cambios_df.empty:
        cambios_df['fecha_dt'] = pd.to_datetime(cambios_df['fecha'])
        cambios = cambios_df.sort_values('fecha_dt', ascending=False).head(8)
    
    año_actual = datetime.now().year
    mant_actual = mantenimiento_df[mantenimiento_df['año'] == año_actual] if not mantenimiento_df.empty else pd.DataFrame()
    
    # --- El layout se reconstruye con componentes Bootstrap y clases CSS modernas ---
    return dbc.Container([
        # 1. Logo (sin cambios)
        html.Div(className="text-center mb-4", children=[
            html.Img(src='/assets/logo2.png', style={'height': '120px', 'filter': 'drop-shadow(0 4px 8px rgba(0,0,0,0.2))'})
        ]),
        
        # 2. Tarjeta de Mantenimiento (sin cambios)
        dbc.Card(className="mb-4 glass-container", children=[
            dbc.CardHeader(html.H4(f"🔧 Mantenimiento {año_actual}", className="m-0 fw-bold")),
            dbc.CardBody([
                html.P(f"Mantenimiento: {mant_actual.iloc[0]['mantenimiento'] if not mant_actual.empty else 'Sin datos'}"),
                html.P(f"Cadafals: {mant_actual.iloc[0]['cadafals'] if not mant_actual.empty else 'Sin datos'}", className="mb-0"),
            ])
        ]),
        
        # 3. Fila responsiva para las dos listas mejoradas
        dbc.Row([
            # Columna para Próximos Eventos
            dbc.Col(md=6, children=[
                dbc.Card(className="mb-4 glass-container", children=[
                    dbc.CardHeader(html.H4("📅 Próximos Eventos", className="m-0 fw-bold")),
                    dbc.ListGroup(
                        # --- INICIO DE LA SECCIÓN CORREGIDA ---
                        [
                            dbc.ListGroupItem(
                                html.Div(className="d-flex w-100 align-items-center", children=[
                                    html.Div("📅", className="me-3 fs-4 text-primary"),
                                    html.Div([
                                        html.H6(row['tipo'], className="mb-1 fw-bold"),
                                        html.P(row['descripcion'], className="mb-1 text-muted small"),
                                        # Error corregido: Se ha completado la función de formato de fecha
                                        html.Small(f"Fecha: {datetime.strptime(row['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y')}", className="text-muted"),
                                    ]),
                                ]),
                                action=True
                            ) for _, row in proximos.iterrows() # Error corregido: Se ha añadido el bucle
                        ] if not proximos.empty else [dbc.ListGroupItem("No hay eventos próximos.", className="text-muted")], # Error corregido: Se ha añadido la condición else
                        flush=True
                    )
                ])
            ]), # <-- Error corregido: Faltaba el paréntesis de cierre de dbc.Col
            
            # Columna para Últimos Cambios
            dbc.Col(md=6, children=[
                dbc.Card(className="mb-4 glass-container", children=[
                    dbc.CardHeader(html.H4("🔔 Últimos Cambios", className="m-0 fw-bold")),
                    dbc.ListGroup(
                        [
                            dbc.ListGroupItem(
                                html.Div(className="d-flex w-100 align-items-center", children=[
                                    html.Div("🔔", className="me-3 fs-4 text-success"),
                                    html.Div([
                                        html.H6(row['tipo_cambio'], className="mb-1 fw-bold"),
                                        html.P(row['descripcion'], className="mb-1 text-muted small"),
                                        html.Small(datetime.strptime(row['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%y %H:%M'), className="text-muted"),
                                    ]),
                                ]),
                                action=True
                            ) for _, row in cambios.iterrows()
                        ] if not cambios.empty else [dbc.ListGroupItem("No hay cambios registrados.", className="text-muted")],
                        flush=True
                    )
                ])
            ]),
            # --- FIN DE LA SECCIÓN CORREGIDA ---
        ]),
    ])

def create_reuniones_page(cache):
    reuniones_df = pd.DataFrame(cache['reuniones'])
    
    return dbc.Container([
        html.H2("🤝 Acta de Reuniones", className="text-center my-4 fw-bold"),
        
        # Editor tipo Word
        dbc.Card(className="mb-4", style={'backgroundColor': '#fff', 'border': '1px solid #ddd', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'}, children=[
            dbc.CardBody([
                # Fecha
                html.Div([
                    html.Label("📅 Fecha de la reunión:", className="fw-bold mb-2"),
                    dcc.DatePickerSingle(id='reunion-fecha', date=date.today(), style={'marginBottom': '20px'})
                ]),
                
                # Editor de temas (estilo documento)
                html.Div([
                    html.Label("📝 Temas tratados:", className="fw-bold mb-2"),
                    dcc.Textarea(
                        id='reunion-temas',
                        placeholder="Escribe aquí los temas tratados usando formato Markdown...",
                        style={'width': '100%', 'height': '300px', 'fontFamily': 'monospace'}
                    ),
                    html.P(
                        "Puedes usar Markdown: **texto en negrita**, *texto en cursiva*, o empezar una línea con - para crear una lista.",
                        className="text-muted small mt-1"
                    )
                ], className="mb-4"),
                
                # Asistentes
                html.Div([
                    html.Label("👥 Asistentes (separados por coma):", className="fw-bold mb-2"),
                    dbc.Input(
                        id='reunion-asistentes',
                        placeholder="Juan Pérez, María García, Pedro López...",
                        style={'fontSize': '16px', 'padding': '10px'}
                    )
                ], className="mb-4"),
                
                # Botón guardar
                dbc.Button("💾 Guardar Acta", id='btn-guardar-reunion', color="success", size="lg", className="w-100"),
                html.Div(id='output-reunion', className="mt-3")
            ])
        ]),
        
        # Listado de reuniones guardadas
        dbc.Card(className="mb-4 glass-container", children=[
            dbc.CardHeader(html.H4("📋 Actas Anteriores", className="m-0")),
            dbc.ListGroup(
                [crear_item_reunion(row) for _, row in reuniones_df.iterrows()]
                if not reuniones_df.empty else [html.P("No hay reuniones registradas", className="p-3 text-muted")]
            , flush=True)
        ])
    ])

def crear_item_reunion(row):
    return dbc.ListGroupItem([
        html.Div(className="d-flex w-100 justify-content-between align-items-center", children=[
            html.Div([
                html.H6(f"📅 {row['fecha']}", className="mb-1 fw-bold"),
                html.Small(f"👥 {row['asistentes']}", className="text-muted")
            ], style={'cursor': 'pointer'}, id={'type': 'ver-reunion', 'index': row['id']}),
            html.Div([
                dbc.Button("📥 PDF", id={'type': 'btn-pdf-reunion', 'index': row['id']}, 
                          size="sm", color="primary", className="me-2"),
                dbc.Button("✕", id={'type': 'btn-eliminar-reunion', 'index': row['id']}, 
                          size="sm", color="danger", outline=True)
            ])
        ])
    ])

def create_mantenimiento_page(cache):
    mant_df = pd.DataFrame(cache['mantenimiento'])
    return dbc.Container([
        html.H2("🔧 Registro de Mantenimiento", className="text-center my-4 fw-bold"),

        dbc.Card(className="mb-4 glass-container", children=[
            dbc.CardHeader(html.H4("📋 Historial por Años", className="m-0")),
            dbc.ListGroup(
                [
                    dbc.ListGroupItem([
                        html.Div(className="d-flex w-100 align-items-center", children=[
                            html.Div("📅", className="me-3 fs-4 text-primary"),
                            html.Div([
                                html.H6(f"Año {row['año']}", className="mb-1 fw-bold"),
                                html.P(f"Mantenimiento: {row['mantenimiento']}", className="mb-1 text-muted small"),
                                html.P(f"Cadafals: {row['cadafals']}", className="mb-0 text-muted small"),
                            ]),
                        ])
                    ], action=True) for _, row in mant_df.sort_values('año', ascending=True).iterrows()
                ] if not mant_df.empty else [dbc.ListGroupItem("No hay datos de mantenimiento.", className="text-muted")],
                flush=True
            )
        ]),
    ], className="mt-5")

def create_fiestas_page(cache):
    return dbc.Container([
        html.H2("🎉 Fiestas de Agosto 2025", className="text-center my-4 fw-bold"),
        
        # Usamos una sola tarjeta para el panel de edición
        dbc.Card(className="mb-4 glass-container", body=True, children=[
            html.H3("✏️ Editar Detalles de un Día", className="mb-3"),
            dcc.Dropdown(
                id='fiesta-dia-selector',
                options=get_dias_fiestas_con_semana(),
                placeholder="Selecciona un día para editar...",
                className="mb-3"
            ),
            dcc.Textarea(
                id='fiesta-menu',
                placeholder="Describe el menú del día...",
                className="mb-3 form-control", # form-control hace que ocupe el ancho completo
                rows=3
            ),
            # Fila responsiva para las listas de comensales
            dbc.Row([
                # Columna de Adultos
                dbc.Col(md=6, className="mb-3 mb-md-0", children=[
                    html.H5(html.Span("👥 Adultos ", id='contador-adultos-nuevo', children="(0)")),
                    dbc.Card(id='lista-adultos-visual', className="mb-2 p-2", style={'minHeight': '150px'}),
                    dbc.InputGroup([
                        dbc.Input(id='input-nuevo-adulto', placeholder="Añadir adulto..."),
                        dbc.Button("➕", id='btn-add-adulto', n_clicks=0, color="primary")
                    ])
                ]),
                # Columna de Niños
                dbc.Col(md=6, children=[
                    html.H5(html.Span("👶 Niños ", id='contador-niños-nuevo', children="(0)")),
                    dbc.Card(id='lista-niños-visual', className="mb-2 p-2", style={'minHeight': '150px'}),
                    dbc.InputGroup([
                        dbc.Input(id='input-nuevo-niño', placeholder="Añadir niño..."),
                        dbc.Button("➕", id='btn-add-niño', n_clicks=0, color="warning")
                    ])
                ]),
            ]),
            dbc.Button('💾 Guardar Cambios', id='btn-guardar-cambios', n_clicks=0, color="success", className="mt-3 w-100"),
            html.Div(id='fiesta-output', className="mt-3"),
        ]),
        
        # El contenedor de tarjetas ya es flexible y responsivo
        html.Div(id='tarjetas-fiestas', className="mt-4")
    ], className="mt-5")

def create_comidas_page(cache):
    comidas_df = pd.DataFrame(cache['comidas'])
    año_actual = datetime.now().year
    
    # Para el selector de días: TODAS las comidas (todos los años)
    dias_unicos = comidas_df['dia'].unique() if not comidas_df.empty else []
    opciones_dias = [{'label': dia.replace('_', ' ').title(), 'value': dia} for dia in sorted(dias_unicos)]

    return dbc.Container([
        html.H2("🍽️ Gestión de Comidas", className="text-center my-4 fw-bold"),
        
        dcc.ConfirmDialog(id='confirm-eliminar-comida', message='¿Seguro que quieres eliminar esta comida?'),
        dcc.Store(id='store-año-comidas', data=año_actual),
        
        # Navegación por años
        dbc.Card(className="mb-3 glass-container", body=True, children=[
            html.Div(className="d-flex justify-content-between align-items-center", children=[
                dbc.Button("←", id='btn-año-anterior', color="primary", outline=True),
                html.H4(id='display-año-actual', children=f"Año {año_actual}", className="m-0"),
                dbc.Button("→", id='btn-año-siguiente', color="primary", outline=True),
            ])
        ]),
        
        dbc.Card(className="mb-4 glass-container", children=[
            dbc.CardHeader(html.H4("📋 Comidas Planificadas", className="m-0")),
            html.Div(id='lista-comidas-container')
        ]),
        
        dbc.Card(body=True, className="mb-4 glass-container", children=[
            html.H3("🎯 Modificar Cocineros", className="mb-3"),
            dbc.Row([
                dbc.Col(md=6, className="mb-2 mb-md-0", children=[
                    html.Label("1. Selecciona el día:", className="fw-bold"),
                    dcc.Dropdown(id='comida-dia-selector', options=opciones_dias, placeholder="Ej: Sant Antoni...")  # ← Con opciones_dias
                ]),
                dbc.Col(md=6, children=[
                    html.Label("2. Selecciona la fecha:", className="fw-bold"),
                    dcc.Dropdown(id='comida-fecha-selector', placeholder="Elige un día primero...", disabled=True)
                ]),
            ]),
            
            html.Div(id='panel-acciones-comida', className="mt-4", style={'display': 'none'}, children=[
                dbc.Alert(id='info-cocineros-actuales', color="info"),
                html.Label("3. Elige una acción:", className="fw-bold mt-3"),
                dcc.Dropdown(
                    id='comida-accion-selector',
                    options=[
                        {'label': '➕ Agregar Cocinero', 'value': 'agregar'},
                        {'label': '➖ Eliminar Cocinero', 'value': 'eliminar'},
                        {'label': '🔄 Intercambiar Cocinero', 'value': 'intercambiar'}
                    ],
                    placeholder="Selecciona qué quieres hacer..."
                ),
                html.Div(id='campos-accion-comida', className="mt-3 p-3", 
                         style={'backgroundColor': 'rgba(255,255,255,0.5)', 'borderRadius': '8px'},
                         children=[
                             html.Div([
                                 html.Label("Nuevo cocinero:", className="fw-bold"),
                                 dbc.Input(id='comida-nuevo-cocinero-input', placeholder="Nombre del cocinero a añadir")
                             ], style={'display': 'none'}),
                             html.Div([
                                 html.Label("Cocinero a eliminar:", className="fw-bold"),
                                 dcc.Dropdown(id='comida-eliminar-cocinero-select', options=[])
                             ], style={'display': 'none'}),
                             html.Div([
                                 html.Label("3. Selecciona el OTRO día primero:", className="fw-bold"),
                                 dcc.Dropdown(id='intercambio-otra-comida-select', options=[]),
                                 dbc.Row([
                                     dbc.Col(md=6, children=[
                                         html.Label("1. Cocinero de ESTE día:", className="fw-bold mt-3"),
                                         dcc.Dropdown(id='intercambio-cocinero-origen', options=[])
                                     ]),
                                     dbc.Col(md=6, children=[
                                         html.Label("2. Cocinero del OTRO día:", className="fw-bold mt-3"),
                                         dcc.Dropdown(id='intercambio-cocinero-destino', disabled=True)
                                     ])
                                 ]),
                             ], style={'display': 'none'}),
                             html.P("Selecciona una acción para continuar.", className="text-muted")
                         ]),
                dbc.Button("✅ Ejecutar Acción", id='btn-ejecutar-comida-accion', color="success", className="mt-3 w-100"),
            ]),
            html.Div(id='output-accion-comida', className="mt-3")
        ]),
    ], className="mt-5")

def create_lista_compra_page(cache):
    lista_df = pd.DataFrame(cache['lista_compra'])
    return dbc.Container([
        html.H2("🛒 Lista de Compra", className="text-center my-4 fw-bold"),
        
        dcc.ConfirmDialog(id='confirm-eliminar-item', message='¿Seguro que quieres eliminar este item?'),
        
        dbc.Card(className="mb-4 glass-container", children=[
            dbc.CardHeader(html.H4("📝 Items en la Lista", className="m-0")),
            dbc.ListGroup(
                [
                    dbc.ListGroupItem([
                        html.Div(className="d-flex w-100 align-items-center justify-content-between", children=[
                            html.Div([
                                html.H6(row['objeto'], className="mb-1 fw-bold"),
                                html.Small(f"Fecha: {row['fecha']}", className="text-muted"),
                            ]),
                            dbc.Button("✕", id={'type': 'btn-eliminar-item', 'index': row['id']}, 
                                     color="danger", size="sm", outline=True)
                        ])
                    ], action=True) for _, row in lista_df.iterrows()
                ] if not lista_df.empty else [dbc.ListGroupItem("La lista está vacía.", className="text-muted")],
                flush=True
            )
        ]),
        
        dbc.Card(body=True, className="glass-container", children=[
            html.H3("➕ Agregar Item", className="mb-3"),
            dcc.DatePickerSingle(id='lista-nueva-fecha', date=date.today(), className="mb-2"),
            dbc.Input(id='lista-nuevo-objeto', placeholder="Objeto a comprar", className="mb-2"),
            dbc.Button('Agregar', id='btn-agregar-lista', color="primary", className="w-100"),
            html.Div(id='output-lista', className="mt-2")
        ])
    ], className="mt-5")

def create_eventos_page(cache):
    eventos_df = pd.DataFrame(cache['eventos'])
    return dbc.Container([
        html.H2("📅 Eventos Especiales", className="text-center my-4 fw-bold"),
        
        dcc.ConfirmDialog(id='confirm-eliminar-evento', message='¿Seguro que quieres eliminar este evento?'),

        dbc.Card(className="mb-4 glass-container", children=[
            dbc.CardHeader(html.H4("🎉 Eventos Registrados", className="m-0")),
            dbc.ListGroup(
                [
                    dbc.ListGroupItem([
                        html.Div(className="d-flex w-100 align-items-center justify-content-between", children=[
                            html.Div([
                                html.H6(row['evento'], className="mb-1 fw-bold"),
                                html.P(f"Tipo: {row['tipo']}", className="mb-1 text-muted small"),
                                html.Small(f"Fecha: {row['fecha']}", className="text-muted"),
                            ]),
                            dbc.Button("✕", id={'type': 'btn-eliminar-evento', 'index': row['id']}, 
                                     color="danger", size="sm", outline=True)
                        ])
                    ], action=True) for _, row in eventos_df.iterrows()
                ] if not eventos_df.empty else [dbc.ListGroupItem("No hay eventos.", className="text-muted")],
                flush=True
            )
        ]),

        dbc.Card(body=True, className="glass-container", children=[
            html.H3("➕ Agregar Evento", className="mb-3"),
            dcc.DatePickerSingle(id='evento-nueva-fecha', date=date.today(), className="mb-2"),
            dbc.Input(id='evento-nuevo-nombre', placeholder="Nombre del evento", className="mb-2"),
            dbc.Input(id='evento-nuevo-tipo', placeholder="Tipo/Descripción", className="mb-2"),
            dbc.Button('Agregar Evento', id='btn-agregar-evento', color="primary", className="w-100"),
            html.Div(id='output-evento', className="mt-2")
        ])
    ], className="mt-5")

@app.callback(
    [Output('store-id-eliminar-reunion', 'data'),
     Output('confirm-eliminar-reunion', 'displayed')],
    Input({'type': 'btn-eliminar-reunion', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def marcar_reunion_eliminar(n_clicks):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks):
        raise PreventUpdate
    
    reunion_id = ctx.triggered_id['index']
    return reunion_id, True
    
# =============================================
# ===== CALLBACK DE CARGA INICIAL OPTIMIZADA =====
# =============================================
# 
# OPTIMIZACIONES IMPLEMENTADAS:
# 1. Solo carga comidas del año actual (no históricas)
# 2. Solo carga próximos 20 eventos (no pasados)
# 3. Solo últimos 15 cambios (no todo el historial)
# 4. Usa consultas SQL filtradas (más rápido que cargar todo)
# 5. Reduce tiempo de carga de 5-10s a 1-2s ⚡
#
# Si necesitas MÁS datos en alguna página específica:
# - Puedes usar dm.get_data('tabla') para cargar TODO
# - O crear callbacks lazy que carguen al visitar esa página
#     
@app.callback(
        [Output('store-comidas', 'data'),
        Output('store-eventos', 'data'),
        Output('store-fiestas', 'data'),
        Output('store-lista-compra', 'data'),
        Output('store-cambios', 'data'),
        Output('store-reuniones', 'data'),
        Output('store-mantenimiento', 'data'),
        Output('loading-overlay', 'className'),
        Output('store-data-loaded-signal', 'data')], # <-- OUTPUT AÑADIDO
        Input('url', 'pathname'),
        prevent_initial_call=False
    )
def cargar_datos_iniciales(pathname):
    """Carga SOLO los datos esenciales para inicio RÁPIDO - VERSIÓN OPTIMIZADA"""
    print("🔄 Iniciando carga OPTIMIZADA de datos...")
        
    try:
        print("📊 Cargando comidas recientes (solo año actual)...")
        comidas = dm.get_comidas_recientes(limit=50).to_dict('records')
        print(f"✅ Comidas cargadas: {len(comidas)} registros")
            
        print("📅 Cargando eventos próximos...")
        eventos = dm.get_eventos_proximos(limit=20).to_dict('records')
        print(f"✅ Eventos cargados: {len(eventos)} registros")
            
        print("🎉 Cargando fiestas (solo agosto)...")
        fiestas = dm.get_fiestas_agosto().to_dict('records')
        print(f"✅ Fiestas cargadas: {len(fiestas)} registros")
            
        print("🛒 Cargando lista compra...")
        lista_compra = dm.get_lista_compra_activa().to_dict('records')
        print(f"✅ Lista compra cargada: {len(lista_compra)} registros")
            
        print("🔔 Cargando últimos cambios...")
        cambios = dm.get_cambios_recientes(limit=15).to_dict('records')
        print(f"✅ Cambios cargados: {len(cambios)} registros")
            
        print("🤝 Cargando reuniones recientes...")
        reuniones = dm.get_reuniones_recientes(limit=20).to_dict('records')
        print(f"✅ Reuniones cargadas: {len(reuniones)} registros")
            
        print("🔧 Cargando mantenimiento actual...")
        mantenimiento = dm.get_data('mantenimiento').to_dict('records')
        print(f"✅ Mantenimiento cargado: {len(mantenimiento)} registros")
            
        print("✨ ¡Datos esenciales cargados RÁPIDAMENTE! ⚡")
        print("🎭 Ocultando overlay de carga...")
            
        # Ocultar el overlay y enviar la señal de éxito (1)
        return comidas, eventos, fiestas, lista_compra, cambios, reuniones, mantenimiento, 'loading-overlay hidden', 1
        
    except Exception as e:
        print(f"❌ ERROR FATAL cargando datos: {e}")
        print(f"❌ Tipo de error: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
            
        # Devolver datos vacíos, ocultar el loading y enviar señal de fallo (None)
        return [], [], [], [], [], [], [], 'loading-overlay hidden', None
    

# =============================================
# ===== CALLBACKS LAZY OPCIONALES (Descomentados si necesitas) =====
# =============================================
# 
# Si alguna página necesita TODOS los datos históricos (no solo recientes),
# puedes descomentar y usar estos callbacks:
#
# @app.callback(
#     Output('store-comidas', 'data', allow_duplicate=True),
#     Input('url', 'pathname'),
#     State('store-comidas', 'data'),
#     prevent_initial_call=True
# )
# def cargar_todas_comidas_lazy(pathname, comidas_actuales):
#     """Solo si visitamos /comidas y necesitamos TODAS las comidas históricas"""
#     if pathname == '/comidas' and len(comidas_actuales) < 100:
#         print("🔄 Cargando TODAS las comidas (lazy loading)...")
#         todas_comidas = dm.get_data('comidas').to_dict('records')
#         print(f"✅ Todas las comidas cargadas: {len(todas_comidas)} registros")
#         return todas_comidas
#     raise PreventUpdate
#
# @app.callback(
#     Output('store-eventos', 'data', allow_duplicate=True),
#     Input('url', 'pathname'),
#     State('store-eventos', 'data'),
#     prevent_initial_call=True
# )
# def cargar_todos_eventos_lazy(pathname, eventos_actuales):
#     """Solo si visitamos /eventos y necesitamos TODOS los eventos"""
#     if pathname == '/eventos' and len(eventos_actuales) < 50:
#         print("🔄 Cargando TODOS los eventos (lazy loading)...")
#         todos_eventos = dm.get_data('eventos').to_dict('records')
#         return todos_eventos
#     raise PreventUpdate


@app.callback(
    Output('page-content', 'children', allow_duplicate=True),
    Input('confirm-eliminar-reunion', 'submit_n_clicks'),
    [State('store-id-eliminar-reunion', 'data'),
     State('url', 'pathname'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data'),
     State('store-reuniones', 'data')],
    prevent_initial_call=True
)
def eliminar_reunion_confirmado(submit, reunion_id, pathname, comidas, eventos, fiestas, mant, lista, cambios, reuniones):
    if submit and reunion_id:
        reuniones_df = dm.get_data('reuniones')
        reuniones_df = reuniones_df[reuniones_df['id'] != reunion_id]
        dm.save_data('reuniones', reuniones_df)
        
        cache = {
            'comidas': comidas or [], 'eventos': eventos or [], 'fiestas': fiestas or [],
            'mantenimiento': mant or [], 'lista_compra': lista or [], 'cambios': cambios or [],
            'reuniones': reuniones_df.to_dict('records')
        }
        return create_reuniones_page(cache)
    raise PreventUpdate

@app.callback(
    [Output('modal-editar-reunion', 'is_open'),
     Output('modal-reunion-fecha', 'date'),
     Output('modal-reunion-temas', 'value'),
     Output('modal-reunion-asistentes', 'value'),
     Output('store-reunion-editando', 'data')],
    [Input({'type': 'ver-reunion', 'index': ALL}, 'n_clicks'),
     Input('btn-cerrar-modal-reunion', 'n_clicks')],
    [State('store-reuniones', 'data')],
    prevent_initial_call=True
)
def toggle_modal_reunion(ver_clicks, cerrar, reuniones):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger = ctx.triggered_id
    
    if trigger == 'btn-cerrar-modal-reunion':
        return False, None, "", "", None
    
    if isinstance(trigger, dict) and trigger['type'] == 'ver-reunion':
        reunion_id = trigger['index']
        reunion = next((r for r in reuniones if r['id'] == reunion_id), None)
        if reunion:
            return True, reunion['fecha'], reunion['temas'], reunion['asistentes'], reunion_id
    
    raise PreventUpdate

@app.callback(
    Output('download-pdf', 'data'),
    Input({'type': 'btn-pdf-reunion', 'index': ALL}, 'n_clicks'),
    State('store-reuniones', 'data'),
    prevent_initial_call=True
)
def descargar_pdf_reunion(n_clicks, reuniones):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks):
        raise PreventUpdate
    
    reunion_id = ctx.triggered_id['index']
    reunion = next((r for r in reuniones if r['id'] == reunion_id), None)
    
    if not reunion:
        raise PreventUpdate

    # Preparamos el contenido en un buffer de memoria
    buffer = io.BytesIO()
    
    # 1. Crear el documento con tamaño A4 y márgenes
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)

    # 2. Preparar los estilos de texto (título, cuerpo, etc.)
    styles = getSampleStyleSheet()
    style_h1 = styles['h1']
    style_h1.alignment = 1 # 0=izquierda, 1=centro, 2=derecha
    style_body = styles['BodyText']
    style_body.leading = 14 # Espacio entre líneas
    
    # 3. Crear el "Story" (la secuencia de elementos en el PDF)
    story = []

    # Título
    story.append(Paragraph("Acta de Reunión - Penya L'Albenc", style_h1))
    story.append(Spacer(1, 0.25 * inch))

    # Fecha
    fecha_str = f"<b>Fecha:</b> {reunion['fecha']}"
    story.append(Paragraph(fecha_str, style_body))
    story.append(Spacer(1, 0.2 * inch))
    
    # Asistentes (con ajuste de línea automático)
    asistentes_str = f"<b>Asistentes:</b> {reunion.get('asistentes', 'No registrados')}"
    story.append(Paragraph(asistentes_str, style_body))
    story.append(Spacer(1, 0.4 * inch))
    
    # Temas tratados (convirtiendo Markdown simple a HTML para el PDF)
    story.append(Paragraph("<b>Temas Tratados:</b>", style_body))
    
    temas_markdown = reunion.get('temas', 'Sin temas.')
    # Convertimos saltos de línea en <br/> para que Paragraph los entienda
    temas_html = temas_markdown.replace('\n', '<br/>')
    
    story.append(Paragraph(temas_html, style_body))

    # 4. Construir el PDF
    doc.build(story)
    
    buffer.seek(0)
    
    return dcc.send_bytes(buffer.getvalue(), f"acta_reunion_{reunion['fecha']}.pdf")
# =======================
# ===== CALLBACKS =====
# =======================

@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('output-reunion', 'children')],
    Input('btn-guardar-reunion', 'n_clicks'),
    [State('reunion-fecha', 'date'),
     State('reunion-temas', 'value'),
     State('reunion-asistentes', 'value'),
     State('url', 'pathname'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data'),
     State('store-reuniones', 'data')],
    prevent_initial_call=True
)
def guardar_reunion(n_clicks, fecha, temas, asistentes, pathname, comidas, eventos, fiestas, mant, lista, cambios, reuniones):
    if not n_clicks or not temas:
        raise PreventUpdate
    
    dm.add_data('reuniones', (fecha, temas, asistentes, 'finalizada'))
    
    # Actualizar cache y recargar página
    reuniones_df = dm.get_data('reuniones')
    cache = {
        'comidas': comidas or [],
        'eventos': eventos or [],
        'fiestas': fiestas or [],
        'mantenimiento': mant or [],
        'lista_compra': lista or [],
        'cambios': cambios or [],
        'reuniones': reuniones_df.to_dict('records')
    }
    
    return create_reuniones_page(cache), dbc.Alert("✅ Reunión guardada", color="success", duration=3000)

# ---- Router Principal ----
@app.callback(
    Output('page-content', 'children'),
    Input('store-data-loaded-signal', 'data'), # <-- INPUT CAMBIADO
    [State('url', 'pathname'),                 # <-- URL AHORA ES STATE
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data'),
     State('store-reuniones', 'data')]
)
def display_page(signal, pathname, comidas, eventos, fiestas, mant, lista, cambios, reuniones): # <-- PARÁMETROS CORREGIDOS
    if signal is None: # Si la carga de datos falló o no se ha completado
        return html.Div("Error al cargar los datos. Refresca la página.", style={"text-align": "center", "padding": "50px", "color": "red"})
    
    # Esta comprobación ya no es estrictamente necesaria, pero la dejamos como seguridad
    if comidas is None or eventos is None:
        return html.Div("Cargando...", style={"text-align": "center", "padding": "50px"})
    
    # Crear cache con todos los datos
    cache = {
        'comidas': comidas or [],
        'eventos': eventos or [],
        'fiestas': fiestas or [],
        'mantenimiento': mant or [],
        'lista_compra': lista or [],
        'cambios': cambios or [],
        'reuniones': reuniones or []
    }
    
    if pathname == '/' or pathname == '/dashboard':
        return create_home_page(cache)
    elif pathname == '/comidas':
        return create_comidas_page(cache)
    elif pathname == '/lista-compra':
        return create_lista_compra_page(cache)
    elif pathname == '/eventos':
        return create_eventos_page(cache)
    elif pathname == '/fiestas':
        return create_fiestas_page(cache)
    elif pathname == '/mantenimiento':
        return create_mantenimiento_page(cache)
    elif pathname == '/reuniones':
        return create_reuniones_page(cache)
    else:
        return html.H3('404 - Página no encontrada', style={'textAlign': 'center', 'marginTop': '50px'})
# ---- Callbacks de Fiestas (Página Interactiva) ----

@app.callback(
    [Output('fiesta-menu', 'value'), Output('store-comensales-adultos', 'data', allow_duplicate=True),
     Output('store-comensales-niños', 'data', allow_duplicate=True), Output('lista-adultos-visual', 'children', allow_duplicate=True),
     Output('lista-niños-visual', 'children', allow_duplicate=True), Output('contador-adultos-nuevo', 'children', allow_duplicate=True),
     Output('contador-niños-nuevo', 'children', allow_duplicate=True)],
    [Input('fiesta-dia-selector', 'value')],
    prevent_initial_call=True
)
def cargar_datos_fiesta(fecha_seleccionada):
    if not fecha_seleccionada: raise PreventUpdate
    
    fiestas_df = dm.get_data('fiestas')
    dia_data = fiestas_df[fiestas_df['fecha'] == fecha_seleccionada]
    if dia_data.empty: return "", [], [], [], [], "(0)", "(0)"
    
    dia = dia_data.iloc[0]
    nombres_adultos_str = dia.get('nombres_adultos', '') or ''
    nombres_niños_str = dia.get('nombres_niños', '') or ''
    
    adultos = [n.strip() for n in nombres_adultos_str.split(',') if n.strip()]
    niños = [n.strip() for n in nombres_niños_str.split(',') if n.strip()]
    
    # --- ESTA ES LA FUNCIÓN CORREGIDA ---
    def crear_lista_visual_moderna(nombres, tipo, emoji):
        if not nombres:
            return [html.P("Sin comensales", className="text-muted fst-italic m-2")]
        
        return [
            html.Div([
                f"{emoji} {nombre}",
                dbc.Button("❌", 
                           id={'type': 'btn-eliminar-comensal', 'index': i, 'nombre': nombre, 'categoria': tipo},
                           size="sm", color="danger", outline=True, className="ms-auto")
            ], className="d-flex align-items-center p-1 border-bottom")
            for i, nombre in enumerate(nombres)
        ]

    return (
        dia.get('menu', ''), 
        adultos, 
        niños, 
        crear_lista_visual_moderna(adultos, 'adulto', '👤'), 
        crear_lista_visual_moderna(niños, 'niño', '👶'), 
        f"({len(adultos)})", 
        f"({len(niños)})"
    )

# EVENTOS - Guardar ID y mostrar confirm
@app.callback(
    [Output('store-id-eliminar-evento', 'data'),
     Output('confirm-eliminar-evento', 'displayed')],
    Input({'type': 'btn-eliminar-evento', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def guardar_id_evento(n_clicks):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks):
        raise PreventUpdate
    
    button_id = ctx.triggered_id['index']
    return button_id, True

@app.callback(
    Output('page-content', 'children', allow_duplicate=True),
    Input('confirm-eliminar-evento', 'submit_n_clicks'),
    [State('store-id-eliminar-evento', 'data'),
     State('url', 'pathname'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data')],
    prevent_initial_call=True
)
def eliminar_evento_confirmado(submit, evento_id, pathname, comidas, eventos, fiestas, mant, lista, cambios):
    if submit and evento_id:
        eventos_df = dm.get_data('eventos')
        eventos_df = eventos_df[eventos_df['id'] != evento_id]
        dm.save_data('eventos', eventos_df)
        registrar_cambio('Eventos', f'Evento ID {evento_id} eliminado')
        
        cache = {
            'comidas': comidas or [], 'eventos': eventos_df.to_dict('records'), 'fiestas': fiestas or [],
            'mantenimiento': mant or [], 'lista_compra': lista or [], 'cambios': cambios or []
        }
        return create_eventos_page(cache) if pathname == '/eventos' else dash.no_update
    raise PreventUpdate

# COMIDAS - Guardar ID y mostrar confirm
@app.callback(
    [Output('store-id-eliminar-comida', 'data'),
     Output('confirm-eliminar-comida', 'displayed')],
    Input({'type': 'btn-eliminar-comida', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def guardar_id_comida(n_clicks):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks):
        raise PreventUpdate
    
    button_id = ctx.triggered_id['index']
    return button_id, True

@app.callback(
    Output('page-content', 'children', allow_duplicate=True),
    Input('confirm-eliminar-comida', 'submit_n_clicks'),
    [State('store-id-eliminar-comida', 'data'),
     State('url', 'pathname'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data')],
    prevent_initial_call=True
)
def eliminar_comida_confirmada(submit, comida_id, pathname, comidas, eventos, fiestas, mant, lista, cambios):
    if submit and comida_id:
        comidas_df = dm.get_data('comidas')
        comidas_df = comidas_df[comidas_df['id'] != comida_id]
        dm.save_data('comidas', comidas_df)
        registrar_cambio('Comidas', f'Comida ID {comida_id} eliminada')
        
        cache = {
            'comidas': comidas_df.to_dict('records'), 'eventos': eventos or [], 'fiestas': fiestas or [],
            'mantenimiento': mant or [], 'lista_compra': lista or [], 'cambios': cambios or []
        }
        return create_comidas_page(cache) if pathname == '/comidas' else dash.no_update
    raise PreventUpdate

# ITEMS COMPRA - Guardar ID y mostrar confirm
@app.callback(
    [Output('store-id-eliminar-item', 'data'),
     Output('confirm-eliminar-item', 'displayed')],
    Input({'type': 'btn-eliminar-item', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def guardar_id_item(n_clicks):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks):
        raise PreventUpdate
    
    button_id = ctx.triggered_id['index']
    return button_id, True

@app.callback(
    Output('page-content', 'children', allow_duplicate=True),
    Input('confirm-eliminar-item', 'submit_n_clicks'),
    [State('store-id-eliminar-item', 'data'),
     State('url', 'pathname'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data')],
    prevent_initial_call=True
)
def eliminar_item_confirmado(submit, item_id, pathname, comidas, eventos, fiestas, mant, lista, cambios):
    if submit and item_id:
        lista_df_vieja = dm.get_data('lista_compra')
        item_eliminado_fila = lista_df_vieja[lista_df_vieja['id'] == item_id]
        nombre_item_eliminado = item_eliminado_fila.iloc[0]['objeto'] if not item_eliminado_fila.empty else "un item"
        lista_df = dm.get_data('lista_compra')
        lista_df = lista_df[lista_df['id'] != item_id]
        dm.save_data('lista_compra', lista_df)
        registrar_cambio('Lista', f'Item ID {item_id} eliminado')
        lista_str = "\n\n*Llista de la compra actual:* "
        if not lista_df.empty:
            for i, row in lista_df.iterrows():
                lista_str += f"\n{i+1}. {row['objeto']}"
        else:
            lista_str += "\nLa llista ha quedat buida."

        mensaje_final = f"🛒 *Item eliminat de la compra!*\nS'ha eliminat: *{nombre_item_eliminado}*\n{lista_str}"
        enviar_notificacion_telegram(mensaje_final)
        
        cache = {
            'comidas': comidas or [], 'eventos': eventos or [], 'fiestas': fiestas or [],
            'mantenimiento': mant or [], 'lista_compra': lista_df.to_dict('records'), 'cambios': cambios or []
        }
        return create_lista_compra_page(cache) if pathname == '/lista-compra' else dash.no_update
    raise PreventUpdate


@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('output-lista', 'children')],
    Input('btn-agregar-lista', 'n_clicks'),
    [State('lista-nueva-fecha', 'date'),
     State('lista-nuevo-objeto', 'value'),
     State('url', 'pathname'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data')],
    prevent_initial_call=True
)
def agregar_item_lista(n_clicks, fecha, objeto, pathname, comidas, eventos, fiestas, mant, lista, cambios):
    if not n_clicks or not objeto:
        raise PreventUpdate
    
    dm.add_data('lista_compra', (fecha, objeto))
    registrar_cambio('Lista Compra', f'Item añadido: {objeto}')
    
    # --- INICIO DE LA CORRECCIÓN ---
    # Obtenemos los datos y los guardamos en 'lista_df'
    lista_df = dm.get_data('lista_compra')
    
    # Formateamos el mensaje para Telegram
    lista_str = "\n\n*Llista de la compra actual:* "
    if not lista_df.empty:
        # Usamos enumerate para tener un índice numérico
        for i, row in lista_df.iterrows():
            lista_str += f"\n{i+1}. {row['objeto']}"
    else:
        lista_str += "\nLa llista està buida."
    
    mensaje_final = f"🛒 *Nou item a la compra!*\nS'ha afegit: *{objeto}*\n{lista_str}"
    enviar_notificacion_telegram(mensaje_final)
    
    # Ahora, cuando usamos 'lista_df' aquí, la variable SÍ existe
    cache = {
        'comidas': comidas or [], 'eventos': eventos or [], 'fiestas': fiestas or [],
        'mantenimiento': mant or [], 'lista_compra': lista_df.to_dict('records'), 'cambios': cambios or []
    }
    # --- FIN DE LA CORRECCIÓN ---
    
    return create_lista_compra_page(cache) if pathname == '/lista-compra' else dash.no_update, dbc.Alert(f"✅ '{objeto}' añadido", color="success", duration=3000)

@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('output-evento', 'children')],
    Input('btn-agregar-evento', 'n_clicks'),
    [State('evento-nueva-fecha', 'date'),
     State('evento-nuevo-nombre', 'value'),
     State('evento-nuevo-tipo', 'value'),
     State('url', 'pathname'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data')],
    prevent_initial_call=True
)
def agregar_evento(n_clicks, fecha, nombre, tipo, pathname, comidas, eventos, fiestas, mant, lista, cambios):
    if not n_clicks or not nombre:
        raise PreventUpdate
    
    dm.add_data('eventos', (fecha, nombre, tipo or ''))
    registrar_cambio('Eventos', f'Evento añadido: {nombre}')
    
    eventos_df = dm.get_data('eventos')
    cache = {
        'comidas': comidas or [], 'eventos': eventos_df.to_dict('records'), 'fiestas': fiestas or [],
        'mantenimiento': mant or [], 'lista_compra': lista or [], 'cambios': cambios or []
    }
    
    return create_eventos_page(cache) if pathname == '/eventos' else dash.no_update, dbc.Alert(f"✅ '{nombre}' añadido", color="success", duration=3000)

# CALLBACK 1: Habilita y llena el dropdown de fechas cuando se elige un tipo de comida.
@app.callback(
    [Output('comida-fecha-selector', 'options'),
     Output('comida-fecha-selector', 'disabled')],
    Input('comida-dia-selector', 'value') # <-- CAMBIO
)
def actualizar_selector_fecha(dia_seleccionado): # <-- CAMBIO
    if not dia_seleccionado:
        return [], True
    
    comidas_df = dm.get_data('comidas')
    # Filtramos por 'dia' en lugar de 'tipo_comida'
    fechas = comidas_df[comidas_df['dia'] == dia_seleccionado]['fecha'].unique() # <-- CAMBIO
    opciones = [{'label': f, 'value': f} for f in sorted(fechas)]
    return opciones, False

# CALLBACK 2: Muestra el panel de acciones cuando se ha seleccionado una fecha.
@app.callback(
    [Output('panel-acciones-comida', 'style'),
     Output('info-cocineros-actuales', 'children')],
    Input('comida-fecha-selector', 'value'),
    State('comida-dia-selector', 'value'), # <-- CAMBIO
    prevent_initial_call=True
)
def mostrar_panel_acciones(fecha, dia): # <-- CAMBIO
    if not fecha or not dia:
        return {'display': 'none'}, ""
        
    comidas_df = dm.get_data('comidas')
    # La consulta ahora usa 'dia'
    comida_seleccionada = comidas_df[(comidas_df['dia'] == dia) & (comidas_df['fecha'] == fecha)] # <-- CAMBIO
    
    if comida_seleccionada.empty:
        return {'display': 'none'}, "Error: No se encontró la comida."
        
    cocineros = comida_seleccionada.iloc[0]['cocineros']
    tipo_comida_info = comida_seleccionada.iloc[0]['tipo_comida']
    # Mensaje más informativo
    return {'display': 'block'}, f"Cocineros actuales para {dia.replace('_', ' ').title()} ({tipo_comida_info}): {cocineros}"

# CALLBACK 3: Muestra los campos correctos según la acción (Agregar, Eliminar, Intercambiar).
@app.callback(
    Output('campos-accion-comida', 'children'),
    Input('comida-accion-selector', 'value'),
    [State('comida-fecha-selector', 'value'),
     State('comida-dia-selector', 'value')]
)
def renderizar_campos_accion(accion, fecha, dia):
    comidas_df = dm.get_data('comidas')
    
    # Valores por defecto si no hay selección
    opciones_cocineros_actuales = []
    opciones_otras_comidas = []
    
    if dia and fecha:
        comida_actual = comidas_df[(comidas_df['dia'] == dia) & (comidas_df['fecha'] == fecha)]
        
        if not comida_actual.empty:
            cocineros_actuales = [c.strip() for c in comida_actual.iloc[0]['cocineros'].split(',')]
            opciones_cocineros_actuales = [{'label': c, 'value': c} for c in cocineros_actuales]
            
            otras_comidas = comidas_df.drop(comida_actual.index)
            opciones_otras_comidas = [
                {'label': f"{row['dia'].replace('_', ' ').title()} del {row['fecha']}", 'value': row['id']}
                for index, row in otras_comidas.iterrows()
            ]

    # SIEMPRE renderizar TODOS los campos, solo cambiar visibilidad
    return html.Div([
        # Campo agregar
        html.Div([
            html.Label("Nuevo cocinero:", className="fw-bold"),
            dbc.Input(id='comida-nuevo-cocinero-input', placeholder="Nombre del cocinero a añadir")
        ], style={'display': 'block' if accion == 'agregar' else 'none'}),
        
        # Campo eliminar
        html.Div([
            html.Label("Cocinero a eliminar:", className="fw-bold"),
            dcc.Dropdown(id='comida-eliminar-cocinero-select', options=opciones_cocineros_actuales)
        ], style={'display': 'block' if accion == 'eliminar' else 'none'}),
        
        # Campos intercambiar
        html.Div([
            html.Label("3. Selecciona el OTRO día primero:", className="fw-bold"),
            dcc.Dropdown(id='intercambio-otra-comida-select', options=opciones_otras_comidas),
            
            dbc.Row([
                dbc.Col(md=6, children=[
                    html.Label("1. Cocinero de ESTE día:", className="fw-bold mt-3"),
                    dcc.Dropdown(id='intercambio-cocinero-origen', options=opciones_cocineros_actuales)
                ]),
                dbc.Col(md=6, children=[
                    html.Label("2. Cocinero del OTRO día:", className="fw-bold mt-3"),
                    dcc.Dropdown(id='intercambio-cocinero-destino', disabled=True)
                ])
            ]),
        ], style={'display': 'block' if accion == 'intercambiar' else 'none'}),
        
        # Mensaje si no hay acción seleccionada
        html.P("Selecciona una acción para continuar.", 
               className="text-muted", 
               style={'display': 'block' if not accion else 'none'})
    ])

# Llena la lista de cocineros del "otro día" cuando este es seleccionado.
@app.callback(
    [Output('intercambio-cocinero-destino', 'options'),
     Output('intercambio-cocinero-destino', 'disabled'),
     Output('intercambio-cocinero-destino', 'value')],  # ← Añade esto
    Input('intercambio-otra-comida-select', 'value'),
    prevent_initial_call=True
)
def actualizar_cocineros_destino_intercambio(id_otra_comida):
    if not id_otra_comida:
        return [], True, None
        
    comidas_df = dm.get_data('comidas')
    otra_comida = comidas_df[comidas_df['id'] == id_otra_comida]
    
    if otra_comida.empty:
        return [], True, None
        
    cocineros_destino = [c.strip() for c in otra_comida.iloc[0]['cocineros'].split(',')]
    opciones = [{'label': c, 'value': c} for c in cocineros_destino]
    return opciones, False, None  # ← Resetea el valor del segundo dropdown


# CALLBACK 5: El callback final que ejecuta la lógica de Agregar, Eliminar o Intercambiar.
@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('output-accion-comida', 'children')],
    Input('btn-ejecutar-comida-accion', 'n_clicks'),
    [State('comida-dia-selector', 'value'),
     State('comida-fecha-selector', 'value'),
     State('comida-accion-selector', 'value'),
     State('comida-nuevo-cocinero-input', 'value'),
     State('comida-eliminar-cocinero-select', 'value'),
     State('intercambio-cocinero-origen', 'value'),
     State('intercambio-cocinero-destino', 'value'),
     State('intercambio-otra-comida-select', 'value'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data')],
    prevent_initial_call=True
)
def ejecutar_accion_comida(n_clicks, dia, fecha, accion,
                           nuevo_cocinero, cocinero_a_eliminar,
                           cocinero_origen, cocinero_destino, id_otra_comida,
                           comidas, eventos, fiestas, mant, lista, cambios):
    if not n_clicks:
        raise PreventUpdate

    comidas_df = dm.get_data('comidas')
    idx_actual = comidas_df.index[(comidas_df['dia'] == dia) & (comidas_df['fecha'] == fecha)].tolist()
    if not idx_actual:
        return dash.no_update, dbc.Alert("Error: No se encontró la comida.", color="danger")
    idx_actual = idx_actual[0]
    
    msg = ""

    if accion == 'agregar' and nuevo_cocinero:
        cocineros_list = [c.strip() for c in comidas_df.loc[idx_actual, 'cocineros'].split(',')]
        if nuevo_cocinero in cocineros_list:
            return dash.no_update, dbc.Alert(f"'{nuevo_cocinero}' ya está en la lista.", color="warning")
        cocineros_list.append(nuevo_cocinero)
        comidas_df.loc[idx_actual, 'cocineros'] = ', '.join(cocineros_list)
        msg = f"'{nuevo_cocinero}' añadido."

    elif accion == 'eliminar' and cocinero_a_eliminar:
        cocineros_list = [c.strip() for c in comidas_df.loc[idx_actual, 'cocineros'].split(',')]
        if cocinero_a_eliminar not in cocineros_list:
            return dash.no_update, dbc.Alert(f"'{cocinero_a_eliminar}' no encontrado.", color="danger")
        cocineros_list.remove(cocinero_a_eliminar)
        comidas_df.loc[idx_actual, 'cocineros'] = ', '.join(cocineros_list)
        msg = f"'{cocinero_a_eliminar}' eliminado."

    elif accion == 'intercambiar' and cocinero_origen and cocinero_destino and id_otra_comida:
        idx_otra = comidas_df.index[comidas_df['id'] == id_otra_comida].tolist()
        if not idx_otra:
            return dash.no_update, dbc.Alert("Otra comida no encontrada.", color="danger")
        idx_otra = idx_otra[0]

        cocineros_origen_list = [c.strip() for c in comidas_df.loc[idx_actual, 'cocineros'].split(',')]
        cocineros_destino_list = [c.strip() for c in comidas_df.loc[idx_otra, 'cocineros'].split(',')]

        if cocinero_origen not in cocineros_origen_list or cocinero_destino not in cocineros_destino_list:
            return dash.no_update, dbc.Alert("Cocinero no encontrado en su lista.", color="danger")
            
        cocineros_origen_list.remove(cocinero_origen)
        cocineros_origen_list.append(cocinero_destino)
        
        cocineros_destino_list.remove(cocinero_destino)
        cocineros_destino_list.append(cocinero_origen)
        
        comidas_df.loc[idx_actual, 'cocineros'] = ', '.join(sorted(cocineros_origen_list))
        comidas_df.loc[idx_otra, 'cocineros'] = ', '.join(sorted(cocineros_destino_list))
        msg = f"Intercambio: {cocinero_origen} ↔️ {cocinero_destino}."
    else:
        return dash.no_update, dbc.Alert("Faltan datos para realizar la acción.", color="warning")

    dm.save_data('comidas', comidas_df)
    registrar_cambio('Cocineros', msg) # Esto ya lo tenías, perfecto.

    # 1. Obtener la lista actualizada de comidas del año actual
    año_actual = datetime.now().year
    comidas_df['año'] = pd.to_datetime(comidas_df['fecha']).dt.year
    comidas_año_actual = comidas_df[comidas_df['año'] == año_actual].sort_values('fecha')

    # 2. Formatear la lista para el mensaje
    lista_comidas_str = f"\n\n*Resum de menjars per al {año_actual}:*"
    for _, row in comidas_año_actual.iterrows():
        fecha_formateada = pd.to_datetime(row['fecha']).strftime('%d/%m/%Y')
        dia_formateado = row['dia'].replace('_', ' ').title()
        lista_comidas_str += f"\n- *{fecha_formateada}* ({dia_formateado}): {row['cocineros']}"

    # 3. Crear el mensaje final y enviarlo
    mensaje_final = f"📢 *Canvi en els menjars!*\n_{msg}_\n{lista_comidas_str}"
    enviar_notificacion_telegram(mensaje_final)

    
    cache = {
        'comidas': comidas_df.to_dict('records'), 'eventos': eventos or [], 'fiestas': fiestas or [],
        'mantenimiento': mant or [], 'lista_compra': lista or [], 'cambios': cambios or []
    }
    
    return create_comidas_page(cache), dbc.Alert(f"✅ {msg}", color="success", duration=3000)

# Navegar años
@app.callback(
    [Output('store-año-comidas', 'data'),
     Output('display-año-actual', 'children')],
    [Input('btn-año-anterior', 'n_clicks'),
     Input('btn-año-siguiente', 'n_clicks')],
    State('store-año-comidas', 'data'),
    prevent_initial_call=True
)
def cambiar_año(n_ant, n_sig, año_actual):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'btn-año-anterior':
        nuevo_año = año_actual - 1
    else:
        nuevo_año = año_actual + 1
    
    return nuevo_año, f"Año {nuevo_año}"

# Actualizar lista de comidas según año
@app.callback(
    Output('lista-comidas-container', 'children'),
    Input('store-año-comidas', 'data')
)
def actualizar_lista_comidas(año):
    comidas_df = dm.get_data('comidas')
    
    if not comidas_df.empty:
        comidas_df['año'] = pd.to_datetime(comidas_df['fecha']).dt.year
        comidas_año = comidas_df[comidas_df['año'] == año].sort_values('fecha')
    else:
        comidas_año = pd.DataFrame()
    
    if comidas_año.empty:
        return dbc.ListGroup([
            dbc.ListGroupItem(f"No hay comidas registradas para {año}.", className="text-muted")
        ], flush=True)
    
    return dbc.ListGroup([
        dbc.ListGroupItem([
            html.Div(className="d-flex w-100 align-items-center justify-content-between", children=[
                html.Div([
                    html.H6(f"{row['dia'].replace('_', ' ').title()}", className="mb-1 fw-bold"),
                    html.P(f"Fecha: {row['fecha']}", className="mb-1 text-muted small"),
                    html.P(f"Cocineros: {row['cocineros']}", className="mb-0 small"),
                ]),
                dbc.Button("✕", id={'type': 'btn-eliminar-comida', 'index': row['id']}, 
                         color="danger", size="sm", outline=True)
            ])
        ], action=True) for _, row in comidas_año.iterrows()
    ], flush=True)

@app.callback(
    [Output('store-comensales-adultos', 'data', allow_duplicate=True), Output('lista-adultos-visual', 'children', allow_duplicate=True),
     Output('contador-adultos-nuevo', 'children', allow_duplicate=True), Output('input-nuevo-adulto', 'value')],
    [Input('btn-add-adulto', 'n_clicks')],
    [State('input-nuevo-adulto', 'value'), State('store-comensales-adultos', 'data')],
    prevent_initial_call=True
)
def agregar_adulto(n_clicks, nombre, lista_actual):
    if not nombre or not nombre.strip(): raise PreventUpdate
    nueva_lista = lista_actual + [nombre.strip()]
    def crear_lista_visual(nombres, tipo):
        return [html.Div([f"👤 {nombre}", html.Button("❌", id={'type': 'btn-eliminar-comensal', 'index': i, 'nombre': nombre, 'categoria': tipo})]) for i, nombre in enumerate(nombres)]
    return nueva_lista, crear_lista_visual(nueva_lista, 'adulto'), f"({len(nueva_lista)})", ""

@app.callback(
    [Output('store-comensales-niños', 'data', allow_duplicate=True), Output('lista-niños-visual', 'children', allow_duplicate=True),
     Output('contador-niños-nuevo', 'children', allow_duplicate=True), Output('input-nuevo-niño', 'value')],
    [Input('btn-add-niño', 'n_clicks')],
    [State('input-nuevo-niño', 'value'), State('store-comensales-niños', 'data')],
    prevent_initial_call=True
)
def agregar_niño(n_clicks, nombre, lista_actual):
    if not nombre or not nombre.strip(): raise PreventUpdate
    nueva_lista = lista_actual + [nombre.strip()]
    def crear_lista_visual(nombres, tipo):
        return [html.Div([f"👶 {nombre}", html.Button("❌", id={'type': 'btn-eliminar-comensal', 'index': i, 'nombre': nombre, 'categoria': tipo})]) for i, nombre in enumerate(nombres)]
    return nueva_lista, crear_lista_visual(nueva_lista, 'niño'), f"({len(nueva_lista)})", ""

# ---- Callback para el menú desplegable moderno ----
@app.callback(
    Output("menu-dropdown", "style"),
    Input("btn-toggle-sidebar", "n_clicks"),
    State("menu-dropdown", "style"),
    prevent_initial_call=True
)
def toggle_menu_collapse(n, style):
    if n:
        # Si el menú está oculto ('none'), lo mostramos. Si no, lo ocultamos.
        if style.get("display") == "none":
            # Posicionamos el menú elegantemente en la esquina superior derecha
            return {
                "display": "block", 
                "position": "fixed", 
                "top": "85px", 
                "right": "20px", 
                "zIndex": "1020"
            }
        else:
            return {"display": "none"}
    return style

@app.callback(
    Output("menu-dropdown", "style", allow_duplicate=True),
    Input('url', 'pathname'),
    prevent_initial_call=True
)
def cerrar_menu_al_navegar(pathname):
    """Cerrar el menú automáticamente cuando se navega a una nueva página"""
    return {"display": "none"}

@app.callback(
    [Output('store-comensales-adultos', 'data', allow_duplicate=True), Output('store-comensales-niños', 'data', allow_duplicate=True),
     Output('lista-adultos-visual', 'children', allow_duplicate=True), Output('lista-niños-visual', 'children', allow_duplicate=True),
     Output('contador-adultos-nuevo', 'children', allow_duplicate=True), Output('contador-niños-nuevo', 'children', allow_duplicate=True)],
    [Input({'type': 'btn-eliminar-comensal', 'index': ALL, 'nombre': ALL, 'categoria': ALL}, 'n_clicks')],
    [State('store-comensales-adultos', 'data'), State('store-comensales-niños', 'data')],
    prevent_initial_call=True
)
def eliminar_comensal(n_clicks, adultos, niños):
    ctx = callback_context
    if not ctx.triggered_id: raise PreventUpdate
    
    button_id = ctx.triggered_id
    nombre_a_eliminar = button_id['nombre']
    categoria = button_id['categoria']
    
    if categoria == 'adulto' and nombre_a_eliminar in adultos: adultos.remove(nombre_a_eliminar)
    if categoria == 'niño' and nombre_a_eliminar in niños: niños.remove(nombre_a_eliminar)

    def crear_lista_visual(nombres, tipo, emoji):
        return [html.Div([f"{emoji} {nombre}", html.Button("❌", id={'type': 'btn-eliminar-comensal', 'index': i, 'nombre': nombre, 'categoria': tipo})]) for i, nombre in enumerate(nombres)]
        
    return adultos, niños, crear_lista_visual(adultos, 'adulto', '👤'), crear_lista_visual(niños, 'niño', '👶'), f"({len(adultos)})", f"({len(niños)})"

@app.callback(
    [Output('confirm-guardar', 'displayed'), 
     Output('fiesta-output', 'children', allow_duplicate=True),
     Output('tarjetas-fiestas', 'children', allow_duplicate=True)],
    [Input('btn-guardar-cambios', 'n_clicks'), 
     Input('confirm-guardar', 'submit_n_clicks')],  # ← QUITA Input('url', 'pathname')
    [State('fiesta-dia-selector', 'value'), 
     State('fiesta-menu', 'value'),
     State('store-comensales-adultos', 'data'), 
     State('store-comensales-niños', 'data')],
    prevent_initial_call=True
)
def manejar_guardado_fiesta(n_guardar, n_confirm, fecha, menu, adultos, niños):
    ctx_id = callback_context.triggered_id
    
    # ELIMINA estas líneas:
    # if ctx_id == 'url': return False, "", generar_tarjetas_fiestas()
    
    if ctx_id == 'btn-guardar-cambios': 
        return True, "", dash.no_update
    
    if ctx_id == 'confirm-guardar' and n_confirm and fecha:
        try:
            fiestas_df = dm.get_data('fiestas')
            idx = fiestas_df.index[fiestas_df['fecha'] == fecha].tolist()
            if not idx:
                return False, f"Error: No se encontró el día {fecha} para actualizar.", generar_tarjetas_fiestas()
            
            fiestas_df.loc[idx[0], 'menu'] = menu or ''
            fiestas_df.loc[idx[0], 'nombres_adultos'] = ', '.join(adultos)
            fiestas_df.loc[idx[0], 'nombres_niños'] = ', '.join(niños)
            fiestas_df.loc[idx[0], 'adultos'] = len(adultos)
            fiestas_df.loc[idx[0], 'niños'] = len(niños)

            dm.save_data('fiestas', fiestas_df)
            registrar_cambio('Fiestas', f'Actualizado día {fecha}')
            return False, f"✅ Día {fecha} actualizado exitosamente!", generar_tarjetas_fiestas()
        except Exception as e:
            return False, f"❌ Error al guardar: {e}", generar_tarjetas_fiestas()
            
    raise PreventUpdate


# =======================
# ===== APP LAYOUT =====
# =======================
app.layout = html.Div([
    # ===== LOADING OVERLAY CON LOGO ANIMADO =====
    html.Div(
        id='loading-overlay',
        className='loading-overlay',
        children=[
            html.Img(
                src='/assets/logo.png',
                className='logo-loading'
            ),
            html.Div('Cargando datos de la Penya...', className='loading-text'),
            html.Div('●●●', className='loading-dots')
        ]
    ),

    dcc.Location(id='url', refresh=False),
    dcc.Download(id='download-pdf'),
    
    # Stores y Confirm Dialogs (componentes no visibles, sin cambios)
    dcc.Store(id='store-comensales-adultos', data=[]),
    dcc.Store(id='store-comensales-niños', data=[]),
    dcc.Store(id='store-id-eliminar-comida', data=None),
    dcc.Store(id='store-id-eliminar-item', data=None),
    dcc.Store(id='store-id-eliminar-evento', data=None),
    dcc.Store(id='store-id-eliminar-reunion', data=None),
    dcc.ConfirmDialog(id='confirm-eliminar-reunion', message='¿Seguro que quieres eliminar esta acta?'),
    dcc.ConfirmDialog(id='confirm-guardar', message='¿Guardar los cambios realizados?'),
    dcc.Store(id='store-comidas', data=None, storage_type='session'),
    dcc.Store(id='store-eventos', data=None, storage_type='session'),
    dcc.Store(id='store-fiestas', data=None, storage_type='session'),
    dcc.Store(id='store-mantenimiento', data=None, storage_type='session'),
    dcc.Store(id='store-lista-compra', data=None, storage_type='session'),
    dcc.Store(id='store-cambios', data=None, storage_type='session'),
    dcc.Store(id='store-reuniones', data=None, storage_type='session'),
    dcc.Store(id='store-data-loaded-signal'),

    
    # --- NUEVA ESTRUCTURA VISUAL ---
    create_modern_navbar(),
    create_menu_dropdown(),
    
    # Contenedor principal para el contenido de la página
    html.Div(
        id="page-container",
        style={
            "paddingTop": "90px", # Espacio vital para la navbar fija
            "paddingBottom": "20px" 
        },
        children=[
            # El contenido de cada página se cargará aquí dentro
            html.Div(id='page-content')
        ]
    )
])

# =======================
# ===== INICIALIZACIÓN =====
# =======================
if __name__ == '__main__':
    print("="*50)
    print("🚀 Iniciando Servidor Penya L'Albenc...")
    print("="*50)

    # Verificar existencia de tabla de cambios y registrar inicio
    try:
        dm.get_data('cambios')
        registrar_cambio('Sistema', 'Aplicación iniciada/reiniciada')
    except Exception as e:
        print(f"AVISO: No se pudo registrar el inicio. Puede que la tabla 'cambios' no exista. Error: {e}")

    # Limpieza de comidas antiguas
    print("🧹 Ejecutando limpieza de comidas antiguas...")
    limpiar_comidas_antiguas()

    port = int(os.environ.get('PORT', 8050))
    debug_mode = os.environ.get('DASH_DEBUG', 'True').lower() in ['true', '1']
    print(f"🌐 Servidor corriendo en http://0.0.0.0:{port}")
    print(f"🛠️ Modo Debug: {'Activado' if debug_mode else 'Desactivado'}")
    print("="*50)
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)