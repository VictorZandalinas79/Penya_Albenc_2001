import threading
import re
from scraper import scrapear_diadia # Importamos la función nueva
import requests
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

# Control de scraping para evitar ejecuciones simultáneas
_scraping_in_progress = False
_last_scraping_time = None

# Control de resumen mensual (día 1 de cada mes)
_ultimo_resumen_mensual = None





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

# --- BUSCA ESTA PARTE EN TU app.py Y REEMPLÁZALA ---

@server.route('/ping')
def ping():
    """
    Endpoint corregido:
    1. Responde 'pong' para que Render y UptimeRobot vean que está vivo.
    2. Ejecuta el scraping en un hilo aparte para no bloquear nada.
    """
    def tarea_background():
        print("⏳ Ejecutando limpieza y scraping desde PING...")
        try:
            import time
            time.sleep(2)
            dm.borrar_noticias_antiguas()
            dm.borrar_agenda_antigua()

            # Verificar si es día 1 para enviar resumen mensual
            enviar_resumen_mensual()

            if dm.necesita_actualizar_noticias(dias=0.25):
                # 1. NOTICIAS (sin notificación Telegram)
                df_n = scrapear_diadia()
                dm.guardar_noticias_nuevas(df_n)

                # 2. AGENDA (sin notificación Telegram)
                from scraper import scrapear_eventos_externos
                df_agenda = scrapear_eventos_externos()
                dm.guardar_agenda_nueva(df_agenda)
        except Exception as e:
            print(f"❌ Error en tarea background: {e}")

    # --- ESTAS DOS LÍNEAS SON LAS QUE FALTABAN ---
    threading.Thread(target=tarea_background).start()
    return "pong", 200 
    # ---------------------------------------------

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

    if not bot_token or not chat_id:
        print("❌ ERROR: Variables de entorno no encontradas.")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': mensaje,
            'parse_mode': 'Markdown'
        }, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram enviado.")
            return True
        else:
            print(f"❌ Error enviando a Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")
        return False

