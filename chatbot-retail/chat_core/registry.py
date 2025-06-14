import sqlite3
from typing import Optional, Dict, Any
import json
from datetime import datetime
from pathlib import Path
import config


class UserRegistry:
    """Manejo de usuarios con SQLite"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.DATABASE_PATH
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos y crea las tablas necesarias"""
        # Crear directorio si no existe
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identificacion TEXT UNIQUE NOT NULL,
                    nombre_completo TEXT NOT NULL,
                    telefono TEXT NOT NULL,
                    email TEXT NOT NULL,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    activo BOOLEAN DEFAULT 1
                )
            """)
            conn.commit()
    
    def user_exists(self, identificacion: str) -> bool:
        """
        Verifica si un usuario existe por su identificación
        
        Args:
            identificacion: ID del usuario
            
        Returns:
            bool: True si existe, False si no
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM usuarios WHERE identificacion = ? AND activo = 1",
                (identificacion,)
            )
            return cursor.fetchone() is not None
    
    def register_user(self, identificacion: str, nombre_completo: str, 
                     telefono: str, email: str) -> bool:
        """
        Registra un nuevo usuario
        
        Args:
            identificacion: ID único del usuario
            nombre_completo: Nombre completo
            telefono: Número de teléfono
            email: Correo electrónico
            
        Returns:
            bool: True si se registró exitosamente, False si ya existe
        """
        if self.user_exists(identificacion):
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO usuarios (identificacion, nombre_completo, telefono, email)
                    VALUES (?, ?, ?, ?)
                """, (identificacion, nombre_completo, telefono, email))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, identificacion: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos de un usuario por su identificación
        
        Args:
            identificacion: ID del usuario
            
        Returns:
            Dict con los datos del usuario o None si no existe
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Para obtener diccionarios
            cursor = conn.cursor()
            cursor.execute("""
                SELECT identificacion, nombre_completo, telefono, email, fecha_registro
                FROM usuarios 
                WHERE identificacion = ? AND activo = 1
            """, (identificacion,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_all_users(self) -> list:
        """
        Obtiene todos los usuarios activos
        
        Returns:
            Lista de diccionarios con datos de usuarios
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT identificacion, nombre_completo, telefono, email, fecha_registro
                FROM usuarios 
                WHERE activo = 1
                ORDER BY fecha_registro DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_user(self, identificacion: str, **kwargs) -> bool:
        """
        Actualiza los datos de un usuario
        
        Args:
            identificacion: ID del usuario
            **kwargs: Campos a actualizar
            
        Returns:
            bool: True si se actualizó, False si no existe
        """
        if not self.user_exists(identificacion):
            return False
        
        # Campos permitidos para actualizar
        allowed_fields = ['nombre_completo', 'telefono', 'email']
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            return False
        
        # Construir query dinámicamente
        set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
        values = list(update_fields.values()) + [identificacion]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE usuarios 
                SET {set_clause}
                WHERE identificacion = ? AND activo = 1
            """, values)
            conn.commit()
            
            return cursor.rowcount > 0
    
    def deactivate_user(self, identificacion: str) -> bool:
        """
        Desactiva un usuario (soft delete)
        
        Args:
            identificacion: ID del usuario
            
        Returns:
            bool: True si se desactivó, False si no existe
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuarios 
                SET activo = 0
                WHERE identificacion = ? AND activo = 1
            """, (identificacion,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def get_user_count(self) -> int:
        """
        Obtiene el número total de usuarios activos
        
        Returns:
            int: Número de usuarios
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE activo = 1")
            return cursor.fetchone()[0]
