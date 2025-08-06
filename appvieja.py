import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table, ALL
from dash.exceptions import PreventUpdate
import dash.dependencies
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import os
from datetime import datetime, date, timedelta
import calendar


# Inicializar la app
is_production = os.environ.get('RENDER') is not None

# Al inicio del archivo, después de crear la app
app = dash.Dash(__name__, suppress_callback_exceptions=True, 
                assets_folder='assets',
                assets_url_path='/assets/')

# AGREGAR ESTO ⬇️
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Penya L'Albenc</title>
        <link rel="shortcut icon" href="/assets/favicon.ico">
        <link rel="icon" type="image/x-icon" href="/assets/favicon.ico">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        {%css%}
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

    # Tabla de fiestas (agregar después de las otras tablas)
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

def migrate_fiestas_table():
    """Agregar columnas faltantes a la tabla fiestas si no existen"""
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    try:
        # Verificar si las columnas ya existen
        cursor.execute("PRAGMA table_info(fiestas)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Agregar columnas faltantes si no existen
        if 'nombres_adultos' not in columns:
            cursor.execute("ALTER TABLE fiestas ADD COLUMN nombres_adultos TEXT DEFAULT ''")
            print("✅ Columna 'nombres_adultos' agregada")
        
        if 'nombres_niños' not in columns:
            cursor.execute("ALTER TABLE fiestas ADD COLUMN nombres_niños TEXT DEFAULT ''")
            print("✅ Columna 'nombres_niños' agregada")
        
        conn.commit()
    except Exception as e:
        print(f"Error en migración: {e}")
    finally:
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
    elif table == 'fiestas':
        cursor.execute("INSERT INTO fiestas (fecha, cocineros, menu, adultos, nombres_adultos, niños, nombres_niños, programa) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data)
    
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

def get_dias_fiestas_con_semana():
        """Obtener días de fiestas con día de la semana en español"""
        from datetime import datetime
        
        dias_semana = {
            0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 
            3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
        }
        
        opciones = []
        for i in range(8, 18):
            fecha_str = f"2025-08-{i:02d}"
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
            dia_semana = dias_semana[fecha_obj.weekday()]
            
            opciones.append({
                'label': f"{dia_semana} {i} de agosto 2025", 
                'value': fecha_str
            })
        
        return opciones

def generar_lista_comensales(nombres_str, tipo):
        """Generar lista visual de comensales con botones eliminar"""
        if not nombres_str or not nombres_str.strip():
            return []
        
        nombres = [nombre.strip() for nombre in nombres_str.split(',') if nombre.strip()]
        
        lista_elementos = []
        for i, nombre in enumerate(nombres):
            elemento = html.Div([
                html.Span(nombre, style={"flex": "1", "padding": "5px"}),
                html.Button("❌", 
                        id={"type": "btn-eliminar-comensal", "index": f"{tipo}-{i}", "nombre": nombre},
                        style={
                            "background": "#F44336", "color": "white", "border": "none",
                            "padding": "2px 6px", "border-radius": "4px", "cursor": "pointer",
                            "font-size": "12px", "margin-left": "10px"
                        })
            ], style={
                "display": "flex", "align-items": "center", "justify-content": "space-between",
                "background": "#f9f9f9", "margin": "3px 0", "padding": "5px", 
                "border-radius": "6px", "border": "1px solid #ddd"
            })
            lista_elementos.append(elemento)
        
        return lista_elementos
        
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

def load_fiestas_agosto_2025():
    """Cargar datos fijos de fiestas agosto 2025"""
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    # Verificar si ya hay datos
    cursor.execute("SELECT COUNT(*) FROM fiestas WHERE fecha BETWEEN '2025-08-08' AND '2025-08-17'")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Datos fijos COMPLETOS para los 10 días
    fiestas_data = [
        ('2025-08-08', 'Oscar Vicente, Serafin Montoliu', '', 0, 'Serafin Montoliu, Alonso Roqueta, Lara Sorribes, J. Ramon Barreda, Victor Zandalinas, Sonia Domingo, Pilar Gimeno Belles, Diego Tena Pitarch, Carmina Escorihuela, David Roig, Lucia Carceller, Miguel A Monfort, Óscar Vicente, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Manel Roig, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '16:30-Final Frontenis|17:30-Final Futbol-sala|19:00-Chupinazo y pasacalle|22:30-Presentacion|00:00-Discomóvil'),
        ('2025-08-09', 'Alfonso Roig, Ana Troncho', '', 0, 'Serafin Montoliu, Alonso Roqueta, Lara Sorribes, Carolina De Toro, J. Ramon Barreda, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, David Roig, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Óscar Vicente, Ana Troncho, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '17:00-Corro de vacas y toro|19:00-Tardeo "Kasparov"|21:00-Cena Popular (concurso manteles - AvLosar)|23:30-Toro embolado|00:30-Grupo Zetak'),
        ('2025-08-10', 'Miguel A. Monfort, Lucia Carceller', '', 0, 'Susana Pitarch, Serafin Montoliu, J. Ramon Barreda, Victor Zandalinas, Sonia Domingo, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Vera Montoliu, Saul Montoliu, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Andres Vicente, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '12:00-Sevillanas tasca comision|17:00-Recortadores|19:00-Tardeo Rumba 13|22:30-Concurso Emboladores|00:00-Tu Cara Me Suena + Noche Spotify en tasca comisión'),
        ('2025-08-11', 'DIA DE LES PENYES', 'Arroz con secreto y costilla / Guiso de toro', 0, 'Alonso Roqueta, Carolina De Toro, J. Ramon Barreda, Pilar Gimeno Belles, Diego Tena Pitarch, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', 'DIA DE LAS PEÑAS|14:00-Comida Arroz con secreto y costilla|16:30-Juego de peñas|21:00-Cena Guiso de toro|A continuación Discomóvil plaza toros'),
        ('2025-08-12', 'Victor Prades, Sara Barcina, J. Fernando Marques', '', 0, 'Alonso Roqueta, J. Ramon Barreda, Victor Zandalinas, Sonia Domingo, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Elena Domingo, Raul Altaba, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Daniel Altaba, Martina Altaba, Andres Vicente, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '17:00-Corro de vacas con charanga|19:00-Tardeo Generación Z|23:00-Toro embolado|00:30-Orquesta Bella Donna y discomóvil'),
        ('2025-08-13', 'David Roig, Carmina Escorihuela', '', 0, 'Carolina De Toro, J. Ramon Barreda, Victor Zandalinas, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Elena Domingo, Raul Altaba, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Daniel Altaba, Martina Altaba, Andres Vicente, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '17:00-Corro de vacas y entrada de toro|18:00-Bureo Parador|19:30-Tarde de rock tasca|22:00-Grupo Garrama|23:30-Toro Embolado|00:00-Tributo Extremoduro en tasca'),
        ('2025-08-14', 'J.Ramon Barreda, Carolina De Toro', '', 0, 'Carolina De Toro, J. Ramon Barreda, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, David Roig, Elena Domingo, Raul Altaba, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Óscar Vicente, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Daniel Altaba, Martina Altaba, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '19:00-Desencajonada de 2 toros y embolada de 1 toro|00:00-Desfile disfraces con charanga y baile con La Freska'),
        ('2025-08-15', 'Raul Altaba, Elena Domingo, Victor Zandalinas, Sonia Domingo', '', 0, 'Serafin Montoliu, Alonso Roqueta, Lara Sorribes, Carolina De Toro, J. Ramon Barreda, Victor Zandalinas, Sonia Domingo, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Elena Domingo, Raul Altaba, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Óscar Vicente, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Daniel Altaba, Martina Altaba, Andres Vicente, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '12:00-Especial con vacas|16:30-Corro de vacas|18:00-Prueba de toro Ventanillo|22:30-Ball Pla|00:00-Toro embolado|00:30-Tributo a la Oreja de Van Gogh en plaza de toros'),
        ('2025-08-16', 'Luis Belles, Marta Fusté, Alonso Roqueta, Lara Sorribes', '', 0, 'Serafin Montoliu, Alonso Roqueta, Lara Sorribes, Carolina De Toro, J. Ramon Barreda, Victor Zandalinas, Sonia Domingo, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, David Roig, Elena Domingo, Raul Altaba, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Óscar Vicente, Sara Barcina, Víctor Prades, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Daniel Altaba, Martina Altaba, Nuria Monfort, Andrea Monfort, Alex Roig', '14:00-Concurso de paellas en av Losar|17:00-Corro de vacas y entrada de toro|19:00-Tardeo Town Folks|21:00-Cena popular concurso de postres en av Losar|23:00-Toro embolado|00:00-Orquesta Vallparaiso en plaza de toros y discomóvil'),
        ('2025-08-17', 'Francisco Vicente, Sugey Guzman, Diego Tena, Pilar Gimeno', '', 0, 'Susana Pitarch, Serafin Montoliu, Alonso Roqueta, Lara Sorribes, J. Ramon Barreda, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Elena Domingo, Raul Altaba, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Vera Montoliu, Saul Montoliu, Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Daniel Altaba, Martina Altaba, Andres Vicente, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '16:30-Espectaculo de motos|18:00-Grison en plaza de toros|22:30-Correfocs'),
    ]
    
    for data in fiestas_data:
        cursor.execute("INSERT INTO fiestas (fecha, cocineros, menu, adultos, nombres_adultos, niños, nombres_niños, programa) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data)
    
    conn.commit()
    conn.close()

def generar_tarjetas_fiestas():
    """Función auxiliar para generar las tarjetas de fiestas - VERSIÓN MEJORADA"""
    try:
        fiestas_df = get_data('fiestas')
        
        # Filtrar solo agosto 2025
        fiestas_agosto = fiestas_df[
            (fiestas_df['fecha'] >= '2025-08-08') & 
            (fiestas_df['fecha'] <= '2025-08-17')
        ].sort_values('fecha') if len(fiestas_df) > 0 else pd.DataFrame()
        
        if len(fiestas_agosto) == 0:
            return [html.P("No hay datos de fiestas de agosto", style={"text-align": "center", "color": "#666"})]
        
        tarjetas = []
        for _, dia in fiestas_agosto.iterrows():
            # Formatear fecha con día de la semana
            try:
                from datetime import datetime
                fecha_obj = datetime.strptime(dia['fecha'], '%Y-%m-%d')
                
                # Diccionario para días en español
                dias_semana = {
                    0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 
                    3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
                }
                
                dia_semana = dias_semana[fecha_obj.weekday()]
                fecha_formateada = f"{dia_semana} {fecha_obj.day} de agosto"
            except:
                fecha_formateada = dia['fecha']
            
            # Procesar programa (split por |)
            eventos = dia['programa'].split('|') if dia['programa'] else ['Sin programa']
            
            # Procesar listas de comensales
            def crear_lista_comensales(nombres_str, emoji, color):
                if not nombres_str or nombres_str.strip() == 'Sin nombres':
                    return html.P("Sin comensales registrados", 
                                 style={"font-style": "italic", "color": "#999", "margin": "0"})
                
                nombres = [nombre.strip() for nombre in nombres_str.split(',') if nombre.strip()]
                if not nombres:
                    return html.P("Sin comensales registrados", 
                                 style={"font-style": "italic", "color": "#999", "margin": "0"})
                
                lista_elementos = []
                for nombre in nombres:
                    lista_elementos.append(
                        html.Div([
                            html.Span(f"{emoji} {nombre}", style={
                                "background": f"linear-gradient(135deg, {color}20 0%, {color}10 100%)",
                                "padding": "4px 8px",
                                "border-radius": "12px",
                                "border": f"1px solid {color}40",
                                "font-size": "0.85rem",
                                "margin": "2px",
                                "display": "inline-block"
                            })
                        ], style={"display": "inline-block", "margin": "1px"})
                    )
                
                return html.Div(lista_elementos, style={
                    "display": "flex", 
                    "flex-wrap": "wrap", 
                    "gap": "4px",
                    "margin": "5px 0"
                })
            
            # Obtener nombres de adultos y niños (con verificación de campos)
            nombres_adultos = dia.get('nombres_adultos', '') or ''
            nombres_niños = dia.get('nombres_niños', '') or ''
            
            # Contar comensales
            def contar_nombres(texto):
                if not texto or not texto.strip():
                    return 0
                nombres = [nombre.strip() for nombre in texto.split(',') if nombre.strip()]
                return len(nombres)
            
            total_adultos = contar_nombres(nombres_adultos)
            total_niños = contar_nombres(nombres_niños)
            
            # Determinar color de la tarjeta según el día
            color_dia = "#FF5722"  # Naranja por defecto
            if "PENYES" in dia['cocineros'].upper():
                color_dia = "#4CAF50"  # Verde para día especial
            elif fecha_obj.weekday() == 5:  # Sábado
                color_dia = "#9C27B0"  # Morado para sábados
            elif fecha_obj.weekday() == 6:  # Domingo
                color_dia = "#2196F3"  # Azul para domingos
            
            tarjeta = html.Div([
                # Cabecera con fecha
                html.Div([
                    html.H4(f"📅 {fecha_formateada}", style={
                        "color": "white", 
                        "margin": "0", 
                        "text-align": "center",
                        "font-size": "1.1rem",
                        "font-weight": "bold"
                    })
                ], style={
                    "background": f"linear-gradient(135deg, {color_dia} 0%, {color_dia}CC 100%)",
                    "padding": "15px",
                    "border-radius": "12px 12px 0 0",
                    "margin": "-20px -20px 15px -20px"
                }),
                
                # Cocineros
                html.Div([
                    html.H6("👨‍🍳 Cocineros:", style={"color": "#4CAF50", "margin-bottom": "5px"}),
                    html.P(dia['cocineros'], style={
                        "margin": "0 0 15px 0", 
                        "font-weight": "bold",
                        "background": "#E8F5E8",
                        "padding": "8px",
                        "border-radius": "6px"
                    })
                ]),
                
                # Menú
                html.Div([
                    html.H6("🍽️ Menú:", style={"color": "#2196F3", "margin-bottom": "5px"}),
                    html.P(dia['menu'] or 'Sin menú definido', style={
                        "margin": "0 0 15px 0", 
                        "font-style": "italic" if not dia['menu'] else "normal",
                        "background": "#E3F2FD" if dia['menu'] else "#F5F5F5",
                        "padding": "8px",
                        "border-radius": "6px",
                        "color": "#333" if dia['menu'] else "#999"
                    })
                ]),
                
                # Comensales Adultos
                html.Div([
                    html.Div([
                        html.H6("👥 Adultos", style={"color": "#9C27B0", "margin": "0", "display": "inline"}),
                        html.Span(f" ({total_adultos})", style={
                            "background": "#9C27B0", 
                            "color": "white", 
                            "padding": "2px 8px", 
                            "border-radius": "10px", 
                            "font-size": "0.8rem",
                            "margin-left": "8px",
                            "font-weight": "bold"
                        })
                    ], style={"margin-bottom": "8px", "display": "flex", "align-items": "center"}),
                    crear_lista_comensales(nombres_adultos, "👤", "#9C27B0")
                ], style={"margin-bottom": "15px"}),
                
                # Comensales Niños
                html.Div([
                    html.Div([
                        html.H6("👶 Niños", style={"color": "#FF9800", "margin": "0", "display": "inline"}),
                        html.Span(f" ({total_niños})", style={
                            "background": "#FF9800", 
                            "color": "white", 
                            "padding": "2px 8px", 
                            "border-radius": "10px", 
                            "font-size": "0.8rem",
                            "margin-left": "8px",
                            "font-weight": "bold"
                        })
                    ], style={"margin-bottom": "8px", "display": "flex", "align-items": "center"}),
                    crear_lista_comensales(nombres_niños, "👶", "#FF9800")
                ], style={"margin-bottom": "15px"}),
                
                # Programa
                html.Div([
                    html.H6("🎪 Programa:", style={"color": "#795548", "margin-bottom": "8px"}),
                    html.Div([
                        html.Div([
                            html.Span("🕐", style={"margin-right": "5px", "color": "#795548"}),
                            html.Span(evento.strip(), style={"font-size": "0.9rem"})
                        ], style={
                            "background": "#F5F5F5",
                            "padding": "6px 10px",
                            "margin": "3px 0",
                            "border-radius": "6px",
                            "border-left": "3px solid #795548"
                        }) for evento in eventos
                    ])
                ]),
                
                # Total de comensales al pie
                html.Div([
                    html.Span(f"👥 Total comensales: {total_adultos + total_niños}", style={
                        "background": "linear-gradient(135deg, #E8EAF6 0%, #C5CAE9 100%)",
                        "color": "#3F51B5",
                        "padding": "8px 15px",
                        "border-radius": "20px",
                        "font-weight": "bold",
                        "font-size": "0.9rem",
                        "display": "inline-block",
                        "width": "100%",
                        "text-align": "center",
                        "margin-top": "10px",
                        "border": "1px solid #3F51B540"
                    })
                ])
                
            ], style={
                "border": f"2px solid {color_dia}40", 
                "margin": "15px", 
                "padding": "20px", 
                "border-radius": "16px",
                "background": "linear-gradient(135deg, #FFFDE7 0%, #FFF9C4 100%)", 
                "box-shadow": f"0 8px 25px {color_dia}20, 0 4px 10px rgba(0,0,0,0.1)",
                "flex": "1",
                "min-width": "350px",
                "max-width": "450px",
                "position": "relative",
                "transition": "transform 0.3s ease, box-shadow 0.3s ease"
            })
            tarjetas.append(tarjeta)
        
        return html.Div(tarjetas, style={
            "display": "flex", 
            "flex-wrap": "wrap", 
            "justify-content": "center",
            "gap": "15px",
            "padding": "10px"
        })
        
    except Exception as e:
        print(f"Error generando tarjetas: {e}")
        import traceback
        traceback.print_exc()
        return [html.P(f"Error cargando datos: {e}", style={"text-align": "center", "color": "red"})]

# Funciones auxiliares para filtros (restauradas)
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

def inicializar_cocineros_desde_comidas():
    """Función auxiliar para inicializar cocineros (ya no es necesaria con get_cocineros_options)"""
    pass

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

def get_eventos_calendario():
    """Obtener todos los eventos para el calendario desde comidas y mantenimiento"""
    try:
        conn = sqlite3.connect('penya_albenc.db')
        
        # Obtener comidas
        comidas_query = """
        SELECT fecha, tipo_comida as evento, tipo_servicio as tipo, 'comida' as categoria
        FROM comidas 
        WHERE fecha >= date('now', '-30 days')
        ORDER BY fecha
        """
        
        # Obtener mantenimiento (convertir año a fecha aproximada)
        mantenimiento_query = """
        SELECT (año || '-01-01') as fecha, mantenimiento as evento, 'Anual' as tipo, 'mantenimiento' as categoria
        FROM mantenimiento 
        WHERE año >= strftime('%Y', 'now')
        ORDER BY año
        """
        
        eventos_comidas = pd.read_sql_query(comidas_query, conn)
        eventos_mantenimiento = pd.read_sql_query(mantenimiento_query, conn)
        
        # Combinar todos los eventos
        eventos = pd.concat([eventos_comidas, eventos_mantenimiento], ignore_index=True)
        
        conn.close()
        return eventos
    except Exception as e:
        print(f"Error obteniendo eventos: {e}")
        return pd.DataFrame()

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

# Versión Ultra Moderna - Dark Theme
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "right": 0,
    "height": "80px",  # ← Más altura para mejor proporción
    "padding": "0 max(1rem, env(safe-area-inset-left)) 0 max(1rem, env(safe-area-inset-right))",  # ← Soporte PWA
    "background": """
        linear-gradient(135deg, 
            rgba(30, 30, 30, 0.95) 0%, 
            rgba(45, 45, 45, 0.95) 50%, 
            rgba(20, 20, 20, 0.95) 100%)
    """,  # ← Dark glassmorphism
    "backdropFilter": "blur(20px) saturate(1.2)",  # ← Efecto moderno
    "borderBottom": "1px solid rgba(255,255,255,0.08)",
    "color": "rgba(255,255,255,0.95)",
    "boxShadow": """
        0 8px 32px rgba(0,0,0,0.12),
        0 2px 8px rgba(0,0,0,0.08),
        inset 0 1px 0 rgba(255,255,255,0.05)
    """,  # ← Sombras premium
    "zIndex": "1000",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "space-between",
    "transition": "all 0.4s cubic-bezier(0.23, 1, 0.32, 1)",  # ← Easing premium
    "WebkitBackdropFilter": "blur(20px) saturate(1.2)",
    # Soporte para notch de móviles
    "paddingTop": "env(safe-area-inset-top)",
}

CONTENT_STYLE = {
    "marginTop": "100px",  # ← Ajustado
    "marginLeft": "clamp(0.5rem, 5vw, 4rem)",  # ← Más responsive
    "marginRight": "clamp(0.5rem, 5vw, 4rem)",
    "padding": "clamp(2rem, 4vw, 4rem) clamp(1.5rem, 3vw, 3rem)",
    "background": """
        linear-gradient(135deg, 
            rgba(248, 250, 252, 0.98) 0%, 
            rgba(241, 245, 249, 0.95) 100%)
    """,  # ← Fondo premium
    "minHeight": "calc(100vh - 100px)",  # ← Altura exacta
    "borderRadius": "32px 32px 0 0",  # ← Bordes más redondeados
    "boxShadow": """
        0 -10px 40px rgba(0,0,0,0.06),
        0 -2px 8px rgba(0,0,0,0.02),
        inset 0 1px 0 rgba(255,255,255,0.8)
    """,  # ← Sombras premium
    "position": "relative",
    "overflow": "hidden",
    "backgroundImage": """
        radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.1) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.08) 0%, transparent 50%),
        radial-gradient(circle at 40% 40%, rgba(120, 200, 255, 0.05) 0%, transparent 50%)
    """,  # ← Efectos de luz múltiples
    "transition": "all 0.4s cubic-bezier(0.23, 1, 0.32, 1)",
    # Animación sutil de entrada
    "animation": "slideInUp 0.6s cubic-bezier(0.23, 1, 0.32, 1)",
}


# Layout del sidebar como navbar horizontal
# Layout del sidebar como navbar horizontal
sidebar = html.Div([
    # Location component
    dcc.Location(id="url"),
    
    # Logo y título (lado izquierdo)
    html.Div([
        html.Img(src="/assets/logo.png", style={
            "width": "50px", "height": "50px", "margin-right": "15px", 
            "border-radius": "8px", "object-fit": "contain"
        }),
        html.H2("Penya L'Albenc", style={
            "font-size": "1.3rem", "margin": "0", 
            "font-weight": "600", "letter-spacing": "-0.5px"
        })
    ], style={"display": "flex", "align-items": "center"}),
    
    # Botón hamburguesa y menú (lado derecho)
    html.Div([
        html.Button("☰", id="btn-toggle-sidebar", 
                    style={
                        "background": "rgba(255,255,255,0.2)", "border": "none", 
                        "color": "white", "font-size": "20px", "cursor": "pointer",
                        "padding": "8px 12px", "border-radius": "6px",
                        "transition": "all 0.3s ease"
                    }),
        
        # Menú desplegable (inicialmente oculto)
        html.Div([
            dcc.Link([
                html.Div([
                    html.Span("🏠", style={"margin-right": "10px"}),
                    html.Span("Inicio")
                ], style={"display": "flex", "align-items": "center"})
            ], href="/", className="nav-link-dropdown"),
            
            dcc.Link([
                html.Div([
                    html.Span("🍽️", style={"margin-right": "10px"}),
                    html.Span("Comidas")
                ], style={"display": "flex", "align-items": "center"})
            ], href="/comidas", className="nav-link-dropdown"),
            
            dcc.Link([
                html.Div([
                    html.Span("🛒", style={"margin-right": "10px"}),
                    html.Span("Lista de Compra")
                ], style={"display": "flex", "align-items": "center"})
            ], href="/lista-compra", className="nav-link-dropdown"),
            
            dcc.Link([
                html.Div([
                    html.Span("🔧", style={"margin-right": "10px"}),
                    html.Span("Mantenimiento")
                ], style={"display": "flex", "align-items": "center"})
            ], href="/mantenimiento", className="nav-link-dropdown"),
            
            dcc.Link([
                html.Div([
                    html.Span("🎉", style={"margin-right": "10px"}),
                    html.Span("Fiestas")
                ], style={"display": "flex", "align-items": "center"})
            ], href="/fiestas", className="nav-link-dropdown"),
            
        ], id="dropdown-menu", className="modern-dropdown")  # ← Sin style inline

    ], style={"position": "relative"})
    
], id="sidebar", style=SIDEBAR_STYLE)

# Layout principal (UNA SOLA VEZ - al final)
content = html.Div(id="page-content", style=CONTENT_STYLE)

# Layout de la app (UNA SOLA VEZ - al final, después de content)
app.layout = html.Div([
    dcc.Store(id="confirm-action"),
    sidebar,
    content
])

# Callback mejorado para mostrar/ocultar el menú desplegable
@app.callback(
    [Output("dropdown-menu", "style"),
     Output("dropdown-menu", "className")],
    [Input("btn-toggle-sidebar", "n_clicks"),
     Input("url", "pathname")],
    prevent_initial_call=True
)
def toggle_dropdown_menu(n_clicks, pathname):
    ctx = callback_context
    
    # Estilos base del menú centrado
    base_style = {
        "position": "fixed",
        "top": "100%",
        "left": "85%",
        "transform": "translate(-50%, -50%)",
        "zIndex": "1003",
        "background": "linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)",  # ← Gradiente sutil
        "borderRadius": "24px",  # ← Más redondeado
        "boxShadow": """
            0 25px 50px rgba(0,0,0,0.15),
            0 0 0 1px rgba(255,255,255,0.05),
            inset 0 1px 0 rgba(255,255,255,0.9)
        """,  # ← Sombras múltiples premium
        "border": "1px solid rgba(226, 232, 240, 0.8)",  # ← Borde más sutil
        "backdropFilter": "blur(20px) saturate(1.1)",  # ← Efecto glassmorphism
        "minWidth": "280px",
        "width": "280px",
        "maxHeight": "50vh",
        "overflowY": "auto",
        "animation": "modalSlide 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)",  # ← Animación con bounce
        "flexDirection": "column",
        "padding": "30px 0",  # ← Más padding vertical
        # Scroll personalizado
        "scrollbarWidth": "thin",
        "scrollbarColor": "#cbd5e1 transparent"
    }
    
    # Si se cambió la página, ocultar el menú
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'url.pathname':
        return {**base_style, "display": "none"}, "modern-dropdown"
    
    # Si se hizo clic en las 3 rayas
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'btn-toggle-sidebar.n_clicks':
        if n_clicks and n_clicks % 2 == 1:  # Impar = mostrar
            return {**base_style, "display": "flex"}, "modern-dropdown show"
        else:  # Par = ocultar
            return {**base_style, "display": "none"}, "modern-dropdown"
    
    # Por defecto oculto
    return {**base_style, "display": "none"}, "modern-dropdown"

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
    elif pathname == "/debug":  # ← AGREGAR ESTO
        return create_debug_page()
    else:
        return create_home_page()


# Callback para cargar datos automáticamente al seleccionar día
@app.callback(
    [Output('fiesta-menu', 'value'),
     Output('store-comensales-adultos', 'data'),
     Output('store-comensales-niños', 'data'),
     Output('lista-adultos-visual', 'children'),
     Output('lista-niños-visual', 'children'),
     Output('contador-adultos-nuevo', 'children'),
     Output('contador-niños-nuevo', 'children')],
    [Input('fiesta-dia-selector', 'value')],  # ← Ahora reacciona al selector
    prevent_initial_call=True
)
def cargar_datos_automaticamente(fecha_seleccionada):
    if not fecha_seleccionada:
        return "", [], [], [], [], "(0)", "(0)"
    
    try:
        fiestas_df = get_data('fiestas')
        dia_data = fiestas_df[fiestas_df['fecha'] == fecha_seleccionada]
        
        if len(dia_data) == 0:
            return "", [], [], [], [], "(0)", "(0)"
        
        dia = dia_data.iloc[0]
        
        # Convertir nombres en listas
        nombres_adultos = [nombre.strip() for nombre in (dia.get('nombres_adultos', '') or '').split(',') if nombre.strip()]
        nombres_niños = [nombre.strip() for nombre in (dia.get('nombres_niños', '') or '').split(',') if nombre.strip()]
        
        # Generar listas visuales
        def crear_lista_visual(nombres, tipo, color):
            if not nombres:
                return [html.P("Sin comensales", style={"color": "#999", "font-style": "italic"})]
            
            elementos = []
            for i, nombre in enumerate(nombres):
                elemento = html.Div([
                    html.Span(f"👤 {nombre}", style={"flex": "1", "padding": "5px"}),
                    html.Button("❌", 
                            id={"type": "btn-eliminar", "categoria": tipo, "index": i, "nombre": nombre},
                            style={
                                "background": "#F44336", "color": "white", "border": "none",
                                "padding": "4px 8px", "border-radius": "4px", "cursor": "pointer",
                                "font-size": "12px", "margin-left": "10px"
                            })
                ], style={
                    "display": "flex", "align-items": "center", "justify-content": "space-between",
                    "background": f"{color}20", "margin": "3px 0", "padding": "8px", 
                    "border-radius": "6px", "border": f"1px solid {color}40"
                })
                elementos.append(elemento)
            
            return elementos
        
        lista_adultos_visual = crear_lista_visual(nombres_adultos, "adultos", "#9C27B0")
        lista_niños_visual = crear_lista_visual(nombres_niños, "niños", "#FF9800")
        
        return (
            dia.get('menu', '') or '',
            nombres_adultos,
            nombres_niños,
            lista_adultos_visual,
            lista_niños_visual,
            f"({len(nombres_adultos)})",
            f"({len(nombres_niños)})"
        )
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return "", [], [], [], [], "(0)", "(0)"

# Callback para agregar adultos
@app.callback(
    [Output('store-comensales-adultos', 'data', allow_duplicate=True),
     Output('lista-adultos-visual', 'children', allow_duplicate=True),
     Output('contador-adultos-nuevo', 'children', allow_duplicate=True),
     Output('input-nuevo-adulto', 'value')],
    [Input('btn-add-adulto', 'n_clicks')],
    [State('input-nuevo-adulto', 'value'),
     State('store-comensales-adultos', 'data')],
    prevent_initial_call=True
)
def agregar_adulto(n_clicks, nuevo_nombre, lista_actual):
    if not n_clicks or not nuevo_nombre or not nuevo_nombre.strip():
        raise PreventUpdate
    
    nuevo_nombre = nuevo_nombre.strip()
    if nuevo_nombre in lista_actual:
        raise PreventUpdate
    
    nueva_lista = lista_actual + [nuevo_nombre]
    
    # Crear lista visual
    elementos = []
    for i, nombre in enumerate(nueva_lista):
        elemento = html.Div([
            html.Span(f"👤 {nombre}", style={"flex": "1", "padding": "5px"}),
            html.Button("❌", 
                    id={"type": "btn-eliminar", "categoria": "adultos", "index": i, "nombre": nombre},
                    style={
                        "background": "#F44336", "color": "white", "border": "none",
                        "padding": "4px 8px", "border-radius": "4px", "cursor": "pointer",
                        "font-size": "12px", "margin-left": "10px"
                    })
        ], style={
            "display": "flex", "align-items": "center", "justify-content": "space-between",
            "background": "#9C27B020", "margin": "3px 0", "padding": "8px", 
            "border-radius": "6px", "border": "1px solid #9C27B040"
        })
        elementos.append(elemento)
    
    return nueva_lista, elementos, f"({len(nueva_lista)})", ""

# Callback para agregar niños
@app.callback(
    [Output('store-comensales-niños', 'data', allow_duplicate=True),
     Output('lista-niños-visual', 'children', allow_duplicate=True),
     Output('contador-niños-nuevo', 'children', allow_duplicate=True),
     Output('input-nuevo-niño', 'value')],
    [Input('btn-add-niño', 'n_clicks')],
    [State('input-nuevo-niño', 'value'),
     State('store-comensales-niños', 'data')],
    prevent_initial_call=True
)
def agregar_niño(n_clicks, nuevo_nombre, lista_actual):
    if not n_clicks or not nuevo_nombre or not nuevo_nombre.strip():
        raise PreventUpdate
    
    nuevo_nombre = nuevo_nombre.strip()
    if nuevo_nombre in lista_actual:
        raise PreventUpdate
    
    nueva_lista = lista_actual + [nuevo_nombre]
    
    # Crear lista visual
    elementos = []
    for i, nombre in enumerate(nueva_lista):
        elemento = html.Div([
            html.Span(f"👶 {nombre}", style={"flex": "1", "padding": "5px"}),
            html.Button("❌", 
                    id={"type": "btn-eliminar", "categoria": "niños", "index": i, "nombre": nombre},
                    style={
                        "background": "#F44336", "color": "white", "border": "none",
                        "padding": "4px 8px", "border-radius": "4px", "cursor": "pointer",
                        "font-size": "12px", "margin-left": "10px"
                    })
        ], style={
            "display": "flex", "align-items": "center", "justify-content": "space-between",
            "background": "#FF980020", "margin": "3px 0", "padding": "8px", 
            "border-radius": "6px", "border": "1px solid #FF980040"
        })
        elementos.append(elemento)
    
    return nueva_lista, elementos, f"({len(nueva_lista)})", ""

# Callback para eliminar comensales (con pattern matching)
@app.callback(
    [Output('store-comensales-adultos', 'data', allow_duplicate=True),
     Output('store-comensales-niños', 'data', allow_duplicate=True),
     Output('lista-adultos-visual', 'children', allow_duplicate=True),
     Output('lista-niños-visual', 'children', allow_duplicate=True),
     Output('contador-adultos-nuevo', 'children', allow_duplicate=True),
     Output('contador-niños-nuevo', 'children', allow_duplicate=True)],
    [Input({"type": "btn-eliminar", "categoria": ALL, "index": ALL, "nombre": ALL}, "n_clicks")],
    [State('store-comensales-adultos', 'data'),
     State('store-comensales-niños', 'data')],
    prevent_initial_call=True
)
def eliminar_comensal(n_clicks_list, adultos_actuales, niños_actuales):
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        raise PreventUpdate
    
    # Encontrar qué botón se presionó
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_data = eval(button_id)  # Convertir string a dict
    
    nombre_eliminar = button_data['nombre']
    categoria = button_data['categoria']
    
    # Eliminar de la lista correspondiente
    if categoria == "adultos" and nombre_eliminar in adultos_actuales:
        adultos_actuales.remove(nombre_eliminar)
    elif categoria == "niños" and nombre_eliminar in niños_actuales:
        niños_actuales.remove(nombre_eliminar)
    
    # Regenerar listas visuales
    def crear_elementos(lista, tipo, emoji, color):
        if not lista:
            return [html.P("Sin comensales", style={"color": "#999", "font-style": "italic"})]
        
        elementos = []
        for i, nombre in enumerate(lista):
            elemento = html.Div([
                html.Span(f"{emoji} {nombre}", style={"flex": "1", "padding": "5px"}),
                html.Button("❌", 
                        id={"type": "btn-eliminar", "categoria": tipo, "index": i, "nombre": nombre},
                        style={
                            "background": "#F44336", "color": "white", "border": "none",
                            "padding": "4px 8px", "border-radius": "4px", "cursor": "pointer",
                            "font-size": "12px", "margin-left": "10px"
                        })
            ], style={
                "display": "flex", "align-items": "center", "justify-content": "space-between",
                "background": f"{color}20", "margin": "3px 0", "padding": "8px", 
                "border-radius": "6px", "border": f"1px solid {color}40"
            })
            elementos.append(elemento)
        
        return elementos
    
    lista_adultos_visual = crear_elementos(adultos_actuales, "adultos", "👤", "#9C27B0")
    lista_niños_visual = crear_elementos(niños_actuales, "niños", "👶", "#FF9800")
    
    return (
        adultos_actuales, niños_actuales,
        lista_adultos_visual, lista_niños_visual,
        f"({len(adultos_actuales)})", f"({len(niños_actuales)})"
    )

# Callback para actualizar día (ACTUALIZADO SIN INPUTS DE NÚMERO)
@app.callback(
    [Output('fiesta-output', 'children'),
     Output('tarjetas-fiestas', 'children')],
    [Input('btn-guardar-cambios', 'n_clicks'),
     Input('url', 'pathname')],
    [State('fiesta-dia-selector', 'value'),
     State('fiesta-menu', 'value'),
     State('store-comensales-adultos', 'data'),
     State('store-comensales-niños', 'data')],
)

def actualizar_y_mostrar_fiestas_mejorado(n_clicks, pathname, fecha, menu, adultos_lista, niños_lista):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Si viene de cambio de página, solo mostrar tarjetas
    if trigger_id == 'url' or not trigger_id:
        return "", generar_tarjetas_fiestas()
    
    # Si viene del botón de guardar
    if trigger_id == 'btn-guardar-cambios' and n_clicks and fecha:
        conn = sqlite3.connect('penya_albenc.db')
        cursor = conn.cursor()
        
        try:
            # Convertir listas a strings
            nombres_adultos = ', '.join(adultos_lista) if adultos_lista else ''
            nombres_niños = ', '.join(niños_lista) if niños_lista else ''
            
            # Buscar el ID del registro
            cursor.execute("SELECT id FROM fiestas WHERE fecha = ?", (fecha,))
            result = cursor.fetchone()
            
            if not result:
                return "⚠️ No se encontró el día seleccionado", generar_tarjetas_fiestas()
            
            dia_id = result[0]
            
            # Actualizar campos
            cursor.execute("""
                UPDATE fiestas 
                SET menu = ?, adultos = ?, niños = ?, nombres_adultos = ?, nombres_niños = ? 
                WHERE id = ?
            """, (menu or '', len(adultos_lista), len(niños_lista), nombres_adultos, nombres_niños, dia_id))
            
            conn.commit()
            tarjetas_actualizadas = generar_tarjetas_fiestas()
            
            return f"✅ Día {fecha} actualizado! 🎉 (Adultos: {len(adultos_lista)}, Niños: {len(niños_lista)})", tarjetas_actualizadas
            
        except Exception as e:
            return f"❌ Error actualizando: {str(e)}", generar_tarjetas_fiestas()
        finally:
            conn.close()
    
    # Fallback
    return "", generar_tarjetas_fiestas()

# Página de inicio
def create_home_page():
    # Obtener datos para resumen
    comidas_df = get_data('comidas')
    lista_df = get_data('lista_compra')
    mantenimiento_df = get_data('mantenimiento')
    eventos_df = get_data('eventos')
    
    # Obtener mantenimiento del año actual
    año_actual = datetime.now().year
    mantenimiento_actual = mantenimiento_df[mantenimiento_df['año'] == año_actual]
    
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
        html.H1("Bienvenido a Penya L'Albenc", style={
            "color": "#2E7D32", 
            "margin-bottom": "30px",
            "text-align": "center"  # ← AGREGAR ESTA LÍNEA
        }),
        
        # PRIMERA FILA: MANTENIMIENTO ACTUAL EN GRANDE
        html.Div([
            html.H3("🔧 Mantenimiento del Año", style={"color": "#FF9800", "margin-bottom": "20px", "text-align": "center"}),
            html.Div([
                html.Div([
                    # Logo al lado del título
                    html.Div([
                        html.Img(src="/assets/logo2.png", style={
                            "width": "200px", "height": "200px", "margin-right": "50px", 
                            "border-radius": "20px", "object-fit": "contain",
                            "box-shadow": "0 4px 8px rgba(0,0,0,0.2)"
                        }),
                        html.H2(f"📅 AÑO {año_actual}", style={"color": "#FF9800", "margin": "0", "font-size": "2.5rem"})
                    ], style={"display": "flex", "align-items": "center", "justify-content": "center", "margin-bottom": "20px"}),
                    
                    html.Div([
                        html.H4("🔨 MANTENIMIENTO:", style={"color": "#E65100", "margin": "0 0 10px 0", "font-size": "1.3rem"}),
                        html.P(mantenimiento_actual.iloc[0]['mantenimiento'] if len(mantenimiento_actual) > 0 else "⚠️ Sin datos de mantenimiento", 
                               style={"margin": "0 0 20px 0", "font-size": "1.1rem", "font-weight": "500", "color": "#333"})
                    ]),
                    
                    html.Div([
                        html.H4("🏗️ CADAFALS:", style={"color": "#F57C00", "margin": "0 0 10px 0", "font-size": "1.3rem"}),
                        html.P(mantenimiento_actual.iloc[0]['cadafals'] if len(mantenimiento_actual) > 0 else "⚠️ Sin datos de cadafals", 
                               style={"margin": "0", "font-size": "1.1rem", "font-weight": "500", "color": "#333"})
                    ])
                    
                ], style={
                    "background": "linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%)", 
                    "padding": "40px", "border-radius": "16px",
                    "box-shadow": "0 8px 20px rgba(0,0,0,0.15)", "text-align": "left",
                    "border": "3px solid #FF9800", "width": "100%", "max-width": "800px", "margin": "0 auto",
                    "position": "relative"  # ← AGREGAR ESTO para la segunda opción
                })
            ], style={"display": "flex", "justify-content": "center", "margin": "20px 0"})
        ]),
        
        # SEGUNDA FILA: Resumen con contadores
        html.Div([
            html.H3("📊 Resumen General", style={"color": "#1976D2", "margin": "40px 0 20px 0"}),
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
                    html.P("Lista de compra", style={"margin": "5px 0"})
                ], className="summary-card", style={
                    "background": "linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)", 
                    "padding": "25px", "margin": "10px", "border-radius": "12px",
                    "box-shadow": "0 4px 6px rgba(0,0,0,0.1)", "text-align": "center"
                }),
                
                html.Div([
                    html.H4(f"{len(mantenimiento_df)}", style={"color": "#FF9800", "margin": "0", "font-size": "2rem"}),
                    html.P("Años programados", style={"margin": "5px 0"})
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
        
        # TERCERA FILA: Próximos eventos
        html.Div([
            html.H3("🔥 Próximos Eventos", style={"color": "#1976D2", "margin": "40px 0 20px 0"}),
            html.Div([
                # Mostrar próximos eventos dinámicamente
                html.Div(id="proximos-eventos-container")
            ])
        ], style={"margin-top": "30px"}),
        
        # CUARTA FILA: Información adicional
        html.Div([
            html.H3("ℹ️ Información Adicional", style={"color": "#1976D2", "margin": "40px 0 20px 0"}),
            html.Div([
                # Último item lista
                html.Div([
                    html.H5("🛒 Último Item Lista", style={"color": "#2196F3", "margin-bottom": "10px"}),
                    html.P(f"📅 {ultima_lista.iloc[0]['fecha'] if len(ultima_lista) > 0 else 'Ninguna'}", 
                           style={"margin": "5px 0"}),
                    html.P(f"📦 {ultima_lista.iloc[0]['objeto'] if len(ultima_lista) > 0 else 'N/A'}", 
                           style={"margin": "5px 0"})
                ], style={
                    "background": "#E8F4FD", "padding": "20px", "margin": "10px", 
                    "border-radius": "8px", "border-left": "4px solid #2196F3", "flex": "1"
                }),
                
                # Calendario del mes
                html.Div([
                    html.H5("📅 Calendario del Mes", style={"color": "#4CAF50", "margin-bottom": "10px"}),
                    calendar_table
                ], style={
                    "background": "#F8F9FA", "padding": "20px", "margin": "10px", 
                    "border-radius": "8px", "border-left": "4px solid #4CAF50", "flex": "2"
                }),
            ], style={"display": "flex", "justify-content": "space-around", "flex-wrap": "wrap", "gap": "20px"})
        ])
    ])
          

# Página de comidas (actualizada con selectores de cocineros únicos)
def create_comidas_page():
    comidas_df = get_data('comidas')
    tipos_comida = get_tipos_comida()
    años_disponibles = get_años_disponibles()
    cocineros_options = get_cocineros_options()
    
    # 1. Ordenar el DataFrame por fecha (de más reciente a más antigua)
    comidas_df['fecha'] = pd.to_datetime(comidas_df['fecha'])  # Asegurar que es datetime
    comidas_df = comidas_df.sort_values('fecha', ascending=True)
    
    return html.Div([
        html.H1("🍽️ Gestión de Comidas", style={
            "color": "#2E7D32", 
            "margin-bottom": "20px",
            "fontSize": "24px",
            "textAlign": "center"
        }),
        
        # Tabla de comidas responsive
        html.H3("📋 Lista de Comidas", style={
            "color": "#2E7D32", 
            "margin": "10px 0 8px 0",
            "fontSize": "18px"
        }),
        html.Div(
            dash_table.DataTable(
                id='tabla-comidas',
                data=comidas_df.to_dict('records'),
                columns=[
                    {"name": "🥘 Tipo", "id": "tipo_comida", "type": "text", "editable": True},
                    {"name": "👨‍🍳 Cocineros", "id": "cocineros", "type": "text", "editable": True},
                    {"name": "📅 Fecha", "id": "fecha", "type": "datetime", "editable": True},
                    {"name": "🍽️ Servicio", "id": "tipo_servicio", "type": "text", "editable": True}
                ],
                sort_by=[{"column_id": "fecha", "direction": "asc"}],
                row_deletable=True,
                editable=True,
                style_table={
                    'overflowX': 'auto',
                    'minWidth': '100%',
                    'maxWidth': '100%'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px',
                    'fontFamily': 'Arial, sans-serif',
                    'fontSize': '12px',
                    'minWidth': '80px',
                    'width': '120px',
                    'maxWidth': '200px',
                    'whiteSpace': 'normal',
                    'lineHeight': '15px'
                },
                style_header={
                    'backgroundColor': '#4CAF50',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'fontSize': '13px',
                    'padding': '8px'
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto'
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
                page_size=10,
                page_action='native',
                fixed_rows={'headers': True}
            ),
            style={
                'width': '100%',
                'overflow': 'auto',
                'border': '1px solid #ddd',
                'borderRadius': '8px',
                'marginBottom': '15px'
            }
        ),
        
        # Gestión de cocineros (responsive)
        html.Div([
            html.H3("👨‍🍳 Gestión de Cocineros", style={
                "color": "#1976D2", 
                "margin-bottom": "10px",
                "fontSize": "18px"
            }),
            html.Div([
                dcc.Input(
                    id='nuevo-cocinero-nombre',
                    placeholder="Nombre del cocinero",
                    type='text',
                    style={
                        "padding": "8px", 
                        "width": "100%", 
                        "margin": "5px 0",
                        "borderRadius": "6px",
                        "border": "1px solid #ddd"
                    }
                ),
                html.Button('➕ Agregar Cocinero', id='btn-add-nuevo-cocinero', n_clicks=0,
                    style={
                        "background": "#9C27B0", 
                        "color": "white", 
                        "border": "none",
                        "padding": "10px", 
                        "width": "100%",
                        "borderRadius": "6px", 
                        "margin": "5px 0", 
                        "cursor": "pointer"
                    }
                )
            ], style={"marginBottom": "10px"}),
            html.P("💡 Agrega nuevos cocineros a la lista maestra", 
                style={
                    "color": "#666", 
                    "fontStyle": "italic", 
                    "margin": "5px 0",
                    "fontSize": "12px"
                }
            )
        ], style={
            "background": "#F3E5F5", 
            "padding": "15px", 
            "borderRadius": "8px", 
            "margin": "15px 0"
        }),
        
        # Formulario para agregar comida (responsive)
        html.Div([
            html.H3("➕ Agregar Comida", style={
                "color": "#4CAF50",
                "fontSize": "18px",
                "marginBottom": "10px"
            }),
            html.Div([
                # Fecha
                html.Div([
                    html.Label("📅 Fecha:", style={
                        "fontWeight": "bold", 
                        "marginBottom": "5px",
                        "fontSize": "14px"
                    }),
                    dcc.DatePickerSingle(
                        id='comida-fecha',
                        date=date.today(),
                        display_format='DD/MM/YYYY',
                        style={"width": "100%"}
                    )
                ], style={"margin": "10px 0"}),
                
                # Tipo de servicio
                html.Div([
                    html.Label("🍽️ Servicio:", style={
                        "fontWeight": "bold", 
                        "marginBottom": "5px",
                        "fontSize": "14px"
                    }),
                    dcc.Dropdown(
                        id='comida-servicio',
                        options=[
                            {'label': '🌅 Comida', 'value': 'Comida'},
                            {'label': '🌙 Cena', 'value': 'Cena'},
                            {'label': '🌅🌙 Comida y Cena', 'value': 'Comida y Cena'}
                        ],
                        placeholder="Selecciona servicio",
                        style={"width": "100%"}
                    )
                ], style={"margin": "10px 0"}),
                
                # Tipo de comida
                html.Div([
                    html.Label("🥘 Tipo:", style={
                        "fontWeight": "bold", 
                        "marginBottom": "5px",
                        "fontSize": "14px"
                    }),
                    dcc.Input(
                        id='comida-tipo', 
                        placeholder="Ej: Comida Normal, Sant Antoni...", 
                        type='text',
                        style={
                            "width": "100%", 
                            "padding": "8px",
                            "borderRadius": "6px",
                            "border": "1px solid #ddd"
                        }
                    )
                ], style={"margin": "10px 0"}),
                
                # Cocineros
                html.Div([
                    html.Label("👨‍🍳 Cocineros:", style={
                        "fontWeight": "bold", 
                        "marginBottom": "5px",
                        "fontSize": "14px"
                    }),
                    dcc.Dropdown(
                        id='comida-cocineros-selector',
                        options=cocineros_options,
                        placeholder="Selecciona cocineros",
                        multi=True,
                        style={"width": "100%"}
                    )
                ], style={"margin": "10px 0"}),
                
                # Botón
                html.Button('✅ Agregar Comida', id='btn-add-comida', n_clicks=0,
                    style={
                        "background": "linear-gradient(45deg, #4CAF50, #45a049)", 
                        "color": "white", 
                        "border": "none", 
                        "padding": "12px",
                        "width": "100%",
                        "borderRadius": "8px", 
                        "fontWeight": "bold", 
                        "cursor": "pointer",
                        "margin": "10px 0",
                        "fontSize": "14px"
                    }
                )
            ], style={"padding": "10px 0"})
        ], style={
            "background": "#F8F9FA", 
            "padding": "15px", 
            "borderRadius": "8px", 
            "margin": "15px 0"
        }),
        
        # Panel avanzado (responsive)
        html.Div([
            html.H3("🔄 Gestión Avanzada", style={
                "color": "#1976D2", 
                "marginBottom": "15px",
                "fontSize": "18px"
            }),
            html.P("💡 Modifica cocineros en múltiples comidas", 
                style={
                    "color": "#666", 
                    "fontStyle": "italic", 
                    "marginBottom": "15px",
                    "fontSize": "14px"
                }
            ),
            
            # Filtros
            html.Div([
                html.H5("🎯 Filtros", style={
                    "color": "#9C27B0", 
                    "marginBottom": "10px",
                    "fontSize": "16px"
                }),
                html.Div([
                    html.Div([
                        html.Label("📅 Año:", style={
                            "fontWeight": "bold", 
                            "color": "#9C27B0",
                            "fontSize": "14px"
                        }),
                        dcc.Dropdown(
                            id='filter-año',
                            options=años_disponibles,
                            placeholder="Año",
                            style={"width": "100%"}
                        )
                    ], style={"margin": "10px 0", "width": "100%"}),
                    
                    html.Div([
                        html.Label("🥘 Tipo:", style={
                            "fontWeight": "bold", 
                            "color": "#9C27B0",
                            "fontSize": "14px"
                        }),
                        dcc.Dropdown(
                            id='filter-tipo',
                            options=tipos_comida,
                            placeholder="Tipo de comida",
                            style={"width": "100%"}
                        )
                    ], style={"margin": "10px 0", "width": "100%"})
                ])
            ], style={
                "background": "#F3E5F5", 
                "padding": "15px", 
                "borderRadius": "8px", 
                "margin": "15px 0"
            }),
            
            # Operaciones
            html.Div([
                # Cambiar cocinero
                html.Div([
                    html.H5("🔄 Cambiar Cocinero", style={
                        "color": "#FF9800", 
                        "marginBottom": "10px",
                        "fontSize": "16px"
                    }),
                    html.Div([
                        dcc.Dropdown(
                            id='cambiar-cocinero-antiguo',
                            options=cocineros_options,
                            placeholder="Actual",
                            style={"width": "100%", "margin": "5px 0"}
                        ),
                        dcc.Dropdown(
                            id='cambiar-cocinero-nuevo',
                            options=cocineros_options,
                            placeholder="Nuevo",
                            style={"width": "100%", "margin": "5px 0"}
                        ),
                        html.Button('🔄 Cambiar', id='btn-cambiar-cocinero', n_clicks=0,
                            style={
                                "background": "#FF9800", 
                                "color": "white", 
                                "border": "none",
                                "padding": "10px", 
                                "width": "100%",
                                "borderRadius": "6px", 
                                "margin": "5px 0", 
                                "cursor": "pointer",
                                "fontSize": "14px"
                            }
                        )
                    ])
                ], style={
                    "background": "#FFF3E0", 
                    "padding": "15px", 
                    "borderRadius": "8px", 
                    "margin": "10px 0"
                }),
                
                # Agregar cocinero
                html.Div([
                    html.H5("➕ Agregar Cocinero", style={
                        "color": "#4CAF50", 
                        "marginBottom": "10px",
                        "fontSize": "16px"
                    }),
                    html.Div([
                        dcc.Dropdown(
                            id='agregar-cocinero',
                            options=cocineros_options,
                            placeholder="Selecciona cocinero",
                            style={"width": "100%", "margin": "5px 0"}
                        ),
                        html.Button('➕ Agregar', id='btn-agregar-cocinero', n_clicks=0,
                            style={
                                "background": "#4CAF50", 
                                "color": "white", 
                                "border": "none",
                                "padding": "10px", 
                                "width": "100%",
                                "borderRadius": "6px", 
                                "margin": "5px 0", 
                                "cursor": "pointer",
                                "fontSize": "14px"
                            }
                        )
                    ])
                ], style={
                    "background": "#E8F5E8", 
                    "padding": "15px", 
                    "borderRadius": "8px", 
                    "margin": "10px 0"
                }),
                
                # Eliminar cocinero
                html.Div([
                    html.H5("➖ Eliminar Cocinero", style={
                        "color": "#F44336", 
                        "marginBottom": "10px",
                        "fontSize": "16px"
                    }),
                    html.Div([
                        dcc.Dropdown(
                            id='eliminar-cocinero',
                            options=cocineros_options,
                            placeholder="Selecciona cocinero",
                            style={"width": "100%", "margin": "5px 0"}
                        ),
                        html.Button('➖ Eliminar', id='btn-eliminar-cocinero', n_clicks=0,
                            style={
                                "background": "#F44336", 
                                "color": "white", 
                                "border": "none",
                                "padding": "10px", 
                                "width": "100%",
                                "borderRadius": "6px", 
                                "margin": "5px 0", 
                                "cursor": "pointer",
                                "fontSize": "14px"
                            }
                        )
                    ])
                ], style={
                    "background": "#FFEBEE", 
                    "padding": "15px", 
                    "borderRadius": "8px", 
                    "margin": "10px 0"
                }),
                
                # Intercambio específico
                html.Div([
                    html.H5("🔄 Intercambio Específico", style={
                        "color": "#9C27B0", 
                        "marginBottom": "10px",
                        "fontSize": "16px"
                    }),
                    html.Div([
                        # Año 1
                        html.Div([
                            html.Label("📅 Año 1:", style={
                                "fontWeight": "bold", 
                                "color": "#9C27B0",
                                "fontSize": "14px"
                            }),
                            dcc.Dropdown(
                                id='int-año1',
                                options=años_disponibles,
                                placeholder="Selecciona año",
                                style={"width": "100%", "margin": "5px 0"}
                            )
                        ], style={"margin": "10px 0"}),
                        
                        # Tipo 1
                        html.Div([
                            html.Label("🥘 Tipo 1:", style={
                                "fontWeight": "bold", 
                                "color": "#9C27B0",
                                "fontSize": "14px"
                            }),
                            dcc.Dropdown(
                                id='int-tipo1',
                                options=tipos_comida,
                                placeholder="Selecciona tipo",
                                style={"width": "100%", "margin": "5px 0"}
                            )
                        ], style={"margin": "10px 0"}),
                        
                        # Cocinero 1
                        html.Div([
                            html.Label("👨‍🍳 Cocinero 1:", style={
                                "fontWeight": "bold", 
                                "color": "#9C27B0",
                                "fontSize": "14px"
                            }),
                            dcc.Dropdown(
                                id='int-cocinero1',
                                options=cocineros_options,
                                placeholder="Selecciona cocinero",
                                style={"width": "100%", "margin": "5px 0"}
                            )
                        ], style={"margin": "10px 0"}),
                        
                        # Año 2
                        html.Div([
                            html.Label("📅 Año 2:", style={
                                "fontWeight": "bold", 
                                "color": "#9C27B0",
                                "fontSize": "14px"
                            }),
                            dcc.Dropdown(
                                id='int-año2',
                                options=años_disponibles,
                                placeholder="Selecciona año",
                                style={"width": "100%", "margin": "5px 0"}
                            )
                        ], style={"margin": "10px 0"}),
                        
                        # Tipo 2
                        html.Div([
                            html.Label("🥘 Tipo 2:", style={
                                "fontWeight": "bold", 
                                "color": "#9C27B0",
                                "fontSize": "14px"
                            }),
                            dcc.Dropdown(
                                id='int-tipo2',
                                options=tipos_comida,
                                placeholder="Selecciona tipo",
                                style={"width": "100%", "margin": "5px 0"}
                            )
                        ], style={"margin": "10px 0"}),
                        
                        # Cocinero 2
                        html.Div([
                            html.Label("👨‍🍳 Cocinero 2:", style={
                                "fontWeight": "bold", 
                                "color": "#9C27B0",
                                "fontSize": "14px"
                            }),
                            dcc.Dropdown(
                                id='int-cocinero2',
                                options=cocineros_options,
                                placeholder="Selecciona cocinero",
                                style={"width": "100%", "margin": "5px 0"}
                            )
                        ], style={"margin": "10px 0"}),
                        
                        # Botón de intercambio
                        html.Button('🔄 Intercambiar', id='btn-intercambiar-especifico', n_clicks=0,
                            style={
                                "background": "#9C27B0", 
                                "color": "white", 
                                "border": "none",
                                "padding": "10px", 
                                "width": "100%",
                                "borderRadius": "6px", 
                                "margin": "5px 0", 
                                "cursor": "pointer",
                                "fontSize": "14px"
                            }
                        )
                    ])
                ], style={
                    "background": "#F3E5F5", 
                    "padding": "15px", 
                    "borderRadius": "8px", 
                    "margin": "10px 0"
                }),
            ])
        ], style={
            "background": "#F5F5F5", 
            "padding": "15px", 
            "borderRadius": "8px", 
            "margin": "15px 0"
        }),
        
        # Mensajes
        html.Div(id='comida-output', style={
            "margin": "15px 0", 
            "padding": "10px",
            "fontSize": "14px"
        })
    ], style={
        "padding": "10px",
        "maxWidth": "100%",
        "overflowX": "hidden"
    })

# Página de lista de compra
def create_lista_compra_page():
    lista_df = get_data('lista_compra')
    
    return html.Div([
        html.H1("🛒 Lista de Compra", style={"color": "#2E7D32", "margin-bottom": "20px", "fontSize": "24px"}),
        
        # Tabla de lista con diseño responsive
        html.H3("📋 Lista de Compras", style={"color": "#2E7D32", "margin": "15px 0 10px 0", "fontSize": "18px"}),
        html.Div(
            dash_table.DataTable(
                id='tabla-lista',
                data=lista_df.to_dict('records'),
                columns=[
                    {"name": "📅 Fecha", "id": "fecha", "type": "datetime", "editable": True},
                    {"name": "📦 Objeto", "id": "objeto", "type": "text", "editable": True}
                ],
                row_deletable=True,
                editable=True,
                style_table={
                    'overflowX': 'auto',
                    'minWidth': '100%',
                    'maxWidth': '100%',
                    'marginBottom': '20px'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px',
                    'fontFamily': 'Arial, sans-serif',
                    'minWidth': '80px',
                    'width': '120px',
                    'maxWidth': '200px',
                    'whiteSpace': 'normal',
                    'fontSize': '12px',
                    'lineHeight': '15px'
                },
                style_header={
                    'backgroundColor': '#2196F3',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'fontSize': '13px',
                    'padding': '8px'
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto'
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
                page_size=10,  # Menos filas por página en móvil
                page_action='native',
                fixed_rows={'headers': True}
            ),
            style={
                'width': '100%',
                'overflow': 'auto',
                'border': '1px solid #ddd',
                'borderRadius': '8px',
                'marginBottom': '15px'
            }
        ),
        
        # Formulario para agregar - Adaptado para móvil
        html.Div([
            html.H3("➕ Agregar Nuevo Item", style={"color": "#2196F3", "fontSize": "18px", "marginBottom": "10px"}),
            html.Div([
                # Fecha en su propia fila
                html.Div([
                    html.Label("📅 Fecha:", style={"font-weight": "bold", "margin-bottom": "5px", "fontSize": "14px"}),
                    dcc.DatePickerSingle(
                        id='lista-fecha',
                        date=date.today(),
                        display_format='DD/MM/YYYY',
                        style={"width": "100%", "marginBottom": "10px"}
                    )
                ], style={"width": "100%", "marginBottom": "10px"}),
                
                # Objeto en su propia fila
                html.Div([
                    html.Label("📦 Objeto a Comprar:", style={"font-weight": "bold", "margin-bottom": "5px", "fontSize": "14px"}),
                    dcc.Input(
                        id='lista-objeto', 
                        placeholder="Ej: Tomates, Pan, Aceite...", 
                        type='text',
                        style={"width": "100%", "padding": "8px", "marginBottom": "10px"}
                    )
                ], style={"width": "100%", "marginBottom": "10px"}),
                
                # Botón centrado
                html.Div(
                    html.Button('✅ Agregar Item', id='btn-add-lista', n_clicks=0,
                               style={
                                   "background": "linear-gradient(45deg, #2196F3, #1976D2)", 
                                   "color": "white", 
                                   "border": "none", 
                                   "padding": "10px 20px",
                                   "border-radius": "8px", 
                                   "font-weight": "bold", 
                                   "cursor": "pointer",
                                   "width": "100%",
                                   "fontSize": "14px"
                               }),
                    style={"width": "100%"}
                )
            ], style={"display": "flex", "flexDirection": "column"})  # Cambiado a columna para móvil
        ], style={
            "background": "#F8F9FA", 
            "padding": "15px", 
            "border-radius": "8px", 
            "margin": "15px 0",
            "fontSize": "14px"
        }),
        
        html.Div(id='lista-output', style={
            "margin": "15px 0", 
            "padding": "10px",
            "fontSize": "14px"
        })
    ], style={"padding": "10px"})  # Padding general para el contenedor principal

# Página de mantenimiento
def create_mantenimiento_page():
    mant_df = get_data('mantenimiento')
    
    return html.Div([
        html.H1("🔧 Mantenimiento", style={"color": "#2E7D32", "margin-bottom": "30px"}),
        
        # Tabla de mantenimiento con diseño responsive
        html.H3("📋 Tareas de Mantenimiento", style={"color": "#2E7D32", "margin": "20px 0 15px 0"}),
        html.Div(
            dash_table.DataTable(
                id='tabla-mant',
                data=mant_df.to_dict('records'),
                columns=[
                    {"name": "📅 Año", "id": "año", "type": "numeric", "editable": True},
                    {"name": "🔨 Mantenimiento", "id": "mantenimiento", "type": "text", "editable": True},
                    {"name": "🏗️ Cadafals", "id": "cadafals", "type": "text", "editable": True}
                ],
                row_deletable=True,
                editable=True,
                style_table={
                    'overflowX': 'auto',
                    'minWidth': '100%',
                    'maxWidth': '100%'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '8px',
                    'fontFamily': 'Arial, sans-serif',
                    'minWidth': '100px',
                    'width': '150px',
                    'maxWidth': '200px',
                    'whiteSpace': 'normal',
                    'fontSize': '12px'
                },
                style_header={
                    'backgroundColor': '#FF9800',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'fontSize': '12px'
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto'
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
                page_size=15,
                page_action='native',
                fixed_rows={'headers': True}
            ),
            style={
                'width': '100%',
                'overflow': 'auto',
                'marginBottom': '20px',
                'border': '1px solid #ddd',
                'borderRadius': '8px'
            }
        ),
        
        # Formulario para agregar (se mantiene igual)
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
            ], style={"display": "flex", "flex-wrap": "wrap", "align-items": "end", "gap": "10px"})
        ], style={"background": "#F8F9FA", "padding": "20px", "border-radius": "12px", "margin": "20px 0"}),
        
        html.Div(id='mant-output', style={"margin": "20px 0", "padding": "10px"})
    ])

def create_fiestas_page():
    return html.Div([
        html.H1("🎉 Fiestas 2025 - Vilafranca", style={"color": "#2E7D32", "margin-bottom": "30px"}),
        
        # Mostrar etiquetas por día
        html.Div(id='tarjetas-fiestas'),
        
        # Formulario de edición MEJORADO
        html.Div([
            html.H3("✏️ Editar Día", style={"color": "#9C27B0", "margin-bottom": "20px"}),
            
            html.Div([
                html.Div([
                    html.Label("📅 Seleccionar Día:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Dropdown(
                        id='fiesta-dia-selector',
                        options=get_dias_fiestas_con_semana(),
                        placeholder="Selecciona el día a editar",
                        style={"width": "100%"}
                    ),
                ], style={"margin": "10px", "flex": "1"}),
            ]),
            
            html.Div([
                html.Div([
                    html.Label("🍽️ Menú:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Textarea(
                        id='fiesta-menu',
                        placeholder="Describe el menú del día...",
                        style={"width": "100%", "height": "80px", "padding": "8px"}
                    )
                ], style={"margin": "10px", "flex": "1"}),
            ]),
            
            # SECCIÓN DE COMENSALES - Nueva versión con listas visuales
            html.Div([
                # Adultos
                html.Div([
                    html.Div([
                        html.H5("👥 Adultos", style={"color": "#9C27B0", "margin": "0"}),
                        html.Span(id='contador-adultos-nuevo', children="(0)", 
                                style={"color": "#9C27B0", "font-weight": "bold", "margin-left": "10px"})
                    ], style={"display": "flex", "align-items": "center", "margin-bottom": "10px"}),
                    
                    html.Div(id='lista-adultos-visual', children=[], 
                            style={"min-height": "100px", "border": "2px dashed #ddd", 
                                "padding": "15px", "border-radius": "8px", "margin-bottom": "10px",
                                "background": "#fafafa"}),
                    
                    html.Div([
                        dcc.Input(id='input-nuevo-adulto', placeholder="Nombre del adulto...", 
                                style={"flex": "1", "padding": "8px", "border-radius": "6px", "border": "1px solid #ddd"}),
                        html.Button("➕ Agregar", id='btn-add-adulto', 
                                style={
                                    "background": "#9C27B0", "color": "white", "border": "none",
                                    "padding": "8px 15px", "margin-left": "10px", "border-radius": "6px",
                                    "cursor": "pointer", "font-weight": "bold"
                                })
                    ], style={"display": "flex", "align-items": "center"})
                ], style={"margin": "10px", "flex": "1"}),
                
                # Niños
                html.Div([
                    html.Div([
                        html.H5("👶 Niños", style={"color": "#FF9800", "margin": "0"}),
                        html.Span(id='contador-niños-nuevo', children="(0)", 
                                style={"color": "#FF9800", "font-weight": "bold", "margin-left": "10px"})
                    ], style={"display": "flex", "align-items": "center", "margin-bottom": "10px"}),
                    
                    html.Div(id='lista-niños-visual', children=[], 
                            style={"min-height": "100px", "border": "2px dashed #ddd", 
                                "padding": "15px", "border-radius": "8px", "margin-bottom": "10px",
                                "background": "#fafafa"}),
                    
                    html.Div([
                        dcc.Input(id='input-nuevo-niño', placeholder="Nombre del niño...", 
                                style={"flex": "1", "padding": "8px", "border-radius": "6px", "border": "1px solid #ddd"}),
                        html.Button("➕ Agregar", id='btn-add-niño', 
                                style={
                                    "background": "#FF9800", "color": "white", "border": "none",
                                    "padding": "8px 15px", "margin-left": "10px", "border-radius": "6px",
                                    "cursor": "pointer", "font-weight": "bold"
                                })
                    ], style={"display": "flex", "align-items": "center"})
                ], style={"margin": "10px", "flex": "1"}),
            ], style={"display": "flex", "gap": "20px", "margin": "20px 0"}),

            # Stores para manejar el estado
            dcc.Store(id='store-comensales-adultos', data=[]),
            dcc.Store(id='store-comensales-niños', data=[]),
            dcc.Store(id='store-menu-actual', data=""),
            dcc.Store(id='store-dia-seleccionado', data=""),
            dcc.ConfirmDialog(
                id='confirm-guardar',
                message='¿Estás seguro de que quieres guardar los cambios?',
            ),

            # Botones
            html.Div([
                html.Button('💾 Guardar Cambios', id='btn-guardar-cambios', n_clicks=0,
                        style={
                            "background": "linear-gradient(45deg, #4CAF50, #45a049)", 
                            "color": "white", "border": "none", "padding": "12px 24px",
                            "border-radius": "8px", "font-weight": "bold", "cursor": "pointer",
                            "margin": "15px 10px"
                        })
            ]),
            
            html.Div(id='fiesta-output', style={"margin": "20px 0", "padding": "10px"})
            
        ], style={"margin-top": "30px", "padding": "25px", "background": "#F8F9FA", "border-radius": "12px"})
    ])

def limpiar_datos_anteriores():
    """Limpiar datos residuales y resetear con datos limpios"""
    conn = sqlite3.connect('penya_albenc.db')
    cursor = conn.cursor()
    
    # Limpiar tablas principales
    cursor.execute("DELETE FROM comidas")
    cursor.execute("DELETE FROM eventos") 
    cursor.execute("DELETE FROM fiestas")
    
    conn.commit()
    conn.close()
    print("🧹 Datos anteriores limpiados")

def create_debug_page():
    """Página temporal para debuggear la base de datos"""
    try:
        # Obtener datos de fiestas
        fiestas_df = get_data('fiestas')
        
        # Verificar estructura de tabla
        conn = sqlite3.connect('penya_albenc.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(fiestas)")
        columnas = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM fiestas")
        total_filas = cursor.fetchone()[0]
        conn.close()
        
        return html.Div([
            html.H1("🐛 Debug Base de Datos", style={"color": "#F44336"}),
            
            html.H3("📊 Estructura de tabla fiestas:"),
            html.Pre(str(columnas), style={"background": "#f5f5f5", "padding": "10px"}),
            
            html.H3(f"📈 Total filas: {total_filas}"),
            
            html.H3("📋 Datos completos:"),
            dash_table.DataTable(
                data=fiestas_df.to_dict('records'),
                columns=[{"name": col, "id": col} for col in fiestas_df.columns],
                style_table={'overflowX': 'auto'},
                page_size=20
            ),
            
            html.H3("🔍 Datos específicos agosto:"),
            html.Pre(str(fiestas_df[
                (fiestas_df['fecha'] >= '2025-08-08') & 
                (fiestas_df['fecha'] <= '2025-08-17')
            ].to_dict('records')), style={"background": "#f5f5f5", "padding": "10px", "white-space": "pre-wrap"})
        ])
        
    except Exception as e:
        return html.Div([
            html.H1("❌ Error en Debug"),
            html.P(f"Error: {str(e)}")
        ])

# Callbacks para comidas (actualizado con selectores únicos)
@app.callback(
    [Output('tabla-comidas', 'data'), Output('comida-output', 'children')],
    [Input('btn-add-comida', 'n_clicks'), 
     Input('btn-cambiar-cocinero', 'n_clicks'),
     Input('btn-agregar-cocinero', 'n_clicks'),
     Input('btn-eliminar-cocinero', 'n_clicks'),
     Input('btn-intercambiar-especifico', 'n_clicks'),
     Input('tabla-comidas', 'data_previous'),
     Input('tabla-comidas', 'data')],
    [State('comida-fecha', 'date'), State('comida-servicio', 'value'),
     State('comida-tipo', 'value'), State('comida-cocineros-selector', 'value'),
     State('filter-año', 'value'), State('filter-tipo', 'value'),
     State('cambiar-cocinero-antiguo', 'value'), State('cambiar-cocinero-nuevo', 'value'),
     State('agregar-cocinero', 'value'), State('eliminar-cocinero', 'value'),
     State('int-año1', 'value'), State('int-tipo1', 'value'), State('int-cocinero1', 'value'),
     State('int-año2', 'value'), State('int-tipo2', 'value'), State('int-cocinero2', 'value')],
    prevent_initial_call=True
)
def update_comidas_con_selectores(n_add, n_cambiar, n_agregar, n_eliminar, n_intercambio,
                                 previous_data, current_data, fecha, servicio, tipo, cocineros_lista, 
                                 filter_año, filter_tipo, cocinero_antiguo, cocinero_nuevo,
                                 nuevo_cocinero, cocinero_eliminar,
                                 int_año1, int_tipo1, int_cocinero1, int_año2, int_tipo2, int_cocinero2):
    ctx = callback_context
    
    if not ctx.triggered:
        try:
            return get_data('comidas').to_dict('records'), ""
        except:
            return [], ""
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Agregar nueva comida (CON SELECTOR)
    if trigger_id == 'btn-add-comida' and n_add > 0:
        if fecha and servicio and tipo and cocineros_lista:
            # Convertir lista de cocineros a string separado por comas
            cocineros_str = ', '.join(cocineros_lista)
            add_data('comidas', (fecha, servicio, tipo, cocineros_str))
            add_data('eventos', (fecha, tipo, servicio))
            return get_data('comidas').to_dict('records'), f"✅ Comida agregada exitosamente! 🎉"
        else:
            return get_data('comidas').to_dict('records'), "⚠️ Por favor completa todos los campos."
    
    # Cambiar cocinero en año + tipo (CON SELECTOR)
    elif trigger_id == 'btn-cambiar-cocinero' and n_cambiar > 0:
        if filter_año and filter_tipo and cocinero_antiguo and cocinero_nuevo:
            resultado = cambiar_cocinero_en_año_tipo(filter_año, filter_tipo, cocinero_antiguo, cocinero_nuevo)
            return get_data('comidas').to_dict('records'), f"🔄 {resultado}"
        else:
            return get_data('comidas').to_dict('records'), "⚠️ Selecciona año, tipo y ambos cocineros."
    
    # Agregar cocinero en año + tipo (CON SELECTOR)
    elif trigger_id == 'btn-agregar-cocinero' and n_agregar > 0:
        if filter_año and filter_tipo and nuevo_cocinero:
            resultado = agregar_cocinero_en_año_tipo(filter_año, filter_tipo, nuevo_cocinero)
            return get_data('comidas').to_dict('records'), f"➕ {resultado}"
        else:
            return get_data('comidas').to_dict('records'), "⚠️ Selecciona año, tipo y cocinero."
    
    # Eliminar cocinero en año + tipo (CON SELECTOR)
    elif trigger_id == 'btn-eliminar-cocinero' and n_eliminar > 0:
        if filter_año and filter_tipo and cocinero_eliminar:
            resultado = eliminar_cocinero_en_año_tipo(filter_año, filter_tipo, cocinero_eliminar)
            return get_data('comidas').to_dict('records'), f"➖ {resultado}"
        else:
            return get_data('comidas').to_dict('records'), "⚠️ Selecciona año, tipo y cocinero."
    
    # NUEVO: Intercambio específico entre diferentes grupos
    elif trigger_id == 'btn-intercambiar-especifico' and n_intercambio > 0:
        if int_año1 and int_tipo1 and int_cocinero1 and int_año2 and int_tipo2 and int_cocinero2:
            resultado = intercambiar_cocineros_especifico(
                int_año1, int_tipo1, int_cocinero1,
                int_año2, int_tipo2, int_cocinero2
            )
            return get_data('comidas').to_dict('records'), f"🔄 {resultado}"
        else:
            return get_data('comidas').to_dict('records'), "⚠️ Completa todos los campos para el intercambio específico."
    
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

# Callback para actualizar opciones dinámicamente
@app.callback(
    [Output('filter-tipo', 'options'),
     Output('int-tipo1', 'options'),
     Output('int-tipo2', 'options')],
    [Input('tabla-comidas', 'data')],
    prevent_initial_call=True
)
def update_filter_options(data):
    tipos = get_tipos_comida()
    return tipos, tipos, tipos

# Callbacks para lista de compra (sin cambios, solo protección)
@app.callback(
    [Output('tabla-lista', 'data'), Output('lista-output', 'children')],
    [Input('btn-add-lista', 'n_clicks'), 
     Input('tabla-lista', 'data_previous'),
     Input('tabla-lista', 'data')],
    [State('lista-fecha', 'date'), State('lista-objeto', 'value')],
    prevent_initial_call=True
)
def update_lista_protegido(n_clicks, previous_data, current_data, fecha, objeto):
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
            for i, (prev_row, curr_row) in enumerate(zip(previous_data, current_data)):
                for key in prev_row.keys():
                    if prev_row[key] != curr_row[key]:
                        update_data('lista_compra', curr_row['id'], key, curr_row[key])
                        return get_data('lista_compra').to_dict('records'), f"✏️ Campo '{key}' actualizado!"
    
    try:
        return get_data('lista_compra').to_dict('records'), ""
    except:
        return [], ""

# Callbacks para mantenimiento (sin cambios, solo protección)
@app.callback(
    [Output('tabla-mant', 'data'), Output('mant-output', 'children')],
    [Input('btn-add-mant', 'n_clicks'), 
     Input('tabla-mant', 'data_previous'),
     Input('tabla-mant', 'data')],
    [State('mant-año', 'value'), State('mant-mantenimiento', 'value'),
     State('mant-cadafals', 'value')],
    prevent_initial_call=True
)
def update_mant_protegido(n_clicks, previous_data, current_data, año, mantenimiento, cadafals):
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
            for i, (prev_row, curr_row) in enumerate(zip(previous_data, current_data)):
                for key in prev_row.keys():
                    if prev_row[key] != curr_row[key]:
                        update_data('mantenimiento', curr_row['id'], key, curr_row[key])
                        return get_data('mantenimiento').to_dict('records'), f"✏️ Campo '{key}' actualizado!"
    
    try:
        return get_data('mantenimiento').to_dict('records'), ""
    except:
        return [], ""

# Callback para mostrar confirmación y guardar
@app.callback(
    [Output('confirm-guardar', 'displayed'),
     Output('fiesta-output', 'children', allow_duplicate=True),
     Output('tarjetas-fiestas', 'children', allow_duplicate=True)],
    [Input('btn-guardar-cambios', 'n_clicks'),
     Input('confirm-guardar', 'submit_n_clicks'),
     Input('url', 'pathname')],
    [State('fiesta-dia-selector', 'value'),
     State('fiesta-menu', 'value'),
     State('store-comensales-adultos', 'data'),
     State('store-comensales-niños', 'data')],
    prevent_initial_call=True
)
def manejar_guardar_con_confirmacion(n_clicks_guardar, n_clicks_confirm, pathname, fecha, menu, adultos_lista, niños_lista):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Si viene de cambio de página, solo mostrar tarjetas
    if trigger_id == 'url':
        return False, "", generar_tarjetas_fiestas()
    
    # Si se hizo clic en "Guardar Cambios", mostrar confirmación
    if trigger_id == 'btn-guardar-cambios' and n_clicks_guardar:
        return True, "", generar_tarjetas_fiestas()  # Mostrar diálogo
    
    # Si se confirmó el guardado
    if trigger_id == 'confirm-guardar' and n_clicks_confirm and fecha:
        conn = sqlite3.connect('penya_albenc.db')
        cursor = conn.cursor()
        
        try:
            # Convertir listas a strings
            nombres_adultos = ', '.join(adultos_lista) if adultos_lista else ''
            nombres_niños = ', '.join(niños_lista) if niños_lista else ''
            
            # Buscar el ID del registro
            cursor.execute("SELECT id FROM fiestas WHERE fecha = ?", (fecha,))
            result = cursor.fetchone()
            
            if not result:
                return False, "⚠️ No se encontró el día seleccionado", generar_tarjetas_fiestas()
            
            dia_id = result[0]
            
            # Actualizar campos
            cursor.execute("""
                UPDATE fiestas 
                SET menu = ?, adultos = ?, niños = ?, nombres_adultos = ?, nombres_niños = ? 
                WHERE id = ?
            """, (menu or '', len(adultos_lista), len(niños_lista), nombres_adultos, nombres_niños, dia_id))
            
            conn.commit()
            tarjetas_actualizadas = generar_tarjetas_fiestas()
            
            return False, f"✅ Día {fecha} guardado exitosamente! 🎉 (Adultos: {len(adultos_lista)}, Niños: {len(niños_lista)})", tarjetas_actualizadas
            
        except Exception as e:
            return False, f"❌ Error guardando: {str(e)}", generar_tarjetas_fiestas()
        finally:
            conn.close()
    
    # Fallback
    return False, "", generar_tarjetas_fiestas()

@app.callback(
    Output('proximos-eventos-container', 'children'),
    [Input('url', 'pathname')]
)
def update_proximos_eventos(pathname):
    if pathname != '/':
        return []
    
    proximos_df = get_proximos_eventos(5)
    
    if len(proximos_df) == 0:
        return [html.P("No hay eventos próximos", style={"text-align": "center", "color": "#666"})]
    
    eventos_cards = []
    for _, evento in proximos_df.iterrows():
        # Formatear fecha a D-M-A
        try:
            from datetime import datetime
            fecha_obj = datetime.strptime(evento['fecha'], '%Y-%m-%d')
            fecha_formateada = fecha_obj.strftime('%d-%m-%Y')
        except:
            fecha_formateada = evento['fecha']
        
        card = html.Div([
            html.H5(f"🎉 {evento['tipo_comida']}", style={"color": "#FF5722", "margin-bottom": "8px"}),
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

# Inicializar la base de datos y cargar datos
init_db()  # Primero crear tablas si no existen
migrate_fiestas_table()  # Luego migrar columnas faltantes
update_mantenimiento_data()  # Cargar datos de mantenimiento <-- AÑADIR ESTO
load_eventos_completos()  # Después cargar datos principales
load_fiestas_agosto_2025()  # Finalmente datos específicos de fiestas

# AGREGAR ESTA LÍNEA ⬇️
migrate_fiestas_table()

# Ejecutar limpieza automática al iniciar
print("🚀 Iniciando aplicación Penya L'Albenc...")
resultado_limpieza = limpiar_eventos_antiguos()
print(f"🧹 {resultado_limpieza}")

# Forzar migración de columnas faltantes
print("🔧 Verificando estructura de tabla fiestas...")
migrate_fiestas_table()

# Verificar que las columnas existen
conn = sqlite3.connect('penya_albenc.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(fiestas)")
columnas = [col[1] for col in cursor.fetchall()]
print(f"📊 Columnas en fiestas: {columnas}")
conn.close()

load_fiestas_agosto_2025()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Servidor iniciado en puerto {port}")
    print("📊 Base de datos inicializada correctamente")
    print("✨ ¡Aplicación lista para usar!")
    print("🧹 Limpiando datos anteriores...")
    limpiar_datos_anteriores()  # ← AGREGAR ESTO
    load_eventos_completos()
    load_fiestas_agosto_2025()

    
    app.run_server(debug=debug, host='0.0.0.0', port=port)