def enviar_resumen_mensual():
    """Genera y envía el resumen mensual por Telegram (eventos, comidas, lista compra)"""
    global _ultimo_resumen_mensual

    hoy = date.today()

    # Solo enviar el día 1 y si no se ha enviado este mes
    if hoy.day != 1:
        return False

    if _ultimo_resumen_mensual and _ultimo_resumen_mensual.month == hoy.month and _ultimo_resumen_mensual.year == hoy.year:
        print("📅 Resumen mensual ya enviado este mes")
        return False

    try:
        meses_catalan = ['Gener', 'Febrer', 'Març', 'Abril', 'Maig', 'Juny',
                         'Juliol', 'Agost', 'Setembre', 'Octubre', 'Novembre', 'Desembre']
        mes_nombre = meses_catalan[hoy.month - 1]
        dies_catalan = ['Dilluns', 'Dimarts', 'Dimecres', 'Dijous', 'Divendres', 'Dissabte', 'Diumenge']

        # Rango: hoy hasta 60 días adelante
        fin = hoy + timedelta(days=60)

        mensaje = f"📆 *RESUM MENSUAL - {mes_nombre} {hoy.year}*\n"
        mensaje += f"_Pròxims esdeveniments fins al {fin.strftime('%d/%m/%Y')}_\n"
        mensaje += "━" * 28 + "\n\n"

        # 1. COMIDAS próximas (con todos los datos)
        comidas_df = dm.get_comidas_recientes(limit=100)
        if not comidas_df.empty:
            comidas_proximas = []
            for _, comida in comidas_df.iterrows():
                try:
                    fecha_comida = pd.to_datetime(comida.get('fecha', '')).date()
                    if hoy <= fecha_comida <= fin:
                        dia_raw = comida.get('dia', '')
                        dia_formateado = dia_raw.replace('_', ' ').title() if dia_raw else ''
                        tipo_comida = comida.get('tipo_comida', '')
                        cocineros = comida.get('cocineros', comida.get('cocinero', '')) or 'Sense cuiner'
                        dia_semana = dies_catalan[fecha_comida.weekday()]
                        fecha_str = fecha_comida.strftime('%d/%m')

                        linea = f"  📅 *{fecha_str}* ({dia_semana})"
                        if dia_formateado:
                            linea += f" — {dia_formateado}"
                        if tipo_comida:
                            linea += f"\n      🍽️ {tipo_comida}"
                        linea += f"\n      👨‍🍳 {cocineros}"
                        comidas_proximas.append((fecha_comida, linea))
                except:
                    pass

            comidas_proximas.sort(key=lambda x: x[0])
            if comidas_proximas:
                mensaje += f"🍳 *MENJARS PRÒXIMS ({len(comidas_proximas)}):*\n"
                mensaje += "\n".join(c[1] for c in comidas_proximas[:15])
                if len(comidas_proximas) > 15:
                    mensaje += f"\n  _...i {len(comidas_proximas) - 15} més_"
                mensaje += "\n\n"

        # 2. EVENTOS próximos (con todos los datos)
        eventos_df = dm.get_eventos_proximos(limit=100)
        if not eventos_df.empty:
            eventos_proximos = []
            for _, evento in eventos_df.iterrows():
                try:
                    fecha_evento = pd.to_datetime(evento.get('fecha', '')).date()
                    if fecha_evento <= fin:
                        nombre = evento.get('nombre', 'Sense nom')
                        tipo = evento.get('tipo', '') or ''
                        dia_semana = dies_catalan[fecha_evento.weekday()]
                        fecha_str = fecha_evento.strftime('%d/%m/%Y')

                        linea = f"  📅 *{fecha_str}* ({dia_semana}) — {nombre}"
                        if tipo:
                            linea += f"\n      🏷️ {tipo}"
                        eventos_proximos.append((fecha_evento, linea))
                except:
                    pass

            eventos_proximos.sort(key=lambda x: x[0])
            if eventos_proximos:
                mensaje += f"🎉 *EVENTS PRÒXIMS ({len(eventos_proximos)}):*\n"
                mensaje += "\n".join(e[1] for e in eventos_proximos[:15])
                if len(eventos_proximos) > 15:
                    mensaje += f"\n  _...i {len(eventos_proximos) - 15} més_"
                mensaje += "\n\n"

        # 3. LISTA DE COMPRA activa (con fechas si las hay)
        lista_df = dm.get_lista_compra_activa()
        if not lista_df.empty:
            mensaje += f"🛒 *LLISTA DE LA COMPRA ({len(lista_df)} items):*\n"
            for _, item in lista_df.iterrows():
                nombre_item = item.get('objeto', item.get('nombre', ''))
                fecha_item = item.get('fecha', item.get('fecha_prevista', ''))
                linea = f"  • {nombre_item}"
                if fecha_item and str(fecha_item).strip() not in ('', 'None', 'nan'):
                    try:
                        fecha_fmt = pd.to_datetime(fecha_item).strftime('%d/%m')
                        linea += f" _(per al {fecha_fmt})_"
                    except:
                        pass
                mensaje += linea + "\n"

        if len(mensaje) < 200:
            mensaje += "  _No hi ha res programat per als pròxims dies._\n"

        mensaje += "\n🤖 _Resum automàtic de Penya L'Albenc_"

        # Telegram tiene límite de 4096 caracteres
        if len(mensaje) > 4000:
            mensaje = mensaje[:3990] + "\n\n_[Missatge retallat]_"

        enviar_notificacion_telegram(mensaje)
        _ultimo_resumen_mensual = hoy
        print(f"📨 Resumen mensual de {mes_nombre} enviado correctamente")
        return True

    except Exception as e:
        print(f"❌ Error generando resumen mensual: {e}")
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
    # 1. Preparación de datos
    eventos_df = pd.DataFrame(cache.get('eventos', []))
    comidas_df = pd.DataFrame(cache.get('comidas', []))
    mantenimiento_df = pd.DataFrame(cache.get('mantenimiento', []))
    noticias_df = pd.DataFrame(cache.get('noticias', [])) 
    agenda_df = pd.DataFrame(cache.get('agenda', []))

    # Obtener mantenimiento del año actual
    año_actual = datetime.now().year
    mant_actual = None
    if not mantenimiento_df.empty:
        mant_año = mantenimiento_df[mantenimiento_df['año'] == año_actual]
        if not mant_año.empty:
            mant_actual = mant_año.iloc[0]
    
    # 2. Lógica de Próximos Eventos
    eventos_lista = []
    if not eventos_df.empty:
        for _, ev in eventos_df.iterrows():
            eventos_lista.append({'fecha': ev['fecha'], 'tipo': ev['evento'], 'descripcion': ev.get('tipo', '')})
    
    if not comidas_df.empty:
        for _, com in comidas_df.iterrows():
            dia = (com.get('dia') or 'Comida').replace('_', ' ').title()
            eventos_lista.append({'fecha': com['fecha'], 'tipo': dia, 'descripcion': f"Cocinan: {com.get('cocineros', 'N/A')}"})
    
    proximos = pd.DataFrame()
    if eventos_lista:
        df_ev = pd.DataFrame(eventos_lista)
        df_ev['fecha_dt'] = pd.to_datetime(df_ev['fecha'])
        proximos = df_ev[df_ev['fecha_dt'] >= pd.Timestamp.now().normalize()].sort_values('fecha_dt').head(6)

    # Historial de derrames (carga directa desde BD para incluir eventos pasados)
    derrames_lista = []
    try:
        derrames_df = dm.get_data_filtered('eventos', where_clause="LOWER(evento) LIKE '%derrama%' OR LOWER(evento) LIKE '%transferencia%'", order_by="fecha DESC")
        for _, row in derrames_df.iterrows():
            texto = str(row['evento'])
            match = re.search(r'(\d+(?:[.,]\d+)?)\s*€?', texto)
            importe = match.group(1) + ' €' if match else None
            derrames_lista.append({'fecha': row['fecha'], 'evento': texto, 'importe': importe})
    except Exception as e:
        print(f"Error cargando derrames: {e}")

    # 3. Diseño de Noticias
    items_noticias = []
    for i, row in enumerate(noticias_df.to_dict('records')):
        items_noticias.append(dbc.Card(className="mb-3 border-0 shadow-sm", children=[
            dbc.Row(className="g-0", children=[
                dbc.Col(xs=4, children=[
                    html.Div(style={"backgroundImage": f"url('{row.get('imagen')}')", "backgroundSize": "cover", "height": "80px"})
                ]),
                dbc.Col(xs=8, children=[
                    dbc.CardBody([
                        html.A(row['titulo'], href=row['link'], target="_blank", style={"fontSize": "0.85rem", "fontWeight": "bold", "color": "#2c3e50"}),
                    ], className="p-2")
                ])
            ])
        ]))

    # --- 4. Lógica de AGENDA (Ordenación por Fecha y Hora) ---
    items_agenda = []
    if not agenda_df.empty:
        def limpiar_fecha_orden(fecha_str):
            if not fecha_str: return pd.Timestamp.max
            try:
                # 1. Limpieza básica
                f = fecha_str.strip().lower()
                # 2. Intentar parsear formato con hora "20/12/2025 - 12:30" o "20/12/25 - 12:30"
                # Usamos dateutil vía pandas para que sea flexible con el año (25 vs 2025)
                if ' - ' in f:
                    return pd.to_datetime(f, dayfirst=True)
                else:
                    # 3. Si no tiene hora, le asignamos las 00:00 para que vaya al principio del día
                    return pd.to_datetime(f, dayfirst=True).replace(hour=0, minute=0)
            except:
                return pd.Timestamp.max # Si falla, al final de la lista

        # Aplicamos la limpieza para ordenar
        agenda_df['f_orden'] = agenda_df['fecha_evento'].apply(limpiar_fecha_orden)
        
        # Filtramos eventos pasados y ordenamos por fecha y hora
        ahora = pd.Timestamp.now()
        hoy = ahora.normalize()
        # Mantenemos sólo eventos con fecha igual o posterior al día actual (y si tienen hora/fecha válida)
        agenda_df = agenda_df[agenda_df['f_orden'] >= hoy].sort_values('f_orden', ascending=True)
        
        for row in agenda_df.to_dict('records'):
            # Color por tipo: Concierto (Rojo), Agenda (Naranja)
            color = "#ff4d4d" if row['tipo'] == 'concierto' else "#ffa500"
            
            # Separar fecha y hora para diseño (si existe el separador)
            partes_fecha = row['fecha_evento'].split(' - ')
            solo_fecha = partes_fecha[0]
            solo_hora = f" 🕒 {partes_fecha[1]}" if len(partes_fecha) > 1 else ""

            items_agenda.append(dbc.ListGroupItem([
                html.Div([
                    html.Span([
                        html.B(solo_fecha, style={"color": color}),
                        html.Small(solo_hora, className="ms-2 text-muted fw-bold"),
                    ]),
                    dbc.Badge(row['origen'], color="light", text_color="dark", className="small border"),
                ], className="d-flex justify-content-between align-items-center"),
                
                html.Div(row['titulo'], style={"fontWeight": "800", "marginTop": "8px", "fontSize": "1rem"}),
                html.Div([
                    html.Span("📍 ", style={"filter": "grayscale(1)"}),
                    html.Span(row['lugar'], className="small text-muted")
                ], className="mt-1"),
                
                html.Div(
                    html.A("🔗 Més informació i entrades", href=row['link'], target="_blank", 
                           className="btn-link small mt-2 d-inline-block", 
                           style={"color": color, "textDecoration": "none", "fontWeight": "600"}),
                    className="text-end"
                )
            ], className="border-start border-4 mb-3 shadow-sm bg-white", 
               style={"borderLeftColor": f"{color} !important", "borderRadius": "8px"}))

    if not items_agenda:
        items_agenda = [html.P("No hi ha esdeveniments pròxims a l'agenda.", className="text-muted text-center py-3 mb-0")]

    # 5. Construcción final
    return dbc.Container([
        # Cabecera: Logo izquierda + Mantenimiento derecha
        dbc.Row(className="align-items-center mb-4 p-3", children=[
            # Logo a la izquierda
            dbc.Col(xs=4, md=3, className="text-center text-md-start", children=[
                html.Img(src='/assets/logo2.png', style={'height': '80px'})
            ]),
            
            # Mantenimiento a la derecha
            dbc.Col(xs=8, md=9, children=[
                dbc.Card(className="border-0 shadow-sm", style={"background": "linear-gradient(135deg, #667eea15 0%, #764ba215 100%)"}, children=[
                    dbc.CardBody(className="py-2 px-3", children=[
                        html.Div(className="d-flex flex-wrap align-items-center gap-3", children=[
                            # Mantenimiento
                            html.Div(className="d-flex align-items-center gap-2", children=[
                                html.Span("🔧", style={"fontSize": "1.3rem"}),
                                html.Div([
                                    html.Small(f"Manteniment {año_actual}", className="text-muted d-block", style={"fontSize": "0.7rem"}),
                                    html.Strong(
                                        mant_actual['mantenimiento'] if mant_actual is not None else "No assignat",
                                        style={"color": "#667eea", "fontSize": "0.95rem"}
                                    ),
                                ]),
                            ]),
                            
                            # Separador vertical (oculto en móvil)
                            html.Div(className="d-none d-md-block", style={"borderLeft": "2px solid #ddd", "height": "35px"}),
                            
                            # Cadafals
                            html.Div(className="d-flex align-items-center gap-2", children=[
                                html.Span("🏗️", style={"fontSize": "1.3rem"}),
                                html.Div([
                                    html.Small("Cadafals", className="text-muted d-block", style={"fontSize": "0.7rem"}),
                                    html.Strong(
                                        mant_actual['cadafals'] if mant_actual is not None else "No assignat",
                                        style={"color": "#764ba2", "fontSize": "0.95rem"}
                                    ),
                                ]),
                            ]),
                        ])
                    ])
                ]) if mant_actual is not None else dbc.Alert(f"⚠️ No hi ha manteniment assignat per a {año_actual}", color="warning", className="mb-0 py-2")
            ]),
        ]),
        
        dbc.Row([
            dbc.Col(md=6, children=[
                dbc.Card(className="mb-4 glass-container", children=[
                    dbc.CardHeader(html.H4("📅 Penya: Pròxims Events", className="m-0")),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            html.H6(row['tipo'], className="mb-0 fw-bold"),
                            html.Small(f"{row['fecha']} - {row['descripcion']}")
                        ]) for _, row in proximos.iterrows()
                    ] if not proximos.empty else [dbc.ListGroupItem("No hay eventos")], flush=True)
                ])
            ]),
            dbc.Col(md=6, children=[
                dbc.Card(className="mb-4 glass-container", children=[
                    dbc.CardHeader(html.H4("📰 Notícies DiaDia", className="m-0")),
                    dbc.CardBody(items_noticias, style={"maxHeight": "300px", "overflowY": "auto"})
                ])
            ]),
        ]),

        dbc.Row([
            dbc.Col(width=12, children=[
                dbc.Card(className="mb-4 glass-container", children=[
                    dbc.CardHeader(html.H4("💸 Historial de Derrames", className="m-0")),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            html.Div(className="d-flex justify-content-between align-items-center", children=[
                                html.Div([
                                    html.Span("📅 ", style={"fontSize": "0.85rem"}),
                                    html.Small(d['fecha'], className="text-muted fw-bold"),
                                    html.Div(d['evento'], style={"fontWeight": "600", "marginTop": "2px"}),
                                ]),
                                dbc.Badge(d['importe'], color="danger", className="fs-6") if d['importe'] else dbc.Badge("Sense import", color="secondary")
                            ])
                        ]) for d in derrames_lista
                    ] if derrames_lista else [dbc.ListGroupItem("No hi ha derrames registrades.", className="text-muted")], flush=True)
                ])
            ])
        ]),

        dbc.Row([
            dbc.Col(width=12, children=[
                dbc.Card(className="mb-4 glass-container", children=[
                    dbc.CardHeader(html.H4("🎸 Concerts i Agenda Castello", className="m-0")),
                    dbc.CardBody(items_agenda, style={"maxHeight": "500px", "overflowY": "auto"})
                ])
            ])
        ])
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
    
    # Para el selector de días: sólo comidas futuras o del día actual
    if not comidas_df.empty:
        comidas_df['fecha_dt'] = pd.to_datetime(comidas_df['fecha'])
        hoy = pd.Timestamp.now().normalize()
        comidas_futuras_df = comidas_df[comidas_df['fecha_dt'] >= hoy]
        dias_unicos = comidas_futuras_df['dia'].unique()
    else:
        dias_unicos = []
        
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
                            dbc.Button("✏️", id={'type': 'btn-editar-item', 'index': row['id']}, 
               color="warning", size="sm", outline=True, className="me-1"),
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
                            dbc.Button("✏️", id={'type': 'btn-editar-evento', 'index': row['id']}, 
                                           color="warning", size="sm", outline=True, className="me-1"),
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
# --- 1. CARGA INICIAL (Corregido: ahora devuelve 11 elementos) ---
@app.callback(
    [Output('store-comidas', 'data'),
    Output('store-eventos', 'data'),
    Output('store-fiestas', 'data'),
    Output('store-lista-compra', 'data'),
    Output('store-cambios', 'data'),
    Output('store-reuniones', 'data'),
    Output('store-mantenimiento', 'data'),
    Output('loading-overlay', 'className'),
    Output('store-data-loaded-signal', 'data'),
    Output('store-noticias', 'data'),
    Output('store-agenda', 'data')], # <--- 11 Salidas
    Input('url', 'pathname'),
    [State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data'),
     State('store-reuniones', 'data'),
     State('store-mantenimiento', 'data')],
    prevent_initial_call=False
)
def cargar_datos_iniciales(pathname, comidas_st, eventos_st, fiestas_st, lista_st, cambios_st, reuniones_st, mant_st):
    # Si los datos ya están en sesión, no recargar la BD
    if all(s is not None for s in [comidas_st, eventos_st, fiestas_st, lista_st, cambios_st, reuniones_st, mant_st]):
        print("✅ Datos en sesión, saltando recarga de BD.")
        return (dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update,
                'loading-overlay hidden', datetime.now().timestamp(),
                dash.no_update, dash.no_update)

    global _scraping_in_progress, _last_scraping_time
    print("🔄 Iniciando carga OPTIMIZADA de datos...")

    def ejecutar_scraping_background():
        global _scraping_in_progress, _last_scraping_time
        try:
            print("🕵️ Gestionando noticias y agenda en segundo plano...")
            dm.borrar_noticias_antiguas()
            if dm.necesita_actualizar_noticias(dias=0.25):
                # Scraping Noticias
                df_nuevas = scrapear_diadia()
                if not df_nuevas.empty: dm.guardar_noticias_nuevas(df_nuevas)
                # Scraping Agenda
                from scraper import scrapear_eventos_externos
                df_agenda = scrapear_eventos_externos()
                if not df_agenda.empty: dm.guardar_agenda_nueva(df_agenda)
            else:
                print("👌 Datos actualizados.")
        finally:
            _scraping_in_progress = False
            _last_scraping_time = datetime.now()

    # Solo iniciar scraping si no hay uno en progreso y han pasado al menos 5 minutos
    tiempo_minimo = timedelta(minutes=5)
    puede_ejecutar = not _scraping_in_progress and (
        _last_scraping_time is None or
        (datetime.now() - _last_scraping_time) > tiempo_minimo
    )

    if puede_ejecutar:
        _scraping_in_progress = True
        threading.Thread(target=ejecutar_scraping_background).start()
    else:
        print("⏳ Scraping omitido (ya en progreso o ejecutado recientemente)")
    
    try:
        comidas = dm.get_comidas_recientes(limit=50).to_dict('records')
        eventos = dm.get_eventos_proximos(limit=20).to_dict('records')
        fiestas = dm.get_fiestas_agosto().to_dict('records')
        lista_compra = dm.get_lista_compra_activa().to_dict('records')
        cambios = dm.get_cambios_recientes(limit=15).to_dict('records')
        reuniones = dm.get_reuniones_recientes(limit=20).to_dict('records')
        mantenimiento = dm.get_data('mantenimiento').to_dict('records')
        print("📰 Cargando noticias...")
        noticias = dm.get_noticias().to_dict('records')

        print("🎸 Cargando agenda...")
        try:
            agenda_df = dm.get_agenda()
            agenda = agenda_df.to_dict('records') if not agenda_df.empty else []
        except Exception as e:
            print(f"⚠️ Agenda aún no disponible: {e}")
            agenda = []
            
        print("✨ ¡Datos cargados! Ocultando overlay...")
        # DEVOLVEMOS LOS 11 ELEMENTOS
        return (comidas, eventos, fiestas, lista_compra, cambios, reuniones, 
                mantenimiento, 'loading-overlay hidden', 1, noticias, agenda)
        
    except Exception as e:
        print(f"❌ ERROR FATAL: {e}")
        # DEVOLVEMOS 11 ELEMENTOS VACÍOS EN CASO DE ERROR
        return [], [], [], [], [], [], [], 'loading-overlay hidden', None, [], []

