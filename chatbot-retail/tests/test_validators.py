import unittest
import sys
import os

# Agregar el directorio padre al path para importar los módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_core.validators import UserValidator


class TestUserValidator(unittest.TestCase):
    """Pruebas unitarias para UserValidator"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.validator = UserValidator()
        
    def _assert_validation_success(self, method, value, description):
        """Helper para validaciones exitosas"""
        is_valid, error_msg = method(value)
        self.assertTrue(is_valid, f"❌ FALLO: {description} - Valor: '{value}' debería ser válido")
        self.assertIsNone(error_msg, f"❌ FALLO: {description} - No debería haber mensaje de error")
        print(f"✅ ÉXITO: {description} - Valor: '{value}' es válido")
        
    def _assert_validation_failure(self, method, value, expected_error_fragment, description):
        """Helper para validaciones fallidas"""
        is_valid, error_msg = method(value)
        self.assertFalse(is_valid, f"❌ FALLO: {description} - Valor: '{value}' debería ser inválido")
        self.assertIsNotNone(error_msg, f"❌ FALLO: {description} - Debería haber mensaje de error")
        self.assertIn(expected_error_fragment, error_msg, 
                     f"❌ FALLO: {description} - Error esperado: '{expected_error_fragment}', Error actual: '{error_msg}'")
        print(f"✅ ÉXITO: {description} - Valor: '{value}' correctamente rechazado con error: '{error_msg}'")
    
    def test_validate_identificacion_valid(self):
        """Test para identificaciones válidas"""
        print("\n🔍 PROBANDO: Validación de identificaciones válidas")
        
        test_cases = [
            ("1234", "identificación mínima de 4 dígitos"),
            ("12345678", "identificación típica de 8 dígitos"), 
            ("12345678901", "identificación máxima de 11 dígitos"),
            ("0000", "identificación con ceros"),
            ("9999999999", "identificación con nueves")
        ]
        
        for identificacion, description in test_cases:
            with self.subTest(identificacion=identificacion):
                self._assert_validation_success(
                    self.validator.validate_identificacion, 
                    identificacion, 
                    f"Identificación válida: {description}"
                )
    
    def test_validate_identificacion_invalid_length(self):
        """Test para identificaciones con longitud inválida"""
        print("\n🔍 PROBANDO: Identificaciones con longitud inválida")
        
        test_cases = [
            ("123", "identificación muy corta (3 dígitos)", "entre 4 y 11 dígitos"),
            ("12", "identificación muy corta (2 dígitos)", "entre 4 y 11 dígitos"),
            ("123456789012", "identificación muy larga (12 dígitos)", "entre 4 y 11 dígitos"),
            ("1234567890123456", "identificación extremadamente larga (16 dígitos)", "entre 4 y 11 dígitos")
        ]
        
        for identificacion, description, expected_error in test_cases:
            with self.subTest(identificacion=identificacion):
                self._assert_validation_failure(
                    self.validator.validate_identificacion,
                    identificacion,
                    expected_error,
                    f"Identificación inválida: {description}"
                )
    
    def test_validate_identificacion_invalid_characters(self):
        """Test para identificaciones con caracteres inválidos"""
        print("\n🔍 PROBANDO: Identificaciones con caracteres no numéricos")
        
        test_cases = [
            ("12a34", "identificación con letra", "dígitos numéricos"),
            ("1234-", "identificación con guión", "dígitos numéricos"),
            ("12.34", "identificación con punto", "dígitos numéricos"),
            ("12 34", "identificación con espacio", "dígitos numéricos"),
            ("12@34", "identificación con símbolo", "dígitos numéricos"),
            ("abcd", "identificación solo letras", "dígitos numéricos")
        ]
        
        for identificacion, description, expected_error in test_cases:
            with self.subTest(identificacion=identificacion):
                self._assert_validation_failure(
                    self.validator.validate_identificacion,
                    identificacion,
                    expected_error,
                    f"Identificación inválida: {description}"
                )
    
    def test_validate_identificacion_empty(self):
        """Test para identificación vacía"""
        print("\n🔍 PROBANDO: Identificaciones vacías o nulas")
        
        test_cases = [
            ("", "cadena vacía", "no puede estar vacía"),
            (None, "valor None", "no puede estar vacía")
        ]
        
        for identificacion, description, expected_error in test_cases:
            with self.subTest(identificacion=str(identificacion)):
                self._assert_validation_failure(
                    self.validator.validate_identificacion,
                    identificacion,
                    expected_error,
                    f"Identificación inválida: {description}"
                )
    
    def test_validate_nombre_completo_valid(self):
        """Test para nombres válidos"""
        print("\n🔍 PROBANDO: Validación de nombres completos válidos")
        
        test_cases = [
            ("Juan Pérez", "nombre simple con tilde"),
            ("María José García", "nombre compuesto con tildes"),
            ("José Luis Rodríguez Martínez", "nombre con múltiples palabras"),
            ("Sofía", "nombre simple"),
            ("Ana María de la Cruz", "nombre con preposiciones"),
            ("Ñoño Español", "nombre con ñ y tildes")
        ]
        
        for nombre, description in test_cases:
            with self.subTest(nombre=nombre):
                self._assert_validation_success(
                    self.validator.validate_nombre_completo,
                    nombre,
                    f"Nombre válido: {description}"
                )
    
    def test_validate_nombre_completo_invalid_characters(self):
        """Test para nombres con caracteres inválidos"""
        print("\n🔍 PROBANDO: Nombres con caracteres no permitidos")
        
        test_cases = [
            ("Juan123", "nombre con números", "solo puede contener letras"),
            ("María@gmail", "nombre con símbolo @", "solo puede contener letras"),
            ("José-Luis", "nombre con guión", "solo puede contener letras"),
            ("Ana_María", "nombre con guión bajo", "solo puede contener letras"),
            ("Pedro.Pablo", "nombre con punto", "solo puede contener letras"),
            ("Carlos#", "nombre con símbolo #", "solo puede contener letras")
        ]
        
        for nombre, description, expected_error in test_cases:
            with self.subTest(nombre=nombre):
                self._assert_validation_failure(
                    self.validator.validate_nombre_completo,
                    nombre,
                    expected_error,
                    f"Nombre inválido: {description}"
                )
    
    def test_validate_nombre_completo_empty(self):
        """Test para nombre vacío"""
        print("\n🔍 PROBANDO: Nombres vacíos o nulos")
        
        test_cases = [
            ("", "cadena vacía", "no puede estar vacío"),
            (None, "valor None", "no puede estar vacío")
        ]
        
        for nombre, description, expected_error in test_cases:
            with self.subTest(nombre=str(nombre)):
                self._assert_validation_failure(
                    self.validator.validate_nombre_completo,
                    nombre,
                    expected_error,
                    f"Nombre inválido: {description}"
                )
    
    def test_validate_nombre_completo_too_long(self):
        """Test para nombre muy largo"""
        print("\n🔍 PROBANDO: Nombres que exceden la longitud máxima")
        
        long_name = "a" * 101  # 101 caracteres
        self._assert_validation_failure(
            self.validator.validate_nombre_completo,
            long_name,
            "más de 100 caracteres",
            "Nombre demasiado largo (101 caracteres)"
        )
    
    def test_validate_telefono_valid(self):
        """Test para teléfonos válidos"""
        print("\n🔍 PROBANDO: Validación de teléfonos válidos")
        
        test_cases = [
            ("3001234567", "celular típico que empieza por 3"),
            ("6012345678", "fijo típico que empieza por 6"),
            ("3999999999", "celular límite superior para 3"),
            ("6999999999", "fijo límite superior para 6"),
            ("3000000000", "celular con ceros"),
            ("6000000000", "fijo con ceros")
        ]
        
        for telefono, description in test_cases:
            with self.subTest(telefono=telefono):
                self._assert_validation_success(
                    self.validator.validate_telefono,
                    telefono,
                    f"Teléfono válido: {description}"
                )
    
    def test_validate_telefono_invalid_start(self):
        """Test para teléfonos que no empiezan por 3 o 6"""
        print("\n🔍 PROBANDO: Teléfonos que no empiezan por 3 o 6")
        
        test_cases = [
            ("1001234567", "teléfono que empieza por 1", "empezar por 3 o 6"),
            ("2001234567", "teléfono que empieza por 2", "empezar por 3 o 6"),
            ("4001234567", "teléfono que empieza por 4", "empezar por 3 o 6"),
            ("5001234567", "teléfono que empieza por 5", "empezar por 3 o 6"),
            ("7001234567", "teléfono que empieza por 7", "empezar por 3 o 6"),
            ("8001234567", "teléfono que empieza por 8", "empezar por 3 o 6"),
            ("9001234567", "teléfono que empieza por 9", "empezar por 3 o 6"),
            ("0001234567", "teléfono que empieza por 0", "empezar por 3 o 6")
        ]
        
        for telefono, description, expected_error in test_cases:
            with self.subTest(telefono=telefono):
                self._assert_validation_failure(
                    self.validator.validate_telefono,
                    telefono,
                    expected_error,
                    f"Teléfono inválido: {description}"
                )
    
    def test_validate_telefono_invalid_length(self):
        """Test para teléfonos con longitud incorrecta"""
        print("\n🔍 PROBANDO: Teléfonos con longitud incorrecta")
        
        test_cases = [
            ("300123456", "teléfono celular muy corto (9 dígitos)", "exactamente 10 dígitos"),
            ("30012345678", "teléfono celular muy largo (11 dígitos)", "exactamente 10 dígitos"),
            ("3001", "teléfono celular extremadamente corto", "exactamente 10 dígitos"),
            ("600123456", "teléfono fijo muy corto (9 dígitos)", "exactamente 10 dígitos"),
            ("60012345678", "teléfono fijo muy largo (11 dígitos)", "exactamente 10 dígitos"),
            ("300", "teléfono con solo 3 dígitos", "exactamente 10 dígitos")
        ]
        
        for telefono, description, expected_error in test_cases:
            with self.subTest(telefono=telefono):
                self._assert_validation_failure(
                    self.validator.validate_telefono,
                    telefono,
                    expected_error,
                    f"Teléfono inválido: {description}"
                )
    
    def test_validate_telefono_invalid_characters(self):
        """Test para teléfonos con caracteres inválidos"""
        print("\n🔍 PROBANDO: Teléfonos con caracteres no numéricos")
        
        test_cases = [
            ("300-123-4567", "teléfono con guiones", "exactamente 10 dígitos"),
            ("300 123 4567", "teléfono con espacios", "exactamente 10 dígitos"),
            ("300.123.4567", "teléfono con puntos", "exactamente 10 dígitos"),
            ("300123456a", "teléfono con letra al final", "exactamente 10 dígitos"),
            ("+3001234567", "teléfono con símbolo +", "exactamente 10 dígitos"),
            ("(300)123456", "teléfono con paréntesis", "exactamente 10 dígitos")
        ]
        
        for telefono, description, expected_error in test_cases:
            with self.subTest(telefono=telefono):
                self._assert_validation_failure(
                    self.validator.validate_telefono,
                    telefono,
                    expected_error,
                    f"Teléfono inválido: {description}"
                )
    
    def test_validate_telefono_empty(self):
        """Test para teléfono vacío"""
        print("\n🔍 PROBANDO: Teléfonos vacíos o nulos")
        
        test_cases = [
            ("", "cadena vacía", "no puede estar vacío"),
            (None, "valor None", "no puede estar vacío")
        ]
        
        for telefono, description, expected_error in test_cases:
            with self.subTest(telefono=str(telefono)):
                self._assert_validation_failure(
                    self.validator.validate_telefono,
                    telefono,
                    expected_error,
                    f"Teléfono inválido: {description}"
                )
    
    def test_validate_email_valid(self):
        """Test para emails válidos"""
        print("\n🔍 PROBANDO: Validación de emails válidos")
        
        test_cases = [
            ("usuario@example.com", "email simple típico"),
            ("test.email@domain.co", "email con punto en parte local"),
            ("user+tag@site.org", "email con símbolo + (tag)"),
            ("name123@test-domain.net", "email con números y guión en dominio"),
            ("a@b.co", "email mínimo válido"),
            ("user_name@example-site.com", "email con guión bajo y dominio compuesto")
        ]
        
        for email, description in test_cases:
            with self.subTest(email=email):
                self._assert_validation_success(
                    self.validator.validate_email,
                    email,
                    f"Email válido: {description}"
                )
    
    def test_validate_email_no_at_symbol(self):
        """Test para emails sin símbolo @"""
        print("\n🔍 PROBANDO: Emails sin símbolo @")
        
        test_cases = [
            ("usuarioexample.com", "email sin @ - falta separador", "debe contener el símbolo @"),
            ("test.email.domain.co", "email con puntos pero sin @", "debe contener el símbolo @"),
            ("plaintext", "texto simple sin @", "debe contener el símbolo @"),
            ("user.domain.com", "formato de dominio sin @", "debe contener el símbolo @")
        ]
        
        for email, description, expected_error in test_cases:
            with self.subTest(email=email):
                self._assert_validation_failure(
                    self.validator.validate_email,
                    email,
                    expected_error,
                    f"Email inválido: {description}"
                )
    
    def test_validate_email_invalid_format(self):
        """Test para emails con formato inválido"""
        print("\n🔍 PROBANDO: Emails con formato inválido")
        
        test_cases = [
            ("@example.com", "email sin parte local", "formato del email no es válido"),
            ("user@", "email sin dominio", "formato del email no es válido"),
            ("user@domain", "email sin TLD", "formato del email no es válido"),
            ("user@@domain.com", "email con doble @", "formato del email no es válido"),
            ("user@domain.", "email con TLD vacío", "formato del email no es válido"),
            ("user space@domain.com", "email con espacios en parte local", "formato del email no es válido"),
            ("user@domain com", "email con espacios en dominio", "formato del email no es válido")
        ]
        
        for email, description, expected_error in test_cases:
            with self.subTest(email=email):
                self._assert_validation_failure(
                    self.validator.validate_email,
                    email,
                    expected_error,
                    f"Email inválido: {description}"
                )
    
    def test_validate_email_empty(self):
        """Test para email vacío"""
        print("\n🔍 PROBANDO: Emails vacíos o nulos")
        
        test_cases = [
            ("", "cadena vacía", "no puede estar vacío"),
            (None, "valor None", "no puede estar vacío")
        ]
        
        for email, description, expected_error in test_cases:
            with self.subTest(email=str(email)):
                self._assert_validation_failure(
                    self.validator.validate_email,
                    email,
                    expected_error,
                    f"Email inválido: {description}"
                )
    
    def test_validate_all_fields_valid(self):
        """Test para validación de todos los campos válidos"""
        print("\n🔍 PROBANDO: Validación completa con todos los campos válidos")
        
        is_valid, errors = self.validator.validate_all_fields(
            identificacion="12345678",
            nombre="Juan Pérez",
            telefono="3001234567", 
            email="juan@example.com"
        )
        
        self.assertTrue(is_valid, "❌ FALLO: Todos los campos válidos deberían pasar la validación")
        self.assertEqual(len(errors), 0, f"❌ FALLO: No debería haber errores, pero se encontraron: {errors}")
        print("✅ ÉXITO: Validación completa exitosa - Todos los campos son válidos")
        print(f"   📝 Datos validados: ID='12345678', Nombre='Juan Pérez', Tel='3001234567', Email='juan@example.com'")
    
    def test_validate_all_fields_multiple_errors(self):
        """Test para validación con múltiples errores"""
        print("\n🔍 PROBANDO: Validación completa con múltiples errores")
        
        is_valid, errors = self.validator.validate_all_fields(
            identificacion="123",        # Muy corto
            nombre="Juan123",           # Caracteres inválidos
            telefono="1234567890",      # No empieza por 3 o 6
            email="invalidemail"        # Sin @
        )
        
        self.assertFalse(is_valid, "❌ FALLO: Datos inválidos deberían fallar la validación")
        self.assertEqual(len(errors), 4, f"❌ FALLO: Deberían ser 4 errores, pero se encontraron {len(errors)}: {errors}")
        
        # Verificar que cada tipo de error está presente
        error_text = " ".join(errors)
        expected_errors = [
            ("entre 4 y 11 dígitos", "identificación muy corta"),
            ("solo puede contener letras", "nombre con números"),
            ("empezar por 3 o 6", "teléfono con prefijo inválido"),
            ("debe contener el símbolo @", "email sin @")
        ]
        
        for expected_fragment, description in expected_errors:
            self.assertIn(expected_fragment, error_text, 
                         f"❌ FALLO: Error esperado '{description}' no encontrado en: {errors}")
        
        print("✅ ÉXITO: Validación múltiple correcta - Se detectaron todos los errores esperados")
        print(f"   📝 Errores encontrados ({len(errors)}):")
        for i, error in enumerate(errors, 1):
            print(f"      {i}. {error}")
    
    def test_validate_all_fields_partial_errors(self):
        """Test para validación con algunos errores"""
        print("\n🔍 PROBANDO: Validación completa con error parcial")
        
        is_valid, errors = self.validator.validate_all_fields(
            identificacion="12345678",   # Válido
            nombre="Juan Pérez",        # Válido
            telefono="1234567890",      # Inválido - no empieza por 3 o 6
            email="juan@example.com"    # Válido
        )
        
        self.assertFalse(is_valid, "❌ FALLO: Datos con un campo inválido deberían fallar la validación")
        self.assertEqual(len(errors), 1, f"❌ FALLO: Debería haber exactamente 1 error, pero se encontraron {len(errors)}: {errors}")
        self.assertIn("empezar por 3 o 6", errors[0], f"❌ FALLO: Error de teléfono esperado, pero se obtuvo: {errors[0]}")
        
        print("✅ ÉXITO: Validación parcial correcta - Se detectó el único error esperado")
        print(f"   📝 Error encontrado: {errors[0]}")
        print("   📝 Campos válidos: identificación, nombre, email")
        print("   📝 Campo inválido: teléfono")


def print_test_summary():
    """Imprime un resumen de las pruebas al finalizar"""
    print("\n" + "="*80)
    print("📊 RESUMEN DE PRUEBAS UNITARIAS - UserValidator")
    print("="*80)
    print("🎯 Componentes probados:")
    print("   ✓ validate_identificacion() - Validación de números de identificación")
    print("   ✓ validate_nombre_completo() - Validación de nombres con tildes y ñ")
    print("   ✓ validate_telefono() - Validación de números celulares y fijos")
    print("   ✓ validate_email() - Validación de direcciones de correo")
    print("   ✓ validate_all_fields() - Validación completa de usuario")
    print("\n🧪 Tipos de pruebas realizadas:")
    print("   • Casos válidos (happy path)")
    print("   • Casos inválidos (edge cases)")
    print("   • Validación de campos vacíos/nulos")
    print("   • Validación de longitudes")
    print("   • Validación de caracteres especiales")
    print("   • Validación de formatos específicos")
    print("="*80)


if __name__ == '__main__':
    # Ejecutar las pruebas
    unittest.main(verbosity=2, exit=False)
    
    # Mostrar resumen
    print_test_summary()
