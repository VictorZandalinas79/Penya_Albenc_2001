"""
Calculador de fechas para fiestas de PENYA L'ALBENC Vilafranca
"""

from datetime import date, timedelta
import calendar

def tercer_sabado_enero(año):
    """Calcular el tercer sábado de enero - Sant Antoni"""
    primer_dia = date(año, 1, 1)
    # Encontrar el primer sábado
    dias_hasta_sabado = (5 - primer_dia.weekday()) % 7  # 5 = sábado
    primer_sabado = primer_dia + timedelta(days=dias_hasta_sabado)
    # El tercer sábado es 14 días después
    tercer_sabado = primer_sabado + timedelta(days=14)
    return tercer_sabado

def sabado_cercano_28_abril(año):
    """Calcular el sábado más cercano al 28 de abril - Brena St Vicent"""
    dia_28 = date(año, 4, 28)
    dia_semana = dia_28.weekday()  # 0=lunes, 6=domingo
    
    if dia_semana == 5:  # Si 28/4 es sábado
        return dia_28
    elif dia_semana < 5:  # Si es antes del sábado
        dias_hasta_sabado = 5 - dia_semana
        return dia_28 + timedelta(days=dias_hasta_sabado)
    else:  # Si es domingo (6)
        return dia_28 - timedelta(days=1)

def tercer_sabado_julio(año):
    """Calcular el tercer sábado de julio - Fira Magdalena"""
    primer_dia = date(año, 7, 1)
    # Encontrar el primer sábado
    dias_hasta_sabado = (5 - primer_dia.weekday()) % 7
    primer_sabado = primer_dia + timedelta(days=dias_hasta_sabado)
    # El tercer sábado es 14 días después
    tercer_sabado = primer_sabado + timedelta(days=14)
    return tercer_sabado

def ultimo_sabado_mayo(año):
    """Calcular el último sábado de mayo - Penya Taurina"""
    # Último día de mayo
    ultimo_dia = date(año, 5, 31)
    dia_semana = ultimo_dia.weekday()
    
    if dia_semana == 5:  # Si 31/5 es sábado
        return ultimo_dia
    elif dia_semana < 5:  # Si es antes del sábado
        dias_atras = dia_semana + 2  # Ir al sábado anterior
        return ultimo_dia - timedelta(days=dias_atras)
    else:  # Si es domingo (6)
        return ultimo_dia - timedelta(days=1)

def generar_fechas_fiestas(año):
    """Generar todas las fechas de fiestas para un año dado"""
    return {
        'sant_antoni': tercer_sabado_enero(año),
        'brena_st_vicent': sabado_cercano_28_abril(año),
        'fira_magdalena': tercer_sabado_julio(año),
        'penya_taurina': ultimo_sabado_mayo(año)
    }