# --- 2. ROUTER PRINCIPAL (Añadido Input de Agenda) ---
@app.callback(
    Output('page-content', 'children', allow_duplicate=True), # <--- AÑADIR allow_duplicate=True
    [Input('store-data-loaded-signal', 'data'),
     Input('store-noticias', 'data'),
     Input('store-agenda', 'data')], 
    [State('url', 'pathname'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data'),
     State('store-reuniones', 'data')],
    prevent_initial_call=True # <--- OBLIGATORIO cuando se usa allow_duplicate
)
def display_page(signal, noticias, agenda, pathname, comidas, eventos, fiestas, mant, lista, cambios, reuniones):
    # El resto de la función se queda exactamente igual a como la tienes...
    if signal is None: 
        return html.Div("Cargando...", style={"text-align": "center", "padding": "50px"})
    
    cache = {
        'comidas': comidas or [],
        'eventos': eventos or [],
        'fiestas': fiestas or [],
        'mantenimiento': mant or [],
        'lista_compra': lista or [],
        'cambios': cambios or [],
        'reuniones': reuniones or [],
        'noticias': noticias or [],
        'agenda': agenda or []
    }
    
    if pathname == '/' or pathname == '/dashboard':
        return create_home_page(cache)
    elif pathname == '/comidas': return create_comidas_page(cache)
    elif pathname == '/lista-compra': return create_lista_compra_page(cache)
    elif pathname == '/eventos': return create_eventos_page(cache)
    elif pathname == '/fiestas': return create_fiestas_page(cache)
    elif pathname == '/mantenimiento': return create_mantenimiento_page(cache)
    elif pathname == '/reuniones': return create_reuniones_page(cache)
    else: return html.H3('404 - No encontrado')

@app.callback(
    [Output('store-noticias', 'data', allow_duplicate=True),
     Output('store-agenda', 'data', allow_duplicate=True),
     Output('interval-check-noticias', 'disabled')],
    [Input('interval-check-noticias', 'n_intervals')],
    [State('store-noticias', 'data'),
     State('store-agenda', 'data')],
    prevent_initial_call=True
)
def verificar_llegada_noticias(n, noticias_actuales, agenda_actual):
    # Si después de 15 intentos (1 minuto) no hay nada, paramos para no saturar
    if n > 15: return dash.no_update, dash.no_update, True

    try:
        noticias_df = dm.get_noticias()
        agenda_df = dm.get_agenda()
        
        noticias_data = noticias_df.to_dict('records') if not noticias_df.empty else []
        agenda_data = agenda_df.to_dict('records') if not agenda_df.empty else []

        # CAMBIO CLAVE: Comparamos si la base de datos tiene MÁS datos de los que hay ahora en pantalla
        hay_novedades_noticias = len(noticias_data) != len(noticias_actuales or [])
        hay_novedades_agenda = len(agenda_data) != len(agenda_actual or [])

        if hay_novedades_noticias or hay_novedades_agenda:
            print(f"🔔 [REFRESCO] ¡Novedades detectadas! Actualizando interfaz...")
            # Devolvemos los datos y NO desactivamos el intervalo aún por si entran más
            return noticias_data, agenda_data, False
            
    except Exception as e:
        print(f"Error en refresco: {e}")
        
    return dash.no_update, dash.no_update, False
    

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
    [Output("modal-foto-noticia", "is_open"),
     Output("imagen-modal-zoom", "src")],
    [Input({'type': 'btn-zoom-img', 'index': ALL}, 'n_clicks'),
     Input("btn-cerrar-modal-zoom", "n_clicks")], 
    [State({'type': 'btn-zoom-img', 'index': ALL}, 'data-src'),
     State("modal-foto-noticia", "is_open")], 
    prevent_initial_call=True
)
def toggle_modal_zoom(n_clicks_img, n_clicks_close, src_list, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return False, ""
    
    # Obtenemos quién disparó el evento
    trigger_info = ctx.triggered[0]
    trigger_id_str = trigger_info['prop_id'].split('.')[0]
    
    # 1. Si se pulsa el botón de cerrar
    if trigger_id_str == "btn-cerrar-modal-zoom":
        return False, ""
    
    # 2. Si el evento viene de una imagen (Pattern Matching)
    if "btn-zoom-img" in trigger_id_str:
        # --- CORRECCIÓN CLAVE ---
        # Verificamos si es un click real.
        # Si 'value' es None o 0, es que el componente se acaba de crear, no se ha pulsado.
        clicks_actuales = trigger_info['value']
        if not clicks_actuales: 
            return False, "" # No hacemos nada si no hay clicks reales
        # ------------------------

        try:
            triggered_id_dict = ctx.triggered_id
            if triggered_id_dict and 'index' in triggered_id_dict:
                idx = triggered_id_dict['index']
                # Buscamos la URL correspondiente en la lista de sources
                # Nota: src_list está ordenado igual que los índices generados por ALL
                if idx < len(src_list):
                    return True, src_list[idx]
        except Exception as e:
            print(f"Error abriendo modal: {e}")
            return False, ""
                
    return is_open, "" # Mantener estado si no es ninguno de los anteriores

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

# ---- Router Principal ---
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
        enviar_notificacion_telegram(f"🗑️ *Event eliminat:* S'ha borrat l'event ID {evento_id}")
        
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
    [Output('page-content', 'children', allow_duplicate=True),
     Output('store-lista-compra', 'data', allow_duplicate=True)],
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
        # Comparar tanto por string como por int para evitar type mismatch
        item_eliminado_fila = lista_df_vieja[lista_df_vieja['id'] == item_id]
        if item_eliminado_fila.empty:
            try:
                item_eliminado_fila = lista_df_vieja[lista_df_vieja['id'] == int(item_id)]
            except (ValueError, TypeError):
                pass
        nombre_item_eliminado = item_eliminado_fila.iloc[0]['objeto'] if not item_eliminado_fila.empty else "un item"
        lista_df = dm.get_data('lista_compra')
        lista_df = lista_df[(lista_df['id'] != item_id) & (lista_df['id'] != (int(item_id) if str(item_id).isdigit() else item_id))]
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

        lista_actualitzada = lista_df.to_dict('records')
        cache = {
            'comidas': comidas or [], 'eventos': eventos or [], 'fiestas': fiestas or [],
            'mantenimiento': mant or [], 'lista_compra': lista_actualitzada, 'cambios': cambios or []
        }
        page = create_lista_compra_page(cache) if pathname == '/lista-compra' else dash.no_update
        return page, lista_actualitzada
    raise PreventUpdate


@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('output-lista', 'children'),
     Output('store-lista-compra', 'data', allow_duplicate=True)],
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

    lista_df = dm.get_data('lista_compra')

    lista_str = "\n\n*Llista de la compra actual:* "
    if not lista_df.empty:
        for i, row in lista_df.iterrows():
            lista_str += f"\n{i+1}. {row['objeto']}"
    else:
        lista_str += "\nLa llista està buida."

    mensaje_final = f"🛒 *Nou item a la compra!*\nS'ha afegit: *{objeto}*\n{lista_str}"
    enviar_notificacion_telegram(mensaje_final)

    lista_actualitzada = lista_df.to_dict('records')
    cache = {
        'comidas': comidas or [], 'eventos': eventos or [], 'fiestas': fiestas or [],
        'mantenimiento': mant or [], 'lista_compra': lista_actualitzada, 'cambios': cambios or []
    }

    return (
        create_lista_compra_page(cache) if pathname == '/lista-compra' else dash.no_update,
        dbc.Alert(f"✅ '{objeto}' añadido", color="success", duration=3000),
        lista_actualitzada
    )

