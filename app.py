import dash
<<<<<<< HEAD
from dash import dcc, html, Input, Output, State, callback_context, dash_table, ALL
from dash.exceptions import PreventUpdate
import dash.dependencies
=======
from dash import dcc, html, Input, Output, State, callback_context, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
>>>>>>> e79d4fc (cambio a supabase)
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
from datetime import datetime, date, timedelta
import calendar

<<<<<<< HEAD
=======
# IMPORTAR DATA MANAGER
from data_manager import dm
>>>>>>> e79d4fc (cambio a supabase)

# Inicializar la app
app = dash.Dash(__name__, 
                suppress_callback_exceptions=True)
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

# ===== FUNCIONES DE UTILIDAD =====

def registrar_cambio(tipo_cambio, descripcion, usuario="Anónimo"):
    """Registrar un cambio en el sistema"""
    try:
        cambios_df = dm.get_data('cambios')
        nueva_fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dm.add_data('cambios', (nueva_fecha, tipo_cambio, descripcion, usuario))
        return True
    except Exception as e:
        print(f"Error registrando cambio: {e}")
        return False

<<<<<<< HEAD
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
        ('2025-08-08', 'Oscar Vicente, Serafin Montoliu', 'Torrada de carne', 0, 'Serafin Montoliu, Alonso Roqueta, Lara Sorribes, J. Ramon Barreda, Victor Zandalinas, Sonia Domingo, Pilar Gimeno Belles, Diego Tena Pitarch, Carmina Escorihuela, David Roig, Lucia Carceller, Miguel A Monfort, Óscar Vicente, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Manel Roig, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '16:30-Final Frontenis|17:30-Final Futbol-sala|19:00-Chupinazo y pasacalle|22:30-Presentacion|00:00-Discomóvil'),
        ('2025-08-09', 'Alfonso Roig, Ana Troncho', 'Entrantes y ensaladilla', 0, 'Serafin Montoliu, Alonso Roqueta, Lara Sorribes, Carolina De Toro, J. Ramon Barreda, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, David Roig, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Óscar Vicente, Ana Troncho, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '17:00-Corro de vacas y toro|19:00-Tardeo "Kasparov"|21:00-Cena Popular (concurso manteles - AvLosar)|23:30-Toro embolado|00:30-Grupo Zetak'),
        ('2025-08-10', 'Miguel A. Monfort, Lucia Carceller', 'Entrantes y ternera guisada', 0, 'Susana Pitarch, Serafin Montoliu, J. Ramon Barreda, Victor Zandalinas, Sonia Domingo, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Vera Montoliu, Saul Montoliu, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Andres Vicente, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '12:00-Sevillanas tasca comision|17:00-Recortadores|19:00-Tardeo Rumba 13|22:30-Concurso Emboladores|00:00-Tu Cara Me Suena + Noche Spotify en tasca comisión'),
        ('2025-08-11', 'DIA DE LES PENYES', 'Arroz con secreto y costilla / Guiso de toro', 0, 'Alonso Roqueta, Carolina De Toro, J. Ramon Barreda, Pilar Gimeno Belles, Diego Tena Pitarch, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', 'DIA DE LAS PEÑAS|14:00-Comida Arroz con secreto y costilla|16:30-Juego de peñas|21:00-Cena Guiso de toro|A continuación Discomóvil plaza toros'),
        ('2025-08-12', 'Victor Prades, Sara Barcina, J. Fernando Marques', 'Fideua de carne (no lleva pescado)', 0, 'Alonso Roqueta, J. Ramon Barreda, Victor Zandalinas, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Elena Domingo, Raul Altaba, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Daniel Altaba, Martina Altaba, Andres Vicente, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '17:00-Corro de vacas con charanga|19:00-Tardeo Generación Z|23:00-Toro embolado|00:30-Orquesta Bella Donna y discomóvil'),
        ('2025-08-13', 'David Roig, Carmina Escorihuela', 'Caldo con pelotas y carrillada', 0, 'Carolina De Toro, J. Ramon Barreda, Victor Zandalinas, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Elena Domingo, Raul Altaba, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Daniel Altaba, Martina Altaba, Andres Vicente, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '17:00-Corro de vacas y entrada de toro|18:00-Bureo Parador|19:30-Tarde de rock tasca|22:00-Grupo Garrama|23:30-Toro Embolado|00:00-Tributo Extremoduro en tasca'),
        ('2025-08-14', 'J.Ramon Barreda, Carolina De Toro', 'Melon con jamon y albondigas', 0, 'Carolina De Toro, J. Ramon Barreda, Pilar Gimeno Belles, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, David Roig, Elena Domingo, Raul Altaba, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Óscar Vicente, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Daniel Altaba, Martina Altaba, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '19:00-Desencajonada de 2 toros y embolada de 1 toro|00:00-Desfile disfraces con charanga y baile con La Freska'),
        ('2025-08-15', 'Raul Altaba, Elena Domingo, Victor Zandalinas, Sonia Domingo', 'Entrantes: pulso con patatas, ensalada Cesar y gambas saladas. Principal: Lomo.', 0, 'Serafin Montoliu, Alonso Roqueta, Lara Sorribes, Carolina De Toro, J. Ramon Barreda, Victor Zandalinas, Sonia Domingo, Diego Tena Pitarch, J. Fernando Marques, Marta Fusté, Luis Bellés, Carmina Escorihuela, David Roig, Elena Domingo, Raul Altaba, Francisco Vicente, Sugey Guzman, Lucia Carceller, Miguel A Monfort, Óscar Vicente, Sara Barcina, Víctor Prades, Ana Troncho, Alfonso Roig', 0, 'Raúl Roqueta, Éric Roqueta, Nuria Barreda, Francesc Barreda, Chloe Bellés, Manel Roig, Daniel Altaba, Martina Altaba, Andres Vicente, Nuria Monfort, Andrea Monfort, Elia Roig, Alex Roig', '12:00-Especial con vacas|16:30-Corro de vacas|18:00-Prueba de toro Ventanillo|22:30-Ball Pla|00:00-Toro embolado|00:30-Tributo a la Oreja de Van Gogh en plaza de toros'),
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
=======
def obtener_ultimos_cambios(n=10):
    """Obtener los últimos N cambios"""
    try:
        cambios_df = dm.get_data('cambios')
        if len(cambios_df) > 0:
            cambios_df['fecha_dt'] = pd.to_datetime(cambios_df['fecha'])
            return cambios_df.sort_values('fecha_dt', ascending=False).head(n)
        return pd.DataFrame()
    except:
        return pd.DataFrame()
>>>>>>> e79d4fc (cambio a supabase)

def get_proximos_eventos(limit=5):
    """Obtener próximos eventos"""
    try:
        eventos_df = dm.get_data('eventos')
        comidas_df = dm.get_data('comidas')
        
        eventos_lista = []
        
        # Agregar eventos especiales
        if len(eventos_df) > 0:
            for _, evento in eventos_df.iterrows():
                eventos_lista.append({
                    'fecha': evento['fecha'],
                    'tipo': evento['evento'],
                    'descripcion': evento.get('tipo', '')
                })
        
        # Agregar comidas
        if len(comidas_df) > 0:
            for _, comida in comidas_df.iterrows():
                eventos_lista.append({
                    'fecha': comida['fecha'],
                    'tipo': comida.get('dia', 'Comida'),
                    'descripcion': f"{comida.get('tipo_comida', '')} - {comida.get('cocineros', '')}"
                })
        
        if eventos_lista:
            df_eventos = pd.DataFrame(eventos_lista)
            df_eventos['fecha_dt'] = pd.to_datetime(df_eventos['fecha'])
            hoy = pd.Timestamp.now().normalize()  # Solo la fecha, sin hora
            df_eventos = df_eventos[df_eventos['fecha_dt'] >= hoy]
            df_eventos = df_eventos.sort_values('fecha_dt').head(limit)
            return df_eventos
        
        return pd.DataFrame()
    except Exception as e:
        print(f"Error obteniendo eventos: {e}")
        return pd.DataFrame()

# ===== ESTILOS INLINE MODERNOS =====

STYLES = {
    'navbar': {
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'right': 0,
        'height': '70px',
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'color': 'white',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'space-between',
        'padding': '0 30px',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.1)',
        'zIndex': '1000'
    },
    'container': {
        'marginTop': '90px',
        'padding': '20px',
        'maxWidth': '1400px',
        'margin': '90px auto 20px auto'
    },
    'card': {
        'background': 'white',
        'borderRadius': '16px',
        'padding': '24px',
        'marginBottom': '20px',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
        'transition': 'all 0.3s ease'
    },
    'button': {
        'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'color': 'white',
        'border': 'none',
        'borderRadius': '8px',
        'padding': '12px 24px',
        'fontSize': '14px',
        'fontWeight': '600',
        'cursor': 'pointer',
        'transition': 'all 0.3s ease',
        'boxShadow': '0 4px 12px rgba(102, 126, 234, 0.4)'
    },
    'input': {
        'width': '100%',
        'padding': '12px',
        'borderRadius': '8px',
        'border': '2px solid #e2e8f0',
        'fontSize': '14px',
        'transition': 'all 0.3s ease',
        'marginBottom': '12px'
    },
    'title': {
        'fontSize': '28px',
        'fontWeight': '700',
        'color': '#1a202c',
        'marginBottom': '24px',
        'display': 'flex',
        'alignItems': 'center',
        'gap': '12px'
    },
    'subtitle': {
        'fontSize': '20px',
        'fontWeight': '600',
        'color': '#2d3748',
        'marginBottom': '16px',
        'display': 'flex',
        'alignItems': 'center',
        'gap': '8px'
    }
}

# ===== LAYOUT =====

def create_navbar():
    return html.Div([
        html.Div([
            html.Div([
                html.Img(src='/assets/logo.png', style={'height': '50px', 'marginRight': '12px'}),  # ← CAMBIADO
                html.H1("Penya L'Albenc", style={'margin': '0', 'fontSize': '24px', 'fontWeight': '700'})
            ], style={'display': 'flex', 'alignItems': 'center'}),
            
            html.Div([
                dcc.Link('🏠 Inicio', href='/', style={'color': 'white', 'textDecoration': 'none', 'fontWeight': '500', 'padding': '0 15px'}),
                dcc.Link('🍽️ Comidas', href='/comidas', style={'color': 'white', 'textDecoration': 'none', 'fontWeight': '500', 'padding': '0 15px'}),
                dcc.Link('🛒 Compra', href='/lista-compra', style={'color': 'white', 'textDecoration': 'none', 'fontWeight': '500', 'padding': '0 15px'}),
                dcc.Link('📅 Eventos', href='/eventos', style={'color': 'white', 'textDecoration': 'none', 'fontWeight': '500', 'padding': '0 15px'}),
                dcc.Link('🎉 Fiestas', href='/fiestas', style={'color': 'white', 'textDecoration': 'none', 'fontWeight': '500', 'padding': '0 15px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '0'})
        ], style=STYLES['navbar'])
    ])

<<<<<<< HEAD
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
=======
>>>>>>> e79d4fc (cambio a supabase)
def create_home_page():
    proximos = get_proximos_eventos(5)
    print(f"DEBUG: Próximos eventos encontrados: {len(proximos)}")  # ← AGREGAR
    if len(proximos) > 0:
        print(proximos[['fecha', 'tipo', 'descripcion']])  # ← AGREGAR
    cambios = obtener_ultimos_cambios(8)
    
    
    # Obtener mantenimiento del año actual
    año_actual = datetime.now().year
    mantenimiento_df = dm.get_data('mantenimiento')
    mant_actual = mantenimiento_df[mantenimiento_df['año'] == año_actual]
    
    return html.Div([
        html.Div([
            # Logos
            html.Div([
                    html.Img(src='/assets/logo2.png', style={
                        'height': '120px', 'margin': '0 20px',
                        'objectFit': 'contain', 'filter': 'drop-shadow(0 4px 6px rgba(0,0,0,0.1))'
                    }),
            ], style={
                'display': 'flex',
                'justifyContent': 'center',
                'alignItems': 'center',
                'marginBottom': '30px',
                'flexWrap': 'wrap',
                'gap': '20px'
            }),
            
            # Mantenimiento del Año
            html.Div([
                html.H3(f"🔧 Mantenimiento {año_actual}", style=STYLES['subtitle']),
                html.Div([
                    html.Div([
                        html.H4("🔨 Mantenimiento:", style={'margin': '0 0 8px 0', 'color': '#ed8936', 'fontSize': '16px'}),
                        html.P(mant_actual.iloc[0]['mantenimiento'] if len(mant_actual) > 0 else 'Sin datos', 
                              style={'margin': '0 0 16px 0', 'fontSize': '14px', 'color': '#2d3748', 'fontWeight': '500'})
                    ]),
                    html.Div([
                        html.H4("🏗️ Cadafals:", style={'margin': '0 0 8px 0', 'color': '#ed8936', 'fontSize': '16px'}),
                        html.P(mant_actual.iloc[0]['cadafals'] if len(mant_actual) > 0 else 'Sin datos', 
                              style={'margin': '0', 'fontSize': '14px', 'color': '#2d3748', 'fontWeight': '500'})
                    ])
                ], style={
                    'background': 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)',
                    'padding': '20px',
                    'borderRadius': '12px',
                    'border': '2px solid #fed7aa'
                })
            ], style=STYLES['card']),
            
            # Próximos eventos
            html.Div([
                html.H3("📅 Próximos Eventos", style=STYLES['subtitle']),
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span("📌", style={'fontSize': '24px', 'marginRight': '12px'}),
                            html.Div([
                                html.H4(html.Strong(row['tipo']), style={'margin': '0', 'fontSize': '16px', 'fontWeight': '700', 'color': '#2d3748'}),
                                html.P(f"{datetime.strptime(row['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y')} - {row['descripcion']}", 
                                      style={'margin': '4px 0 0 0', 'fontSize': '14px', 'color': '#718096'})
                            ])
                        ], style={'display': 'flex', 'alignItems': 'center', 'padding': '16px', 'background': '#f7fafc', 'borderRadius': '8px', 'marginBottom': '8px'})
                    ]) for _, row in proximos.iterrows()
                ] if len(proximos) > 0 else [html.P("No hay eventos próximos", style={'color': '#a0aec0', 'fontStyle': 'italic'})])
            ], style=STYLES['card']),
            
            # Últimos cambios
            html.Div([
                html.H3("🔔 Últimos Cambios en la App", style=STYLES['subtitle']),
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span("✓", style={'fontSize': '20px', 'marginRight': '12px', 'color': '#48bb78'}),
                            html.Div([
                                html.P(f"{row['tipo_cambio']}: {row['descripcion']}", 
                                      style={'margin': '0', 'fontSize': '14px', 'color': '#2d3748', 'fontWeight': '500'}),
                                html.P(datetime.strptime(row['fecha'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M'), 
                                      style={'margin': '4px 0 0 0', 'fontSize': '12px', 'color': '#a0aec0'})
                            ])
                        ], style={'display': 'flex', 'alignItems': 'start', 'padding': '12px', 'background': '#f0fff4', 'borderRadius': '8px', 'marginBottom': '8px', 'borderLeft': '3px solid #48bb78'})
                    ]) for _, row in cambios.iterrows()
                ] if len(cambios) > 0 else [html.P("No hay cambios registrados", style={'color': '#a0aec0', 'fontStyle': 'italic'})])
            ], style=STYLES['card']),
            
        ], style=STYLES['container'])
    ])

