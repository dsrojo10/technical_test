import streamlit as st
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Importar módulos del proyecto
from chat_core import ChatManager
import config

# Configuración de la página
st.set_page_config(
    page_title="Asistente Virtual - SuperMercado",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
<style>
.main {
    padding-top: 2rem;
}

.stChatMessage {
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

.user-message {
    background-color: #e3f2fd;
}

.assistant-message {
    background-color: #f5f5f5;
}

.header {
    text-align: center;
    padding: 1rem 0;
    background: linear-gradient(90deg, #2196F3, #21CBF3);
    color: white;
    border-radius: 0.5rem;
    margin-bottom: 2rem;
}

.status-info {
    background-color: #e8f5e8;
    padding: 0.5rem;
    border-radius: 0.3rem;
    border-left: 4px solid #4CAF50;
    margin: 1rem 0;
}

.error-info {
    background-color: #ffeaa7;
    padding: 0.5rem;
    border-radius: 0.3rem;
    border-left: 4px solid #fdcb6e;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Inicializa el estado de la sesión"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "chat_manager" not in st.session_state:
        st.session_state.chat_manager = ChatManager()
    
    if "session_data" not in st.session_state:
        st.session_state.session_data = {}


def display_chat_messages():
    """Muestra los mensajes del chat"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def display_sidebar_info():
    """Muestra información en la barra lateral"""
    with st.sidebar:
        st.title("ℹ️ Información")
        
        # Estado de la conversación
        if hasattr(st.session_state, 'chat_manager'):
            status = st.session_state.chat_manager.get_conversation_status(st.session_state.session_data)
            
            st.subheader("Estado actual")
            state_display = {
                "welcome": "🏠 Bienvenida",
                "identify_user_type": "👤 Identificando tipo de usuario",
                "existing_user_id": "🔍 Validando usuario existente",
                "new_user_id": "📝 Registro - Identificación",
                "new_user_name": "📝 Registro - Nombre",
                "new_user_phone": "📝 Registro - Teléfono",
                "new_user_email": "📝 Registro - Email",
                "chat_active": "💬 Chat activo"
            }
            
            current_state = status.get("state", "welcome")
            st.info(state_display.get(current_state, current_state))
            
            # Usuario actual
            if status.get("user_authenticated"):
                user = status.get("current_user")
                if user:
                    st.subheader("Usuario actual")
                    st.success(f"👋 {user['nombre_completo']}")
                    with st.expander("Ver detalles"):
                        st.write(f"**ID:** {user['identificacion']}")
                        st.write(f"**Teléfono:** {user['telefono']}")
                        st.write(f"**Email:** {user['email']}")
            
            # Progreso de registro
            registration = status.get("registration_progress", {})
            if registration:
                st.subheader("Progreso de registro")
                progress_items = {
                    "identificacion": "✅ Identificación",
                    "nombre_completo": "✅ Nombre",
                    "telefono": "✅ Teléfono",
                    "email": "✅ Email"
                }
                
                for key, label in progress_items.items():
                    if key in registration:
                        st.write(label)
        
        st.divider()
        
        # Información del bot
        st.subheader("🤖 Sobre el asistente")
        st.write("""
        Este asistente virtual puede ayudarte con:
        
        • 🕒 Horarios de atención
        • 🎁 Información sobre promociones  
        • ❓ Preguntas frecuentes
        • 📞 Información de contacto
        
        **Tipos de consulta:**
        - Horarios de la tienda
        - Programa Suma y Gana
        - Preguntas generales
        """)
        
        st.divider()
        
        # Botón para reiniciar
        if st.button("🔄 Reiniciar conversación", type="secondary"):
            st.session_state.messages = []
            st.session_state.session_data = {}
            st.rerun()


def main():
    """Función principal de la aplicación"""
    
    # Verificar configuración
    if not config.OPENAI_API_KEY:
        st.error("⚠️ **Configuración requerida:** Por favor configura tu API key de OpenAI en las variables de entorno o en .streamlit/secrets.toml")
        st.info("Agrega tu API key en `.streamlit/secrets.toml`: \n```\nOPENAI_API_KEY = \"tu-api-key-aqui\"\n```")
        st.stop()
    
    # Inicializar estado
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="header">
        <h1>🛒 Asistente Virtual SuperMercado</h1>
        <p>Tu asistente personal para consultas y atención al cliente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    display_sidebar_info()
    
    # Mensaje de bienvenida inicial - solo si no hay mensajes Y no hay estado de conversación
    if not st.session_state.messages and not st.session_state.session_data:
        # Procesar el mensaje de bienvenida a través del chat manager
        welcome_response, initial_session = st.session_state.chat_manager.handle_message(
            "", st.session_state.session_data
        )
        st.session_state.session_data = initial_session
        st.session_state.messages.append({"role": "assistant", "content": welcome_response})
    
    # Mostrar mensajes
    display_chat_messages()
    
    # Input del usuario
    if prompt := st.chat_input("Escribe tu mensaje aquí..."):
        # Agregar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Mostrar mensaje del usuario inmediatamente
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Procesar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Procesando..."):
                try:
                    response, updated_session = st.session_state.chat_manager.handle_message(
                        prompt, 
                        st.session_state.session_data
                    )
                    
                    # Actualizar estado de sesión
                    st.session_state.session_data = updated_session
                    
                    # Mostrar respuesta
                    st.markdown(response)
                    
                    # Agregar respuesta a mensajes
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = "Lo siento, hubo un error procesando tu mensaje. Por favor intenta de nuevo."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    logging.error(f"Error en la aplicación: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
        f"© 2025 SuperMercado - Asistente Virtual | Desarrollado con Streamlit y OpenAI"
        "</div>", 
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
