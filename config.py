"""
Configuración central para la aplicación PENYA L'ALBENC
"""
import os
from pathlib import Path

class Config:
    """Configuración principal de la aplicación"""
    
    # Información de la aplicación
    APP_NAME = "PENYA L'ALBENC"
    VERSION = "1.0.0"
    
    # Configuración de seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'penya-secret-key-2025'
    
    # Rutas de archivos
    BASE_DIR = Path(__file__).parent
    DATA_FOLDER = BASE_DIR / 'data'
    BACKUP_FOLDER = DATA_FOLDER / 'backups'
    ASSETS_FOLDER = BASE_DIR / 'assets'
    
    # Asegurar que existen las carpetas
    DATA_FOLDER.mkdir(exist_ok=True)
    BACKUP_FOLDER.mkdir(exist_ok=True)
    ASSETS_FOLDER.mkdir(exist_ok=True)
    
    # Archivos de datos
    COMIDAS_FILE = DATA_FOLDER / 'comidas.parquet'
    LISTA_COMPRA_FILE = DATA_FOLDER / 'lista_compra.parquet'
    MANTENIMIENTO_FILE = DATA_FOLDER / 'mantenimiento.parquet'
    FIESTAS_FILE = DATA_FOLDER / 'fiestas.parquet'
    
    # Configuración del servidor
    HOST = os.environ.get('HOST') or '127.0.0.1'
    PORT = int(os.environ.get('PORT') or 8050)
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Colores del tema PENYA L'ALBENC
    COLORS = {
        'primary': '#2E8B57',      # Verde mar
        'secondary': '#4682B4',    # Azul acero
        'accent': '#20B2AA',       # Verde azulado claro
        'background': '#F0F8FF',   # Azul muy claro
        'text': '#2F4F4F',         # Gris oscuro
        'white': '#FFFFFF',
        'light_gray': '#f9f9f9',
        'success': '#28a745',
        'warning': '#ffc107',
        'error': '#dc3545'
    }
    
    # Usuarios y contraseñas hasheadas (SHA1)
    # En producción, usar una base de datos y bcrypt
    USERS = {
        "admin": "d033e22ae348aeb5660fc2140aec35850c4da997",  # password: "hello"
        "penya": "356a192b7913b04c54574d18c28d46e6395428ab"   # password: "1"
    }
    
    # Configuración de backup
    BACKUP_ENABLED = True
    MAX_BACKUPS = 10  # Máximo número de backups a mantener
    
    # Opciones de la aplicación
    ITEMS_PER_PAGE = 50
    DATE_FORMAT = 'DD/MM/YYYY'
    
    # Configuración de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'app.log'