def limpiar_comidas_antiguas():
    """Borrar automáticamente comidas de años anteriores al actual"""
    try:
        año_actual = datetime.now().year
        comidas_df = dm.get_data('comidas')
        
        if len(comidas_df) > 0:
            comidas_df['fecha_dt'] = pd.to_datetime(comidas_df['fecha'])
            comidas_df['año'] = comidas_df['fecha_dt'].dt.year
            
            antes = len(comidas_df)
            comidas_df = comidas_df[comidas_df['año'] >= año_actual]
            despues = len(comidas_df)
            
            if antes > despues:
                # Eliminar columnas temporales
                comidas_df = comidas_df.drop(['fecha_dt', 'año'], axis=1)
                dm.save_data('comidas', comidas_df)
                eliminadas = antes - despues
                print(f"🗑️ Limpieza automática: {eliminadas} comidas antiguas eliminadas")
                registrar_cambio('Sistema', f'Limpieza automática: {eliminadas} comidas antiguas eliminadas')
                return True
        return False
    except Exception as e:
        print(f"Error en limpieza automática: {e}")
        return False

def create_fiestas_page():
    fiestas_df = dm.get_data('fiestas')
    
    # Filtrar solo agosto 2025
    fiestas_agosto = fiestas_df[
        (fiestas_df['fecha'] >= '2025-08-08') & 
        (fiestas_df['fecha'] <= '2025-08-17')
    ].sort_values('fecha') if len(fiestas_df) > 0 else pd.DataFrame()
    
    tarjetas = []
    for _, dia in fiestas_agosto.iterrows():
        fecha_obj = datetime.strptime(dia['fecha'], '%Y-%m-%d')
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        eventos = dia['programa'].split('|') if dia['programa'] else []
        
        tarjeta = html.Div([
            html.H4(f"{dias_semana[fecha_obj.weekday()]} {fecha_obj.day} de Agosto", 
                   style={'color': '#667eea', 'marginBottom': '12px', 'fontSize': '18px'}),
            html.Div([
                html.Strong("Cocineros: "), dia['cocineros']
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Strong("Menú: "), dia['menu'] if dia['menu'] else 'No especificado'
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Strong("Adultos: "), f"{len(dia['nombres_adultos'].split(',')) if dia['nombres_adultos'] else 0}"
            ], style={'marginBottom': '8px'}),
            html.Div([
                html.Strong("Niños: "), f"{len(dia['nombres_niños'].split(',')) if dia['nombres_niños'] else 0}"
            ], style={'marginBottom': '12px'}),
            html.Div([
                html.Strong("Programa:"),
                html.Ul([html.Li(ev.strip()) for ev in eventos])
            ])
        ], style={**STYLES['card'], 'border': '2px solid #667eea', 'marginBottom': '16px'})
        
        tarjetas.append(tarjeta)
    
    return html.Div([
        html.Div([
<<<<<<< HEAD
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
=======
            html.H2("Fiestas Agosto 2025 - Vilafranca", style=STYLES['title']),
            html.P("Datos de solo lectura", style={'color': '#718096', 'fontStyle': 'italic', 'marginBottom': '20px'}),
            html.Div(tarjetas if tarjetas else [html.P("No hay datos de fiestas")])
        ], style=STYLES['container'])
>>>>>>> e79d4fc (cambio a supabase)
    ])