@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('output-evento', 'children'),
     Output('store-eventos', 'data', allow_duplicate=True)],
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

    # Formatear mensaje para Telegram
    mensaje = f"📅 *Nou event afegit!*\n\n*{nombre}*\nData: {fecha}\nTipus: {tipo or 'No especificat'}"
    enviar_notificacion_telegram(mensaje)

    eventos_df = dm.get_eventos_proximos(limit=20)
    eventos_records = eventos_df.to_dict('records')
    cache = {
        'comidas': comidas or [], 'eventos': eventos_records, 'fiestas': fiestas or [],
        'mantenimiento': mant or [], 'lista_compra': lista or [], 'cambios': cambios or []
    }

    page = create_eventos_page(cache) if pathname == '/eventos' else dash.no_update
    return page, dbc.Alert(f"✅ '{nombre}' añadido", color="success", duration=3000), eventos_records

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
        comidas_df['fecha_dt'] = pd.to_datetime(comidas_df['fecha'])
        comidas_df['año'] = comidas_df['fecha_dt'].dt.year
        hoy = pd.Timestamp.now().normalize()
        # Filtramos por el año seleccionado y descartamos fechas pasadas
        comidas_año = comidas_df[(comidas_df['año'] == año) & (comidas_df['fecha_dt'] >= hoy)].sort_values('fecha')
    else:
        comidas_año = pd.DataFrame()
    
    if comidas_año.empty:
        return dbc.ListGroup([
            dbc.ListGroupItem(f"No hay comidas próximas registradas para {año}.", className="text-muted")
        ], flush=True)
    
    return dbc.ListGroup([
        dbc.ListGroupItem([
            html.Div(className="d-flex w-100 align-items-center justify-content-between", children=[
                html.Div([
                    html.H6(f"{row['dia'].replace('_', ' ').title()}", className="mb-1 fw-bold"),
                    html.P(f"Fecha: {row['fecha']}", className="mb-1 text-muted small"),
                    html.P(f"Tipo: {row.get('tipo_comida', '')}", className="mb-0 small text-muted"),
                    html.P(f"Cocineros: {row['cocineros']}", className="mb-0 small"),
                ]),
                html.Div([
                    dbc.Button("✏️", id={'type': 'btn-editar-comida', 'index': row['id']},
                             color="primary", size="sm", outline=True, className="me-1"),
                    dbc.Button("✕", id={'type': 'btn-eliminar-comida', 'index': row['id']},
                             color="danger", size="sm", outline=True)
                ])
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
    return nueva_lista, crear_lista_visual(nueva_lista, 'adulto', '👤'), f"({len(nueva_lista)})", ""

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
    return nueva_lista, crear_lista_visual(nueva_lista, 'niño', '👶'), f"({len(nueva_lista)})", ""

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

# Callback para abrir modal y cargar datos actuales
@app.callback(
    [Output('modal-editar-item', 'is_open'),
     Output('editar-item-objeto', 'value'),
     Output('editar-item-fecha', 'date'),
     Output('store-id-editar-item', 'data')],
    [Input({'type': 'btn-editar-item', 'index': ALL}, 'n_clicks'),
     Input('btn-cancelar-edicion-item', 'n_clicks')],
    [State('store-lista-compra', 'data')],
    prevent_initial_call=True
)
def abrir_modal_editar_item(n_editar, n_cancelar, lista):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger = ctx.triggered_id
    
    # Si es cancelar, cerrar modal
    if trigger == 'btn-cancelar-edicion-item':
        return False, "", None, None
    
    # Si es botón de editar, verificar que hubo click real
    if isinstance(trigger, dict) and trigger['type'] == 'btn-editar-item':
        # Verificar que realmente se hizo click (no solo render inicial)
        if not any(n_editar):
            raise PreventUpdate
            
        item_id = trigger['index']
        item = next((i for i in lista if i['id'] == item_id), None)
        if item:
            return True, item['objeto'], item['fecha'], item_id
    
    raise PreventUpdate

# Callback para guardar la edición
@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('modal-editar-item', 'is_open', allow_duplicate=True),
     Output('store-lista-compra', 'data', allow_duplicate=True)],
    Input('btn-guardar-edicion-item', 'n_clicks'),
    [State('store-id-editar-item', 'data'),
     State('editar-item-objeto', 'value'),
     State('editar-item-fecha', 'date'),
     State('store-lista-compra', 'data'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-cambios', 'data'),
     State('store-noticias', 'data'),
     State('store-agenda', 'data')],
    prevent_initial_call=True
)
def guardar_edicion_item(n_clicks, item_id, nuevo_objeto, nueva_fecha, lista, comidas, eventos, fiestas, mant, cambios, noticias, agenda):
    if not n_clicks or not item_id:
        raise PreventUpdate

    lista_df = dm.get_data('lista_compra')
    idx = lista_df.index[lista_df['id'] == item_id].tolist()
    if not idx:
        try:
            idx = lista_df.index[lista_df['id'] == int(item_id)].tolist()
        except (ValueError, TypeError):
            pass

    if idx:
        lista_df.loc[idx[0], 'objeto'] = nuevo_objeto
        lista_df.loc[idx[0], 'fecha'] = nueva_fecha
        dm.save_data('lista_compra', lista_df)
        registrar_cambio('Lista', f'Item editado: {nuevo_objeto}')
        mensaje_telegram = f"🛒 *Llista de la compra modificada*\nS'ha editat l'item: *{nuevo_objeto}*\nNova data prevista: {nueva_fecha}"
        enviar_notificacion_telegram(mensaje_telegram)
    else:
        print(f"❌ guardar_edicion_item: no se encontró item_id={item_id} en BD")

    lista_actualitzada = lista_df.to_dict('records')
    cache_actualizado = {
        'comidas': comidas or [],
        'eventos': eventos or [],
        'fiestas': fiestas or [],
        'mantenimiento': mant or [],
        'lista_compra': lista_actualitzada,
        'cambios': cambios or [],
        'noticias': noticias or [],
        'agenda': agenda or []
    }

    return create_lista_compra_page(cache_actualizado), False, lista_actualitzada

# Callback para abrir modal de editar evento
@app.callback(
    [Output('modal-editar-evento', 'is_open'),
     Output('editar-evento-nombre', 'value'),
     Output('editar-evento-tipo', 'value'),
     Output('editar-evento-fecha', 'date'),
     Output('store-id-editar-evento', 'data')],
    [Input({'type': 'btn-editar-evento', 'index': ALL}, 'n_clicks'),
     Input('btn-cancelar-edicion-evento', 'n_clicks')],
    [State('store-eventos', 'data')],
    prevent_initial_call=True
)
def abrir_modal_editar_evento(n_editar, n_cancelar, eventos):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger = ctx.triggered_id
    
    # Si es cancelar, cerrar modal
    if trigger == 'btn-cancelar-edicion-evento':
        return False, "", "", None, None
    
    # Si es botón de editar, verificar que hubo click real
    if isinstance(trigger, dict) and trigger['type'] == 'btn-editar-evento':
        if not any(n_editar):
            raise PreventUpdate
            
        evento_id = trigger['index']
        evento = next((e for e in eventos if e['id'] == evento_id), None)
        if evento:
            return True, evento['evento'], evento.get('tipo', ''), evento['fecha'], evento_id
    
    raise PreventUpdate


# Callback para guardar la edición de evento
@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('modal-editar-evento', 'is_open', allow_duplicate=True)],
    Input('btn-guardar-edicion-evento', 'n_clicks'),
    [State('store-id-editar-evento', 'data'),
     State('editar-evento-nombre', 'value'),
     State('editar-evento-tipo', 'value'),
     State('editar-evento-fecha', 'date'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data')],
    prevent_initial_call=True
)
def guardar_edicion_evento(n_clicks, evento_id, nuevo_nombre, nuevo_tipo, nueva_fecha, 
                           comidas, eventos, fiestas, mant, lista, cambios):
    if not n_clicks or not evento_id:
        raise PreventUpdate
    
    # Actualizar en base de datos con UPDATE directo (seguro con múltiples workers)
    dm.update_data('eventos', evento_id, {
        'evento': nuevo_nombre,
        'tipo': nuevo_tipo,
        'fecha': nueva_fecha
    })

    registrar_cambio('Eventos', f'Evento editado: {nuevo_nombre}')
    enviar_notificacion_telegram(f"✏️ *Event editat:* {nuevo_nombre}\nData: {nueva_fecha}")

    # Reconstruir página con datos frescos de la BD
    eventos_df = dm.get_data('eventos')
    cache = {
        'comidas': comidas or [],
        'eventos': eventos_df.to_dict('records'),
        'fiestas': fiestas or [],
        'mantenimiento': mant or [],
        'lista_compra': lista or [],
        'cambios': cambios or []
    }
    return create_eventos_page(cache), False
    
# Callback para abrir modal de editar comida
@app.callback(
    [Output('modal-editar-comida', 'is_open'),
     Output('editar-comida-dia', 'value'),
     Output('editar-comida-tipo', 'value'),
     Output('editar-comida-fecha', 'date'),
     Output('editar-comida-cocineros', 'value'),
     Output('store-id-editar-comida', 'data')],
    [Input({'type': 'btn-editar-comida', 'index': ALL}, 'n_clicks'),
     Input('btn-cancelar-edicion-comida', 'n_clicks')],
    State('store-comidas', 'data'),
    prevent_initial_call=True
)
def abrir_modal_editar_comida(n_editar, n_cancelar, comidas_data):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger = ctx.triggered_id

    if trigger == 'btn-cancelar-edicion-comida':
        return False, "", "", None, "", None

    if isinstance(trigger, dict) and trigger['type'] == 'btn-editar-comida':
        if not any(n_editar):
            raise PreventUpdate

        comida_id = trigger['index']

        # Buscar primero en el store (sin llamada a BD)
        comida = pd.DataFrame()
        if comidas_data:
            df_store = pd.DataFrame(comidas_data)
            if not df_store.empty and 'id' in df_store.columns:
                comida = df_store[df_store['id'] == comida_id]

        # Fallback a BD si no estaba en el store
        if comida.empty:
            comidas_df = dm.get_data('comidas')
            comida = comidas_df[comidas_df['id'] == comida_id]

        if not comida.empty:
            row = comida.iloc[0]
            return True, row['dia'], row.get('tipo_comida', ''), row['fecha'], row['cocineros'], comida_id

    raise PreventUpdate


# Callback para guardar la edición de comida
@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('modal-editar-comida', 'is_open', allow_duplicate=True),
     Output('store-comidas', 'data', allow_duplicate=True)],
    Input('btn-guardar-edicion-comida', 'n_clicks'),
    [State('store-id-editar-comida', 'data'),
     State('editar-comida-dia', 'value'),
     State('editar-comida-tipo', 'value'),
     State('editar-comida-fecha', 'date'),
     State('editar-comida-cocineros', 'value'),
     State('store-comidas', 'data'),
     State('store-eventos', 'data'),
     State('store-fiestas', 'data'),
     State('store-mantenimiento', 'data'),
     State('store-lista-compra', 'data'),
     State('store-cambios', 'data')],
    prevent_initial_call=True
)
def guardar_edicion_comida(n_clicks, comida_id, nuevo_dia, nuevo_tipo, nueva_fecha, nuevos_cocineros,
                           comidas, eventos, fiestas, mant, lista, cambios):
    if not n_clicks or not comida_id:
        raise PreventUpdate

    comidas_df = dm.get_data('comidas')
    # Intentar coincidir por tipo int o string
    idx = comidas_df.index[comidas_df['id'] == comida_id].tolist()
    if not idx:
        try:
            idx = comidas_df.index[comidas_df['id'] == int(comida_id)].tolist()
        except (ValueError, TypeError):
            pass

    if idx:
        comidas_df.loc[idx[0], 'dia'] = nuevo_dia or ''
        comidas_df.loc[idx[0], 'tipo_comida'] = nuevo_tipo or ''
        comidas_df.loc[idx[0], 'fecha'] = nueva_fecha or ''
        comidas_df.loc[idx[0], 'cocineros'] = nuevos_cocineros or ''
        dm.save_data('comidas', comidas_df)

        registrar_cambio('Comidas', f'Comida editada: {nuevo_dia} ({nueva_fecha})')
        dia_formateado = nuevo_dia.replace('_', ' ').title() if nuevo_dia else nuevo_dia
        enviar_notificacion_telegram(
            f"✏️ *Menjar editat:* {dia_formateado}\nData: {nueva_fecha}\nCuiners: {nuevos_cocineros}"
        )
    else:
        print(f"❌ guardar_edicion_comida: no se encontró comida_id={comida_id} en BD")

    comidas_actualitzades = comidas_df.to_dict('records')
    cache = {
        'comidas': comidas_actualitzades,
        'eventos': eventos or [],
        'fiestas': fiestas or [],
        'mantenimiento': mant or [],
        'lista_compra': lista or [],
        'cambios': cambios or []
    }
    return create_comidas_page(cache), False, comidas_actualitzades


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
            enviar_notificacion_telegram(f"🎉 *Fiestas Agosto:* S'han actualitzat les dades (menú/assistents) del dia *{fecha}*")
            return False, f"✅ Día {fecha} actualizado exitosamente!", generar_tarjetas_fiestas()
        except Exception as e:
            enviar_notificacion_telegram(f"🎉 *Fiestas Agosto:* S'ha actualitzat el menú/asistents del dia *{fecha}*")
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
    dcc.Store(id='store-noticias', data=None, storage_type='session'),
    dcc.Store(id='store-agenda', data=None, storage_type='session'),
    dcc.Interval(id='interval-check-noticias', interval=30000, n_intervals=0),  # 30 segundos para reducir carga

    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("📸 Detalle de la imagen"), close_button=True),
            dbc.ModalBody(html.Img(id='imagen-modal-zoom', src='', style={'width': '100%'})),
            # AÑADIMOS PIE DE PÁGINA CON BOTÓN CERRAR
            dbc.ModalFooter(
                dbc.Button("Cerrar", id="btn-cerrar-modal-zoom", className="ms-auto", n_clicks=0)
            )
        ],
        id="modal-foto-noticia",
        size="lg",
        is_open=False,
        centered=True,
        zIndex=1050,
    ),

    # Modal para editar item de compra  <-- AÑADIR AQUÍ
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("✏️ Editar Item")),
        dbc.ModalBody([
            dbc.Input(id='editar-item-objeto', placeholder="Nombre del objeto"),
            dcc.DatePickerSingle(id='editar-item-fecha', className="mt-2")
        ]),
        dbc.ModalFooter([
            dbc.Button("Guardar", id='btn-guardar-edicion-item', color="success"),
            dbc.Button("Cancelar", id='btn-cancelar-edicion-item', color="secondary")
        ])
    ], id='modal-editar-item', is_open=False),

