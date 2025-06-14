from enum import Enum
from typing import Optional, Dict, Any, Tuple
import logging

from .registry import UserRegistry
from .validators import UserValidator
from .qa_engine import QAEngine
import config


class ConversationState(Enum):
    """Estados de la conversación"""
    WELCOME = "welcome"
    IDENTIFY_USER_TYPE = "identify_user_type"
    EXISTING_USER_ID = "existing_user_id"
    NEW_USER_ID = "new_user_id"
    NEW_USER_NAME = "new_user_name"
    NEW_USER_PHONE = "new_user_phone"
    NEW_USER_EMAIL = "new_user_email"
    CHAT_ACTIVE = "chat_active"


class ChatManager:
    """Maneja el flujo de conversación del chatbot"""
    
    def __init__(self):
        self.registry = UserRegistry()
        self.validator = UserValidator()
        # Usar el motor QA mejorado
        self.qa_engine = QAEngine()
        
        # Inicializar documentos
        self.qa_engine.process_documents()
    
    def handle_message(self, message: str, session_state: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Maneja un mensaje del usuario y retorna la respuesta
        
        Args:
            message: Mensaje del usuario
            session_state: Estado de la sesión actual
            
        Returns:
            Tuple[str, Dict]: (respuesta, nuevo_estado_sesion)
        """
        # Inicializar estado si es nuevo
        if "conversation_state" not in session_state:
            session_state["conversation_state"] = ConversationState.WELCOME.value
            session_state["user_data"] = {}
            session_state["current_user"] = None
        
        current_state = session_state["conversation_state"]
        message_lower = message.lower().strip()
        
        # Manejar estados de conversación
        if current_state == ConversationState.WELCOME.value:
            return self._handle_welcome(message_lower, session_state)
            
        elif current_state == ConversationState.IDENTIFY_USER_TYPE.value:
            return self._handle_user_type_identification(message_lower, session_state)
            
        elif current_state == ConversationState.EXISTING_USER_ID.value:
            return self._handle_existing_user_id(message, session_state)
            
        elif current_state == ConversationState.NEW_USER_ID.value:
            return self._handle_new_user_id(message, session_state)
            
        elif current_state == ConversationState.NEW_USER_NAME.value:
            return self._handle_new_user_name(message, session_state)
            
        elif current_state == ConversationState.NEW_USER_PHONE.value:
            return self._handle_new_user_phone(message, session_state)
            
        elif current_state == ConversationState.NEW_USER_EMAIL.value:
            return self._handle_new_user_email(message, session_state)
            
        elif current_state == ConversationState.CHAT_ACTIVE.value:
            return self._handle_active_chat(message, session_state)
        
        # Estado desconocido - reiniciar
        return self._reset_conversation(session_state)
    
    def _handle_welcome(self, message: str, session_state: Dict) -> Tuple[str, Dict]:
        """Maneja el mensaje de bienvenida inicial"""
        # Si es el primer mensaje (vacío), solo retornar el mensaje de bienvenida
        if not message.strip():
            session_state["conversation_state"] = ConversationState.IDENTIFY_USER_TYPE.value
            return config.WELCOME_MESSAGE, session_state
        
        # Si ya hay un mensaje, procesarlo como identificación de tipo de usuario
        return self._handle_user_type_identification(message, session_state)
    
    def _handle_user_type_identification(self, message: str, session_state: Dict) -> Tuple[str, Dict]:
        """Identifica si es cliente nuevo o frecuente"""
        if any(word in message for word in ["nuevo", "nueva", "registrar", "registro"]):
            session_state["conversation_state"] = ConversationState.NEW_USER_ID.value
            return "Perfecto! Vamos a registrarte. Primero necesito tu número de identificación (entre 4 y 11 dígitos):", session_state
            
        elif any(word in message for word in ["frecuente", "cuenta", "tengo", "ya", "registrado"]):
            session_state["conversation_state"] = ConversationState.EXISTING_USER_ID.value
            return "¡Excelente! Por favor ingresa tu número de identificación para verificar tu cuenta:", session_state
        
        return "No entendí tu respuesta. Por favor indica si eres un cliente nuevo o ya tienes cuenta con nosotros.", session_state
    
    def _handle_existing_user_id(self, message: str, session_state: Dict) -> Tuple[str, Dict]:
        """Maneja la identificación de usuarios existentes"""
        identificacion = message.strip()
        
        # Validar formato
        is_valid, error = self.validator.validate_identificacion(identificacion)
        if not is_valid:
            return f"❌ {error} Por favor ingresa tu identificación correctamente:", session_state
        
        # Verificar si existe
        user = self.registry.get_user(identificacion)
        if user:
            session_state["current_user"] = user
            session_state["conversation_state"] = ConversationState.CHAT_ACTIVE.value
            return f"¡Hola {user['nombre_completo']}! 😊 ¿En qué puedo ayudarte hoy?", session_state
        else:
            session_state["conversation_state"] = ConversationState.IDENTIFY_USER_TYPE.value
            return "No encontré tu identificación en nuestro sistema. ¿Te gustaría registrarte como cliente nuevo?", session_state
    
    def _handle_new_user_id(self, message: str, session_state: Dict) -> Tuple[str, Dict]:
        """Maneja el registro de identificación para nuevos usuarios"""
        identificacion = message.strip()
        
        # Validar formato
        is_valid, error = self.validator.validate_identificacion(identificacion)
        if not is_valid:
            return f"❌ {error} Por favor intenta de nuevo:", session_state
        
        # Verificar que no exista
        if self.registry.user_exists(identificacion):
            return "❌ Esta identificación ya está registrada. ¿Eres un cliente frecuente? Si es así, puedes identificarte directamente.", session_state
        
        session_state["user_data"]["identificacion"] = identificacion
        session_state["conversation_state"] = ConversationState.NEW_USER_NAME.value
        return "✅ Perfecto! Ahora necesito tu nombre completo:", session_state
    
    def _handle_new_user_name(self, message: str, session_state: Dict) -> Tuple[str, Dict]:
        """Maneja el registro del nombre"""
        nombre = message.strip()
        
        # Validar formato
        is_valid, error = self.validator.validate_nombre_completo(nombre)
        if not is_valid:
            return f"❌ {error} Por favor intenta de nuevo:", session_state
        
        session_state["user_data"]["nombre_completo"] = nombre
        session_state["conversation_state"] = ConversationState.NEW_USER_PHONE.value
        return "✅ Excelente! Ahora necesito tu número de teléfono (10 dígitos, iniciando por 3 o 6):", session_state
    
    def _handle_new_user_phone(self, message: str, session_state: Dict) -> Tuple[str, Dict]:
        """Maneja el registro del teléfono"""
        telefono = message.strip()
        
        # Validar formato
        is_valid, error = self.validator.validate_telefono(telefono)
        if not is_valid:
            return f"❌ {error} Por favor intenta de nuevo:", session_state
        
        session_state["user_data"]["telefono"] = telefono
        session_state["conversation_state"] = ConversationState.NEW_USER_EMAIL.value
        return "✅ Perfecto! Por último, necesito tu correo electrónico:", session_state
    
    def _handle_new_user_email(self, message: str, session_state: Dict) -> Tuple[str, Dict]:
        """Maneja el registro del email y completa el registro"""
        email = message.strip()
        
        # Validar formato
        is_valid, error = self.validator.validate_email(email)
        if not is_valid:
            return f"❌ {error} Por favor intenta de nuevo:", session_state
        
        session_state["user_data"]["email"] = email
        
        # Registrar usuario
        user_data = session_state["user_data"]
        success = self.registry.register_user(
            user_data["identificacion"],
            user_data["nombre_completo"],
            user_data["telefono"],
            user_data["email"]
        )
        
        if success:
            # Obtener datos del usuario registrado
            user = self.registry.get_user(user_data["identificacion"])
            session_state["current_user"] = user
            session_state["conversation_state"] = ConversationState.CHAT_ACTIVE.value
            
            return f"🎉 ¡Registro completado exitosamente! Bienvenido/a {user_data['nombre_completo']}. ¿En qué puedo ayudarte hoy?", session_state
        else:
            return "❌ Hubo un error en el registro. Por favor contacta al servicio al cliente.", session_state
    
    def _handle_active_chat(self, message: str, session_state: Dict) -> Tuple[str, Dict]:
        """Maneja el chat activo con preguntas y respuestas mejoradas"""
        try:
            # Detectar preguntas sobre las capacidades del chatbot
            message_lower = message.lower().strip()
            if self._is_bot_capability_question(message_lower):
                return self._respond_bot_capabilities(session_state)
            
            # Preparar contexto del usuario
            user_context = {}
            if session_state.get("current_user"):
                user_context = {
                    "customer_type": "frecuente" if session_state["current_user"] else "nuevo",
                    "user_id": session_state["current_user"].get("identificacion") if session_state["current_user"] else None
                }
            
            # Usar el motor de QA mejorado para responder
            answer, sources, metadata = self.qa_engine.ask_question(message, user_context)
            
            # Agregar información de fuentes si están disponibles
            if sources:
                source_text = ", ".join(sources)
                answer += f"\n\n📚 *Información obtenida de: {source_text}*"
            
            # Agregar sugerencias contextuales si la calidad de respuesta es baja
            if metadata.get("quality_score", 0) < 0.6:
                suggestions = self.qa_engine.get_context_aware_suggestions(message)
                if suggestions:
                    answer += f"\n\n💡 **También podrías preguntar:**\n"
                    for suggestion in suggestions[:2]:  # Máximo 2 sugerencias
                        answer += f"• {suggestion}\n"
            
            # Agregar información de calidad para debugging (solo en desarrollo)
            if config.DEBUG if hasattr(config, 'DEBUG') else False:
                answer += f"\n\n🔍 *Score: {metadata.get('quality_score', 0):.2f}, Fuentes: {metadata.get('sources_used', 0)}*"
            
            return answer, session_state
            
        except Exception as e:
            logging.error(f"Error en chat activo: {str(e)}")
            return "Lo siento, hubo un problema procesando tu consulta. Por favor intenta de nuevo o contacta al servicio al cliente.", session_state
    
    def _reset_conversation(self, session_state: Dict) -> Tuple[str, Dict]:
        """Reinicia la conversación"""
        session_state["conversation_state"] = ConversationState.WELCOME.value
        session_state["user_data"] = {}
        session_state["current_user"] = None
        
        return "Hubo un problema. Vamos a empezar de nuevo. " + config.WELCOME_MESSAGE, session_state
    
    def get_conversation_status(self, session_state: Dict) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la conversación
        
        Returns:
            Dict con información del estado actual
        """
        return {
            "state": session_state.get("conversation_state", ConversationState.WELCOME.value),
            "user_authenticated": session_state.get("current_user") is not None,
            "current_user": session_state.get("current_user"),
            "registration_progress": session_state.get("user_data", {})
        }
    
    def _is_bot_capability_question(self, message: str) -> bool:
        """Detecta si la pregunta es sobre las capacidades del chatbot"""
        capability_keywords = [
            "en qué me puedes ayudar",
            "qué puedes hacer",
            "cómo me ayudas",
            "cuáles son tus funciones",
            "qué servicios ofreces",
            "para qué sirves",
            "qué información tienes",
            "en qué me sirves",
            "cómo funciona este chat",
            "qué consultas puedo hacer",
            "dime qué haces",
            "cuál es tu propósito",
            "qué tipo de ayuda das",
            "qué preguntas puedo hacerte"
        ]
        
        return any(keyword in message for keyword in capability_keywords)
    
    def _respond_bot_capabilities(self, session_state: Dict) -> Tuple[str, Dict]:
        """Responde con las capacidades del chatbot"""
        user_name = ""
        if session_state.get("current_user"):
            user_name = f" {session_state['current_user']['nombre_completo']}"
        
        response = f"""¡Hola{user_name}! 🤖 Soy tu asistente virtual del supermercado y puedo ayudarte proporcionando información sobre:

🕒 **Horarios de Atención**
• Horarios de todas nuestras sucursales
• Días y horas específicas de operación
• Información sobre horarios especiales

🎁 **Promociones y Ofertas**
• Programa "Suma y Gana" 
• Descuentos y promociones vigentes
• Cómo acumular y redimir puntos

❓ **Preguntas Frecuentes**
• Métodos de pago
• Políticas de la tienda
• Procedimientos y servicios
• Información general del supermercado

**¿Cómo funciono?**
Busco en nuestra base de información oficial para darte respuestas precisas y actualizadas. Simplemente pregúntame lo que necesites saber sobre cualquiera de estos temas.

**Ejemplos de preguntas que puedes hacerme:**
• "¿Cuáles son los horarios de la sucursal Centro?"
• "¿Cómo funciona el programa Suma y Gana?"
• "¿Qué promociones tienen disponibles?"
• "¿Qué métodos de pago aceptan?"

¿En qué te gustaría que te ayude hoy? 😊"""

        return response, session_state
