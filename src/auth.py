"""
Sistema de autenticación para PENYA L'ALBENC
Maneja login, logout y verificación de credenciales
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class AuthManager:
    """Gestor de autenticación"""
    
    def __init__(self):
        self.config = Config()
        self.active_sessions = {}  # En producción usar Redis o base de datos
        self.session_timeout = timedelta(hours=8)  # Sesión válida por 8 horas
    
    def hash_password(self, password: str) -> str:
        """
        Generar hash SHA1 de la contraseña
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            str: Hash SHA1 de la contraseña
        """
        return hashlib.sha1(password.encode()).hexdigest()
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """
        Verificar credenciales de usuario
        
        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano
            
        Returns:
            bool: True si las credenciales son válidas
        """
        try:
            if not username or not password:
                logger.warning("⚠️ Intento de login con credenciales vacías")
                return False
            
            if username in self.config.USERS:
                password_hash = self.hash_password(password)
                is_valid = self.config.USERS[username] == password_hash
                
                if is_valid:
                    logger.info(f"✅ Login exitoso para usuario: {username}")
                else:
                    logger.warning(f"❌ Credenciales incorrectas para usuario: {username}")
                
                return is_valid
            else:
                logger.warning(f"❌ Usuario no encontrado: {username}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error verificando credenciales: {e}")
            return False
    
    def create_session(self, username: str) -> Dict[str, Any]:
        """
        Crear sesión para usuario autenticado
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Dict con datos de la sesión
        """
        session_data = {
            'authenticated': True,
            'username': username,
            'login_time': datetime.now(),
            'expires_at': datetime.now() + self.session_timeout
        }
        
        # En una aplicación real, aquí generarías un token único
        session_id = f"{username}_{datetime.now().timestamp()}"
        self.active_sessions[session_id] = session_data
        
        logger.info(f"🔑 Sesión creada para {username}")
        return session_data
    
    def validate_session(self, session_data: Optional[Dict[str, Any]]) -> bool:
        """
        Validar si una sesión es válida
        
        Args:
            session_data: Datos de la sesión
            
        Returns:
            bool: True si la sesión es válida
        """
        if not session_data:
            return False
        
        try:
            if not session_data.get('authenticated', False):
                return False
            
            # Verificar si la sesión no ha expirado
            login_time = session_data.get('login_time')
            if isinstance(login_time, str):
                login_time = datetime.fromisoformat(login_time)
            elif not isinstance(login_time, datetime):
                return False
            
            if datetime.now() - login_time > self.session_timeout:
                logger.info(f"⏰ Sesión expirada para {session_data.get('username')}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validando sesión: {e}")
            return False
    
    def logout_session(self, session_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cerrar sesión
        
        Args:
            session_data: Datos de la sesión actual
            
        Returns:
            Dict con sesión limpia
        """
        if session_data and session_data.get('username'):
            logger.info(f"👋 Logout de usuario: {session_data['username']}")
        
        return {'authenticated': False}
    
    def get_user_info(self, username: str) -> Dict[str, Any]:
        """
        Obtener información del usuario
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Dict con información del usuario
        """
        user_roles = {
            'admin': {
                'role': 'Administrador',
                'permissions': ['read', 'write', 'delete', 'admin'],
                'description': 'Acceso completo al sistema'
            },
            'penya': {
                'role': 'Usuario Penya',
                'permissions': ['read', 'write'],
                'description': 'Usuario estándar de la penya'
            }
        }
        
        return user_roles.get(username, {
            'role': 'Usuario',
            'permissions': ['read'],
            'description': 'Usuario estándar'
        })
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de sesiones activas
        
        Returns:
            Dict con estadísticas
        """
        active_count = len([
            session for session in self.active_sessions.values()
            if self.validate_session(session)
        ])
        
        return {
            'active_sessions': active_count,
            'total_sessions': len(self.active_sessions),
            'timeout_hours': self.session_timeout.total_seconds() / 3600
        }

# Instancia global del gestor de autenticación
auth_manager = AuthManager()

def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """
    Función de conveniencia para autenticar usuario
    
    Args:
        username: Nombre de usuario
        password: Contraseña
        
    Returns:
        Dict con resultado de autenticación
    """
    if auth_manager.verify_credentials(username, password):
        return auth_manager.create_session(username)
    else:
        return {'authenticated': False, 'error': 'Credenciales incorrectas'}

def is_authenticated(session_data: Optional[Dict[str, Any]]) -> bool:
    """
    Función de conveniencia para verificar autenticación
    
    Args:
        session_data: Datos de la sesión
        
    Returns:
        bool: True si está autenticado
    """
    return auth_manager.validate_session(session_data)

def logout_user(session_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Función de conveniencia para logout
    
    Args:
        session_data: Datos de la sesión
        
    Returns:
        Dict con sesión limpia
    """
    return auth_manager.logout_session(session_data)

def get_current_user(session_data: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Obtener usuario actual de la sesión
    
    Args:
        session_data: Datos de la sesión
        
    Returns:
        str: Nombre de usuario o None
    """
    if is_authenticated(session_data):
        return session_data.get('username')
    return None

def has_permission(session_data: Optional[Dict[str, Any]], permission: str) -> bool:
    """
    Verificar si el usuario tiene un permiso específico
    
    Args:
        session_data: Datos de la sesión
        permission: Permiso a verificar ('read', 'write', 'delete', 'admin')
        
    Returns:
        bool: True si tiene el permiso
    """
    username = get_current_user(session_data)
    if not username:
        return False
    
    user_info = auth_manager.get_user_info(username)
    return permission in user_info.get('permissions', [])

# Decorador para requerir autenticación (para uso futuro)
def require_auth(func):
    """
    Decorador para funciones que requieren autenticación
    
    Uso:
        @require_auth
        def some_protected_function(session_data, ...):
            pass
    """
    def wrapper(session_data, *args, **kwargs):
        if not is_authenticated(session_data):
            raise PermissionError("Autenticación requerida")
        return func(session_data, *args, **kwargs)
    return wrapper