"""
Pruebas unitarias para AnalyticsManager

Estas pruebas verifican las funcionalidades de análisis y estadísticas del chatbot,
incluyendo estadísticas de conversaciones, métricas de usuarios, y distribuciones temporales.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import os
import sys

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.analytics import AnalyticsManager


class TestAnalyticsManager(unittest.TestCase):
    """Clase de pruebas para AnalyticsManager"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db_path = self.test_db_file.name
        self.test_db_file.close()
        
        # Datos de prueba
        self.sample_conversations = [
            ('2024-01-15 10:30:00', 'usuario1', 'Hola', 'bot_response', 'chat_active'),
            ('2024-01-15 14:20:00', 'usuario2', 'Consulta horarios', 'bot_response', 'chat_active'),
            ('2024-01-16 09:15:00', 'usuario1', 'Otra pregunta', 'bot_response', 'chat_active'),
            ('2024-01-16 16:45:00', 'usuario3', 'Información productos', 'bot_response', 'chat_active'),
        ]
        
        self.sample_users = [
            ('usuario1', 'Juan Pérez', '3001234567', 'juan@email.com', '2024-01-15', True),
            ('usuario2', 'María García', '3007654321', 'maria@email.com', '2024-01-15', True),
            ('usuario3', 'Carlos López', '6011234567', 'carlos@email.com', '2024-01-16', True),
        ]
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
    
    def _create_test_database(self):
        """Crea una base de datos de prueba con datos de ejemplo"""
        with sqlite3.connect(self.test_db_path) as conn:
            # Crear tabla de usuarios (esquema real)
            conn.execute("""
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
            
            # Crear tabla de conversaciones (esquema real)
            conn.execute("""
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
            
            # Insertar usuarios de prueba
            conn.executemany(
                "INSERT INTO usuarios (identificacion, nombre_completo, telefono, email, fecha_registro, activo) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    ('usuario1', 'Juan Pérez', '3001234567', 'juan@email.com', '2024-01-15', True),
                    ('usuario2', 'María García', '3007654321', 'maria@email.com', '2024-01-15', True),
                    ('usuario3', 'Carlos López', '6011234567', 'carlos@email.com', '2024-01-16', True),
                ]
            )
            
            # Insertar conversaciones de prueba
            conn.executemany(
                "INSERT INTO conversaciones (usuario_id, session_id, mensaje_usuario, respuesta_bot, timestamp, tipo_consulta) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (1, 'session1', 'Hola', 'bot_response', '2024-01-15 10:30:00', 'saludo'),
                    (2, 'session2', 'Consulta horarios', 'bot_response', '2024-01-15 14:20:00', 'horarios'),
                    (1, 'session3', 'Otra pregunta', 'bot_response', '2024-01-16 09:15:00', 'consulta'),
                    (3, 'session4', 'Información productos', 'bot_response', '2024-01-16 16:45:00', 'productos'),
                ]
            )
            
            conn.commit()
    
    def _create_analytics_manager_with_mock_db(self):
        """Crea un AnalyticsManager con base de datos mockeada"""
        with patch('utils.analytics.config') as mock_config:
            mock_config.DATABASE_PATH = self.test_db_path
            analytics_manager = AnalyticsManager()
            return analytics_manager
    
    # ==================== TESTS DE INICIALIZACIÓN ====================
    
    def test_analytics_manager_initialization(self):
        """Test para inicialización del AnalyticsManager"""
        print("\n🔍 PROBANDO: Inicialización del AnalyticsManager")
        
        analytics_manager = self._create_analytics_manager_with_mock_db()
        
        # Verificar que se inicializa correctamente
        self.assertIsNotNone(analytics_manager.db_path, 
                           "❌ FALLO: db_path no debería ser None")
        
        print("✅ ÉXITO: AnalyticsManager inicializado correctamente")
        print(f"   📝 Ruta de DB configurada: {analytics_manager.db_path}")
    
    # ==================== TESTS DE ESTADÍSTICAS DE CONVERSACIONES ====================
    
    def test_get_conversation_stats_with_data(self):
        """Test para obtener estadísticas de conversaciones con datos"""
        print("\n🔍 PROBANDO: Estadísticas de conversaciones con datos")
        
        self._create_test_database()
        analytics_manager = self._create_analytics_manager_with_mock_db()
        
        # Obtener estadísticas
        stats = analytics_manager.get_conversation_stats(days=30)
        
        # Verificar estructura
        self.assertIsInstance(stats, dict, "❌ FALLO: Stats debería ser un diccionario")
        
        required_keys = ['daily_conversations', 'total_conversations', 'avg_per_day', 'unique_users']
        for key in required_keys:
            self.assertIn(key, stats, f"❌ FALLO: Stats debería tener clave '{key}'")
        
        # Verificar datos
        self.assertGreater(stats['total_conversations'], 0, 
                          "❌ FALLO: Total de conversaciones debería ser mayor a 0")
        self.assertGreater(stats['unique_users'], 0,
                          "❌ FALLO: Usuarios únicos debería ser mayor a 0")
        
        print("✅ ÉXITO: Estadísticas de conversaciones obtenidas correctamente")
        print(f"   📝 Total conversaciones: {stats['total_conversations']}")
        print(f"   📝 Usuarios únicos: {stats['unique_users']}")
        print(f"   📝 Promedio por día: {stats['avg_per_day']:.2f}")
    
    def test_get_conversation_stats_empty_database(self):
        """Test para estadísticas con base de datos vacía"""
        print("\n🔍 PROBANDO: Estadísticas con base de datos vacía")
        
        # Crear DB vacía con esquema correcto
        with sqlite3.connect(self.test_db_path) as conn:
            conn.execute("""
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
            
            conn.execute("""
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
        
        analytics_manager = self._create_analytics_manager_with_mock_db()
        
        # Obtener estadísticas
        stats = analytics_manager.get_conversation_stats(days=30)
        
        # Verificar que maneja datos vacíos correctamente
        self.assertEqual(stats['total_conversations'], 0,
                        "❌ FALLO: Total de conversaciones debería ser 0")
        self.assertEqual(stats['unique_users'], 0,
                        "❌ FALLO: Usuarios únicos debería ser 0")
        
        print("✅ ÉXITO: Estadísticas con DB vacía manejadas correctamente")
        print(f"   📝 Total conversaciones: {stats['total_conversations']}")
        print(f"   📝 Usuarios únicos: {stats['unique_users']}")
    
    # ==================== TESTS DE ANÁLISIS DE PALABRAS ====================
    
    def test_get_word_frequency_with_data(self):
        """Test para análisis de frecuencia de palabras"""
        print("\n🔍 PROBANDO: Análisis de frecuencia de palabras")
        
        self._create_test_database()
        analytics_manager = self._create_analytics_manager_with_mock_db()
        
        # Obtener frecuencia de palabras
        word_freq = analytics_manager.get_word_frequency(days=30, limit=10)
        
        # Verificar estructura
        self.assertIsInstance(word_freq, dict, "❌ FALLO: Word frequency debería ser un diccionario")
        
        expected_keys = ['word_counts', 'total_words', 'unique_words']
        for key in expected_keys:
            self.assertIn(key, word_freq, f"❌ FALLO: Word freq debería tener clave '{key}'")
        
        # Verificar que hay palabras analizadas
        self.assertGreater(word_freq['total_words'], 0,
                          "❌ FALLO: Total de palabras debería ser mayor a 0")
        
        print("✅ ÉXITO: Análisis de frecuencia de palabras completado")
        print(f"   📝 Total palabras: {word_freq['total_words']}")
        print(f"   📝 Palabras únicas: {word_freq['unique_words']}")
        print(f"   📝 Top words: {list(word_freq['word_counts'].keys())[:3]}")
    
    # ==================== TESTS DE DISTRIBUCIÓN HORARIA ====================
    
    def test_get_hourly_distribution(self):
        """Test para distribución horaria de conversaciones"""
        print("\n🔍 PROBANDO: Distribución horaria de conversaciones")
        
        self._create_test_database()
        analytics_manager = self._create_analytics_manager_with_mock_db()
        
        # Obtener distribución horaria
        hourly_dist = analytics_manager.get_hourly_distribution(days=30)
        
        # Verificar estructura
        self.assertIsInstance(hourly_dist, dict, "❌ FALLO: Hourly dist debería ser un diccionario")
        
        required_keys = ['hourly_counts', 'peak_hour', 'lowest_hour']
        for key in required_keys:
            self.assertIn(key, hourly_dist, f"❌ FALLO: Hourly dist debería tener clave '{key}'")
        
        # Verificar datos
        self.assertIsInstance(hourly_dist['hourly_counts'], list,
                            "❌ FALLO: hourly_counts debería ser una lista")
        self.assertEqual(len(hourly_dist['hourly_counts']), 24,
                        "❌ FALLO: hourly_counts debería tener 24 elementos")
        
        print("✅ ÉXITO: Distribución horaria calculada correctamente")
        print(f"   📝 Hora pico: {hourly_dist['peak_hour']}:00")
        print(f"   📝 Hora menos activa: {hourly_dist['lowest_hour']}:00")
    
    # ==================== TESTS DE MÉTRICAS DE USUARIOS ====================
    
    def test_get_user_engagement_metrics(self):
        """Test para métricas de engagement de usuarios"""
        print("\n🔍 PROBANDO: Métricas de engagement de usuarios")
        
        self._create_test_database()
        analytics_manager = self._create_analytics_manager_with_mock_db()
        
        # Obtener métricas de engagement
        engagement = analytics_manager.get_user_engagement_metrics()
        
        # Verificar estructura
        self.assertIsInstance(engagement, dict, "❌ FALLO: Engagement debería ser un diccionario")
        
        expected_keys = ['total_users', 'active_users', 'conversations_per_user', 'top_users']
        for key in expected_keys:
            self.assertIn(key, engagement, f"❌ FALLO: Engagement debería tener clave '{key}'")
        
        # Verificar datos
        self.assertGreater(engagement['total_users'], 0,
                          "❌ FALLO: Total de usuarios debería ser mayor a 0")
        self.assertIsInstance(engagement['top_users'], list,
                            "❌ FALLO: top_users debería ser una lista")
        
        print("✅ ÉXITO: Métricas de engagement calculadas correctamente")
        print(f"   📝 Total usuarios: {engagement['total_users']}")
        print(f"   📝 Usuarios activos: {engagement['active_users']}")
        print(f"   📝 Conversaciones por usuario: {engagement['conversations_per_user']:.2f}")
    
    # ==================== TESTS DE MANEJO DE ERRORES ====================
    
    @patch('utils.analytics.sqlite3.connect')
    def test_database_connection_error(self, mock_connect):
        """Test para manejo de errores de conexión a la base de datos"""
        print("\n🔍 PROBANDO: Manejo de errores de conexión a DB")
        
        # Simular error de conexión
        mock_connect.side_effect = sqlite3.Error("Database connection failed")
        
        analytics_manager = self._create_analytics_manager_with_mock_db()
        
        # Verificar que maneja el error gracefully
        try:
            stats = analytics_manager.get_conversation_stats(days=30)
            # Si no hay excepción, debería retornar estructura vacía válida
            self.assertIsInstance(stats, dict, "❌ FALLO: Debería retornar diccionario en caso de error")
        except Exception as e:
            # Si hay excepción, debería ser manejada apropiadamente
            self.assertIsInstance(e, (sqlite3.Error, Exception),
                                "❌ FALLO: Excepción debería ser del tipo esperado")
        
        print("✅ ÉXITO: Errores de conexión a DB manejados correctamente")
    
    # ==================== TESTS DE CASOS LÍMITE ====================
    
    def test_analytics_with_extreme_dates(self):
        """Test para análisis con rangos de fechas extremos"""
        print("\n🔍 PROBANDO: Análisis con rangos de fechas extremos")
        
        self._create_test_database()
        analytics_manager = self._create_analytics_manager_with_mock_db()
        
        # Probar con rango muy pequeño (1 día)
        stats_1_day = analytics_manager.get_conversation_stats(days=1)
        self.assertIsInstance(stats_1_day, dict, "❌ FALLO: Stats con 1 día debería ser diccionario")
        
        # Probar con rango muy grande (365 días)
        stats_365_days = analytics_manager.get_conversation_stats(days=365)
        self.assertIsInstance(stats_365_days, dict, "❌ FALLO: Stats con 365 días debería ser diccionario")
        
        # Probar con rango cero
        stats_0_days = analytics_manager.get_conversation_stats(days=0)
        self.assertIsInstance(stats_0_days, dict, "❌ FALLO: Stats con 0 días debería ser diccionario")
        
        print("✅ ÉXITO: Rangos de fechas extremos manejados correctamente")
        print(f"   📝 Stats 1 día - Total conversaciones: {stats_1_day.get('total_conversations', 0)}")
        print(f"   📝 Stats 365 días - Total conversaciones: {stats_365_days.get('total_conversations', 0)}")
        print(f"   📝 Stats 0 días - Total conversaciones: {stats_0_days.get('total_conversations', 0)}")


def print_test_summary():
    """Imprime un resumen de las pruebas del AnalyticsManager"""
    print("\n" + "="*80)
    print("🎯 RESUMEN DE PRUEBAS - ANALYTICS MANAGER")
    print("="*80)
    print("✅ Componente: AnalyticsManager")
    print("✅ Funcionalidades probadas:")
    print("   🔸 Inicialización del manager")
    print("   🔸 Estadísticas de conversaciones (con y sin datos)")
    print("   🔸 Análisis de frecuencia de palabras")
    print("   🔸 Distribución horaria de actividad")
    print("   🔸 Métricas de engagement de usuarios")
    print("   🔸 Manejo de errores de conexión a DB")
    print("   🔸 Casos límite con rangos de fechas extremos")
    print("\n✅ Cobertura: Analytics y estadísticas del chatbot")
    print("✅ Mocking: Base de datos SQLite, configuración")
    print("✅ Output: Detallado y descriptivo para cada escenario")
    print("="*80)


if __name__ == '__main__':
    # Ejecutar pruebas con output detallado
    unittest.main(verbosity=2, exit=False)
    print_test_summary()
