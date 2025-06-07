#!/usr/bin/env python3
"""
Script principal para ejecutar la aplicación PENYA L'ALBENC

Uso:
    python run.py
    
Variables de entorno opcionales:
    HOST: Dirección IP del servidor (default: 127.0.0.1)
    PORT: Puerto del servidor (default: 8050)
    DEBUG: Modo debug (default: True)
    SECRET_KEY: Clave secreta para sesiones
"""

import sys
import logging
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config

# Configurar logging antes de importar la aplicación
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Verificar que todas las dependencias estén instaladas"""
    required_packages = ['dash', 'pandas', 'plotly', 'pyarrow']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"❌ Paquetes faltantes: {', '.join(missing)}")
        logger.error("💡 Instala con: pip install -r requirements.txt")
        return False
    
    return True

def create_data_folder():
    """Crear carpeta de datos si no existe"""
    try:
        Config.DATA_FOLDER.mkdir(exist_ok=True)
        Config.BACKUP_FOLDER.mkdir(exist_ok=True)
        logger.info(f"📁 Carpetas de datos verificadas: {Config.DATA_FOLDER}")
        return True
    except Exception as e:
        logger.error(f"❌ Error creando carpetas: {e}")
        return False

def main():
    """Función principal para ejecutar la aplicación"""
    try:
        # Mostrar información de inicio
        print("=" * 60)
        print(f"🏛️  {Config.APP_NAME} v{Config.VERSION}")
        print("=" * 60)
        
        # Verificar dependencias
        logger.info("🔍 Verificando dependencias...")
        if not check_dependencies():
            sys.exit(1)
        
        # Crear carpetas necesarias
        logger.info("📁 Verificando estructura de carpetas...")
        if not create_data_folder():
            sys.exit(1)
        
        # Importar y ejecutar la aplicación
        logger.info("🚀 Importando aplicación...")
        from app import app
        
        # FORZAR actualización con datos reales del PDF
        logger.info("📊 Actualizando con datos reales de PENYA L'ALBENC...")
        try:
            from src.data_manager import force_update_real_data
            mant_count, comidas_count = force_update_real_data()
            logger.info(f"✅ Datos reales cargados: {mant_count} años mantenimiento, {comidas_count} comidas del PDF")
        except Exception as e:
            logger.warning(f"⚠️ Error actualizando datos reales: {e}")
            logger.info("📋 Creando datos básicos...")
            from src.data_manager import create_initial_data
            create_initial_data()
        
        # Información del servidor
        logger.info(f"🌐 Iniciando servidor en http://{Config.HOST}:{Config.PORT}")
        logger.info(f"🔧 Modo debug: {Config.DEBUG}")
        logger.info(f"📊 Datos almacenados en: {Config.DATA_FOLDER}")
        logger.info("👥 Usuarios disponibles: admin, penya")
        
        print("\n" + "=" * 60)
        print(f"🚀 SERVIDOR INICIADO - PENYA L'ALBENC VILAFRANCA")
        print(f"📍 URL: http://{Config.HOST}:{Config.PORT}")
        print(f"🔑 Usuario: admin | Contraseña: hello")
        print(f"🔑 Usuario: penya | Contraseña: 1")
        print("📊 Datos reales del PDF incluidos (2025-2045)")
        print("⏹️  Presiona Ctrl+C para detener")
        print("=" * 60 + "\n")
        
        # Ejecutar el servidor
        app.run_server(
            debug=Config.DEBUG,
            host=Config.HOST,
            port=Config.PORT,
            use_reloader=Config.DEBUG,
            dev_tools_hot_reload=Config.DEBUG,
            dev_tools_props_check=Config.DEBUG
        )
        
    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        logger.error("🔍 Verifica que todas las dependencias estén instaladas")
        logger.error("💡 Ejecuta: pip install -r requirements.txt")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("\n👋 Aplicación detenida por el usuario")
        print("\n🛑 Servidor detenido. ¡Hasta luego!")
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        logger.error("📧 Si el problema persiste, reporta este error")
        sys.exit(1)

if __name__ == '__main__':
    main()