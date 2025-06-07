"""
Gestor de datos para PENYA L'ALBENC
Maneja la lectura, escritura y operaciones con archivos Parquet
"""

import pandas as pd
import logging
from datetime import date, datetime
from pathlib import Path
import shutil
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class DataManager:
    """Clase para gestionar los datos de la aplicación"""
    
    def __init__(self):
        """Inicializar el gestor de datos"""
        self.config = Config()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Asegurar que existen todos los directorios necesarios"""
        self.config.DATA_FOLDER.mkdir(exist_ok=True)
        self.config.BACKUP_FOLDER.mkdir(exist_ok=True)
        logger.info(f"📁 Directorios verificados: {self.config.DATA_FOLDER}")
    
    def create_backup(self, filename: str) -> bool:
        """
        Crear backup de un archivo antes de modificarlo
        
        Args:
            filename: Nombre del archivo a respaldar
            
        Returns:
            bool: True si el backup fue exitoso
        """
        try:
            source_file = self.config.DATA_FOLDER / filename
            if source_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{filename.replace('.parquet', '')}_{timestamp}.parquet"
                backup_file = self.config.BACKUP_FOLDER / backup_name
                
                shutil.copy2(source_file, backup_file)
                logger.info(f"💾 Backup creado: {backup_name}")
                
                # Limpiar backups antiguos
                self._cleanup_old_backups(filename.replace('.parquet', ''))
                return True
        except Exception as e:
            logger.error(f"❌ Error creando backup de {filename}: {e}")
            return False
    
    def _cleanup_old_backups(self, base_filename: str):
        """Limpiar backups antiguos manteniendo solo los más recientes"""
        try:
            backup_files = list(self.config.BACKUP_FOLDER.glob(f"{base_filename}_*.parquet"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Eliminar backups antiguos si hay más del máximo permitido
            for old_backup in backup_files[self.config.MAX_BACKUPS:]:
                old_backup.unlink()
                logger.info(f"🗑️ Backup antiguo eliminado: {old_backup.name}")
                
        except Exception as e:
            logger.error(f"❌ Error limpiando backups: {e}")
    
    def save_dataframe(self, df: pd.DataFrame, filename: str) -> bool:
        """
        Guardar DataFrame en archivo Parquet con backup
        
        Args:
            df: DataFrame a guardar
            filename: Nombre del archivo
            
        Returns:
            bool: True si el guardado fue exitoso
        """
        try:
            file_path = self.config.DATA_FOLDER / filename
            
            # Crear backup si el archivo existe
            if file_path.exists() and self.config.BACKUP_ENABLED:
                self.create_backup(filename)
            
            # Guardar el archivo
            df.to_parquet(file_path, index=False)
            logger.info(f"💾 Datos guardados en {filename}: {len(df)} registros")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando {filename}: {e}")
            return False
    
    def load_dataframe(self, filename: str) -> pd.DataFrame:
        """
        Cargar DataFrame desde archivo Parquet
        
        Args:
            filename: Nombre del archivo a cargar
            
        Returns:
            pd.DataFrame: DataFrame cargado o vacío si hay error
        """
        try:
            file_path = self.config.DATA_FOLDER / filename
            
            if file_path.exists():
                df = pd.read_parquet(file_path)
                logger.info(f"📖 Datos cargados de {filename}: {len(df)} registros")
                return df
            else:
                logger.warning(f"⚠️ Archivo no encontrado: {filename}")
                return self._create_empty_dataframe(filename)
                
        except Exception as e:
            logger.error(f"❌ Error cargando {filename}: {e}")
            return self._create_empty_dataframe(filename)
    
    def _create_empty_dataframe(self, filename: str) -> pd.DataFrame:
        """Crear DataFrame vacío según el tipo de archivo"""
        
        schemas = {
            'comidas.parquet': {
                'fecha': pd.Series([], dtype='datetime64[ns]'),
                'tipo_evento': pd.Series([], dtype='object'),
                'tipo_comida': pd.Series([], dtype='object'),
                'cocineros': pd.Series([], dtype='object')
            },
            'lista_compra.parquet': {
                'fecha': pd.Series([], dtype='datetime64[ns]'),
                'articulos': pd.Series([], dtype='object')
            },
            'mantenimiento.parquet': {
                'año': pd.Series([], dtype='int64'),
                'mantenimiento': pd.Series([], dtype='object'),
                'cadafals': pd.Series([], dtype='object')
            },
            'fiestas.parquet': {
                'fecha': pd.Series([], dtype='datetime64[ns]'),
                'tipo_fiesta': pd.Series([], dtype='object'),
                'encargados_cocina': pd.Series([], dtype='object'),
                'menu_cena': pd.Series([], dtype='object')
            },
            'cambios_log.parquet': {
                'timestamp': pd.Series([], dtype='datetime64[ns]'),
                'seccion': pd.Series([], dtype='object'),
                'tipo_cambio': pd.Series([], dtype='object'),
                'descripcion': pd.Series([], dtype='object'),
                'usuario': pd.Series([], dtype='object')
            }
        }
        
        if filename in schemas:
            return pd.DataFrame(schemas[filename])
        else:
            logger.warning(f"⚠️ Schema no definido para {filename}")
            return pd.DataFrame()

# Instancia global del gestor de datos
data_manager = DataManager()

def log_cambio(seccion, tipo_cambio, descripcion, usuario='sistema'):
    """Registrar un cambio en el log"""
    try:
        from datetime import datetime
        
        # Cargar log existente o crear nuevo
        try:
            log_df = data_manager.load_dataframe('cambios_log.parquet')
        except:
            log_df = pd.DataFrame({
                'timestamp': [],
                'seccion': [],
                'tipo_cambio': [],
                'descripcion': [],
                'usuario': []
            })
        
        # Agregar nuevo cambio
        nuevo_cambio = pd.DataFrame({
            'timestamp': [datetime.now()],
            'seccion': [seccion],
            'tipo_cambio': [tipo_cambio],
            'descripcion': [descripcion],
            'usuario': [usuario]
        })
        
        log_df = pd.concat([log_df, nuevo_cambio], ignore_index=True)
        
        # Mantener solo los últimos 100 cambios
        if len(log_df) > 100:
            log_df = log_df.tail(100)
        
        data_manager.save_dataframe(log_df, 'cambios_log.parquet')
        logger.info(f"📝 Cambio registrado: {seccion} - {tipo_cambio}")
        
    except Exception as e:
        logger.error(f"Error registrando cambio: {e}")

def obtener_ultimos_cambios(n=10):
    """Obtener los últimos N cambios"""
    try:
        log_df = data_manager.load_dataframe('cambios_log.parquet')
        if len(log_df) == 0:
            return []
        
        # Ordenar por timestamp descendente y tomar los últimos N
        log_df = log_df.sort_values('timestamp', ascending=False).head(n)
        return log_df.to_dict('records')
    except:
        return []

def force_update_real_data():
    """Forzar la actualización con datos reales del PDF"""
    logger.info("🔄 Forzando actualización con datos reales del PDF...")
    
    # Importar el calculador de fechas
    from src.fecha_calculator import generar_fechas_fiestas, obtener_datos_año, obtener_todos_los_años
    
    # Crear backup de datos existentes si existen
    for archivo in ['mantenimiento.parquet', 'comidas.parquet']:
        archivo_path = Config.DATA_FOLDER / archivo
        if archivo_path.exists():
            data_manager.create_backup(archivo)
    
    # FORZAR actualización de mantenimiento
    logger.info("📋 Actualizando mantenimiento con datos reales...")
    años = obtener_todos_los_años()
    mantenimiento_data = []
    
    for año in años:
        datos_año = obtener_datos_año(año)
        mantenimiento_data.append({
            'año': año,
            'mantenimiento': datos_año.get('manteniment', ''),
            'cadafals': datos_año.get('cadafals', '')
        })
    
    mant_df = pd.DataFrame(mantenimiento_data)
    data_manager.save_dataframe(mant_df, 'mantenimiento.parquet')
    log_cambio('Mantenimiento', 'Actualización masiva', f'Cargados {len(mant_df)} años del PDF (2025-2045)')
    logger.info(f"✅ Mantenimiento actualizado: {len(mant_df)} años (2025-2045)")
    
    # FORZAR actualización de COMIDAS con nueva estructura de 4 columnas
    logger.info("🍽️ Actualizando comidas con nueva estructura (4 columnas)...")
    comidas_data = []
    
    from datetime import timedelta
    
    for año in años:
        fechas_año = generar_fechas_fiestas(año)
        datos_año = obtener_datos_año(año)
        
        # Sant Antoni (tercer sábado enero - solo cena)
        if 'sant_antoni' in fechas_año and 'sant_antoni' in datos_año:
            comidas_data.append({
                'fecha': fechas_año['sant_antoni'],
                'tipo_evento': 'Sant Antoni',
                'tipo_comida': 'Cena',
                'cocineros': datos_año['sant_antoni']
            })
        
        # Brena St Vicent (sábado cercano 28 abril - comida y cena)
        if 'brena_st_vicent' in fechas_año and 'brena_st_vicent' in datos_año:
            comidas_data.append({
                'fecha': fechas_año['brena_st_vicent'],
                'tipo_evento': 'Brena St Vicent',
                'tipo_comida': 'Comida y Cena',
                'cocineros': datos_año['brena_st_vicent']
            })
        
        # Fira Magdalena (tercer sábado julio - comida y cena)
        if 'fira_magdalena' in fechas_año and 'fira_magdalena' in datos_año:
            comidas_data.append({
                'fecha': fechas_año['fira_magdalena'],
                'tipo_evento': 'Fira Magdalena',
                'tipo_comida': 'Comida y Cena',
                'cocineros': datos_año['fira_magdalena']
            })
        
        # Penya Taurina (último sábado mayo - solo comida)
        if 'penya_taurina' in fechas_año and 'penya_taurina' in datos_año:
            comidas_data.append({
                'fecha': fechas_año['penya_taurina'],
                'tipo_evento': 'Penya Taurina',
                'tipo_comida': 'Comida',
                'cocineros': datos_año['penya_taurina']
            })
    
    # Agregar algunas comidas adicionales de semana normal con rotación
    base_date = date.today()
    encargados_rotacion = [
        "David, Juan Fernando", "Diego, Miguel A.", "Xisco, Serafin", 
        "Juan Ramon, Oscar", "Alfonso, Victor Z.", "Miguel A., Raul A.", 
        "Lluis, Alonso", "Victor M., Raul M."
    ]
    
    # Agregar comidas de semana para las próximas 4 semanas
    for i in range(28):
        fecha = base_date + timedelta(days=i)
        # Solo días laborables (lunes a viernes) para comidas normales
        if fecha.weekday() < 5:  # Lunes a viernes
            # Verificar que no coincida con fechas especiales ya agregadas
            fecha_existente = any(
                item['fecha'] == fecha 
                for item in comidas_data
            )
            if not fecha_existente:
                comidas_data.append({
                    'fecha': fecha,
                    'tipo_evento': 'Comida Normal',
                    'tipo_comida': 'Comida',
                    'cocineros': encargados_rotacion[i % len(encargados_rotacion)]
                })
    
    comidas_df = pd.DataFrame(comidas_data)
    comidas_df = comidas_df.sort_values('fecha')
    data_manager.save_dataframe(comidas_df, 'comidas.parquet')
    log_cambio('Comidas', 'Actualización masiva', f'Cargadas {len(comidas_df)} comidas con nueva estructura 4 columnas')
    logger.info(f"✅ Comidas actualizadas: {len(comidas_df)} registros con nueva estructura")
    
    # LIMPIAR fiestas (dejar vacío para eventos especiales futuros)
    logger.info("🎉 Limpiando fiestas (quedará vacío para eventos especiales futuros)...")
    fiestas_df = pd.DataFrame({
        'fecha': [],
        'tipo_fiesta': [],
        'encargados_cocina': [],
        'menu_cena': []
    })
    data_manager.save_dataframe(fiestas_df, 'fiestas.parquet')
    log_cambio('Fiestas', 'Limpieza', 'Tabla vaciada para eventos especiales futuros')
    logger.info("✅ Fiestas limpiadas (vacías para eventos especiales futuros)")
    
    return len(mant_df), len(comidas_df)

def create_initial_data():
    """Crear archivos de datos iniciales con datos reales de PENYA L'ALBENC y nueva estructura"""
    logger.info("🔧 Creando datos reales de PENYA L'ALBENC con nueva estructura...")
    
    # Importar el calculador de fechas
    from src.fecha_calculator import generar_fechas_fiestas, obtener_datos_año, obtener_todos_los_años
    
    # SIEMPRE crear/actualizar mantenimiento con datos reales del PDF
    logger.info("📋 Creando datos de mantenimiento reales...")
    años = obtener_todos_los_años()
    mantenimiento_data = []
    
    for año in años:
        datos_año = obtener_datos_año(año)
        mantenimiento_data.append({
            'año': año,
            'mantenimiento': datos_año.get('manteniment', ''),
            'cadafals': datos_año.get('cadafals', '')
        })
    
    mant_df = pd.DataFrame(mantenimiento_data)
    data_manager.save_dataframe(mant_df, 'mantenimiento.parquet')
    log_cambio('Mantenimiento', 'Inicialización', f'Creados {len(mant_df)} años del PDF')
    logger.info(f"✅ Mantenimiento: {len(mant_df)} años creados (2025-2045) con datos reales")
    
    # CREAR comidas con nueva estructura de 4 columnas
    logger.info("🍽️ Creando comidas con nueva estructura de 4 columnas...")
    comidas_data = []
    
    from datetime import timedelta
    
    # Primero, agregar las fechas especiales del PDF
    for año in [2025, 2026, 2027]:  # Solo algunos años iniciales
        fechas_año = generar_fechas_fiestas(año)
        datos_año = obtener_datos_año(año)
        
        # Sant Antoni (solo cena)
        if 'sant_antoni' in fechas_año and 'sant_antoni' in datos_año:
            comidas_data.append({
                'fecha': fechas_año['sant_antoni'],
                'tipo_evento': 'Sant Antoni',
                'tipo_comida': 'Cena',
                'cocineros': datos_año['sant_antoni']
            })
        
        # Brena St Vicent (comida y cena)
        if 'brena_st_vicent' in fechas_año and 'brena_st_vicent' in datos_año:
            comidas_data.append({
                'fecha': fechas_año['brena_st_vicent'],
                'tipo_evento': 'Brena St Vicent',
                'tipo_comida': 'Comida y Cena',
                'cocineros': datos_año['brena_st_vicent']
            })
        
        # Fira Magdalena (comida y cena)
        if 'fira_magdalena' in fechas_año and 'fira_magdalena' in datos_año:
            comidas_data.append({
                'fecha': fechas_año['fira_magdalena'],
                'tipo_evento': 'Fira Magdalena',
                'tipo_comida': 'Comida y Cena',
                'cocineros': datos_año['fira_magdalena']
            })
        
        # Penya Taurina (solo comida)
        if 'penya_taurina' in fechas_año and 'penya_taurina' in datos_año:
            comidas_data.append({
                'fecha': fechas_año['penya_taurina'],
                'tipo_evento': 'Penya Taurina',
                'tipo_comida': 'Comida',
                'cocineros': datos_año['penya_taurina']
            })
    
    # Luego, agregar comidas normales de semana
    base_date = date.today()
    encargados_rotacion = [
        "David, Juan Fernando", "Diego, Miguel A.", "Xisco, Serafin", 
        "Juan Ramon, Oscar", "Alfonso, Victor Z.", "Miguel A., Raul A.", 
        "Lluis, Alonso", "Victor M., Raul M."
    ]
    
    # Agregar 4 semanas de comidas normales
    for i in range(28):
        fecha = base_date + timedelta(days=i)
        # Solo días laborables para comidas normales
        if fecha.weekday() < 5:  # Lunes a viernes
            # Verificar que no coincida con fechas especiales
            fecha_existente = any(
                item['fecha'] == fecha 
                for item in comidas_data
            )
            if not fecha_existente:
                comidas_data.append({
                    'fecha': fecha,
                    'tipo_evento': 'Comida Normal',
                    'tipo_comida': 'Comida',
                    'cocineros': encargados_rotacion[i % len(encargados_rotacion)]
                })
        
        # Cenas de fin de semana
        if fecha.weekday() >= 4:  # Viernes a domingo
            fecha_existente = any(
                item['fecha'] == fecha 
                for item in comidas_data
            )
            if not fecha_existente:
                comidas_data.append({
                    'fecha': fecha,
                    'tipo_evento': 'Comida Normal',
                    'tipo_comida': 'Cena',
                    'cocineros': encargados_rotacion[(i+1) % len(encargados_rotacion)]
                })
    
    comidas_df = pd.DataFrame(comidas_data)
    comidas_df = comidas_df.sort_values('fecha')
    data_manager.save_dataframe(comidas_df, 'comidas.parquet')
    log_cambio('Comidas', 'Inicialización', f'Creadas {len(comidas_df)} comidas con estructura 4 columnas')
    logger.info(f"✅ Comidas: {len(comidas_df)} registros creados con nueva estructura 4 columnas")
    
    # FIESTAS: Dejar vacío para eventos especiales futuros
    logger.info("🎉 Creando tabla de fiestas vacía (para eventos especiales futuros)...")
    fiestas_df = pd.DataFrame({
        'fecha': [],
        'tipo_fiesta': [],
        'encargados_cocina': [],
        'menu_cena': []
    })
    data_manager.save_dataframe(fiestas_df, 'fiestas.parquet')
    log_cambio('Fiestas', 'Inicialización', 'Tabla vacía creada para eventos especiales')
    logger.info("✅ Fiestas: Tabla vacía creada (lista para eventos especiales)")
    
    # Crear datos básicos para lista de compra (solo si no existe)
    if not Config.LISTA_COMPRA_FILE.exists():
        logger.info("🛒 Creando datos de lista de compra básicos...")
        from datetime import timedelta
        
        compras_data = [
            (date.today() - timedelta(days=3), "Pan, Leche, Huevos, Aceite de oliva"),
            (date.today() - timedelta(days=2), "Tomates, Cebolla, Ajo, Pimientos"),
            (date.today() - timedelta(days=1), "Arroz, Lentejas, Garbanzos, Pasta"),
            (date.today(), "Pollo, Pescado, Ternera, Cerdo"),
            (date.today() + timedelta(days=1), "Yogur, Queso, Mantequilla, Nata"),
            (date.today() + timedelta(days=2), "Manzanas, Plátanos, Naranjas, Limones"),
            (date.today() + timedelta(days=3), "Patatas, Zanahorias, Calabacín, Brócoli"),
            (date.today() + timedelta(days=4), "Detergente, Papel higiénico, Servilletas"),
        ]
        
        lista_df = pd.DataFrame({
            'fecha': [item[0] for item in compras_data],
            'articulos': [item[1] for item in compras_data]
        })
        data_manager.save_dataframe(lista_df, 'lista_compra.parquet')
        log_cambio('Lista Compra', 'Inicialización', f'Creadas {len(lista_df)} entradas básicas')
        logger.info(f"✅ Lista de compra: {len(lista_df)} registros creados")

