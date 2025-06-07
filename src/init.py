"""
PENYA L'ALBENC - Paquete principal

Este paquete contiene todos los módulos para la aplicación
de gestión de PENYA L'ALBENC.

Módulos:
- auth: Sistema de autenticación
- data_manager: Gestión de datos Parquet
- layouts: Interfaces de usuario (futuro)
- callbacks: Lógica de callbacks (futuro)
- utils: Utilidades generales (futuro)
"""

__version__ = "1.0.0"
__author__ = "PENYA L'ALBENC"
__description__ = "Sistema de gestión integral para PENYA L'ALBENC"

# Importar módulos principales para facilitar el acceso
from .auth import auth_manager, authenticate_user, is_authenticated
from .data_manager import data_manager, load_all_data, save_data, create_initial_data

__all__ = [
    'auth_manager',
    'authenticate_user', 
    'is_authenticated',
    'data_manager',
    'load_all_data',
    'save_data',
    'create_initial_data'
]