# Datos de personas por año y evento (del PDF completo)
DATOS_PENYA = {
    2025: {
        'manteniment': 'David, Juan Fernando',
        'cadafals': 'David, Juan Fernando, Diego, Miguel A.',
        'sant_antoni': 'Lluis, Alonso, Raul A., David',
        'brena_st_vicent': 'Xisco, Serafin, Alfonso, Raul M.',
        'fira_magdalena': 'Juan Ramon, Victor Z., Miguel A., Oscar',
        'penya_taurina': 'Juan Fernando, Victor M., Diego'
    },
    2026: {
        'manteniment': 'Diego, Miguel A.',
        'cadafals': 'Diego, Miguel A., Xisco, Serafin',
        'sant_antoni': 'Serafin, Juan Fernando, Oscar, Alfonso',
        'brena_st_vicent': 'Alonso, Victor M., Juan Ramon, Miguel A.',
        'fira_magdalena': 'Xisco, David, Diego, Raul A.',
        'penya_taurina': 'Victor Z., Lluis, Raul M.'
    },
    2027: {
        'manteniment': 'Xisco, Serafin',
        'cadafals': 'Xisco, Serafin, Juan Ramon, Oscar',
        'sant_antoni': 'Raul A., Diego, Alonso, Victor Z.',
        'brena_st_vicent': 'Lluis, David, Oscar, Serafin',
        'fira_magdalena': 'Juan Fernando, Victor M., Alfonso, Juan Ramon',
        'penya_taurina': 'Xisco, Miguel A., Raul M.'
    },
    2028: {
        'manteniment': 'Juan Ramon, Oscar',
        'cadafals': 'Juan Ramon, Oscar, Alfonso, Victor Z.',
        'sant_antoni': 'Juan Fernando, Serafin, Alfonso, David',
        'brena_st_vicent': 'Xisco, Diego, Victor Z., Juan Ramon',
        'fira_magdalena': 'Raul M., Oscar, Miguel A., Raul A.',
        'penya_taurina': 'Victor M., Alonso, Lluis'
    },
    2029: {
        'manteniment': 'Alfonso, Victor Z.',
        'cadafals': 'Alfonso, Victor Z., David, Victor M.',
        'sant_antoni': 'Victor M., Raul A., Xisco, Miguel A.',
        'brena_st_vicent': 'Alonso, Lluis, Juan Fernando, Serafin',
        'fira_magdalena': 'Victor Z., Diego, Juan Ramon, David',
        'penya_taurina': 'Oscar, Raul M., Alfonso'
    },
    2030: {
        'manteniment': 'David, Victor M.',
        'cadafals': 'David, Victor M., Xisco, Alonso',
        'sant_antoni': 'Juan Fernando, Alonso, Diego, Victor Z.',
        'brena_st_vicent': 'Raul A., Oscar, David, Alfonso',
        'fira_magdalena': 'Serafin, Miguel A., Victor M., Lluis',
        'penya_taurina': 'Xisco, Juan Ramon, Raul M.'
    },
    2031: {
        'manteniment': 'Xisco, Alonso',
        'cadafals': 'Xisco, Alonso, Serafin, Raul M.',
        'sant_antoni': 'Victor M., Juan Ramon, Oscar, David',
        'brena_st_vicent': 'Raul M., Alonso, Lluis, Xisco',
        'fira_magdalena': 'Diego, Raul A., Juan Fernando, Victor Z.',
        'penya_taurina': 'Alfonso, Serafin, Miguel A.'
    },
    2032: {
        'manteniment': 'Serafin, Raul M.',
        'cadafals': 'Serafin, Raul M., Alfonso, Raul A.',
        'sant_antoni': 'Victor Z., Raul M., Serafin, Juan Fernando',
        'brena_st_vicent': 'Victor M., Raul A., Diego, Alfonso',
        'fira_magdalena': 'Juan Ramon, Oscar, Lluis, Miguel A.',
        'penya_taurina': 'David, Xisco, Alonso'
    },
    2033: {
        'manteniment': 'Alfonso, Raul A.',
        'cadafals': 'Alfonso, Raul A., Miguel A., Juan Fernando',
        'sant_antoni': 'Alfonso, Miguel A., Victor M., David',
        'brena_st_vicent': 'Xisco, Lluis, Alonso, Victor Z.',
        'fira_magdalena': 'Raul M., Juan Fernando, Serafin, Raul A.',
        'penya_taurina': 'Diego, Juan Ramon, Oscar'
    },
    2034: {
        'manteniment': 'Miguel A., Juan Fernando',
        'cadafals': 'Miguel A., Juan Fernando, Oscar, Diego',
        'sant_antoni': 'Raul A., Lluis, Diego, Juan Fernando',
        'brena_st_vicent': 'Alfonso, Victor M., David, Serafin',
        'fira_magdalena': 'Juan Ramon, Oscar, Xisco, Victor Z.',
        'penya_taurina': 'Raul M., Miguel A., Alonso'
    },
    2035: {
        'manteniment': 'Oscar, Diego',
        'cadafals': 'Oscar, Diego, Juan Ramon, Victor M.',
        'sant_antoni': 'Juan Ramon, Alonso, Xisco, David',
        'brena_st_vicent': 'Raul A., Lluis, Diego, Victor Z.',
        'fira_magdalena': 'Victor M., Alfonso, Juan Fernando, Miguel A.',
        'penya_taurina': 'Raul M., Oscar, Serafin'
    },
    2036: {
        'manteniment': 'Juan Ramon, Victor M.',
        'cadafals': 'Juan Ramon, Victor M., David, Victor Z.',
        'sant_antoni': 'Victor Z., Diego, Raul A., Raul M.',
        'brena_st_vicent': 'Juan Fernando, Alfonso, David, Oscar',
        'fira_magdalena': 'Serafin, Lluis, Xisco, Juan Ramon',
        'penya_taurina': 'Alonso, Victor M., Miguel A.'
    },
    2037: {
        'manteniment': 'David, Victor Z.',
        'cadafals': 'David, Victor Z., Xisco, Raul M.',
        'sant_antoni': 'Alfonso, Victor M., Miguel A., Xisco',
        'brena_st_vicent': 'Alonso, Raul M., Raul A., Lluis',
        'fira_magdalena': 'Diego, Victor Z., David, Juan Fernando',
        'penya_taurina': 'Oscar, Serafin, Juan Ramon'
    },
    2038: {
        'manteniment': 'Xisco, Raul M.',
        'cadafals': 'Xisco, Raul M., Serafin, Alonso',
        'sant_antoni': 'Raul A., Raul M., Juan Fernando, David',
        'brena_st_vicent': 'Victor Z., Juan Ramon, Diego, Victor M.',
        'fira_magdalena': 'Alonso, Oscar, Xisco, Alfonso',
        'penya_taurina': 'Miguel A., Serafin, Lluis'
    },
    2039: {
        'manteniment': 'Serafin, Alonso',
        'cadafals': 'Serafin, Alonso, Alfonso, Raul A.',
        'sant_antoni': 'Oscar, Serafin, Juan Ramon, Alfonso',
        'brena_st_vicent': 'Raul M., Lluis, Alonso, Juan Fernando',
        'fira_magdalena': 'Victor M., Raul A., Diego, Miguel A.',
        'penya_taurina': 'Victor Z., David, Xisco'
    },
    2040: {
        'manteniment': 'Alfonso, Raul A.',
        'cadafals': 'Alfonso, Juan Fernando, Miguel A., Raul A.',
        'sant_antoni': 'Xisco, Raul M., David, Victor Z.',
        'brena_st_vicent': 'Alfonso, Victor M., Diego, Oscar',
        'fira_magdalena': 'Serafin, Lluis, Alonso, Juan Fernando',
        'penya_taurina': 'Miguel A., Raul A., Juan Ramon'
    },
    2041: {
        'manteniment': 'Miguel A., Juan Fernando',
        'cadafals': 'Miguel A., Juan Fernando, Oscar, Victor M.',
        'sant_antoni': 'Serafin, Miguel A., Alonso, Raul A.',
        'brena_st_vicent': 'Lluis, Raul M., Juan Ramon, David',
        'fira_magdalena': 'Diego, Xisco, Victor Z., Victor M.',
        'penya_taurina': 'Oscar, Juan Fernando, Alfonso'
    },
    2042: {
        'manteniment': 'Oscar, Victor M.',
        'cadafals': 'Oscar, Victor M., Alfonso, Diego',
        'sant_antoni': 'Lluis, Raul M., Juan Ramon, Oscar',
        'brena_st_vicent': 'Alonso, Miguel A., Raul A., Xisco',
        'fira_magdalena': 'Alfonso, Juan Fernando, Serafin, David',
        'penya_taurina': 'Victor M., Victor Z., Diego'
    },
    2043: {
        'manteniment': 'Alfonso, Diego',
        'cadafals': 'Alfonso, Diego, Juan Ramon, Alonso',
        'sant_antoni': 'Alfonso, Xisco, Victor M., Juan Fernando',
        'brena_st_vicent': 'Victor Z., Diego, Juan Ramon, David',
        'fira_magdalena': 'Raul M., Alonso, Lluis, Miguel A.',
        'penya_taurina': 'Serafin, Raul A., Oscar'
    },
    2044: {
        'manteniment': 'Juan Ramon, Alonso',
        'cadafals': 'Juan Ramon, Alonso, Miguel A., Victor Z.',
        'sant_antoni': 'Diego, Miguel A., Serafin, Oscar',
        'brena_st_vicent': 'Juan Fernando, Alfonso, Alonso, Raul A.',
        'fira_magdalena': 'Victor M., Xisco, Victor Z., David',
        'penya_taurina': 'Lluis, Juan Ramon, Raul M.'
    },
    2045: {
        'manteniment': 'Miguel A., Victor Z.',
        'cadafals': 'Miguel A., Victor Z., Serafin, Juan Fernando',
        'sant_antoni': 'Victor M., Alonso, Alfonso, Raul A.',
        'brena_st_vicent': 'Xisco, Diego, Raul M., Serafin',
        'fira_magdalena': 'Oscar, Miguel A., Juan Ramon, Juan Fernando',
        'penya_taurina': 'Lluis, David, Victor Z.'
    }
}

def obtener_datos_año(año):
    """Obtener datos de un año específico"""
    return DATOS_PENYA.get(año, {})

def obtener_todos_los_años():
    """Obtener lista de todos los años disponibles"""
    return sorted(DATOS_PENYA.keys())