def load_all_data() -> Dict[str, pd.DataFrame]:
    """
    Cargar todos los datos de la aplicación
    
    Returns:
        Dict con todos los DataFrames
    """
    return {
        'comidas': data_manager.load_dataframe('comidas.parquet'),
        'lista_compra': data_manager.load_dataframe('lista_compra.parquet'),
        'mantenimiento': data_manager.load_dataframe('mantenimiento.parquet'),
        'fiestas': data_manager.load_dataframe('fiestas.parquet')
    }

def save_data(df: pd.DataFrame, data_type: str) -> bool:
    """
    Guardar datos según el tipo
    
    Args:
        df: DataFrame a guardar
        data_type: Tipo de datos ('comidas', 'lista_compra', 'mantenimiento', 'fiestas')
        
    Returns:
        bool: True si fue exitoso
    """
    filename_map = {
        'comidas': 'comidas.parquet',
        'lista_compra': 'lista_compra.parquet',
        'mantenimiento': 'mantenimiento.parquet',
        'fiestas': 'fiestas.parquet'
    }
    
    if data_type in filename_map:
        return data_manager.save_dataframe(df, filename_map[data_type])
    else:
        logger.error(f"❌ Tipo de datos no válido: {data_type}")
        return False

def get_data_stats() -> Dict[str, Any]:
    """
    Obtener estadísticas de los datos
    
    Returns:
        Dict con estadísticas de cada tabla
    """
    data = load_all_data()
    stats = {}
    
    for key, df in data.items():
        stats[key] = {
            'total_records': len(df),
            'columns': list(df.columns),
            'last_modified': Config.DATA_FOLDER.joinpath(f"{key}.parquet").stat().st_mtime if Config.DATA_FOLDER.joinpath(f"{key}.parquet").exists() else None
        }
    
    return stats

def export_data_to_csv(output_dir: Optional[str] = None) -> bool:
    """
    Exportar todos los datos a archivos CSV
    
    Args:
        output_dir: Directorio de salida (opcional)
        
    Returns:
        bool: True si fue exitoso
    """
    try:
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Config.DATA_FOLDER / 'exports'
        
        output_path.mkdir(exist_ok=True)
        
        data = load_all_data()
        for key, df in data.items():
            csv_file = output_path / f"{key}.csv"
            df.to_csv(csv_file, index=False)
            logger.info(f"📄 Exportado: {csv_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error exportando datos: {e}")
        return False