def create_comidas_page():
    comidas_df = dm.get_data('comidas')
    print(f"DEBUG: Total comidas cargadas: {len(comidas_df)}")
    cocineros_unicos = set()
    
    for _, row in comidas_df.iterrows():
        if pd.notna(row.get('cocineros')):
            cocineros_unicos.update([c.strip() for c in str(row['cocineros']).split(',')])
    
    cocineros_options = [{'label': c, 'value': c} for c in sorted(cocineros_unicos)]
    
    return html.Div([
        html.Div([
            html.H2("🍽️ Gestión de Comidas", style=STYLES['title']),
            
            # TABLA DE COMIDAS
            html.Div([
                html.H3("📋 Comidas Planificadas", style=STYLES['subtitle']),
                dash_table.DataTable(
                    id='tabla-comidas',
                    data=comidas_df.to_dict('records'),
                    columns=[
                        {"name": "📅 Fecha", "id": "fecha", "type": "datetime", "editable": True},
                        {"name": "🎉 Día", "id": "dia", "type": "text", "editable": True},
                        {"name": "🍽️ Tipo", "id": "tipo_comida", "type": "text", "editable": True},
                        {"name": "👨‍🍳 Cocineros", "id": "cocineros", "type": "text", "editable": True},
                    ],
                    row_deletable=True,
                    editable=True,
                    sort_action="native",
                    filter_action="native",
                    page_size=25,  
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '12px',
                        'fontSize': '14px',
                        'fontFamily': 'Inter, sans-serif'
                    },
                    style_header={
                        'backgroundColor': '#667eea',
                        'color': 'white',
                        'fontWeight': '600',
                        'border': 'none'
                    },
                    style_data={
                        'border': 'none',
                        'borderBottom': '1px solid #e2e8f0'
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': '#f7fafc'}
                    ]
                )
            ], style=STYLES['card']),
            
            # GESTIÓN POR DÍA ESPECÍFICO (PRIMERO)
            html.Div([
                html.H3("🎯 Modificar Cocineros de un Día", style=STYLES['subtitle']),
                
                html.Label("1️⃣ Seleccionar día:", style={'fontWeight': '600', 'marginBottom': '8px', 'display': 'block'}),
                dcc.Dropdown(
                    id='selector-dia',
                    options=[
                        {'label': 'Sant Antoni', 'value': 'sant_antoni'},
                        {'label': 'Brena St Vicent', 'value': 'brena_st_vicent'},
                        {'label': 'Fira Magdalena', 'value': 'fira_magdalena'},
                        {'label': 'Penya Taurina', 'value': 'penya_taurina'}
                    ],
                    placeholder="Seleccionar día",
                    style={'marginBottom': '16px'}
                ),
                
                html.Label("2️⃣ Seleccionar fecha:", style={'fontWeight': '600', 'marginBottom': '8px', 'display': 'block'}),
                dcc.Dropdown(
                    id='selector-fecha-dia',
                    placeholder="Primero selecciona un día",
                    style={'marginBottom': '16px'}
                ),
                
                html.Div(id='info-comida-seleccionada', style={'marginBottom': '16px'}),
                
                html.Label("3️⃣ Acción:", style={'fontWeight': '600', 'marginBottom': '8px', 'display': 'block'}),
                dcc.Dropdown(
                    id='accion-cocinero',
                    options=[
                        {'label': '➕ Agregar cocinero', 'value': 'agregar'},
                        {'label': '➖ Eliminar cocinero', 'value': 'eliminar'},
                        {'label': '🔄 Intercambiar cocinero', 'value': 'intercambiar'}
                    ],
                    placeholder="Seleccionar acción",
                    style={'marginBottom': '12px'}
                ),
                
                html.Div(id='campos-accion'),
                
                html.Button('✅ Ejecutar', id='btn-ejecutar-accion', style=STYLES['button']),
                html.Div(id='output-accion', style={'marginTop': '12px'})
            ], style=STYLES['card']),
            
            # GESTIÓN GLOBAL DE COCINEROS
            html.Div([
                html.H3("🔄 Gestión Global de Cocineros", style=STYLES['subtitle']),
                
                html.Div([
                    html.Label("Intercambiar en TODAS las comidas:", style={'fontWeight': '600', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(id='inter-cocinero1', options=cocineros_options, placeholder="Cocinero 1", style={'marginBottom': '8px'}),
                    dcc.Dropdown(id='inter-cocinero2', options=cocineros_options, placeholder="Cocinero 2", style={'marginBottom': '8px'}),
                    html.Button('Intercambiar', id='btn-intercambiar', style={**STYLES['button'], 'background': 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)'}),
                ], style={'marginBottom': '20px'}),
                
                html.Div([
                    html.Label("Agregar a TODAS las comidas:", style={'fontWeight': '600', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.Input(id='agregar-cocinero-nombre', placeholder="Nombre del cocinero", style=STYLES['input']),
                    html.Button('Agregar a todas', id='btn-agregar-cocinero-todas', style={**STYLES['button'], 'background': 'linear-gradient(135deg, #4299e1 0%, #3182ce 100%)'}),
                ], style={'marginBottom': '20px'}),
                
                html.Div([
                    html.Label("Eliminar de TODAS las comidas:", style={'fontWeight': '600', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(id='eliminar-cocinero-select', options=cocineros_options, placeholder="Seleccionar cocinero", style={'marginBottom': '8px'}),
                    html.Button('Eliminar de todas', id='btn-eliminar-cocinero-todas', style={**STYLES['button'], 'background': 'linear-gradient(135deg, #f56565 0%, #e53e3e 100%)'}),
                ]),
                
                html.Div(id='output-intercambio', style={'marginTop': '12px'})
            ], style=STYLES['card']),
            
            # AGREGAR NUEVA COMIDA (AL FINAL)
            html.Div([
                html.H3("➕ Agregar Nueva Comida", style=STYLES['subtitle']),
                dcc.DatePickerSingle(id='nueva-fecha', date=date.today(), display_format='DD/MM/YYYY'),
                dcc.Input(id='nuevo-dia', placeholder="Día (ej: sant_antoni)", style=STYLES['input']),
                dcc.Dropdown(
                    id='nuevo-servicio',
                    options=[
                        {'label': '🌅 Comida', 'value': 'Comida'},
                        {'label': '🌙 Cena', 'value': 'Cena'},
                        {'label': '🌅🌙 Comida y Cena', 'value': 'Comida y Cena'}
                    ],
                    placeholder="Tipo de comida",
                    style={'marginBottom': '12px'}
                ),
                dcc.Dropdown(id='nuevos-cocineros', options=cocineros_options, multi=True, placeholder="Seleccionar cocineros", style={'marginBottom': '12px'}),
                html.Button('✅ Agregar Comida', id='btn-agregar-comida', style=STYLES['button']),
                html.Div(id='output-comida', style={'marginTop': '12px'})
            ], style=STYLES['card']),
            
        ], style=STYLES['container'])
    ])

def create_lista_compra_page():
    lista_df = dm.get_data('lista_compra')
    
    return html.Div([
        html.Div([
            html.H2("🛒 Lista de Compra", style=STYLES['title']),
            
            # Tabla
            html.Div([
                html.H3("📝 Items", style=STYLES['subtitle']),
                dash_table.DataTable(
                    id='tabla-lista',
                    data=lista_df.to_dict('records'),
                    columns=[
                        {"name": "📅 Fecha", "id": "fecha", "type": "datetime", "editable": True},
                        {"name": "📦 Objeto", "id": "objeto", "type": "text", "editable": True},
                    ],
                    row_deletable=True,
                    editable=True,
                    sort_action="native",
                    page_size=20,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '12px',
                        'fontSize': '14px',
                        'fontFamily': 'Inter, sans-serif'
                    },
                    style_header={
                        'backgroundColor': '#48bb78',
                        'color': 'white',
                        'fontWeight': '600',
                        'border': 'none'
                    },
                    style_data={
                        'border': 'none',
                        'borderBottom': '1px solid #e2e8f0'
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': '#f7fafc'}
                    ]
                )
            ], style=STYLES['card']),
            
            # Agregar item
            html.Div([
                html.H3("➕ Agregar Item", style=STYLES['subtitle']),
                dcc.DatePickerSingle(id='lista-nueva-fecha', date=date.today(), display_format='DD/MM/YYYY'),
                dcc.Input(id='lista-nuevo-objeto', placeholder="Objeto a comprar", style=STYLES['input']),
                html.Button('✅ Agregar', id='btn-agregar-lista', style=STYLES['button']),
                html.Div(id='output-lista', style={'marginTop': '12px'})
            ], style=STYLES['card']),
            
        ], style=STYLES['container'])
    ])

def create_eventos_page():
    eventos_df = dm.get_data('eventos')
    
    return html.Div([
        html.Div([
            html.H2("📅 Eventos Especiales", style=STYLES['title']),
            
            # Tabla
            html.Div([
                html.H3("🎉 Eventos Registrados", style=STYLES['subtitle']),
                dash_table.DataTable(
                    id='tabla-eventos',
                    data=eventos_df.to_dict('records'),
                    columns=[
                        {"name": "📅 Fecha", "id": "fecha", "type": "datetime", "editable": True},
                        {"name": "🎊 Evento", "id": "evento", "type": "text", "editable": True},
                        {"name": "📝 Tipo", "id": "tipo", "type": "text", "editable": True},
                    ],
                    row_deletable=True,
                    editable=True,
                    sort_action="native",
                    page_size=15,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '12px',
                        'fontSize': '14px',
                        'fontFamily': 'Inter, sans-serif'
                    },
                    style_header={
                        'backgroundColor': '#ed8936',
                        'color': 'white',
                        'fontWeight': '600',
                        'border': 'none'
                    },
                    style_data={
                        'border': 'none',
                        'borderBottom': '1px solid #e2e8f0'
                    },
                    style_data_conditional=[
                        {'if': {'row_index': 'odd'}, 'backgroundColor': '#f7fafc'}
                    ]
                )
            ], style=STYLES['card']),
            
            # Agregar evento
            html.Div([
                html.H3("➕ Agregar Evento", style=STYLES['subtitle']),
                dcc.DatePickerSingle(id='evento-nueva-fecha', date=date.today(), display_format='DD/MM/YYYY'),
                dcc.Input(id='evento-nuevo-nombre', placeholder="Nombre del evento", style=STYLES['input']),
                dcc.Input(id='evento-nuevo-tipo', placeholder="Tipo/Descripción", style=STYLES['input']),
                html.Button('✅ Agregar Evento', id='btn-agregar-evento', style=STYLES['button']),
                html.Div(id='output-evento', style={'marginTop': '12px'})
            ], style=STYLES['card']),
            
        ], style=STYLES['container'])
    ])

<<<<<<< HEAD
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
=======
# ===== CALLBACKS =====
>>>>>>> e79d4fc (cambio a supabase)

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/comidas':
        return create_comidas_page()
    elif pathname == '/lista-compra':
        return create_lista_compra_page()
    elif pathname == '/eventos':
        return create_eventos_page()
    elif pathname == '/fiestas':
        return create_fiestas_page()
    else:
        return create_home_page()

# Callback para comidas
@app.callback(
    [Output('tabla-comidas', 'data'),
     Output('output-comida', 'children'),
     Output('confirm-delete', 'displayed'),
     Output('store-datos-borrar', 'data')],
    [Input('btn-agregar-comida', 'n_clicks'),
     Input('btn-intercambiar', 'n_clicks'),
     Input('tabla-comidas', 'data'),
     Input('confirm-delete', 'submit_n_clicks')],
    [State('tabla-comidas', 'data_previous'),
     State('store-datos-borrar', 'data'),
     State('nueva-fecha', 'date'),
     State('nuevo-dia', 'value'),
     State('nuevo-servicio', 'value'),
     State('nuevos-cocineros', 'value'),
     State('inter-cocinero1', 'value'),
     State('inter-cocinero2', 'value')],
    prevent_initial_call=True
)
def update_comidas(n_add, n_inter, current_data, confirm_clicks, previous_data, 
                   datos_borrar, fecha, tipo, servicio, cocineros, coc1, coc2):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger == 'btn-agregar-comida' and all([fecha, tipo, servicio, cocineros]):
        cocineros_str = ', '.join(cocineros)
        dm.add_data('comidas', (fecha, tipo, servicio, cocineros_str))
        registrar_cambio('Comida', f'Agregada: {tipo} - {fecha}')
        return dm.get_data('comidas').to_dict('records'), "✅ Comida agregada correctamente", False, None
    
    elif trigger == 'btn-intercambiar' and coc1 and coc2:
        comidas_df = dm.get_data('comidas')
        cambios = 0
        for idx, row in comidas_df.iterrows():
            if pd.notna(row['cocineros']):
                cocineros_lista = [c.strip() for c in row['cocineros'].split(',')]
                if coc1 in cocineros_lista:
                    cocineros_lista = [coc2 if c == coc1 else c for c in cocineros_lista]
                    comidas_df.at[idx, 'cocineros'] = ', '.join(cocineros_lista)
                    cambios += 1
                elif coc2 in cocineros_lista:
                    cocineros_lista = [coc1 if c == coc2 else c for c in cocineros_lista]
                    comidas_df.at[idx, 'cocineros'] = ', '.join(cocineros_lista)
                    cambios += 1
        
        dm.save_data('comidas', comidas_df)
        registrar_cambio('Cocineros', f'Intercambiados: {coc1} ↔ {coc2}')
        return comidas_df.to_dict('records'), f"✅ Intercambiados en {cambios} comidas", False, None
    
    elif trigger == 'confirm-delete' and datos_borrar:
        # Usuario confirmó - borrar usando los datos guardados en el store
        registrar_cambio('Comida', 'Eliminada una comida')
        dm.save_data('comidas', pd.DataFrame(datos_borrar))
        return datos_borrar, "✅ Comida eliminada", False, None
    
    elif trigger == 'tabla-comidas':
        if previous_data is not None and len(current_data) < len(previous_data):
            # Se intentó borrar - guardar datos y mostrar confirmación
            return previous_data, "", True, current_data  # ← Guardar current_data en store
        elif previous_data is not None and current_data != previous_data:
            # Edición
            registrar_cambio('Comida', 'Modificada una comida')
            dm.save_data('comidas', pd.DataFrame(current_data))
            return current_data, "", False, None
    
    return dm.get_data('comidas').to_dict('records'), "", False, None

# Callback para lista de compra
@app.callback(
    [Output('tabla-lista', 'data'),
     Output('output-lista', 'children')],
    [Input('btn-agregar-lista', 'n_clicks'),
     Input('tabla-lista', 'data'),
     Input('tabla-lista', 'data_previous')],
    [State('lista-nueva-fecha', 'date'),
     State('lista-nuevo-objeto', 'value')],
    prevent_initial_call=True
)
def update_lista(n_add, current_data, previous_data, fecha, objeto):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger == 'btn-agregar-lista' and fecha and objeto:
        dm.add_data('lista_compra', (fecha, objeto))
        registrar_cambio('Lista Compra', f'Agregado: {objeto}')
        return dm.get_data('lista_compra').to_dict('records'), "✅ Item agregado"
    
    elif trigger == 'tabla-lista':
        if previous_data is not None and current_data != previous_data:
            if len(current_data) < len(previous_data):
                registrar_cambio('Lista Compra', 'Eliminado un item')
            else:
                registrar_cambio('Lista Compra', 'Modificado un item')
            
            dm.save_data('lista_compra', pd.DataFrame(current_data))
            return current_data, ""
    
    return dm.get_data('lista_compra').to_dict('records'), ""

# Callback para mostrar campos según acción
@app.callback(
    Output('campos-accion-dia', 'children'),
    [Input('accion-dia-especifico', 'value')],
    [State('tabla-comidas', 'data')]
)
def mostrar_campos_accion(accion, comidas_data):
    if not accion:
        return []
    
    comidas_df = pd.DataFrame(comidas_data) if comidas_data else dm.get_data('comidas')
    cocineros_unicos = set()
    for _, row in comidas_df.iterrows():
        if pd.notna(row.get('cocineros')):
            cocineros_unicos.update([c.strip() for c in str(row['cocineros']).split(',')])
    cocineros_options = [{'label': c, 'value': c} for c in sorted(cocineros_unicos)]
    
    if accion == 'agregar':
        return [
            dcc.Input(id='dia-nuevo-cocinero', placeholder="Nombre del cocinero", style=STYLES['input'])
        ]
    elif accion == 'eliminar':
        return [
            dcc.Dropdown(id='dia-cocinero-eliminar', options=cocineros_options, placeholder="Cocinero a eliminar", style={'marginBottom': '12px'})
        ]
    elif accion == 'intercambiar':
        return [
            dcc.Dropdown(id='dia-cocinero-origen', options=cocineros_options, placeholder="Cocinero actual", style={'marginBottom': '8px'}),
            dcc.Dropdown(id='dia-cocinero-destino', options=cocineros_options, placeholder="Nuevo cocinero", style={'marginBottom': '8px'})
        ]
    return []

# Callback para ejecutar acción en día específico
@app.callback(
    [Output('output-dia-especifico', 'children'),
     Output('tabla-comidas', 'data', allow_duplicate=True)],
    [Input('btn-ejecutar-dia-especifico', 'n_clicks')],
    [State('selector-dia-especifico', 'value'),
     State('fecha-dia-especifico', 'date'),
     State('accion-dia-especifico', 'value'),
     State('dia-nuevo-cocinero', 'value'),
     State('dia-cocinero-eliminar', 'value'),
     State('dia-cocinero-origen', 'value'),
     State('dia-cocinero-destino', 'value')],
    prevent_initial_call=True
)
def ejecutar_accion_dia(n_clicks, dia, fecha, accion, nuevo_coc, elim_coc, origen_coc, destino_coc):
    if not n_clicks or not dia or not fecha or not accion:
        raise PreventUpdate
    
    comidas_df = dm.get_data('comidas')
    
    # Filtrar por día y fecha
    mask = (comidas_df['dia'] == dia) & (comidas_df['fecha'] == fecha)
    
    if not mask.any():
        return f"⚠️ No se encontró comida para {dia} en {fecha}", comidas_df.to_dict('records')
    
    idx = comidas_df[mask].index[0]
    cocineros_str = comidas_df.at[idx, 'cocineros']
    cocineros_lista = [c.strip() for c in cocineros_str.split(',')]
    
    if accion == 'agregar' and nuevo_coc:
        if nuevo_coc not in cocineros_lista:
            cocineros_lista.append(nuevo_coc)
            comidas_df.at[idx, 'cocineros'] = ', '.join(cocineros_lista)
            dm.save_data('comidas', comidas_df)
            registrar_cambio('Cocineros', f'Agregado {nuevo_coc} a {dia} del {fecha}')
            return f"✅ {nuevo_coc} agregado a {dia}", comidas_df.to_dict('records')
        return f"⚠️ {nuevo_coc} ya está en esta comida", comidas_df.to_dict('records')
    
    elif accion == 'eliminar' and elim_coc:
        if elim_coc in cocineros_lista and len(cocineros_lista) > 1:
            cocineros_lista.remove(elim_coc)
            comidas_df.at[idx, 'cocineros'] = ', '.join(cocineros_lista)
            dm.save_data('comidas', comidas_df)
            registrar_cambio('Cocineros', f'Eliminado {elim_coc} de {dia} del {fecha}')
            return f"✅ {elim_coc} eliminado de {dia}", comidas_df.to_dict('records')
        return f"⚠️ No se puede eliminar (no encontrado o es el único)", comidas_df.to_dict('records')
    
    elif accion == 'intercambiar' and origen_coc and destino_coc:
        if origen_coc in cocineros_lista:
            cocineros_lista = [destino_coc if c == origen_coc else c for c in cocineros_lista]
            comidas_df.at[idx, 'cocineros'] = ', '.join(cocineros_lista)
            dm.save_data('comidas', comidas_df)
            registrar_cambio('Cocineros', f'Intercambiado {origen_coc} → {destino_coc} en {dia} del {fecha}')
            return f"✅ {origen_coc} → {destino_coc} en {dia}", comidas_df.to_dict('records')
        return f"⚠️ {origen_coc} no encontrado en esta comida", comidas_df.to_dict('records')
    
    raise PreventUpdate

# Callback para eventos
@app.callback(
    [Output('tabla-eventos', 'data'),
     Output('output-evento', 'children')],
    [Input('btn-agregar-evento', 'n_clicks'),
     Input('tabla-eventos', 'data'),
     Input('tabla-eventos', 'data_previous')],
    [State('evento-nueva-fecha', 'date'),
     State('evento-nuevo-nombre', 'value'),
     State('evento-nuevo-tipo', 'value')],  # ← SOLO ESTOS STATES
    prevent_initial_call=True
)
def update_eventos(n_add, current_data, previous_data, fecha, nombre, tipo):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger == 'btn-agregar-evento' and fecha and nombre:
        dm.add_data('eventos', (fecha, nombre, tipo or ''))
        registrar_cambio('Eventos', f'Agregado: {nombre}')
        return dm.get_data('eventos').to_dict('records'), "✅ Evento agregado"
    
    elif trigger == 'tabla-eventos':
        if previous_data is not None and current_data != previous_data:
            if len(current_data) < len(previous_data):
                registrar_cambio('Eventos', 'Eliminado un evento')
            else:
                registrar_cambio('Eventos', 'Modificado un evento')
            
            dm.save_data('eventos', pd.DataFrame(current_data))
            return current_data, ""
    
    return dm.get_data('eventos').to_dict('records'), ""

# Callback para cargar fechas según día seleccionado
@app.callback(
    Output('selector-fecha-dia', 'options'),
    [Input('selector-dia', 'value')]
)
def cargar_fechas_dia(dia):
    if not dia:
        return []
    
    comidas_df = dm.get_data('comidas')
    fechas_dia = comidas_df[comidas_df['dia'] == dia]['fecha'].tolist()
    
    return [{'label': f, 'value': f} for f in sorted(fechas_dia)]

# Callback para mostrar info de comida seleccionada
@app.callback(
    Output('info-comida-seleccionada', 'children'),
    [Input('selector-fecha-dia', 'value')],
    [State('selector-dia', 'value')]
)
def mostrar_info_comida(fecha, dia):
    if not fecha or not dia:
        return []
    
    comidas_df = dm.get_data('comidas')
    comida = comidas_df[(comidas_df['dia'] == dia) & (comidas_df['fecha'] == fecha)]
    
    if len(comida) == 0:
        return []
    
    row = comida.iloc[0]
    return html.Div([
        html.Strong("Cocineros actuales: "),
        html.Span(row['cocineros'], style={'color': '#667eea', 'fontWeight': '600'})
    ], style={'padding': '12px', 'background': '#f7fafc', 'borderRadius': '8px'})

# Callback para mostrar campos según acción
@app.callback(
    Output('campos-accion', 'children'),
    [Input('accion-cocinero', 'value')],
    [State('tabla-comidas', 'data')]
)
def mostrar_campos(accion, comidas_data):
    if not accion:
        return []
    
    comidas_df = pd.DataFrame(comidas_data) if comidas_data else dm.get_data('comidas')
    cocineros_unicos = set()
    for _, row in comidas_df.iterrows():
        if pd.notna(row.get('cocineros')):
            cocineros_unicos.update([c.strip() for c in str(row['cocineros']).split(',')])
    cocineros_options = [{'label': c, 'value': c} for c in sorted(cocineros_unicos)]
    
    if accion == 'agregar':
        return dcc.Input(id='nuevo-cocinero-dia', placeholder="Nombre del cocinero", style=STYLES['input'])
    elif accion == 'eliminar':
        return dcc.Dropdown(id='eliminar-cocinero-dia', options=cocineros_options, placeholder="Cocinero a eliminar", style={'marginBottom': '12px'})
    elif accion == 'intercambiar':
        return [
            dcc.Dropdown(id='cocinero-origen-dia', options=cocineros_options, placeholder="Cocinero actual", style={'marginBottom': '8px'}),
            dcc.Dropdown(id='cocinero-destino-dia', options=cocineros_options, placeholder="Nuevo cocinero", style={'marginBottom': '8px'})
        ]
    return []

# Callback para ejecutar acción
@app.callback(
    [Output('output-accion', 'children'),
     Output('tabla-comidas', 'data', allow_duplicate=True),
     Output('info-comida-seleccionada', 'children', allow_duplicate=True)],
    [Input('btn-ejecutar-accion', 'n_clicks')],
    [State('selector-dia', 'value'),
     State('selector-fecha-dia', 'value'),
     State('accion-cocinero', 'value'),
     State('nuevo-cocinero-dia', 'value'),
     State('eliminar-cocinero-dia', 'value'),
     State('cocinero-origen-dia', 'value'),
     State('cocinero-destino-dia', 'value')],
    prevent_initial_call=True
)
def ejecutar_accion(n_clicks, dia, fecha, accion, nuevo, eliminar, origen, destino):
    if not n_clicks or not dia or not fecha or not accion:
        raise PreventUpdate
    
    comidas_df = dm.get_data('comidas')
    mask = (comidas_df['dia'] == dia) & (comidas_df['fecha'] == fecha)
    
    if not mask.any():
        return "⚠️ No se encontró la comida", comidas_df.to_dict('records'), []
    
    idx = comidas_df[mask].index[0]
    cocineros_lista = [c.strip() for c in comidas_df.at[idx, 'cocineros'].split(',')]
    
    if accion == 'agregar' and nuevo:
        if nuevo not in cocineros_lista:
            cocineros_lista.append(nuevo)
            comidas_df.at[idx, 'cocineros'] = ', '.join(cocineros_lista)
            dm.save_data('comidas', comidas_df)
            registrar_cambio('Cocineros', f'Agregado {nuevo} a {dia} - {fecha}')
            info = html.Div([html.Strong("Cocineros actuales: "), html.Span(', '.join(cocineros_lista), style={'color': '#667eea', 'fontWeight': '600'})], 
                          style={'padding': '12px', 'background': '#f7fafc', 'borderRadius': '8px'})
            return f"✅ {nuevo} agregado", comidas_df.to_dict('records'), info
        return f"⚠️ {nuevo} ya está", comidas_df.to_dict('records'), []
    
    elif accion == 'eliminar' and eliminar:
        if eliminar in cocineros_lista and len(cocineros_lista) > 1:
            cocineros_lista.remove(eliminar)
            comidas_df.at[idx, 'cocineros'] = ', '.join(cocineros_lista)
            dm.save_data('comidas', comidas_df)
            registrar_cambio('Cocineros', f'Eliminado {eliminar} de {dia} - {fecha}')
            info = html.Div([html.Strong("Cocineros actuales: "), html.Span(', '.join(cocineros_lista), style={'color': '#667eea', 'fontWeight': '600'})], 
                          style={'padding': '12px', 'background': '#f7fafc', 'borderRadius': '8px'})
            return f"✅ {eliminar} eliminado", comidas_df.to_dict('records'), info
        return "⚠️ No se puede eliminar", comidas_df.to_dict('records'), []
    
    elif accion == 'intercambiar' and origen and destino:
        if origen in cocineros_lista:
            cocineros_lista = [destino if c == origen else c for c in cocineros_lista]
            comidas_df.at[idx, 'cocineros'] = ', '.join(cocineros_lista)
            dm.save_data('comidas', comidas_df)
            registrar_cambio('Cocineros', f'{origen} → {destino} en {dia} - {fecha}')
            info = html.Div([html.Strong("Cocineros actuales: "), html.Span(', '.join(cocineros_lista), style={'color': '#667eea', 'fontWeight': '600'})], 
                          style={'padding': '12px', 'background': '#f7fafc', 'borderRadius': '8px'})
            return f"✅ {origen} → {destino}", comidas_df.to_dict('records'), info
        return f"⚠️ {origen} no encontrado", comidas_df.to_dict('records'), []
    
    raise PreventUpdate

# Store para guardar datos temporales del borrado
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='store-datos-borrar'),  
    dcc.ConfirmDialog(
        id='confirm-delete',
        message='¿Estás seguro de eliminar esta comida?',
    ),
    create_navbar(),
    html.Div(id='page-content')
])


# ===== INICIALIZACIÓN =====

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 PENYA L'ALBENC - Versión Moderna")
    print("=" * 60)
    
    # VERIFICAR DATOS CARGADOS
    print("\n📊 VERIFICACIÓN DE DATOS:")
    for tabla in ['comidas', 'eventos', 'lista_compra', 'mantenimiento', 'fiestas']:
        df = dm.get_data(tabla)
        print(f"  • {tabla}: {len(df)} filas")
        if len(df) > 0:
            print(f"    Columnas: {list(df.columns)}")
    print("=" * 60)
    
    # Asegurar que existe la tabla de cambios
    try:
        cambios_df = dm.get_data('cambios')
        if len(cambios_df) == 0:
            registrar_cambio('Sistema', 'Aplicación inicializada')
    except:
        pass
    
    # LIMPIEZA AUTOMÁTICA
    print("\n🧹 Ejecutando limpieza automática de comidas antiguas...")
    limpiar_comidas_antiguas()
    
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Puerto: {port}")
    print(f"🛠️ Debug: {debug}")
    print("=" * 60)
    
    app.run_server(debug=debug, host='0.0.0.0', port=port)