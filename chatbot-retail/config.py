import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

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

# Configuración de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")  # Opcional
OPENAI_MODEL = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")
EMBEDDING_MODEL = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")

# Validar que la API key esté configurada
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY no está configurada. Por favor, configúrala en el archivo .env")

# Configuración del chatbot
BOT_NAME = "Asistente Virtual SuperMercado"
MAX_TOKENS = 1000
TEMPERATURE = 0.7

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
