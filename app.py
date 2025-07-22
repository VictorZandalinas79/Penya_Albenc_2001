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
        ('2025-08-08', 'Juan, Pedro, María', '', 0, '', 0, '', '20:00-Pregón|21:30-Verbena'),
        ('2025-08-09', 'Ana, Luis, Carlos', '', 0, '', 0, '', '19:00-Pasacalles|22:00-Concierto'),
        ('2025-08-10', 'Miguel, Sofia, David', '', 0, '', 0, '', '18:00-Misa|20:00-Cena'),
        ('2025-08-11', 'Laura, Javier, Rosa', '', 0, '', 0, '', '19:30-Teatro|22:30-Baile'),
        ('2025-08-12', 'Antonio, Elena, Pablo', '', 0, '', 0, '', '20:00-Fuegos artificiales'),
        ('2025-08-13', 'Carmen, Fernando, Lucia', '', 0, '', 0, '', '19:00-Concursos|21:00-Música'),
        ('2025-08-14', 'Roberto, Isabel, Mario', '', 0, '', 0, '', '18:30-Procesión|22:00-Verbena'),
        ('2025-08-15', 'Beatriz, Raúl, Ana', '', 0, '', 0, '', '19:00-Misa Mayor|21:30-Gran Baile'),
        ('2025-08-16', 'Diego, Cristina, José', '', 0, '', 0, '', '20:00-Actuaciones|23:00-Fiesta'),
        ('2025-08-17', 'María, Carlos, Pilar', '', 0, '', 0, '', '18:00-Clausura|21:00-Cena final'),
    ]
    
    for data in fiestas_data:
        cursor.execute("INSERT INTO fiestas (fecha, cocineros, menu, adultos, nombres_adultos, niños, nombres_niños, programa) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data)
    
    conn.commit()
    conn.close()

def generar_tarjetas_fiestas():
    """Función auxiliar para generar las tarjetas de fiestas"""
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
            # Formatear fecha
            try:
                from datetime import datetime
                fecha_obj = datetime.strptime(dia['fecha'], '%Y-%m-%d')
                fecha_formateada = fecha_obj.strftime('%d de agosto')
            except:
                fecha_formateada = dia['fecha']
            
            # Procesar programa (split por |)
            eventos = dia['programa'].split('|') if dia['programa'] else ['Sin programa']
            
            # Procesar nombres adultos y niños (con verificación de campo)
            nombres_adultos = dia.get('nombres_adultos', '') or 'Sin nombres'
            nombres_niños = dia.get('nombres_niños', '') or 'Sin nombres'
            
            tarjeta = html.Div([
                html.H4(f"📅 {fecha_formateada}", style={"color": "#FF5722", "margin-bottom": "15px", "text-align": "center"}),
                
                html.Div([
                    html.H6("👨‍🍳 Cocineros:", style={"color": "#4CAF50", "margin-bottom": "5px"}),
                    html.P(dia['cocineros'], style={"margin": "0 0 10px 0", "font-weight": "bold"})
                ]),
                
                html.Div([
                    html.H6("🍽️ Menú:", style={"color": "#2196F3", "margin-bottom": "5px"}),
                    html.P(dia['menu'] or 'Sin menú definido', style={"margin": "0 0 10px 0", "font-style": "italic" if not dia['menu'] else "normal"})
                ]),
                
                html.Div([
                    html.H6("👥 Adultos:", style={"color": "#9C27B0", "margin-bottom": "5px"}),
                    html.P(f"Total: {dia['adultos']}", style={"margin": "0 0 5px 0", "font-weight": "bold"}),
                    html.P(f"Nombres: {nombres_adultos}", style={"margin": "0 0 10px 0", "font-size": "0.9rem", "color": "#666"})
                ]),
                
                html.Div([
                    html.H6("👶 Niños:", style={"color": "#FF9800", "margin-bottom": "5px"}),
                    html.P(f"Total: {dia['niños']}", style={"margin": "0 0 5px 0", "font-weight": "bold"}),
                    html.P(f"Nombres: {nombres_niños}", style={"margin": "0 0 10px 0", "font-size": "0.9rem", "color": "#666"})
                ]),
                
                html.Div([
                    html.H6("🎪 Programa:", style={"color": "#795548", "margin-bottom": "5px"}),
                    html.Ul([
                        html.Li(evento.strip(), style={"margin": "2px 0"}) 
                        for evento in eventos
                    ], style={"margin": "0", "padding-left": "20px"})
                ])
            ], style={
                "border": "2px solid #E0E0E0", 
                "margin": "15px", 
                "padding": "20px", 
                "border-radius": "12px",
                "background": "linear-gradient(135deg, #FFFDE7 0%, #FFF9C4 100%)", 
                "box-shadow": "0 4px 8px rgba(0,0,0,0.1)",
                "flex": "1",
                "min-width": "320px",
                "max-width": "400px"
            })
            tarjetas.append(tarjeta)
        
        return html.Div(tarjetas, style={"display": "flex", "flex-wrap": "wrap", "justify-content": "center"})
        
    except Exception as e:
        print(f"Error generando tarjetas: {e}")
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
        html.Img(
            src="/assets/logo.png",
            style={
                "width": "80px", 
                "height": "80px", 
                "margin": "0 auto 15px auto", 
                "display": "block",
                "border-radius": "10px",
                "object-fit": "contain"
            }
        ),
        html.H2("Penya L'Albenc", 
            style={"font-size": "1.6rem", "margin-bottom": "10px", "text-align": "center"}),
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
    elif pathname == "/debug":  # ← AGREGAR ESTO
        return create_debug_page()
    else:
        return create_home_page()


# Callback para cargar datos del día seleccionado (CORREGIDO)
@app.callback(
    [Output('fiesta-menu', 'value'),
     Output('fiesta-adultos', 'value'),
     Output('fiesta-niños', 'value'),
     Output('fiesta-nombres-adultos', 'value'),
     Output('fiesta-nombres-niños', 'value')],
    [Input('btn-load-fiesta', 'n_clicks')],
    [State('fiesta-dia-selector', 'value')],
    prevent_initial_call=True
)
def cargar_datos_fiesta(n_clicks, fecha_seleccionada):
    if not n_clicks or not fecha_seleccionada:
        return "", None, None, "", ""
    
    try:
        fiestas_df = get_data('fiestas')
        dia_data = fiestas_df[fiestas_df['fecha'] == fecha_seleccionada]
        
        if len(dia_data) == 0:
            return "", None, None, "", ""
        
        dia = dia_data.iloc[0]
        return (
            dia.get('menu', '') or '',
            dia.get('adultos', 0) or 0,
            dia.get('niños', 0) or 0,
            dia.get('nombres_adultos', '') or '',
            dia.get('nombres_niños', '') or ''
        )
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return "", None, None, "", ""

# Callback para actualizar día (CON LOGS DETALLADOS)
@app.callback(
    [Output('fiesta-output', 'children'),
     Output('tarjetas-fiestas', 'children')],
    [Input('btn-update-fiesta', 'n_clicks'),
     Input('url', 'pathname')],  # ← AGREGAR ESTO
    [State('fiesta-dia-selector', 'value'),
     State('fiesta-menu', 'value'),
     State('fiesta-adultos', 'value'),
     State('fiesta-niños', 'value'),
     State('fiesta-nombres-adultos', 'value'),
     State('fiesta-nombres-niños', 'value')],
    prevent_initial_call=True
)
def actualizar_y_mostrar_fiestas(n_clicks, pathname, fecha, menu, adultos, niños, nombres_adultos, nombres_niños):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Si viene de cambio de página, solo mostrar tarjetas
    if trigger_id == 'url' or not trigger_id:
        if pathname != '/fiestas':
            return "", []
        return "", generar_tarjetas_fiestas()
    
    # Si viene del botón de actualizar
    if trigger_id == 'btn-update-fiesta' and n_clicks and fecha:
        print(f"🔍 CALLBACK LLAMADO: n_clicks={n_clicks}, fecha={fecha}")
        
        try:
            print(f"🔍 DATOS A ACTUALIZAR:")
            print(f"  fecha={fecha}")
            print(f"  menu='{menu}'")
            print(f"  adultos={adultos}")
            print(f"  niños={niños}")
            print(f"  nombres_adultos='{nombres_adultos}'")
            print(f"  nombres_niños='{nombres_niños}'")
            
            # Buscar el ID del registro
            fiestas_df = get_data('fiestas')
            print(f"🔍 Total filas en DB: {len(fiestas_df)}")
            
            dia_data = fiestas_df[fiestas_df['fecha'] == fecha]
            print(f"🔍 Filas encontradas para {fecha}: {len(dia_data)}")
            
            if len(dia_data) == 0:
                print("❌ No se encontró el día seleccionado")
                return "⚠️ No se encontró el día seleccionado", generar_tarjetas_fiestas()
            
            dia_id = dia_data.iloc[0]['id']
            print(f"🔍 ID encontrado: {dia_id}")
            # TEMPORAL - verificar si las columnas existen
            cursor.execute("SELECT nombres_adultos, nombres_niños FROM fiestas WHERE id = ?", (dia_id,))
            verificacion = cursor.fetchone()
            print(f"🔍 COLUMNAS EXISTEN: {verificacion}")
            print(f"🔍 Datos actuales: {dia_data.iloc[0].to_dict()}")
            
            # Actualizar campo por campo con verificación
            print("🔧 Actualizando campos...")
            
            update_data('fiestas', dia_id, 'menu', menu or '')
            update_data('fiestas', dia_id, 'adultos', adultos or 0)
            update_data('fiestas', dia_id, 'niños', niños or 0)
            update_data('fiestas', dia_id, 'nombres_adultos', nombres_adultos or '')
            update_data('fiestas', dia_id, 'nombres_niños', nombres_niños or '')
            print("✅ Todos los campos actualizados")
            
            # Verificar que se actualizó
            fiestas_verificacion = get_data('fiestas')
            dia_actualizado = fiestas_verificacion[fiestas_verificacion['fecha'] == fecha].iloc[0]
            print(f"🔍 DATOS DESPUÉS DE UPDATE: {dia_actualizado.to_dict()}")
            
            # REGENERAR TARJETAS INMEDIATAMENTE
            tarjetas_actualizadas = generar_tarjetas_fiestas()
            print("✅ Tarjetas regeneradas")
            
            return f"✅ Día {fecha} actualizado exitosamente! 🎉", tarjetas_actualizadas
            
        except Exception as e:
            print(f"❌ ERROR GENERAL: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"❌ Error actualizando: {str(e)}", generar_tarjetas_fiestas()
    
    # Fallback - mostrar tarjetas
    return "", generar_tarjetas_fiestas()

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
        
        # Próximos eventos (en lugar de últimas actividades)
        html.Div([
            html.H3("🔥 Próximos Eventos", style={"color": "#1976D2", "margin": "30px 0 20px 0"}),
            html.Div([
                # Mostrar próximos eventos dinámicamente
                html.Div(id="proximos-eventos-container")
            ])
        ], style={"margin-top": "30px"}),
                
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
                
                # Referencia rápida al mantenimiento
                html.Div([
                    html.H5("🔧 Mantenimiento Actual", style={"color": "#FF9800", "margin-bottom": "10px"}),
                    html.P(f"📅 Año {datetime.now().year}", style={"margin": "5px 0"}),
                    html.P("👀 Ver detalles abajo", style={"margin": "5px 0", "font-size": "0.9rem", "font-style": "italic"})
                ], style={
                    "background": "#FFF8E1", "padding": "20px", "margin": "10px", 
                    "border-radius": "8px", "border-left": "4px solid #FF9800"
                }),
                ], style={"display": "flex", "justify-content": "space-around", "flex-wrap": "wrap"}),
          

