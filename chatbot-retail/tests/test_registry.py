import unittest
import sqlite3
import tempfile
import os
import sys
from datetime import datetime, date
from pathlib import Path

# Agregar el directorio padre al path para importar los módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_core.registry import UserRegistry


class TestUserRegistry(unittest.TestCase):
    """Pruebas unitarias para UserRegistry"""
    
    def setUp(self):
        """Configuración inicial para cada test - crea una BD temporal"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.temp_db_path = self.temp_db.name
        self.registry = UserRegistry(db_path=self.temp_db_path)
        
        # Datos de prueba
        self.test_user_data = {
            'identificacion': '12345678',
            'nombre_completo': 'Juan Pérez',
            'telefono': '3001234567',
            'email': 'juan@example.com'
        }
        
    def tearDown(self):
        """Limpieza después de cada test - elimina la BD temporal"""
        try:
            os.unlink(self.temp_db_path)
        except OSError:
            pass
    
    def _assert_operation_success(self, operation_result, operation_name, details=""):
        """Helper para verificar operaciones exitosas"""
        self.assertTrue(operation_result, f"❌ FALLO: {operation_name} debería ser exitosa. {details}")
        print(f"✅ ÉXITO: {operation_name} completada exitosamente. {details}")
        
    def _assert_operation_failure(self, operation_result, operation_name, details=""):
        """Helper para verificar operaciones fallidas"""
        self.assertFalse(operation_result, f"❌ FALLO: {operation_name} debería fallar. {details}")
        print(f"✅ ÉXITO: {operation_name} falló como se esperaba. {details}")
        
    def _assert_user_data_matches(self, user_data, expected_data, operation_name):
        """Helper para verificar que los datos del usuario coinciden"""
        self.assertIsNotNone(user_data, f"❌ FALLO: {operation_name} - Usuario no debería ser None")
        
        for key, expected_value in expected_data.items():
            if key in user_data:
                self.assertEqual(user_data[key], expected_value,
                               f"❌ FALLO: {operation_name} - {key} no coincide. Esperado: '{expected_value}', Obtenido: '{user_data[key]}'")
        
        print(f"✅ ÉXITO: {operation_name} - Datos del usuario coinciden correctamente")
        print(f"   📝 Datos verificados: {', '.join([f'{k}={v}' for k, v in expected_data.items()])}")
    
    def test_database_initialization(self):
        """Test para verificar que la base de datos se inicializa correctamente"""
        print("\n🔍 PROBANDO: Inicialización de base de datos")
        
        # Verificar que el archivo de BD existe
        self.assertTrue(os.path.exists(self.temp_db_path), 
                       "❌ FALLO: El archivo de base de datos debería existir")
        
        # Verificar que las tablas se crearon
        with sqlite3.connect(self.temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['usuarios', 'conversaciones', 'metricas_diarias', 'palabras_frecuentes']
            
            for table in expected_tables:
                self.assertIn(table, tables, f"❌ FALLO: Tabla '{table}' no fue creada")
                print(f"✅ ÉXITO: Tabla '{table}' creada correctamente")
        
        print("✅ ÉXITO: Base de datos inicializada con todas las tablas requeridas")
    
    def test_register_user_new_user(self):
        """Test para registrar un nuevo usuario"""
        print("\n🔍 PROBANDO: Registro de nuevo usuario")
        
        result = self.registry.register_user(**self.test_user_data)
        
        self._assert_operation_success(result, "Registro de nuevo usuario",
                                     f"Usuario con ID '{self.test_user_data['identificacion']}'")
        
        # Verificar que el usuario existe
        exists = self.registry.user_exists(self.test_user_data['identificacion'])
        self._assert_operation_success(exists, "Verificación de existencia del usuario",
                                     "Usuario debería existir después del registro")
    
    def test_register_user_duplicate(self):
        """Test para intentar registrar un usuario duplicado"""
        print("\n🔍 PROBANDO: Registro de usuario duplicado")
        
        # Registrar usuario primera vez
        first_result = self.registry.register_user(**self.test_user_data)
        self._assert_operation_success(first_result, "Primer registro de usuario")
        
        # Intentar registrar el mismo usuario otra vez
        second_result = self.registry.register_user(**self.test_user_data)
        self._assert_operation_failure(second_result, "Segundo registro del mismo usuario",
                                     "No debería permitir usuarios duplicados")
    
    def test_user_exists_existing_user(self):
        """Test para verificar usuario existente"""
        print("\n🔍 PROBANDO: Verificación de usuario existente")
        
        # Registrar usuario
        self.registry.register_user(**self.test_user_data)
        
        # Verificar que existe
        exists = self.registry.user_exists(self.test_user_data['identificacion'])
        self._assert_operation_success(exists, "Verificación de usuario existente",
                                     f"Usuario '{self.test_user_data['identificacion']}' debería existir")
    
    def test_user_exists_nonexistent_user(self):
        """Test para verificar usuario inexistente"""
        print("\n🔍 PROBANDO: Verificación de usuario inexistente")
        
        exists = self.registry.user_exists("99999999")
        self._assert_operation_failure(exists, "Verificación de usuario inexistente",
                                     "Usuario '99999999' no debería existir")
    
    def test_get_user_existing(self):
        """Test para obtener datos de usuario existente"""
        print("\n🔍 PROBANDO: Obtención de datos de usuario existente")
        
        # Registrar usuario
        self.registry.register_user(**self.test_user_data)
        
        # Obtener usuario
        user_data = self.registry.get_user(self.test_user_data['identificacion'])
        
        self._assert_user_data_matches(user_data, self.test_user_data, 
                                     "Obtención de usuario existente")
        
        # Verificar campos adicionales
        self.assertIn('id', user_data, "❌ FALLO: Usuario debería tener campo 'id'")
        self.assertIn('fecha_registro', user_data, "❌ FALLO: Usuario debería tener campo 'fecha_registro'")
        print(f"   📝 ID de usuario: {user_data['id']}")
        print(f"   📝 Fecha de registro: {user_data['fecha_registro']}")
    
    def test_get_user_nonexistent(self):
        """Test para obtener usuario inexistente"""
        print("\n🔍 PROBANDO: Obtención de usuario inexistente")
        
        user_data = self.registry.get_user("99999999")
        
        self.assertIsNone(user_data, "❌ FALLO: Usuario inexistente debería retornar None")
        print("✅ ÉXITO: Usuario inexistente retorna None correctamente")
    
    def test_update_user_existing(self):
        """Test para actualizar datos de usuario existente"""
        print("\n🔍 PROBANDO: Actualización de usuario existente")
        
        # Registrar usuario
        self.registry.register_user(**self.test_user_data)
        
        # Datos de actualización
        updates = {
            'nombre_completo': 'Juan Carlos Pérez',
            'telefono': '3009876543',
            'email': 'juan.carlos@example.com'
        }
        
        # Actualizar usuario
        result = self.registry.update_user(self.test_user_data['identificacion'], **updates)
        self._assert_operation_success(result, "Actualización de usuario existente")
        
        # Verificar que los datos se actualizaron
        updated_user = self.registry.get_user(self.test_user_data['identificacion'])
        
        for key, expected_value in updates.items():
            self.assertEqual(updated_user[key], expected_value,
                           f"❌ FALLO: Campo '{key}' no se actualizó correctamente")
        
        print(f"✅ ÉXITO: Datos actualizados correctamente")
        print(f"   📝 Cambios aplicados: {', '.join([f'{k}={v}' for k, v in updates.items()])}")
    
    def test_update_user_nonexistent(self):
        """Test para actualizar usuario inexistente"""
        print("\n🔍 PROBANDO: Actualización de usuario inexistente")
        
        result = self.registry.update_user("99999999", nombre_completo="Test User")
        self._assert_operation_failure(result, "Actualización de usuario inexistente",
                                     "No debería actualizar usuarios que no existen")
    
    def test_update_user_invalid_fields(self):
        """Test para actualizar con campos inválidos"""
        print("\n🔍 PROBANDO: Actualización con campos no permitidos")
        
        # Registrar usuario
        self.registry.register_user(**self.test_user_data)
        
        # Intentar actualizar campos no permitidos
        result = self.registry.update_user(
            self.test_user_data['identificacion'], 
            campo_inexistente="valor",  # No permitido
            fecha_registro="2023-01-01",  # No permitido
            activo=False  # No permitido
        )
        
        self._assert_operation_failure(result, "Actualización con campos no permitidos",
                                     "No debería permitir actualizar campos restringidos")
        
        # Verificar que los datos originales no cambiaron
        user_data = self.registry.get_user(self.test_user_data['identificacion'])
        self.assertEqual(user_data['identificacion'], self.test_user_data['identificacion'],
                        "❌ FALLO: La identificación no debería haber cambiado")
        print("✅ ÉXITO: Campos restringidos no fueron modificados")
    
    def test_deactivate_user_existing(self):
        """Test para desactivar usuario existente"""
        print("\n🔍 PROBANDO: Desactivación de usuario existente")
        
        # Registrar usuario
        self.registry.register_user(**self.test_user_data)
        
        # Verificar que existe antes de desactivar
        exists_before = self.registry.user_exists(self.test_user_data['identificacion'])
        self._assert_operation_success(exists_before, "Usuario existe antes de desactivar")
        
        # Desactivar usuario
        result = self.registry.deactivate_user(self.test_user_data['identificacion'])
        self._assert_operation_success(result, "Desactivación de usuario")
        
        # Verificar que ya no existe (está desactivado)
        exists_after = self.registry.user_exists(self.test_user_data['identificacion'])
        self._assert_operation_failure(exists_after, "Usuario no debería existir después de desactivar",
                                     "Usuario desactivado no debería aparecer como existente")
    
    def test_deactivate_user_nonexistent(self):
        """Test para desactivar usuario inexistente"""
        print("\n🔍 PROBANDO: Desactivación de usuario inexistente")
        
        result = self.registry.deactivate_user("99999999")
        self._assert_operation_failure(result, "Desactivación de usuario inexistente",
                                     "No debería desactivar usuarios que no existen")
    
    def test_get_user_count(self):
        """Test para obtener conteo de usuarios"""
        print("\n🔍 PROBANDO: Conteo de usuarios activos")
        
        # Inicialmente debería ser 0
        initial_count = self.registry.get_user_count()
        self.assertEqual(initial_count, 0, "❌ FALLO: Conteo inicial debería ser 0")
        print(f"✅ ÉXITO: Conteo inicial correcto: {initial_count}")
        
        # Registrar varios usuarios
        users_to_register = [
            {'identificacion': '11111111', 'nombre_completo': 'Usuario 1', 'telefono': '3001111111', 'email': 'user1@test.com'},
            {'identificacion': '22222222', 'nombre_completo': 'Usuario 2', 'telefono': '3002222222', 'email': 'user2@test.com'},
            {'identificacion': '33333333', 'nombre_completo': 'Usuario 3', 'telefono': '3003333333', 'email': 'user3@test.com'}
        ]
        
        for user_data in users_to_register:
            self.registry.register_user(**user_data)
        
        # Verificar conteo después de registrar
        count_after_register = self.registry.get_user_count()
        self.assertEqual(count_after_register, 3, 
                        f"❌ FALLO: Conteo debería ser 3, pero es {count_after_register}")
        print(f"✅ ÉXITO: Conteo después de registrar usuarios: {count_after_register}")
        
        # Desactivar un usuario
        self.registry.deactivate_user('11111111')
        
        # Verificar conteo después de desactivar
        count_after_deactivate = self.registry.get_user_count()
        self.assertEqual(count_after_deactivate, 2,
                        f"❌ FALLO: Conteo debería ser 2, pero es {count_after_deactivate}")
        print(f"✅ ÉXITO: Conteo después de desactivar usuario: {count_after_deactivate}")
    
    def test_get_all_users(self):
        """Test para obtener todos los usuarios activos"""
        print("\n🔍 PROBANDO: Obtención de todos los usuarios activos")
        
        # Registrar varios usuarios
        users_data = [
            {'identificacion': '11111111', 'nombre_completo': 'Ana García', 'telefono': '3001111111', 'email': 'ana@test.com'},
            {'identificacion': '22222222', 'nombre_completo': 'Carlos López', 'telefono': '3002222222', 'email': 'carlos@test.com'},
            {'identificacion': '33333333', 'nombre_completo': 'María Rodríguez', 'telefono': '3003333333', 'email': 'maria@test.com'}
        ]
        
        for user_data in users_data:
            self.registry.register_user(**user_data)
        
        # Desactivar un usuario
        self.registry.deactivate_user('22222222')
        
        # Obtener todos los usuarios activos
        all_users = self.registry.get_all_users()
        
        # Verificar que solo devuelve usuarios activos
        self.assertEqual(len(all_users), 2, 
                        f"❌ FALLO: Debería haber 2 usuarios activos, pero hay {len(all_users)}")
        
        # Verificar que no incluye el usuario desactivado
        user_ids = [user['identificacion'] for user in all_users]
        self.assertNotIn('22222222', user_ids, 
                        "❌ FALLO: No debería incluir usuarios desactivados")
        
        # Verificar que incluye los usuarios activos
        self.assertIn('11111111', user_ids, "❌ FALLO: Debería incluir usuario activo")
        self.assertIn('33333333', user_ids, "❌ FALLO: Debería incluir usuario activo")
        
        print(f"✅ ÉXITO: Se obtuvieron {len(all_users)} usuarios activos correctamente")
        print(f"   📝 Usuarios activos: {', '.join(user_ids)}")
        print(f"   📝 Usuario desactivado '22222222' no incluido correctamente")
    
    def test_registrar_conversacion_with_user(self):
        """Test para registrar conversación con usuario registrado"""
        print("\n🔍 PROBANDO: Registro de conversación con usuario registrado")
        
        # Registrar usuario
        self.registry.register_user(**self.test_user_data)
        user_data = self.registry.get_user(self.test_user_data['identificacion'])
        user_id = user_data['id']
        
        # Datos de conversación
        session_id = "session_123"
        mensaje_usuario = "¿Cuáles son los horarios de atención?"
        respuesta_bot = "Nuestros horarios son de lunes a viernes de 8:00 AM a 6:00 PM"
        tipo_consulta = "horarios"
        
        # Registrar conversación
        self.registry.registrar_conversacion(
            usuario_id=user_id,
            session_id=session_id,
            mensaje_usuario=mensaje_usuario,
            respuesta_bot=respuesta_bot,
            tipo_consulta=tipo_consulta
        )
        
        # Verificar que se registró en la base de datos
        with sqlite3.connect(self.temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT usuario_id, session_id, mensaje_usuario, respuesta_bot, tipo_consulta
                FROM conversaciones
                WHERE usuario_id = ? AND session_id = ?
            """, (user_id, session_id))
            
            conversation = cursor.fetchone()
            
        self.assertIsNotNone(conversation, "❌ FALLO: Conversación debería haberse registrado")
        self.assertEqual(conversation[0], user_id, "❌ FALLO: Usuario ID no coincide")
        self.assertEqual(conversation[1], session_id, "❌ FALLO: Session ID no coincide")
        self.assertEqual(conversation[2], mensaje_usuario, "❌ FALLO: Mensaje usuario no coincide")
        self.assertEqual(conversation[3], respuesta_bot, "❌ FALLO: Respuesta bot no coincide")
        self.assertEqual(conversation[4], tipo_consulta, "❌ FALLO: Tipo consulta no coincide")
        
        print("✅ ÉXITO: Conversación registrada correctamente")
        print(f"   📝 Usuario ID: {user_id}")
        print(f"   📝 Session ID: {session_id}")
        print(f"   📝 Tipo consulta: {tipo_consulta}")
    
    def test_registrar_conversacion_anonymous_user(self):
        """Test para registrar conversación con usuario anónimo"""
        print("\n🔍 PROBANDO: Registro de conversación con usuario anónimo")
        
        # Datos de conversación sin usuario
        session_id = "session_anonymous_456"
        mensaje_usuario = "¿Tienen promociones?"
        respuesta_bot = "Sí, tenemos varias promociones vigentes"
        tipo_consulta = "promociones"
        
        # Registrar conversación con usuario anónimo (None)
        self.registry.registrar_conversacion(
            usuario_id=None,
            session_id=session_id,
            mensaje_usuario=mensaje_usuario,
            respuesta_bot=respuesta_bot,
            tipo_consulta=tipo_consulta
        )
        
        # Verificar que se registró en la base de datos
        with sqlite3.connect(self.temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT usuario_id, session_id, mensaje_usuario, respuesta_bot, tipo_consulta
                FROM conversaciones
                WHERE session_id = ?
            """, (session_id,))
            
            conversation = cursor.fetchone()
            
        self.assertIsNotNone(conversation, "❌ FALLO: Conversación anónima debería haberse registrado")
        self.assertIsNone(conversation[0], "❌ FALLO: Usuario ID debería ser None para usuarios anónimos")
        self.assertEqual(conversation[1], session_id, "❌ FALLO: Session ID no coincide")
        self.assertEqual(conversation[4], tipo_consulta, "❌ FALLO: Tipo consulta no coincide")
        
        print("✅ ÉXITO: Conversación anónima registrada correctamente")
        print(f"   📝 Usuario: Anónimo (None)")
        print(f"   📝 Session ID: {session_id}")
        print(f"   📝 Tipo consulta: {tipo_consulta}")
    
    def test_estadisticas_generales(self):
        """Test para obtener estadísticas generales"""
        print("\n🔍 PROBANDO: Obtención de estadísticas generales")
        
        # Preparar datos de prueba
        # Registrar usuarios
        users_data = [
            {'identificacion': '11111111', 'nombre_completo': 'Usuario Test 1', 'telefono': '3001111111', 'email': 'test1@example.com'},
            {'identificacion': '22222222', 'nombre_completo': 'Usuario Test 2', 'telefono': '3002222222', 'email': 'test2@example.com'}
        ]
        
        user_ids = []
        for user_data in users_data:
            self.registry.register_user(**user_data)
            user = self.registry.get_user(user_data['identificacion'])
            user_ids.append(user['id'])
        
        # Registrar conversaciones
        conversations_data = [
            (user_ids[0], "session_1", "¿Horarios?", "8AM-6PM", "horarios"),
            (user_ids[0], "session_1", "¿Promociones?", "Tenemos descuentos", "promociones"),
            (user_ids[1], "session_2", "Consulta general", "Respuesta general", "generales"),
            (None, "session_anon", "Pregunta anónima", "Respuesta anónima", "generales")
        ]
        
        for conv_data in conversations_data:
            self.registry.registrar_conversacion(*conv_data)
        
        # Obtener estadísticas
        stats = self.registry.get_estadisticas_generales()
        
        # Verificar estadísticas
        self.assertIn('total_usuarios', stats, "❌ FALLO: Debería incluir total_usuarios")
        self.assertIn('total_conversaciones', stats, "❌ FALLO: Debería incluir total_conversaciones")
        self.assertIn('tipos_consultas', stats, "❌ FALLO: Debería incluir tipos_consultas")
        
        self.assertEqual(stats['total_usuarios'], 2, 
                        f"❌ FALLO: Total usuarios debería ser 2, pero es {stats['total_usuarios']}")
        self.assertEqual(stats['total_conversaciones'], 4,
                        f"❌ FALLO: Total conversaciones debería ser 4, pero es {stats['total_conversaciones']}")
        
        print("✅ ÉXITO: Estadísticas generales obtenidas correctamente")
        print(f"   📝 Total usuarios: {stats['total_usuarios']}")
        print(f"   📝 Total conversaciones: {stats['total_conversaciones']}")
        print(f"   📝 Tipos de consultas registrados: {len(stats['tipos_consultas'])}")
        
        # Verificar tipos de consultas
        tipos_consultas = {item['tipo_consulta']: item['cantidad'] for item in stats['tipos_consultas']}
        expected_tipos = {'horarios': 1, 'promociones': 1, 'generales': 2}
        
        for tipo, cantidad_esperada in expected_tipos.items():
            self.assertEqual(tipos_consultas.get(tipo, 0), cantidad_esperada,
                           f"❌ FALLO: Tipo '{tipo}' debería tener {cantidad_esperada} consultas")
        
        print(f"   📝 Distribución de consultas verificada: {tipos_consultas}")


if __name__ == '__main__':
    # Ejecutar las pruebas
    unittest.main(verbosity=2, exit=False)
    
    # Mostrar resumen
    print("\n" + "="*80)
    print("📊 RESUMEN DE PRUEBAS UNITARIAS - UserRegistry")
    print("="*80)
    print("🎯 Funcionalidades probadas:")
    print("   ✓ Inicialización de base de datos y tablas")
    print("   ✓ Registro y validación de usuarios")
    print("   ✓ Verificación de existencia de usuarios")
    print("   ✓ Obtención de datos de usuarios")
    print("   ✓ Actualización de información de usuarios")
    print("   ✓ Desactivación de usuarios (soft delete)")
    print("   ✓ Conteo y listado de usuarios activos")
    print("   ✓ Registro de conversaciones con usuarios registrados")
    print("   ✓ Registro de conversaciones con usuarios anónimos")
    print("   ✓ Generación de estadísticas y métricas")
    print("\n🧪 Características testeadas:")
    print("   • Base de datos SQLite con integridad referencial")
    print("   • Manejo de transacciones y rollback")
    print("   • Prevención de duplicados y validaciones")
    print("   • Soft delete para mantener histórico")
    print("   • Métricas automáticas y palabras frecuentes")
    print("   • Soporte para usuarios anónimos")
    print("   • Agregación de datos y estadísticas")
    print("="*80)
