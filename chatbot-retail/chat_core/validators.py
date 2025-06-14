import re
from typing import Optional, Tuple
from pydantic import BaseModel, validator


class UserData(BaseModel):
    """Modelo de datos para usuarios"""
    identificacion: str
    nombre_completo: str
    telefono: str
    email: str


class UserValidator:
    """Validador de datos de usuario con regex"""
    
    @staticmethod
    def validate_identificacion(identificacion: str) -> Tuple[bool, Optional[str]]:
        """
        Valida identificación: 4-11 dígitos numéricos
        
        Returns:
            Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
        """
        if not identificacion:
            return False, "La identificación no puede estar vacía"
        
        if not re.match(r'^\d{4,11}$', identificacion):
            return False, "La identificación debe tener entre 4 y 11 dígitos numéricos"
        
        return True, None
    
    @staticmethod
    def validate_nombre_completo(nombre: str) -> Tuple[bool, Optional[str]]:
        """
        Valida nombre: 1-100 letras, permite tildes y ñ
        
        Returns:
            Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
        """
        if not nombre:
            return False, "El nombre no puede estar vacío"
        
        if len(nombre) > 100:
            return False, "El nombre no puede tener más de 100 caracteres"
        
        # Permite letras, espacios, tildes y ñ
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            return False, "El nombre solo puede contener letras, espacios y tildes"
        
        return True, None
    
    @staticmethod
    def validate_telefono(telefono: str) -> Tuple[bool, Optional[str]]:
        """
        Valida teléfono: exactamente 10 dígitos, iniciando por 3 o 6
        
        Returns:
            Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
        """
        if not telefono:
            return False, "El teléfono no puede estar vacío"
        
        if not re.match(r'^[36]\d{9}$', telefono):
            return False, "El teléfono debe tener exactamente 10 dígitos y empezar por 3 o 6"
        
        return True, None
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Valida email: debe contener @
        
        Returns:
            Tuple[bool, Optional[str]]: (es_valido, mensaje_error)
        """
        if not email:
            return False, "El email no puede estar vacío"
        
        if '@' not in email:
            return False, "El email debe contener el símbolo @"
        
        # Validación básica de email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return False, "El formato del email no es válido"
        
        return True, None
    
    @classmethod
    def validate_all_fields(cls, identificacion: str, nombre: str, telefono: str, email: str) -> Tuple[bool, list]:
        """
        Valida todos los campos del usuario
        
        Returns:
            Tuple[bool, list]: (todos_validos, lista_errores)
        """
        errors = []
        
        is_valid, error = cls.validate_identificacion(identificacion)
        if not is_valid:
            errors.append(error)
        
        is_valid, error = cls.validate_nombre_completo(nombre)
        if not is_valid:
            errors.append(error)
        
        is_valid, error = cls.validate_telefono(telefono)
        if not is_valid:
            errors.append(error)
        
        is_valid, error = cls.validate_email(email)
        if not is_valid:
            errors.append(error)
        
        return len(errors) == 0, errors
