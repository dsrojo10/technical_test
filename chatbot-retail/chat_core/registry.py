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
            
            # Tabla de usuarios
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
            
            # Tabla de conversaciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    session_id TEXT NOT NULL,
                    mensaje_usuario TEXT NOT NULL,
                    respuesta_bot TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tipo_consulta TEXT,
                    satisfaccion INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            """)
            
            # Tabla de métricas diarias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metricas_diarias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE UNIQUE NOT NULL,
                    total_mensajes INTEGER DEFAULT 0,
                    usuarios_unicos INTEGER DEFAULT 0,
                    usuarios_nuevos INTEGER DEFAULT 0,
                    consultas_horarios INTEGER DEFAULT 0,
                    consultas_promociones INTEGER DEFAULT 0,
                    consultas_generales INTEGER DEFAULT 0
                )
            """)
            
            # Tabla de palabras frecuentes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS palabras_frecuentes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    palabra TEXT UNIQUE NOT NULL,
                    frecuencia INTEGER DEFAULT 0,
                    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            
            # Tabla de métricas diarias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metricas_diarias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATE NOT NULL,
                    total_mensajes INTEGER DEFAULT 0,
                    usuarios_unicos INTEGER DEFAULT 0,
                    usuarios_nuevos INTEGER DEFAULT 0,
                    consultas_horarios INTEGER DEFAULT 0,
                    consultas_promociones INTEGER DEFAULT 0,
                    consultas_generales INTEGER DEFAULT 0,
                    UNIQUE(fecha)
                )
            """)
            
            # Tabla de palabras clave frecuentes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS palabras_frecuentes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    palabra TEXT NOT NULL,
                    frecuencia INTEGER DEFAULT 1,
                    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(palabra)
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
    
    def registrar_conversacion(self, usuario_id: Optional[int], session_id: str, 
                              mensaje_usuario: str, respuesta_bot: str, 
                              tipo_consulta: Optional[str] = None) -> None:
        """
        Registra una conversación en la base de datos
        
        Args:
            usuario_id: ID del usuario (None para usuarios anónimos)
            session_id: ID de la sesión
            mensaje_usuario: Mensaje del usuario
            respuesta_bot: Respuesta del bot
            tipo_consulta: Tipo de consulta (horarios, promociones, general)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversaciones 
                (usuario_id, session_id, mensaje_usuario, respuesta_bot, tipo_consulta)
                VALUES (?, ?, ?, ?, ?)
            """, (usuario_id, session_id, mensaje_usuario, respuesta_bot, tipo_consulta))
            
            # Actualizar métricas diarias
            self._actualizar_metricas_diarias(cursor, tipo_consulta)
            
            # Actualizar palabras frecuentes
            self._actualizar_palabras_frecuentes(cursor, mensaje_usuario)
            
            conn.commit()
    
    def _actualizar_metricas_diarias(self, cursor, tipo_consulta: Optional[str]):
        """Actualiza las métricas del día actual"""
        from datetime import date
        
        hoy = date.today()
        
        # Insertar o actualizar métricas del día
        cursor.execute("""
            INSERT OR IGNORE INTO metricas_diarias (fecha) VALUES (?)
        """, (hoy,))
        
        # Incrementar contador de mensajes
        cursor.execute("""
            UPDATE metricas_diarias 
            SET total_mensajes = total_mensajes + 1
            WHERE fecha = ?
        """, (hoy,))
        
        # Incrementar contador específico según tipo de consulta
        if tipo_consulta:
            campo_consulta = f"consultas_{tipo_consulta}"
            cursor.execute(f"""
                UPDATE metricas_diarias 
                SET {campo_consulta} = {campo_consulta} + 1
                WHERE fecha = ?
            """, (hoy,))
    
    def _actualizar_palabras_frecuentes(self, cursor, mensaje: str):
        """Actualiza las palabras frecuentes basadas en el mensaje"""
        import re
        from collections import Counter
        
        # Limpiar y tokenizar el mensaje
        palabras = re.findall(r'\b[a-záéíóúñ]{3,}\b', mensaje.lower())
        
        # Filtrar palabras comunes sin valor analítico
        stop_words = {
            'que', 'como', 'cuando', 'donde', 'porque', 'para', 'con', 'por', 
            'del', 'una', 'los', 'las', 'tiene', 'esta', 'pero', 'más'
        }
        palabras_relevantes = [p for p in palabras if p not in stop_words and len(p) > 3]
        
        # Actualizar frecuencias
        for palabra in palabras_relevantes:
            cursor.execute("""
                INSERT OR REPLACE INTO palabras_frecuentes (palabra, frecuencia, ultima_actualizacion)
                VALUES (?, COALESCE((SELECT frecuencia FROM palabras_frecuentes WHERE palabra = ?), 0) + 1, CURRENT_TIMESTAMP)
            """, (palabra, palabra))
    
    def get_estadisticas_generales(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales del chatbot"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            stats = {}
            
            # Estadísticas de usuarios
            cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE activo = 1")
            stats['total_usuarios'] = cursor.fetchone()['total']
            
            # Estadísticas de conversaciones
            cursor.execute("SELECT COUNT(*) as total FROM conversaciones")
            stats['total_conversaciones'] = cursor.fetchone()['total']
            
            # Conversaciones por día (últimos 7 días)
            cursor.execute("""
                SELECT DATE(timestamp) as fecha, COUNT(*) as conversaciones
                FROM conversaciones 
                WHERE timestamp >= date('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY fecha DESC
            """)
            stats['conversaciones_ultimos_7_dias'] = [dict(row) for row in cursor.fetchall()]
            
            # Tipos de consultas más frecuentes
            cursor.execute("""
                SELECT tipo_consulta, COUNT(*) as cantidad
                FROM conversaciones 
                WHERE tipo_consulta IS NOT NULL
                GROUP BY tipo_consulta
                ORDER BY cantidad DESC
            """)
            stats['tipos_consultas'] = [dict(row) for row in cursor.fetchall()]
            
            # Usuarios más activos
            cursor.execute("""
                SELECT u.nombre_completo, COUNT(c.id) as total_mensajes
                FROM usuarios u
                LEFT JOIN conversaciones c ON u.id = c.usuario_id
                WHERE u.activo = 1
                GROUP BY u.id, u.nombre_completo
                ORDER BY total_mensajes DESC
                LIMIT 10
            """)
            stats['usuarios_mas_activos'] = [dict(row) for row in cursor.fetchall()]
            
            # Palabras más frecuentes
            cursor.execute("""
                SELECT palabra, frecuencia
                FROM palabras_frecuentes
                ORDER BY frecuencia DESC
                LIMIT 20
            """)
            stats['palabras_frecuentes'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    def get_metricas_periodo(self, dias: int = 30) -> Dict[str, Any]:
        """Obtiene métricas para un período específico"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    fecha,
                    total_mensajes,
                    usuarios_unicos,
                    usuarios_nuevos,
                    consultas_horarios,
                    consultas_promociones,
                    consultas_generales
                FROM metricas_diarias
                WHERE fecha >= date('now', '-{} days')
                ORDER BY fecha DESC
            """.format(dias))
            
            return [dict(row) for row in cursor.fetchall()]