# Página de comidas (actualizada con selectores de cocineros únicos)
def create_comidas_page():
    comidas_df = get_data('comidas')
    tipos_comida = get_tipos_comida()
    años_disponibles = get_años_disponibles()
    cocineros_options = get_cocineros_options()
    
    return html.Div([
        html.H1("🍽️ Gestión de Comidas", style={"color": "#2E7D32", "margin-bottom": "30px"}),
        
        # Tabla de comidas PRIMERO
        html.H3("📋 Lista de Comidas", style={"color": "#2E7D32", "margin": "20px 0 15px 0"}),
        dash_table.DataTable(
            id='tabla-comidas',
            data=comidas_df.to_dict('records'),
            columns=[
                {"name": "🆔 ID", "id": "id", "type": "numeric", "editable": False},
                {"name": "📅 Fecha", "id": "fecha", "type": "datetime", "editable": True,
                "format": {"specifier": "%d-%m-%Y"}},
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
        
        # Gestión de cocineros únicos
        html.Div([
            html.H3("👨‍🍳 Gestión de Cocineros", style={"color": "#1976D2", "margin-bottom": "15px"}),
            html.Div([
                dcc.Input(
                    id='nuevo-cocinero-nombre',
                    placeholder="Nombre del nuevo cocinero",
                    type='text',
                    style={"padding": "8px", "width": "250px", "margin": "5px"}
                ),
                html.Button('➕ Agregar Cocinero', id='btn-add-nuevo-cocinero', n_clicks=0,
                           style={
                               "background": "#9C27B0", "color": "white", "border": "none",
                               "padding": "8px 16px", "border-radius": "6px", "margin": "5px", "cursor": "pointer"
                           })
            ], style={"display": "flex", "align-items": "center", "gap": "5px"}),
            html.P("💡 Agrega nuevos cocineros a la lista maestra para usarlos en los selectores", 
                   style={"color": "#666", "font-style": "italic", "margin": "10px 0"})
        ], style={"background": "#F3E5F5", "padding": "15px", "border-radius": "8px", "margin": "15px 0"}),
        
        # Formulario para agregar comida (CON SELECTORES)
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
                    dcc.Dropdown(
                        id='comida-cocineros-selector',
                        options=cocineros_options,
                        placeholder="Selecciona cocineros (múltiple)",
                        multi=True,
                        style={"width": "100%"}
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
        
        # Panel avanzado de gestión de cocineros (MEJORADO CON SELECTORES)
        html.Div([
            html.H3("🔄 Gestión Avanzada de Cocineros", style={"color": "#1976D2", "margin-bottom": "20px"}),
            html.P("💡 Selecciona año y tipo de comida para modificar cocineros en TODAS las comidas de esa categoría", 
                   style={"color": "#666", "font-style": "italic", "margin-bottom": "20px"}),
            
            # Filtros principales
            html.Div([
                html.H5("🎯 Seleccionar Comidas a Modificar", style={"color": "#9C27B0", "margin-bottom": "15px"}),
                html.Div([
                    html.Div([
                        html.Label("📅 Año:", style={"font-weight": "bold", "color": "#9C27B0"}),
                        dcc.Dropdown(
                            id='filter-año',
                            options=años_disponibles,
                            placeholder="Selecciona el año",
                            style={"width": "150px"}
                        )
                    ], style={"margin": "10px"}),
                    
                    html.Div([
                        html.Label("🥘 Tipo de Comida:", style={"font-weight": "bold", "color": "#9C27B0"}),
                        dcc.Dropdown(
                            id='filter-tipo',
                            options=tipos_comida,
                            placeholder="Selecciona el tipo",
                            style={"width": "200px"}
                        )
                    ], style={"margin": "10px"}),
                ], style={"display": "flex", "align-items": "end", "gap": "10px"})
            ], style={"background": "#F3E5F5", "padding": "15px", "border-radius": "8px", "margin": "15px 0"}),
            
            # Operaciones disponibles CON SELECTORES
            html.Div([
                # Cambiar cocinero por otro
                html.Div([
                    html.H5("🔄 Cambiar Cocinero", style={"color": "#FF9800", "margin-bottom": "10px"}),
                    html.Div([
                        dcc.Dropdown(
                            id='cambiar-cocinero-antiguo',
                            options=cocineros_options,
                            placeholder="Cocinero actual",
                            style={"width": "150px", "margin": "5px"}
                        ),
                        html.Span("→", style={"margin": "0 10px", "font-size": "20px", "color": "#FF9800"}),
                        dcc.Dropdown(
                            id='cambiar-cocinero-nuevo',
                            options=cocineros_options,
                            placeholder="Cocinero nuevo",
                            style={"width": "150px", "margin": "5px"}
                        ),
                        html.Button('🔄 Cambiar', id='btn-cambiar-cocinero', n_clicks=0,
                                   style={
                                       "background": "#FF9800", "color": "white", "border": "none",
                                       "padding": "8px 16px", "border-radius": "6px", "margin": "5px", "cursor": "pointer"
                                   })
                    ], style={"display": "flex", "align-items": "center", "gap": "5px", "flex-wrap": "wrap"})
                ], style={"background": "#FFF3E0", "padding": "15px", "border-radius": "8px", "margin": "10px"}),
                
                # Agregar cocinero
                html.Div([
                    html.H5("➕ Agregar Cocinero", style={"color": "#4CAF50", "margin-bottom": "10px"}),
                    html.Div([
                        dcc.Dropdown(
                            id='agregar-cocinero',
                            options=cocineros_options,
                            placeholder="Selecciona cocinero a agregar",
                            style={"width": "250px", "margin": "5px"}
                        ),
                        html.Button('➕ Agregar', id='btn-agregar-cocinero', n_clicks=0,
                                   style={
                                       "background": "#4CAF50", "color": "white", "border": "none",
                                       "padding": "8px 16px", "border-radius": "6px", "margin": "5px", "cursor": "pointer"
                                   })
                    ], style={"display": "flex", "align-items": "center", "gap": "5px"})
                ], style={"background": "#E8F5E8", "padding": "15px", "border-radius": "8px", "margin": "10px"}),
                
                # Eliminar cocinero
                html.Div([
                    html.H5("➖ Eliminar Cocinero", style={"color": "#F44336", "margin-bottom": "10px"}),
                    html.Div([
                        dcc.Dropdown(
                            id='eliminar-cocinero',
                            options=cocineros_options,
                            placeholder="Selecciona cocinero a eliminar",
                            style={"width": "250px", "margin": "5px"}
                        ),
                        html.Button('➖ Eliminar', id='btn-eliminar-cocinero', n_clicks=0,
                                   style={
                                       "background": "#F44336", "color": "white", "border": "none",
                                       "padding": "8px 16px", "border-radius": "6px", "margin": "5px", "cursor": "pointer"
                                   })
                    ], style={"display": "flex", "align-items": "center", "gap": "5px"})
                ], style={"background": "#FFEBEE", "padding": "15px", "border-radius": "8px", "margin": "10px"}),
                
                # NUEVO: Intercambio específico entre diferentes grupos
                html.Div([
                    html.H5("🔄 Intercambio Específico", style={"color": "#9C27B0", "margin-bottom": "10px"}),
                    html.P("Intercambia cocineros entre diferentes años/tipos", style={"color": "#666", "font-size": "0.9rem", "margin-bottom": "10px"}),
                    html.Div([
                        # Grupo 1
                        html.Div([
                            html.Label("Grupo 1:", style={"font-weight": "bold", "color": "#9C27B0", "margin-bottom": "5px"}),
                            dcc.Dropdown(
                                id='intercambio-año1',
                                options=años_disponibles,
                                placeholder="Año 1",
                                style={"width": "120px", "margin": "2px"}
                            ),
                            dcc.Dropdown(
                                id='intercambio-tipo1',
                                options=tipos_comida,
                                placeholder="Tipo 1",
                                style={"width": "140px", "margin": "2px"}
                            ),
                            dcc.Dropdown(
                                id='intercambio-cocinero1',
                                options=cocineros_options,
                                placeholder="Cocinero 1",
                                style={"width": "140px", "margin": "2px"}
                            )
                        ], style={"display": "flex", "flex-direction": "column", "gap": "5px", "margin": "5px"}),
                        
                        html.Span("↔️", style={"margin": "0 15px", "font-size": "24px", "align-self": "center"}),
                        
                        # Grupo 2
                        html.Div([
                            html.Label("Grupo 2:", style={"font-weight": "bold", "color": "#9C27B0", "margin-bottom": "5px"}),
                            dcc.Dropdown(
                                id='intercambio-año2',
                                options=años_disponibles,
                                placeholder="Año 2",
                                style={"width": "120px", "margin": "2px"}
                            ),
                            dcc.Dropdown(
                                id='intercambio-tipo2',
                                options=tipos_comida,
                                placeholder="Tipo 2",
                                style={"width": "140px", "margin": "2px"}
                            ),
                            dcc.Dropdown(
                                id='intercambio-cocinero2',
                                options=cocineros_options,
                                placeholder="Cocinero 2",
                                style={"width": "140px", "margin": "2px"}
                            )
                        ], style={"display": "flex", "flex-direction": "column", "gap": "5px", "margin": "5px"}),
                        
                        html.Button('🔄 Intercambiar', id='btn-intercambiar-especifico', n_clicks=0,
                                   style={
                                       "background": "#9C27B0", "color": "white", "border": "none",
                                       "padding": "12px 20px", "border-radius": "6px", "margin": "10px", 
                                       "cursor": "pointer", "align-self": "center"
                                   })
                    ], style={"display": "flex", "align-items": "start", "gap": "10px", "flex-wrap": "wrap"})
                ], style={"background": "#F3E5F5", "padding": "15px", "border-radius": "8px", "margin": "10px"}),
                
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

def create_fiestas_page():
    return html.Div([
        html.H1("🎉 Fiestas de Agosto 2025", style={"color": "#2E7D32", "margin-bottom": "30px"}),
        
        # Mostrar etiquetas por día
        html.Div(id='tarjetas-fiestas'),
        
        # Formulario de edición FUNCIONAL
        html.Div([
            html.H3("✏️ Editar Día", style={"color": "#9C27B0", "margin-bottom": "20px"}),
            
            html.Div([
                html.Div([
                    html.Label("📅 Seleccionar Día:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Dropdown(
                        id='fiesta-dia-selector',
                        options=[
                            {'label': f"{i} de agosto 2025", 'value': f"2025-08-{i:02d}"} 
                            for i in range(8, 18)
                        ],
                        placeholder="Selecciona el día a editar",
                        style={"width": "100%"}
                    )
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
                ], style={"margin": "10px", "flex": "2"}),
                
                html.Div([
                    html.Label("👥 Número de Adultos:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='fiesta-adultos',
                        type='number',
                        placeholder="0",
                        min=0,
                        style={"width": "100%", "padding": "8px"}
                    )
                ], style={"margin": "10px", "flex": "1"}),
                
                html.Div([
                    html.Label("👶 Número de Niños:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Input(
                        id='fiesta-niños',
                        type='number',
                        placeholder="0",
                        min=0,
                        style={"width": "100%", "padding": "8px"}
                    )
                ], style={"margin": "10px", "flex": "1"}),
            ], style={"display": "flex", "gap": "10px"}),
            
            html.Div([
                html.Div([
                    html.Label("👥 Nombres de Adultos:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Textarea(
                        id='fiesta-nombres-adultos',
                        placeholder="Escribe los nombres separados por comas: Juan, María, Pedro...",
                        style={"width": "100%", "height": "60px", "padding": "8px"}
                    )
                ], style={"margin": "10px", "flex": "1"}),
                
                html.Div([
                    html.Label("👶 Nombres de Niños:", style={"font-weight": "bold", "margin-bottom": "5px"}),
                    dcc.Textarea(
                        id='fiesta-nombres-niños',
                        placeholder="Escribe los nombres separados por comas: Ana, Luis, Carlos...",
                        style={"width": "100%", "height": "60px", "padding": "8px"}
                    )
                ], style={"margin": "10px", "flex": "1"}),
            ], style={"display": "flex", "gap": "10px"}),
            
            html.Div([
                html.Button('✅ Actualizar Día', id='btn-update-fiesta', n_clicks=0,
                           style={
                               "background": "linear-gradient(45deg, #9C27B0, #7B1FA2)", 
                               "color": "white", "border": "none", "padding": "12px 24px",
                               "border-radius": "8px", "font-weight": "bold", "cursor": "pointer",
                               "margin": "15px 10px"
                           }),
                
                html.Button('🔄 Cargar Datos del Día', id='btn-load-fiesta', n_clicks=0,
                           style={
                               "background": "linear-gradient(45deg, #2196F3, #1976D2)", 
                               "color": "white", "border": "none", "padding": "12px 24px",
                               "border-radius": "8px", "font-weight": "bold", "cursor": "pointer",
                               "margin": "15px 10px"
                           })
            ]),
            
            html.Div(id='fiesta-output', style={"margin": "20px 0", "padding": "10px"})
            
        ], style={"margin-top": "30px", "padding": "25px", "background": "#F8F9FA", "border-radius": "12px"})
    ])

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

# Callbacks para tablón de anuncios
@app.callback(
    Output('modal-anuncio', 'style'),
    [Input('btn-nuevo-anuncio', 'n_clicks'),
     Input('btn-cancelar-anuncio', 'n_clicks'),
     Input('btn-publicar-anuncio', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_modal_anuncio(n_nuevo, n_cancelar, n_publicar):
    ctx = callback_context
    if not ctx.triggered:
        return {"display": "none"}
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'btn-nuevo-anuncio':
        return {
            "position": "fixed", "top": "0", "left": "0", "width": "100%", "height": "100%",
            "background": "rgba(0,0,0,0.5)", "display": "flex", "align-items": "center",
            "justify-content": "center", "z-index": "1000"
        }
    else:  # cancelar o publicar
        return {"display": "none"}

@app.callback(
    [Output('lista-noticias', 'children'),
     Output('anuncio-titulo', 'value'),
     Output('anuncio-contenido', 'value')],
    [Input('btn-publicar-anuncio', 'n_clicks'),
     Input({'type': 'btn-delete-noticia', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State('anuncio-titulo', 'value'),
     State('anuncio-contenido', 'value'),
     State('anuncio-autor', 'value')],
    prevent_initial_call=True
)
def manage_noticias(n_publicar, n_delete_list, titulo, contenido, autor):
    ctx = callback_context
    
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update
    
    trigger_info = ctx.triggered[0]['prop_id']
    
    # Publicar nuevo anuncio
    if 'btn-publicar-anuncio' in trigger_info and n_publicar > 0:
        if titulo and contenido:
            add_noticia(titulo, contenido, autor or 'Administrador')
            # Limpiar campos y recargar lista
            noticias_df = get_noticias()
            nueva_lista = [
                html.Div([
                    html.H5(noticia['titulo'], style={"color": "#1976D2", "margin": "0 0 8px 0"}),
                    html.P(noticia['contenido'], style={"margin": "0 0 10px 0", "color": "#333"}),
                    html.Div([
                        html.Span(f"👤 {noticia['autor']}", style={"font-size": "0.85rem", "color": "#666", "margin-right": "15px"}),
                        html.Span(f"📅 {noticia['fecha_creacion'][:16]}", style={"font-size": "0.85rem", "color": "#666", "margin-right": "10px"}),
                        html.Button('🗑️', id={'type': 'btn-delete-noticia', 'index': noticia['id']}, n_clicks=0,
                                   style={"background": "#F44336", "color": "white", "border": "none",
                                         "padding": "4px 8px", "border-radius": "4px", "cursor": "pointer",
                                         "font-size": "0.8rem", "float": "right"})
                    ])
                ], style={
                    "background": "linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)",
                    "padding": "15px", "margin": "10px 0", "border-radius": "8px",
                    "border-left": "4px solid #2196F3", "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"
                })
                for noticia in noticias_df.to_dict('records')[:5]
            ]
            return nueva_lista, "", ""  # Limpiar campos
    
    # Eliminar anuncio
    elif 'btn-delete-noticia' in trigger_info:
        # Extraer el ID del anuncio a eliminar
        import json
        prop_id_dict = json.loads(trigger_info.split('.')[0])
        noticia_id = prop_id_dict['index']
        
        # Verificar si realmente se hizo clic
        if any(n_delete_list):
            delete_noticia(noticia_id)
            
            # Recargar lista
            noticias_df = get_noticias()
            nueva_lista = [
                html.Div([
                    html.H5(noticia['titulo'], style={"color": "#1976D2", "margin": "0 0 8px 0"}),
                    html.P(noticia['contenido'], style={"margin": "0 0 10px 0", "color": "#333"}),
                    html.Div([
                        html.Span(f"👤 {noticia['autor']}", style={"font-size": "0.85rem", "color": "#666", "margin-right": "15px"}),
                        html.Span(f"📅 {noticia['fecha_creacion'][:16]}", style={"font-size": "0.85rem", "color": "#666", "margin-right": "10px"}),
                        html.Button('🗑️', id={'type': 'btn-delete-noticia', 'index': noticia['id']}, n_clicks=0,
                                   style={"background": "#F44336", "color": "white", "border": "none",
                                         "padding": "4px 8px", "border-radius": "4px", "cursor": "pointer",
                                         "font-size": "0.8rem", "float": "right"})
                    ])
                ], style={
                    "background": "linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)",
                    "padding": "15px", "margin": "10px 0", "border-radius": "8px",
                    "border-left": "4px solid #2196F3", "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"
                })
                for noticia in noticias_df.to_dict('records')[:5]
            ] if len(noticias_df) > 0 else [
                html.Div([
                    html.P("No hay anuncios publicados", style={"text-align": "center", "color": "#666", "font-style": "italic"})
                ], style={"padding": "20px"})
            ]
            return nueva_lista, dash.no_update, dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update

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
     State('intercambio-año1', 'value'), State('intercambio-tipo1', 'value'), State('intercambio-cocinero1', 'value'),
     State('intercambio-año2', 'value'), State('intercambio-tipo2', 'value'), State('intercambio-cocinero2', 'value')],
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
     Output('intercambio-tipo1', 'options'),
     Output('intercambio-tipo2', 'options')],
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
init_db()
load_eventos_completos()

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
    
    app.run_server(debug=debug, host='0.0.0.0', port=port)