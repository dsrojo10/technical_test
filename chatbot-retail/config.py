import os
from pathlib import Path
import streamlit as st

def get_secrets():
    """Obtener secrets de Streamlit de forma segura"""
    try:
        return st.secrets
    except Exception:
        # Fallback si no estamos en contexto de Streamlit
        return {}

def get_config_value(key, default=None):
    """Obtener valor de configuración desde secrets"""
    secrets = get_secrets()
    return secrets.get(key, default)

# Configuración de rutas
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"

# Archivos de documentos
HORARIOS_FILE = DOCUMENTS_DIR / "Horarios.xlsx"
SUMA_GANA_FILE = DOCUMENTS_DIR / "Suma_Gana.pdf"
PREGUNTAS_FILE = DOCUMENTS_DIR / "Preguntas_Frecuentes.docx"

# Base de datos
DATABASE_PATH = DATA_DIR / "users.db"

# Configuración de OpenAI (se carga dinámicamente)
def get_openai_config():
    """Obtener configuración de OpenAI"""
    api_key = get_config_value("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY no está configurada. Por favor, configúrala en Streamlit Secrets o en .streamlit/secrets.toml")
    
    return {
        "api_key": api_key,
        "org_id": get_config_value("OPENAI_ORG_ID"),
        "model": get_config_value("CHAT_MODEL", "gpt-3.5-turbo"),
        "embedding_model": get_config_value("EMBEDDINGS_MODEL", "text-embedding-3-small")
    }

# Variables que se pueden importar directamente (sin secrets)
OPENAI_MODEL = get_config_value("CHAT_MODEL", "gpt-3.5-turbo")
EMBEDDING_MODEL = get_config_value("EMBEDDINGS_MODEL", "text-embedding-3-small")

# Configuración del chatbot
BOT_NAME = "Asistente Virtual SuperMercado"
MAX_TOKENS = 1000
TEMPERATURE = 0.7
DEBUG = str(get_config_value("DEBUG", "false")).lower() == "true"

# Mensajes del sistema
WELCOME_MESSAGE = """¡Hola! Soy tu asistente virtual del supermercado. 
¿Eres un cliente nuevo o ya tienes cuenta con nosotros?

Responde:
- "Soy nuevo" o "Cliente nuevo" para registrarte
- "Ya tengo cuenta" o "Cliente frecuente" para identificarte"""

SYSTEM_PROMPT = """Eres un asistente virtual amigable de un supermercado. 
Tu trabajo es ayudar a los clientes con sus consultas sobre horarios, promociones y preguntas frecuentes.
Responde de manera natural y conversacional, basándote únicamente en la información proporcionada.
Si no tienes información específica, indica que no cuentas con esa información y sugiere contactar al servicio al cliente."""