dcc.Store(id='store-id-editar-item', data=None),

# Modal para editar evento  <-- AÑADIR ESTO
dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("✏️ Editar Evento")),
    dbc.ModalBody([
        dbc.Input(id='editar-evento-nombre', placeholder="Nombre del evento", className="mb-2"),
        dbc.Input(id='editar-evento-tipo', placeholder="Tipo/Descripción", className="mb-2"),
        dcc.DatePickerSingle(id='editar-evento-fecha', className="mt-2")
    ]),
    dbc.ModalFooter([
        dbc.Button("Guardar", id='btn-guardar-edicion-evento', color="success"),
        dbc.Button("Cancelar", id='btn-cancelar-edicion-evento', color="secondary")
    ])
], id='modal-editar-evento', is_open=False),

dcc.Store(id='store-id-editar-evento', data=None),

# Modal para editar comida
dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("✏️ Editar Comida")),
    dbc.ModalBody([
        html.Label("Día (nombre):", className="fw-bold"),
        dbc.Input(id='editar-comida-dia', placeholder="Ej: Sant Antoni", className="mb-2"),
        html.Label("Tipo de comida:", className="fw-bold"),
        dbc.Input(id='editar-comida-tipo', placeholder="Ej: Dinar, Sopar...", className="mb-2"),
        html.Label("Fecha:", className="fw-bold"),
        dcc.DatePickerSingle(id='editar-comida-fecha', className="mb-2 d-block"),
        html.Label("Cocineros:", className="fw-bold"),
        dbc.Input(id='editar-comida-cocineros', placeholder="Nombres separados por coma"),
    ]),
    dbc.ModalFooter([
        dbc.Button("Guardar", id='btn-guardar-edicion-comida', color="success"),
        dbc.Button("Cancelar", id='btn-cancelar-edicion-comida', color="secondary")
    ])
], id='modal-editar-comida', is_open=False),

dcc.Store(id='store-id-editar-comida', data=None),

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
            dcc.Loading(
                id="loading-page-content",
                type="circle",
                color="#667eea",
                children=html.Div(id='page-content')
            )
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