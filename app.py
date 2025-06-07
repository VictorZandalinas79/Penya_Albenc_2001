import dash
from dash import dcc, html, Input, Output, State, dash_table, callback
import pandas as pd
import sys
from pathlib import Path
from datetime import date
import logging

# Agregar el directorio src al path para importaciones
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Importar módulos personalizados
from config import Config
from src.auth import authenticate_user, is_authenticated, logout_user, get_current_user
from src.data_manager import load_all_data, save_data, create_initial_data

# Configurar logging
logger = logging.getLogger(__name__)

# Crear archivos iniciales si no existen
create_initial_data()

# Configuración de la aplicación
config = Config()
app = dash.Dash(__name__, assets_folder=config.ASSETS_FOLDER, suppress_callback_exceptions=True)
app.title = config.APP_NAME

# CSS personalizado integrado
app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, {config.COLORS['background']} 0%, #E6F3FF 100%);
                margin: 0;
                padding: 0;
                color: {config.COLORS['text']};
            }}
            .header {{
                background: linear-gradient(135deg, {config.COLORS['primary']} 0%, {config.COLORS['secondary']} 100%);
                color: {config.COLORS['white']};
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .card {{
                background: {config.COLORS['white']};
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                margin: 20px;
                padding: 20px;
                border-left: 5px solid {config.COLORS['primary']};
            }}
        </style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
'''

# Layout de login
login_layout = html.Div([
    html.Div([
        html.H1(config.APP_NAME, 
                style={'textAlign': 'center', 'color': 'white', 'marginBottom': '30px'}),
        html.Div([
            dcc.Input(id='username', type='text', placeholder='Usuario',
                     style={'width': '100%', 'padding': '15px', 'margin': '10px 0',
                           'border': f'2px solid {config.COLORS["primary"]}', 'borderRadius': '5px'}),
            dcc.Input(id='password', type='password', placeholder='Contraseña',
                     style={'width': '100%', 'padding': '15px', 'margin': '10px 0',
                           'border': f'2px solid {config.COLORS["primary"]}', 'borderRadius': '5px'}),
            html.Button('Iniciar Sesión', id='login-button',
                       style={'width': '100%', 'padding': '15px', 'margin': '20px 0',
                             'backgroundColor': config.COLORS['primary'], 'color': 'white',
                             'border': 'none', 'borderRadius': '5px', 'fontSize': '16px',
                             'cursor': 'pointer'}),
            html.Div(id='login-output', style={'color': 'red', 'textAlign': 'center'})
        ], style={'backgroundColor': 'white', 'padding': '40px', 'borderRadius': '10px',
                 'boxShadow': '0 4px 15px rgba(0,0,0,0.1)', 'maxWidth': '400px',
                 'margin': '0 auto'})
    ], style={'padding': '100px 20px', 'background': f'linear-gradient(135deg, {config.COLORS["primary"]} 0%, {config.COLORS["secondary"]} 100%)',
             'minHeight': '100vh'})
])

# Layout principal
main_layout = html.Div([
    # Header con logo
    html.Div([
        html.Img(src=app.get_asset_url('logo.png'), 
                style={'height': '60px', 'margin-right': '20px'}),
        html.H1(f"{config.APP_NAME} - Sistema de Gestión", 
                style={'margin': '0', 'textAlign': 'center', 'flex-grow': '1'}),
        html.Button('Cerrar Sesión', id='logout-button',
                   style={'padding': '10px 20px',
                         'backgroundColor': config.COLORS['accent'], 'color': 'white',
                         'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'})
    ], style={'display': 'flex', 'alignItems': 'center', 'padding': '15px 20px',
             'background': f'linear-gradient(135deg, {config.COLORS["primary"]} 0%, {config.COLORS["secondary"]} 100%)',
             'color': 'white', 'position': 'relative'}),
    
    # Navegación (tabs)
    html.Div([
        dcc.Tabs(id='main-tabs', value='inicio', children=[
            dcc.Tab(label='🏠 Inicio', value='inicio',
                   style={'backgroundColor': config.COLORS['background']},
                   selected_style={'backgroundColor': config.COLORS['primary'], 'color': 'white'}),
            dcc.Tab(label='📅 Comidas', value='comidas',
                   style={'backgroundColor': config.COLORS['background']},
                   selected_style={'backgroundColor': config.COLORS['primary'], 'color': 'white'}),
            # Resto de tabs igual...
        ])
    ], style={'margin': '20px'}),
    
    # Contenido principal
    html.Div(id='tab-content', className='card')
])

# Layout inicial
app.layout = html.Div([
    dcc.Store(id='session-store', storage_type='session'),
    html.Div(id='page-content')
])

# Callbacks principales
@app.callback(
    Output('page-content', 'children'),
    Input('session-store', 'data')
)
def display_page(session_data):
    """Mostrar página según estado de autenticación"""
    if is_authenticated(session_data):
        logger.info(f"Usuario autenticado: {get_current_user(session_data)}")
        return main_layout
    return login_layout

@app.callback(
    [Output('session-store', 'data'),
     Output('login-output', 'children')],
    Input('login-button', 'n_clicks'),
    [State('username', 'value'),
     State('password', 'value')]
)
def login(n_clicks, username, password):
    """Procesar login de usuario"""
    if n_clicks:
        if username and password:
            session_data = authenticate_user(username, password)
            if session_data.get('authenticated'):
                return session_data, ''
            else:
                return {'authenticated': False}, 'Credenciales incorrectas'
        else:
            return {'authenticated': False}, 'Por favor, complete todos los campos'
    return {'authenticated': False}, ''

@app.callback(
    Output('session-store', 'data', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def logout(n_clicks, session_data):
    """Procesar logout de usuario"""
    if n_clicks and n_clicks > 0:
        return logout_user(session_data)
    return dash.no_update

@app.callback(
    Output('tab-content', 'children'),
    Input('main-tabs', 'value'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def render_tab_content(active_tab, session_data):
    """Renderizar contenido de las pestañas"""
    if not is_authenticated(session_data):
        return html.Div("⚠️ No autenticado", style={'padding': '20px', 'textAlign': 'center'})
    
    try:
        if active_tab == 'inicio' or active_tab is None:
            return create_inicio_tab()
        
        # Cargar datos usando el data manager
        data = load_all_data()
        
        if active_tab == 'comidas':
            return create_comidas_tab(data['comidas'])
        elif active_tab == 'lista_compra':
            return create_lista_compra_tab(data['lista_compra'])
        elif active_tab == 'mantenimiento':
            return create_mantenimiento_tab(data['mantenimiento'])
        elif active_tab == 'fiestas':
            return create_fiestas_tab(data['fiestas'])
        else:
            # Tab por defecto
            return create_inicio_tab()
            
    except Exception as e:
        logger.error(f"Error cargando contenido de tab {active_tab}: {e}")
        return html.Div([
            html.H3("Error cargando datos"),
            html.P(f"Error: {str(e)}"),
            html.Button("Reintentar", id="retry-btn", 
                       style={'padding': '10px 20px', 'backgroundColor': config.COLORS['primary'],
                             'color': 'white', 'border': 'none', 'borderRadius': '5px'})
        ], style={'padding': '20px', 'textAlign': 'center'})

# Callback para mostrar/ocultar campo de nuevo tipo de evento
@app.callback(
    Output('comida-nuevo-tipo', 'style'),
    Input('comida-tipo-evento', 'value'),
    prevent_initial_call=True
)
def toggle_nuevo_tipo(tipo_evento):
    """Mostrar campo para nuevo tipo de evento"""
    if tipo_evento == 'NUEVO':
        return {'width': '250px', 'margin': '10px', 'padding': '10px', 'display': 'block'}
    return {'width': '250px', 'margin': '10px', 'padding': '10px', 'display': 'none'}

# Callback para agregar nueva comida con confirmación
@app.callback(
    [Output('comidas-table', 'data'),
     Output('resumen-cambios-comidas', 'children'),
     Output('modal-confirmacion', 'children')],
    Input('add-comida-btn', 'n_clicks'),
    [State('comida-fecha', 'date'),
     State('comida-tipo-evento', 'value'),
     State('comida-nuevo-tipo', 'value'),
     State('comida-tipo-comida', 'value'),
     State('comida-cocineros', 'value'),
     State('comidas-table', 'data')],
    prevent_initial_call=True
)
def add_comida_with_confirmation(n_clicks, fecha, tipo_evento, nuevo_tipo, tipo_comida, cocineros, current_data):
    """Agregar nueva comida con confirmación"""
    if not n_clicks or not fecha or not tipo_evento or not tipo_comida or not cocineros:
        return current_data or [], dash.no_update, dash.no_update
    
    # Usar nuevo tipo si se seleccionó
    if tipo_evento == 'NUEVO' and nuevo_tipo:
        tipo_evento = nuevo_tipo
    elif tipo_evento == 'NUEVO':
        return current_data or [], dash.no_update, create_modal_error("Debes especificar el nombre del nuevo tipo de evento")
    
    # Verificar si ya existe
    if current_data:
        existe = any(
            row['fecha'] == fecha and 
            row['tipo_evento'] == tipo_evento and 
            row['tipo_comida'] == tipo_comida
            for row in current_data
        )
        if existe:
            return current_data, dash.no_update, create_modal_error("Ya existe una entrada para esa fecha, tipo de evento y tipo de comida")
    
    # Mostrar modal de confirmación
    descripcion = f"Agregar {tipo_comida} el {fecha} ({tipo_evento}) con cocineros: {cocineros}"
    modal = create_modal_confirmacion("Confirmar Agregar Comida", descripcion, 'confirmar-add-comida')
    
    return current_data or [], dash.no_update, modal

# Callback para manejar confirmación de agregar comida
@app.callback(
    [Output('comidas-table', 'data', allow_duplicate=True),
     Output('resumen-cambios-comidas', 'children', allow_duplicate=True),
     Output('modal-confirmacion', 'children', allow_duplicate=True)],
    Input('confirmar-add-comida', 'n_clicks'),
    [State('comida-fecha', 'date'),
     State('comida-tipo-evento', 'value'),
     State('comida-nuevo-tipo', 'value'),
     State('comida-tipo-comida', 'value'),
     State('comida-cocineros', 'value'),
     State('comidas-table', 'data')],
    prevent_initial_call=True
)
def confirmar_add_comida(n_clicks, fecha, tipo_evento, nuevo_tipo, tipo_comida, cocineros, current_data):
    """Confirmar agregar nueva comida"""
    if not n_clicks:
        return current_data or [], dash.no_update, dash.no_update
    
    # Usar nuevo tipo si se seleccionó
    if tipo_evento == 'NUEVO' and nuevo_tipo:
        tipo_evento = nuevo_tipo
    
    if current_data is None:
        current_data = []
    
    # Agregar nueva comida
    new_row = {
        'fecha': fecha, 
        'tipo_evento': tipo_evento, 
        'tipo_comida': tipo_comida, 
        'cocineros': cocineros
    }
    current_data.append(new_row)
    
    # Guardar y registrar cambio
    df = pd.DataFrame(current_data)
    save_data(df, 'comidas')
    
    from src.data_manager import log_cambio, obtener_ultimos_cambios
    log_cambio('Comidas', 'Agregar', f'{tipo_comida} el {fecha} ({tipo_evento}): {cocineros}')
    
    # Actualizar resumen de cambios
    ultimos_cambios = obtener_ultimos_cambios(5)
    resumen = create_resumen_cambios(ultimos_cambios)
    
    logger.info(f"Nueva comida agregada: {new_row}")
    return current_data, resumen, html.Div()  # Cerrar modal

# Callback para actualizar opciones de intercambio individual
@app.callback(
    [Output('intercambio-fecha-origen', 'options'),
     Output('intercambio-fecha-destino', 'options')],
    Input('comidas-table', 'data'),
    prevent_initial_call=True
)
def update_intercambio_options(comidas_data):
    """Actualizar opciones para intercambio individual"""
    if not comidas_data:
        return [], []
    
    opciones = []
    for i, row in enumerate(comidas_data):
        fecha = row.get('fecha', '')
        tipo_evento = row.get('tipo_evento', '')
        tipo_comida = row.get('tipo_comida', '')
        label = f"{fecha} - {tipo_evento} ({tipo_comida})"
        opciones.append({'label': label, 'value': i})  # Usar índice como value
    
    return opciones, opciones

# Callback para actualizar cocineros disponibles según fecha seleccionada
@app.callback(
    Output('intercambio-cocinero-origen', 'options'),
    Input('intercambio-fecha-origen', 'value'),
    State('comidas-table', 'data'),
    prevent_initial_call=True
)
def update_cocineros_origen(fecha_idx, comidas_data):
    """Actualizar cocineros disponibles para fecha origen"""
    if fecha_idx is None or not comidas_data or fecha_idx >= len(comidas_data):
        return []
    
    cocineros_str = comidas_data[fecha_idx].get('cocineros', '')
    cocineros = [c.strip() for c in cocineros_str.split(',') if c.strip()]
    return [{'label': cocinero, 'value': cocinero} for cocinero in cocineros]

@app.callback(
    Output('intercambio-cocinero-destino', 'options'),
    Input('intercambio-fecha-destino', 'value'),
    State('comidas-table', 'data'),
    prevent_initial_call=True
)
def update_cocineros_destino(fecha_idx, comidas_data):
    """Actualizar cocineros disponibles para fecha destino"""
    if fecha_idx is None or not comidas_data or fecha_idx >= len(comidas_data):
        return []
    
    cocineros_str = comidas_data[fecha_idx].get('cocineros', '')
    cocineros = [c.strip() for c in cocineros_str.split(',') if c.strip()]
    return [{'label': cocinero, 'value': cocinero} for cocinero in cocineros]

# Callback para intercambio individual de cocineros
@app.callback(
    [Output('comidas-table', 'data', allow_duplicate=True),
     Output('intercambio-individual-mensaje', 'children'),
     Output('intercambio-individual-mensaje', 'style'),
     Output('resumen-cambios-comidas', 'children', allow_duplicate=True)],
    Input('intercambiar-individual-btn', 'n_clicks'),
    [State('intercambio-fecha-origen', 'value'),
     State('intercambio-cocinero-origen', 'value'),
     State('intercambio-fecha-destino', 'value'),
     State('intercambio-cocinero-destino', 'value'),
     State('comidas-table', 'data')],
    prevent_initial_call=True
)
def intercambiar_cocineros_individual(n_clicks, fecha_origen_idx, cocinero_origen, fecha_destino_idx, cocinero_destino, current_data):
    """Intercambiar cocineros individuales entre dos fechas"""
    if not n_clicks or fecha_origen_idx is None or fecha_destino_idx is None or not cocinero_origen or not cocinero_destino:
        return current_data or [], "", {}, dash.no_update
    
    if not current_data or fecha_origen_idx >= len(current_data) or fecha_destino_idx >= len(current_data):
        return current_data or [], "❌ Error: Fechas no válidas", {'color': 'red'}, dash.no_update
    
    if fecha_origen_idx == fecha_destino_idx:
        return current_data, "❌ No puedes intercambiar en la misma fecha", {'color': 'red'}, dash.no_update
    
    try:
        # Obtener listas de cocineros
        cocineros_origen = [c.strip() for c in current_data[fecha_origen_idx]['cocineros'].split(',')]
        cocineros_destino = [c.strip() for c in current_data[fecha_destino_idx]['cocineros'].split(',')]
        
        # Verificar que los cocineros existen
        if cocinero_origen not in cocineros_origen:
            return current_data, f"❌ {cocinero_origen} no está en la fecha origen", {'color': 'red'}, dash.no_update
        
        if cocinero_destino not in cocineros_destino:
            return current_data, f"❌ {cocinero_destino} no está en la fecha destino", {'color': 'red'}, dash.no_update
        
        # Realizar intercambio
        idx_origen = cocineros_origen.index(cocinero_origen)
        idx_destino = cocineros_destino.index(cocinero_destino)
        
        cocineros_origen[idx_origen] = cocinero_destino
        cocineros_destino[idx_destino] = cocinero_origen
        
        # Actualizar datos
        current_data[fecha_origen_idx]['cocineros'] = ', '.join(cocineros_origen)
        current_data[fecha_destino_idx]['cocineros'] = ', '.join(cocineros_destino)
        
        # Guardar cambios
        df = pd.DataFrame(current_data)
        save_data(df, 'comidas')
        
        # Registrar cambio
        from src.data_manager import log_cambio, obtener_ultimos_cambios
        descripcion = f"Intercambio: {cocinero_origen} ↔ {cocinero_destino}"
        log_cambio('Comidas', 'Intercambio Individual', descripcion)
        
        # Actualizar resumen
        ultimos_cambios = obtener_ultimos_cambios(5)
        resumen = create_resumen_cambios(ultimos_cambios)
        
        mensaje = f"✅ Intercambio realizado: {cocinero_origen} ↔ {cocinero_destino}"
        estilo = {'color': 'green', 'fontWeight': 'bold'}
        
        logger.info(f"Intercambio individual: {descripcion}")
        return current_data, mensaje, estilo, resumen
        
    except Exception as e:
        logger.error(f"Error en intercambio individual: {e}")
        return current_data, f"❌ Error: {str(e)}", {'color': 'red'}, dash.no_update

# Callback para actualizar resumen de cambios automáticamente
@app.callback(
    Output('ultimos-cambios-inicio', 'children'),
    Input('interval-cambios', 'n_intervals'),
    prevent_initial_call=True
)
def actualizar_cambios_inicio(n_intervals):
    """Actualizar resumen de cambios en página de inicio"""
    from src.data_manager import obtener_ultimos_cambios
    ultimos_cambios = obtener_ultimos_cambios(10)
    return create_resumen_cambios(ultimos_cambios)

def create_modal_confirmacion(titulo, descripcion, button_id):
    """Crear modal de confirmación"""
    return html.Div([
        html.Div([
            html.Div([
                html.H4(titulo, style={'margin': '0 0 15px 0', 'color': config.COLORS['primary']}),
                html.P(descripcion, style={'margin': '0 0 20px 0'}),
                html.Div([
                    html.Button('✅ Confirmar', id=button_id,
                               style={'margin': '5px', 'padding': '10px 20px',
                                     'backgroundColor': config.COLORS['primary'], 'color': 'white',
                                     'border': 'none', 'borderRadius': '5px'}),
                    html.Button('❌ Cancelar', id='cancelar-modal',
                               style={'margin': '5px', 'padding': '10px 20px',
                                     'backgroundColor': '#dc3545', 'color': 'white',
                                     'border': 'none', 'borderRadius': '5px'})
                ])
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px',
                     'maxWidth': '500px', 'margin': 'auto'})
        ], style={'position': 'fixed', 'top': '0', 'left': '0', 'width': '100%', 'height': '100%',
                 'backgroundColor': 'rgba(0,0,0,0.5)', 'display': 'flex', 'alignItems': 'center',
                 'justifyContent': 'center', 'zIndex': '9999'})
    ])

def create_modal_error(mensaje):
    """Crear modal de error"""
    return html.Div([
        html.Div([
            html.Div([
                html.H4("❌ Error", style={'margin': '0 0 15px 0', 'color': '#dc3545'}),
                html.P(mensaje, style={'margin': '0 0 20px 0'}),
                html.Button('Cerrar', id='cerrar-error',
                           style={'padding': '10px 20px', 'backgroundColor': '#dc3545', 
                                 'color': 'white', 'border': 'none', 'borderRadius': '5px'})
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px',
                     'maxWidth': '400px', 'margin': 'auto'})
        ], style={'position': 'fixed', 'top': '0', 'left': '0', 'width': '100%', 'height': '100%',
                 'backgroundColor': 'rgba(0,0,0,0.5)', 'display': 'flex', 'alignItems': 'center',
                 'justifyContent': 'center', 'zIndex': '9999'})
    ])

# Callback para cerrar modales
@app.callback(
    Output('modal-confirmacion', 'children', allow_duplicate=True),
    [Input('cancelar-modal', 'n_clicks'),
     Input('cerrar-error', 'n_clicks')],
    prevent_initial_call=True
)
def cerrar_modal(cancelar, cerrar):
    """Cerrar modal"""
    if cancelar or cerrar:
        return html.Div()
    return dash.no_update

def create_comidas_tab(comidas_df):
    """Crear contenido de la pestaña comidas con nueva estructura de 4 columnas"""
    # Asegurar que comidas_df es un DataFrame válido
    if comidas_df is None or comidas_df.empty:
        comidas_data = []
    else:
        comidas_data = comidas_df.to_dict('records')
    
    # Obtener tipos de evento únicos para el dropdown
    tipos_evento_existentes = list(set([row.get('tipo_evento', '') for row in comidas_data if row.get('tipo_evento')]))
    tipos_evento_base = ['Sant Antoni', 'Brena St Vicent', 'Fira Magdalena', 'Penya Taurina', 'Comida Normal']
    tipos_evento = list(set(tipos_evento_base + tipos_evento_existentes))
    
    # Obtener últimos cambios para mostrar en resumen
    from src.data_manager import obtener_ultimos_cambios
    ultimos_cambios = obtener_ultimos_cambios(5)
    
    return html.Div([
        # Resumen de últimos cambios
        html.Div([
            html.H4("📊 Últimos Cambios", style={'margin': '0 0 15px 0', 'color': config.COLORS['primary']}),
            html.Div(id='resumen-cambios-comidas', children=[
                create_resumen_cambios(ultimos_cambios)
            ])
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 
                 'margin': '0 0 20px 0', 'border': f'2px solid {config.COLORS["accent"]}'}),
        
        html.H2("Gestión de Comidas - PENYA L'ALBENC", style={'color': config.COLORS['primary']}),
        
        # Sección para agregar nueva comida
        html.Div([
            html.H4("Agregar Nueva Comida"),
            html.Div([
                dcc.DatePickerSingle(id='comida-fecha', date=date.today(),
                                   display_format='DD/MM/YYYY',
                                   style={'margin': '10px'}),
                dcc.Dropdown(id='comida-tipo-evento', 
                           options=[{'label': tipo, 'value': tipo} for tipo in tipos_evento] + 
                                  [{'label': '+ Nuevo tipo', 'value': 'NUEVO'}],
                           placeholder='Tipo de evento',
                           style={'width': '200px', 'margin': '10px'}),
                dcc.Input(id='comida-nuevo-tipo', placeholder='Nombre del nuevo tipo de evento',
                         style={'width': '250px', 'margin': '10px', 'padding': '10px', 'display': 'none'}),
                dcc.Dropdown(id='comida-tipo-comida',
                           options=[
                               {'label': 'Comida', 'value': 'Comida'},
                               {'label': 'Cena', 'value': 'Cena'},
                               {'label': 'Comida y Cena', 'value': 'Comida y Cena'}
                           ],
                           placeholder='Tipo comida',
                           style={'width': '150px', 'margin': '10px'}),
                dcc.Input(id='comida-cocineros', placeholder='Cocineros (ej: David, Juan Fernando)',
                         style={'width': '300px', 'margin': '10px', 'padding': '10px'}),
                html.Button('Agregar', id='add-comida-btn',
                           style={'margin': '10px', 'padding': '10px 20px',
                                 'backgroundColor': config.COLORS['primary'], 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'})
        ], style={'backgroundColor': config.COLORS['light_gray'], 'padding': '20px', 
                 'borderRadius': '10px', 'margin': '20px 0'}),
        
        # Sección para intercambio individual de cocineros
        html.Div([
            html.H4("🔄 Intercambio Individual de Cocineros"),
            html.P("Intercambia un cocinero específico entre dos fechas sin afectar a los demás", 
                   style={'fontStyle': 'italic', 'margin': '0 0 15px 0'}),
            html.Div([
                html.Div([
                    html.Label("Fecha Origen:", style={'fontWeight': 'bold', 'display': 'block'}),
                    dcc.Dropdown(id='intercambio-fecha-origen', 
                               placeholder='Selecciona fecha origen',
                               style={'width': '250px', 'margin': '5px 10px 10px 0'})
                ], style={'margin': '10px'}),
                html.Div([
                    html.Label("Cocinero a intercambiar:", style={'fontWeight': 'bold', 'display': 'block'}),
                    dcc.Dropdown(id='intercambio-cocinero-origen', 
                               placeholder='Selecciona cocinero',
                               style={'width': '200px', 'margin': '5px 10px 10px 0'})
                ], style={'margin': '10px'}),
                html.Div([
                    html.Label("Fecha Destino:", style={'fontWeight': 'bold', 'display': 'block'}),
                    dcc.Dropdown(id='intercambio-fecha-destino', 
                               placeholder='Selecciona fecha destino',
                               style={'width': '250px', 'margin': '5px 10px 10px 0'})
                ], style={'margin': '10px'}),
                html.Div([
                    html.Label("Cocinero a intercambiar:", style={'fontWeight': 'bold', 'display': 'block'}),
                    dcc.Dropdown(id='intercambio-cocinero-destino', 
                               placeholder='Selecciona cocinero',
                               style={'width': '200px', 'margin': '5px 10px 10px 0'})
                ], style={'margin': '10px'}),
                html.Button('🔄 Intercambiar Cocineros', id='intercambiar-individual-btn',
                           style={'margin': '10px', 'padding': '10px 20px',
                                 'backgroundColor': config.COLORS['accent'], 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px'}),
                html.Div(id='intercambio-individual-mensaje', style={'margin': '10px', 'fontWeight': 'bold'})
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'alignItems': 'end'})
        ], style={'backgroundColor': '#e8f4f8', 'padding': '20px', 
                 'borderRadius': '10px', 'margin': '20px 0', 'border': f'2px solid {config.COLORS["accent"]}'}),
        
        # Tabla de comidas con nueva estructura de 4 columnas
        dash_table.DataTable(
            id='comidas-table',
            data=comidas_data,
            columns=[
                {'name': 'Fecha', 'id': 'fecha', 'type': 'datetime'},
                {'name': 'Tipo de Evento', 'id': 'tipo_evento', 'presentation': 'dropdown'},
                {'name': 'Tipo Comida', 'id': 'tipo_comida', 'presentation': 'dropdown'},
                {'name': 'Cocineros', 'id': 'cocineros'}
            ],
            editable=True,
            row_deletable=True,
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': config.COLORS['primary'], 'color': 'white'},
            style_data={'backgroundColor': 'white'},
            dropdown={
                'tipo_evento': {
                    'options': [{'label': tipo, 'value': tipo} for tipo in tipos_evento]
                },
                'tipo_comida': {
                    'options': [
                        {'label': 'Comida', 'value': 'Comida'},
                        {'label': 'Cena', 'value': 'Cena'},
                        {'label': 'Comida y Cena', 'value': 'Comida y Cena'}
                    ]
                }
            },
            sort_action="native",
            sort_by=[{'column_id': 'fecha', 'direction': 'asc'}]
        ),
        
        # Modal de confirmación
        dcc.Store(id='confirmacion-data'),
        html.Div(id='modal-confirmacion')
    ])

def create_resumen_cambios(cambios):
    """Crear componente de resumen de cambios"""
    if not cambios:
        return html.P("No hay cambios recientes", style={'fontStyle': 'italic', 'color': '#666'})
    
    items = []
    for cambio in cambios:
        timestamp = cambio.get('timestamp', '')
        if hasattr(timestamp, 'strftime'):
            timestamp_str = timestamp.strftime('%d/%m %H:%M')
        else:
            timestamp_str = str(timestamp)[:16] if timestamp else ''
        
        items.append(html.Div([
            html.Span(f"{timestamp_str}", style={'fontWeight': 'bold', 'color': config.COLORS['primary']}),
            html.Span(f" [{cambio.get('seccion', '')}] ", style={'fontWeight': 'bold'}),
            html.Span(f"{cambio.get('tipo_cambio', '')}: ", style={'color': config.COLORS['accent']}),
            html.Span(cambio.get('descripcion', ''))
        ], style={'margin': '5px 0', 'padding': '5px', 'backgroundColor': 'white', 
                 'borderRadius': '5px', 'fontSize': '14px'}))
    
    return html.Div(items)

def create_lista_compra_tab(lista_df):
    """Crear contenido de la pestaña lista de compra"""
    # Asegurar que lista_df es un DataFrame válido
    if lista_df is None or lista_df.empty:
        lista_data = []
    else:
        lista_data = lista_df.to_dict('records')
    
    return html.Div([
        html.H2("Lista de Compra", style={'color': config.COLORS['primary']}),
        
        # Sección para agregar artículos
        html.Div([
            html.H4("Agregar Artículos"),
            html.Div([
                dcc.DatePickerSingle(id='compra-fecha', date=date.today(),
                                   display_format='DD/MM/YYYY',
                                   style={'margin': '10px'}),
                dcc.Input(id='compra-articulos', placeholder='Artículos (ej: Pan, Leche, Huevos)',
                         style={'width': '400px', 'margin': '10px', 'padding': '10px'}),
                html.Button('Agregar', id='add-compra-btn',
                           style={'margin': '10px', 'padding': '10px 20px',
                                 'backgroundColor': config.COLORS['secondary'], 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'})
        ], style={'backgroundColor': config.COLORS['light_gray'], 'padding': '20px', 
                 'borderRadius': '10px', 'margin': '20px 0'}),
        
        # Sección de plantillas rápidas
        html.Div([
            html.H4("🚀 Plantillas Rápidas"),
            html.Div([
                html.Button('🥖 Básicos', id='plantilla-basicos',
                           style={'margin': '5px', 'padding': '8px 15px',
                                 'backgroundColor': config.COLORS['accent'], 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px', 'fontSize': '12px'}),
                html.Button('🥩 Carnes', id='plantilla-carnes',
                           style={'margin': '5px', 'padding': '8px 15px',
                                 'backgroundColor': config.COLORS['accent'], 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px', 'fontSize': '12px'}),
                html.Button('🥬 Verduras', id='plantilla-verduras',
                           style={'margin': '5px', 'padding': '8px 15px',
                                 'backgroundColor': config.COLORS['accent'], 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px', 'fontSize': '12px'}),
                html.Button('🧽 Limpieza', id='plantilla-limpieza',
                           style={'margin': '5px', 'padding': '8px 15px',
                                 'backgroundColor': config.COLORS['accent'], 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px', 'fontSize': '12px'})
            ], style={'display': 'flex', 'flexWrap': 'wrap'}),
            html.Div(id='plantilla-mensaje', style={'margin': '10px', 'fontStyle': 'italic'})
        ], style={'backgroundColor': '#f0f8ff', 'padding': '15px', 
                 'borderRadius': '10px', 'margin': '20px 0', 'border': f'1px solid {config.COLORS["accent"]}'}),
        
        # Tabla de compras
        dash_table.DataTable(
            id='compra-table',
            data=lista_data,
            columns=[
                {'name': 'Fecha', 'id': 'fecha', 'type': 'datetime'},
                {'name': 'Artículos', 'id': 'articulos'}
            ],
            editable=True,
            row_deletable=True,
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': config.COLORS['secondary'], 'color': 'white'},
            style_data={'backgroundColor': 'white'},
            sort_action="native",
            sort_by=[{'column_id': 'fecha', 'direction': 'desc'}]
        )
    ])

def create_mantenimiento_tab(mant_df):
    """Crear contenido de la pestaña mantenimiento"""
    # Asegurar que mant_df es un DataFrame válido
    if mant_df is None or mant_df.empty:
        mant_data = []
    else:
        mant_data = mant_df.to_dict('records')
    
    return html.Div([
        html.H2("Mantenimiento y Cadafals", style={'color': config.COLORS['primary']}),
        html.Div([
            html.H4("Agregar Año de Mantenimiento"),
            html.Div([
                dcc.Input(id='mant-año', type='number', placeholder='Año',
                         value=2025, style={'width': '100px', 'margin': '10px', 'padding': '10px'}),
                dcc.Input(id='mant-encargados-mant', placeholder='Encargados Mantenimiento (ej: David, Juan Fernando)',
                         style={'width': '300px', 'margin': '10px', 'padding': '10px'}),
                dcc.Input(id='mant-encargados-cad', placeholder='Encargados Cadafals (ej: Diego, Miguel A.)',
                         style={'width': '300px', 'margin': '10px', 'padding': '10px'}),
                html.Button('Agregar', id='add-mant-btn',
                           style={'margin': '10px', 'padding': '10px 20px',
                                 'backgroundColor': config.COLORS['accent'], 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'})
        ], style={'backgroundColor': config.COLORS['light_gray'], 'padding': '20px', 
                 'borderRadius': '10px', 'margin': '20px 0'}),
        
        html.Div([
            html.H4("ℹ️ Información"),
            html.P("📋 Mantenimiento: Encargados del mantenimiento general del local"),
            html.P("🏗️ Cadafals: Encargados de montar y desmontar estructuras para fiestas"),
        ], style={'backgroundColor': '#f0f8ff', 'padding': '15px', 
                 'borderRadius': '10px', 'margin': '20px 0', 'border': f'1px solid {config.COLORS["accent"]}'}),
        
        dash_table.DataTable(
            id='mant-table',
            data=mant_data,
            columns=[
                {'name': 'Año', 'id': 'año', 'type': 'numeric'},
                {'name': 'Mantenimiento', 'id': 'mantenimiento'},
                {'name': 'Cadafals', 'id': 'cadafals'}
            ],
            editable=True,
            row_deletable=True,
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': config.COLORS['accent'], 'color': 'white'},
            style_data={'backgroundColor': 'white'},
            sort_action="native",
            sort_by=[{'column_id': 'año', 'direction': 'asc'}]
        )
    ])

def create_fiestas_tab(fiestas_df):
    """Crear contenido de la pestaña fiestas"""
    # Asegurar que fiestas_df es un DataFrame válido
    if fiestas_df is None or fiestas_df.empty:
        fiestas_data = []
    else:
        fiestas_data = fiestas_df.to_dict('records')
    
    # Tipos de fiesta para eventos especiales
    tipos_fiesta = [
        'Cumpleaños',
        'Aniversario',
        'Bautizo',
        'Comunión',
        'Boda',
        'Reunión Familiar',
        'Celebración Especial',
        'Evento Deportivo',
        'Fiesta Temática',
        'Otro'
    ]
    
    return html.Div([
        html.H2("Gestión de Fiestas Especiales - PENYA L'ALBENC", style={'color': config.COLORS['primary']}),
        
        # Información sobre las fiestas especiales
        html.Div([
            html.H4("ℹ️ Información sobre Fiestas"),
            html.P("🍽️ Las comidas regulares y fechas tradicionales (Sant Antoni, Brena St Vicent, etc.) están en la pestaña 'Comidas'"),
            html.P("🎉 Esta sección es para eventos especiales como cumpleaños, bodas, celebraciones particulares, etc."),
            html.P("📅 Puedes agregar cualquier evento especial que celebre la penya")
        ], style={'backgroundColor': '#f0f8ff', 'padding': '15px', 
                 'borderRadius': '10px', 'margin': '20px 0', 'border': f'1px solid {config.COLORS["accent"]}'}),
        
        html.Div([
            html.H4("Agregar Evento Especial"),
            html.Div([
                dcc.DatePickerSingle(id='fiesta-fecha', date=date.today(),
                                   display_format='DD/MM/YYYY',
                                   style={'margin': '10px'}),
                dcc.Dropdown(id='fiesta-tipo', 
                           options=[{'label': tipo, 'value': tipo} for tipo in tipos_fiesta],
                           placeholder='Tipo de evento especial',
                           style={'width': '200px', 'margin': '10px'}),
                dcc.Input(id='fiesta-encargados', placeholder='Encargados (ej: David, Juan Fernando)',
                         style={'width': '300px', 'margin': '10px', 'padding': '10px'}),
                dcc.Input(id='fiesta-menu', placeholder='Menú especial (ej: Tarta de cumpleaños, Cava)',
                         style={'width': '350px', 'margin': '10px', 'padding': '10px'}),
                html.Button('Agregar Evento', id='add-fiesta-btn',
                           style={'margin': '10px', 'padding': '10px 20px',
                                 'backgroundColor': config.COLORS['primary'], 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'})
        ], style={'backgroundColor': config.COLORS['light_gray'], 'padding': '20px', 
                 'borderRadius': '10px', 'margin': '20px 0'}),
        
        # Mostrar mensaje si está vacío
        html.Div([
            html.H4("📋 Estado Actual"),
            html.P(f"Eventos especiales registrados: {len(fiestas_data)}", 
                  style={'fontSize': '16px', 'fontWeight': 'bold'}),
            html.P("🎯 Esta tabla estará vacía hasta que agregues eventos especiales" if len(fiestas_data) == 0 
                  else f"✅ Tienes {len(fiestas_data)} eventos especiales programados", 
                  style={'fontStyle': 'italic'})
        ], style={'backgroundColor': '#fff8e1', 'padding': '15px', 
                 'borderRadius': '10px', 'margin': '20px 0', 'border': '1px solid #ffc107'}),
        
        dash_table.DataTable(
            id='fiestas-table',
            data=fiestas_data,
            columns=[
                {'name': 'Fecha', 'id': 'fecha', 'type': 'datetime'},
                {'name': 'Tipo de Evento', 'id': 'tipo_fiesta', 'presentation': 'dropdown'},
                {'name': 'Encargados', 'id': 'encargados_cocina'},
                {'name': 'Menú/Detalles', 'id': 'menu_cena'}
            ],
            editable=True,
            row_deletable=True,
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': config.COLORS['primary'], 'color': 'white'},
            style_data={'backgroundColor': 'white'},
            dropdown={
                'tipo_fiesta': {
                    'options': [{'label': tipo, 'value': tipo} for tipo in tipos_fiesta]
                }
            },
            sort_action="native",
            sort_by=[{'column_id': 'fecha', 'direction': 'asc'}]
        )
    ])

# Callback para inicializar contenido al autenticarse
@app.callback(
    Output('tab-content', 'children', allow_duplicate=True),
    Input('page-content', 'children'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def initialize_tab_content(page_children, session_data):
    """Inicializar contenido de pestañas al autenticarse"""
    if is_authenticated(session_data):
        # Cargar datos y mostrar pestaña de comidas por defecto
        try:
            data = load_all_data()
            return create_comidas_tab(data['comidas'])
        except Exception as e:
            logger.error(f"Error inicializando contenido: {e}")
            return html.Div(f"Error cargando datos: {str(e)}")
    return dash.no_update

# Callbacks para agregar datos (actualizados con nueva estructura)
@app.callback(
    Output('mant-table', 'data'),
    Input('add-mant-btn', 'n_clicks'),
    [State('mant-año', 'value'),
     State('mant-encargados-mant', 'value'),
     State('mant-encargados-cad', 'value'),
     State('mant-table', 'data')],
    prevent_initial_call=True
)
def add_mantenimiento_with_logging(n_clicks, año, encargados_mant, encargados_cad, current_data):
    """Agregar nuevo mantenimiento con logging"""
    if n_clicks and año and encargados_mant and encargados_cad:
        if current_data is None:
            current_data = []
        
        # Verificar si ya existe el año
        existe = any(row['año'] == año for row in current_data)
        if existe:
            return current_data  # No agregar si ya existe
        
        new_row = {'año': año, 'mantenimiento': encargados_mant, 'cadafals': encargados_cad}
        current_data.append(new_row)
        df = pd.DataFrame(current_data)
        save_data(df, 'mantenimiento')
        
        # Registrar cambio
        from src.data_manager import log_cambio
        log_cambio('Mantenimiento', 'Agregar', f'Año {año}: Mant({encargados_mant}) / Cad({encargados_cad})')
        
        logger.info(f"Nuevo mantenimiento agregado: {new_row}")
        return current_data
    return current_data or []

# Callbacks para intercambiar y copiar encargados
@app.callback(
    [Output('comidas-table', 'data', allow_duplicate=True),
     Output('intercambio-mensaje', 'children'),
     Output('intercambio-mensaje', 'style')],
    Input('intercambiar-btn', 'n_clicks'),
    [State('fecha-origen', 'value'),
     State('fecha-destino', 'value'),
     State('comidas-table', 'data')],
    prevent_initial_call=True
)
def intercambiar_encargados(n_clicks, fecha_origen, fecha_destino, current_data):
    """Intercambiar encargados entre dos fechas"""
    if not n_clicks or not fecha_origen or not fecha_destino or not current_data:
        return current_data or [], "", {}
    
    if fecha_origen == fecha_destino:
        return current_data, "❌ No puedes intercambiar con la misma fecha", {'color': config.COLORS['error']}
    
    try:
        # Parsear fechas
        fecha_orig_parts = fecha_origen.split('|')
        fecha_dest_parts = fecha_destino.split('|')
        fecha_orig_str, tipo_orig = fecha_orig_parts[0], fecha_orig_parts[1]
        fecha_dest_str, tipo_dest = fecha_dest_parts[0], fecha_dest_parts[1]
        
        # Encontrar los registros
        origen_idx = None
        destino_idx = None
        
        for i, row in enumerate(current_data):
            if row['fecha'] == fecha_orig_str and row['tipo'] == tipo_orig:
                origen_idx = i
            elif row['fecha'] == fecha_dest_str and row['tipo'] == tipo_dest:
                destino_idx = i
        
        if origen_idx is not None and destino_idx is not None:
            # Intercambiar encargados
            encargados_orig = current_data[origen_idx]['encargados']
            encargados_dest = current_data[destino_idx]['encargados']
            
            current_data[origen_idx]['encargados'] = encargados_dest
            current_data[destino_idx]['encargados'] = encargados_orig
            
            # Guardar cambios
            df = pd.DataFrame(current_data)
            save_data(df, 'comidas')
            
            mensaje = f"✅ Intercambio realizado: {encargados_orig} ↔ {encargados_dest}"
            estilo = {'color': config.COLORS['success']}
            logger.info(f"Intercambio de encargados: {fecha_orig_str} ↔ {fecha_dest_str}")
            
            return current_data, mensaje, estilo
        else:
            return current_data, "❌ Error: No se encontraron las fechas seleccionadas", {'color': config.COLORS['error']}
            
    except Exception as e:
        logger.error(f"Error en intercambio: {e}")
        return current_data, f"❌ Error: {str(e)}", {'color': config.COLORS['error']}

@app.callback(
    [Output('comidas-table', 'data', allow_duplicate=True),
     Output('copia-mensaje', 'children'),
     Output('copia-mensaje', 'style')],
    Input('copiar-btn', 'n_clicks'),
    [State('fecha-copiar', 'value'),
     State('nueva-fecha', 'date'),
     State('nuevo-tipo', 'value'),
     State('comidas-table', 'data')],
    prevent_initial_call=True
)
def copiar_encargados(n_clicks, fecha_copiar, nueva_fecha, nuevo_tipo, current_data):
    """Copiar encargados a una nueva fecha"""
    if not n_clicks or not fecha_copiar or not nueva_fecha or not nuevo_tipo:
        return current_data or [], "", {}
    
    if not current_data:
        return [], "❌ No hay datos para copiar", {'color': config.COLORS['error']}
    
    try:
        # Parsear fecha origen
        fecha_copiar_parts = fecha_copiar.split('|')
        fecha_copiar_str, tipo_copiar = fecha_copiar_parts[0], fecha_copiar_parts[1]
        
        # Encontrar el registro a copiar
        encargados_copiar = None
        for row in current_data:
            if row['fecha'] == fecha_copiar_str and row['tipo'] == tipo_copiar:
                encargados_copiar = row['encargados']
                break
        
        if encargados_copiar:
            # Verificar si ya existe esa fecha y tipo
            existe = any(row['fecha'] == nueva_fecha and row['tipo'] == nuevo_tipo for row in current_data)
            
            if existe:
                return current_data, "❌ Ya existe una entrada para esa fecha y tipo", {'color': config.COLORS['error']}
            
            # Añadir nueva entrada
            new_row = {
                'fecha': nueva_fecha,
                'tipo': nuevo_tipo,
                'encargados': encargados_copiar
            }
            current_data.append(new_row)
            
            # Guardar cambios
            df = pd.DataFrame(current_data)
            save_data(df, 'comidas')
            
            mensaje = f"✅ Copiado: {encargados_copiar} → {nueva_fecha} ({nuevo_tipo})"
            estilo = {'color': config.COLORS['success']}
            logger.info(f"Encargados copiados: {encargados_copiar} a {nueva_fecha}")
            
            return current_data, mensaje, estilo
        else:
            return current_data, "❌ No se encontró la fecha origen", {'color': config.COLORS['error']}
            
    except Exception as e:
        logger.error(f"Error en copia: {e}")
        return current_data, f"❌ Error: {str(e)}", {'color': config.COLORS['error']}

# Callbacks para plantillas rápidas de compra
@app.callback(
    [Output('compra-articulos', 'value'),
     Output('plantilla-mensaje', 'children')],
    [Input('plantilla-basicos', 'n_clicks'),
     Input('plantilla-carnes', 'n_clicks'),
     Input('plantilla-verduras', 'n_clicks'),
     Input('plantilla-limpieza', 'n_clicks')],
    prevent_initial_call=True
)
def aplicar_plantilla_compra(basicos, carnes, verduras, limpieza):
    """Aplicar plantillas rápidas para la lista de compra"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    plantillas = {
        'plantilla-basicos': "Pan, Leche, Huevos, Aceite de oliva, Sal, Azúcar",
        'plantilla-carnes': "Pollo, Ternera, Cerdo, Pescado blanco, Atún",
        'plantilla-verduras': "Tomates, Cebolla, Pimientos, Lechuga, Zanahorias, Patatas",
        'plantilla-limpieza': "Detergente, Papel higiénico, Servilletas, Jabón, Lejía"
    }
    
    nombres_plantillas = {
        'plantilla-basicos': "🥖 Básicos",
        'plantilla-carnes': "🥩 Carnes",
        'plantilla-verduras': "🥬 Verduras",
        'plantilla-limpieza': "🧽 Limpieza"
    }
    
    if trigger_id in plantillas:
        articulos = plantillas[trigger_id]
        mensaje = f"✅ Plantilla '{nombres_plantillas[trigger_id]}' aplicada"
        return articulos, mensaje
    
    return "", ""

# Callback para actualizar opciones de los dropdowns cuando cambian los datos
@app.callback(
    [Output('fecha-origen', 'options'),
     Output('fecha-destino', 'options'),
     Output('fecha-copiar', 'options')],
    Input('comidas-table', 'data'),
    prevent_initial_call=True
)
def update_dropdown_options(comidas_data):
    """Actualizar opciones de los dropdowns cuando cambian los datos"""
    if not comidas_data:
        return [], [], []
    
    opciones = [{'label': f"{row['fecha']} - {row['tipo']} - {row['encargados']}", 
                'value': f"{row['fecha']}|{row['tipo']}"} 
               for row in comidas_data]
    
    return opciones, opciones, opciones

# Callbacks para guardar cambios en las tablas (estos usan prevent_initial_call automáticamente)
@app.callback(
    Output('comidas-table', 'data', allow_duplicate=True),
    Input('comidas-table', 'data'),
    prevent_initial_call=True
)
def save_comidas_changes(data):
    """Guardar cambios en comidas"""
    if data:
        df = pd.DataFrame(data)
        save_data(df, 'comidas')
        logger.info(f"Cambios guardados en comidas: {len(df)} registros")
    return data

@app.callback(
    Output('compra-table', 'data', allow_duplicate=True),
    Input('compra-table', 'data'),
    prevent_initial_call=True
)
def save_compra_changes(data):
    """Guardar cambios en lista de compra"""
    if data:
        df = pd.DataFrame(data)
        save_data(df, 'lista_compra')
        logger.info(f"Cambios guardados en lista_compra: {len(df)} registros")
    return data

@app.callback(
    Output('mant-table', 'data', allow_duplicate=True),
    Input('mant-table', 'data'),
    prevent_initial_call=True
)
def save_mant_changes(data):
    """Guardar cambios en mantenimiento"""
    if data:
        df = pd.DataFrame(data)
        save_data(df, 'mantenimiento')
        logger.info(f"Cambios guardados en mantenimiento: {len(df)} registros")
    return data

@app.callback(
    Output('fiestas-table', 'data', allow_duplicate=True),
    Input('fiestas-table', 'data'),
    prevent_initial_call=True
)
def save_fiestas_changes(data):
    """Guardar cambios en fiestas"""
    if data:
        df = pd.DataFrame(data)
        save_data(df, 'fiestas')
        logger.info(f"Cambios guardados en fiestas: {len(df)} registros")
    return data

if __name__ == '__main__':
    # Este bloque solo se ejecuta si se llama directamente a app.py
    # Normalmente se ejecuta a través de run.py
    logger.warning("Ejecutando app.py directamente. Se recomienda usar 'python run.py'")
    app.run_server(debug=config.DEBUG, host=config.HOST, port=config.PORT)