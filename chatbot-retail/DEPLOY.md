# Deploy Instructions for Streamlit Cloud

## ✅ Configuración Completada

- ✅ Migración de `.env` a `.streamlit/secrets.toml`
- ✅ Configuración de Python 3.11.9 para compatibilidad
- ✅ Eliminación de dependencia `python-dotenv`
- ✅ Configuración dinámica de secrets

## 🚀 Deployment Steps

1. **Push your code to GitHub** 
   - Asegúrate de que `.streamlit/secrets.toml` NO esté en tu repositorio (ya está en `.gitignore`)

2. **Go to [Streamlit Cloud](https://share.streamlit.io/)**

3. **Deploy your app** seleccionando tu repositorio y la rama `main`
   - Main file path: `chatbot-retail/streamlit_app.py`

4. **Click "Advanced settings" antes de hacer deploy**

5. **En el campo "Secrets", pega exactamente este contenido:**

```toml
# Configuración de OpenAI
OPENAI_API_KEY = "sk-proj-your-actual-key-here"

# Configuración de modelos
CHAT_MODEL = "gpt-3.5-turbo"
EMBEDDINGS_MODEL = "text-embedding-3-small"

# Configuración de desarrollo
DEBUG = false
```

6. **⚠️ IMPORTANTE: Reemplaza `sk-proj-your-actual-key-here`** con tu API key real de OpenAI

7. **Click "Deploy"** 

## 🔧 Características de la Nueva Configuración

- **Carga dinámica de secrets**: Los secrets se cargan solo cuando se necesitan
- **Mejor manejo de errores**: Mensajes más claros si falta configuración
- **Compatibilidad con Streamlit Cloud**: Usa `st.secrets` nativo
- **Python 3.11.9**: Versión compatible especificada en `runtime.txt`

## 💻 Local Development

Para desarrollo local, edita `.streamlit/secrets.toml` con tus credenciales:

```toml
OPENAI_API_KEY = "tu-api-key-local"
CHAT_MODEL = "gpt-3.5-turbo"
EMBEDDINGS_MODEL = "text-embedding-3-small"
DEBUG = true
```

## 🔍 Troubleshooting

Si tienes errores de `OPENAI_API_KEY no configurada`:

1. **En Streamlit Cloud**: Verifica que hayas pegado los secrets correctamente en "Advanced settings"
2. **Local**: Verifica que `.streamlit/secrets.toml` existe y tiene el formato correcto
3. **Formato**: Asegúrate de usar comillas en los valores string en el archivo `.toml`
