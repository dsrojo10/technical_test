# Chatbot Retail - Asistente Virtual SuperMercado

## Descripción

Chatbot inteligente para atención al cliente de un supermercado que utiliza procesamiento de lenguaje natural, embeddings y modelos LLM para responder preguntas frecuentes de manera conversacional.

## Características

- ✅ **Registro y autenticación de usuarios** (nuevos y frecuentes)
- ✅ **Validación robusta de datos** con regex y Pydantic
- ✅ **Procesamiento de lenguaje natural** con OpenAI GPT-3.5/4
- ✅ **Sistema de embeddings** para búsqueda semántica
- ✅ **Interfaz conversacional** con Streamlit
- ✅ **Base de datos SQLite** para persistencia
- ✅ **Procesamiento de documentos** (Excel, PDF, Word)
- ✅ **Reconocimiento de voz** para mensajes por audio
- ✅ **Dashboard de Analytics** con estadísticas y métricas de uso
- ✅ **Análisis de palabras clave** y patrones de conversación
- ✅ **Seguimiento de usuarios activos** y métricas de engagement

## 📊 Funcionalidad de Analytics

El sistema incluye un dashboard completo de analytics accessible desde la interfaz principal:

### Características del Dashboard:
- **Acceso protegido**: Contraseña de administrador requerida
- **Tendencias de uso**: Gráficos de conversaciones por día y hora
- **Análisis de tipos de consulta**: Distribución de categorías de preguntas
- **Usuarios más activos**: Ranking de usuarios por engagement
- **Análisis de palabras clave**: Términos más frecuentes en conversaciones
- **Métricas de tiempo real**: Estadísticas actualizadas automáticamente

### Cómo acceder:
1. En la barra lateral, introduce la contraseña de administrador
2. Haz clic en "📊 Ver Analytics"
3. Explora las diferentes pestañas del dashboard

### Métricas disponibles:
- Total de conversaciones por período
- Usuarios únicos activos
- Distribución horaria de uso
- Palabras clave más frecuentes
- Tipos de consulta más comunes
- Engagement de usuarios registrados vs anónimos

## Estructura del Proyecto

```
chatbot-retail/
├── streamlit_app.py           # Aplicación principal Streamlit
├── config.py                  # Configuración y constantes
├── chat_core/
│   ├── __init__.py
│   ├── registry.py            # CRUD de usuarios (SQLite)
│   ├── validators.py          # Validaciones con regex
│   ├── qa_engine.py           # Embeddings + LLM
│   └── chat_manager.py        # Lógica del flujo de conversación
├── data/
│   ├── documents/             # Archivos fuente
│   │   ├── Horarios.xlsx
│   │   ├── Suma_Gana.pdf
│   │   └── Preguntas_frecuentes.docx
│   ├── users.db              # Base de datos SQLite
│   └── embeddings/           # Cache de embeddings
├── utils/
│   ├── __init__.py
│   └── document_processor.py  # Extracción de texto
├── requirements.txt
├── .streamlit/
│   └── secrets.toml          # API keys
└── README.md
```

## Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <url-repositorio>
   cd chatbot-retail
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar API Key de OpenAI**
   
   Opción A - Archivo secrets.toml (recomendado):
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Editar secrets.toml y agregar tu API key
   ```
   
   Opción B - Variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env y agregar tu API key
   export OPENAI_API_KEY="tu-api-key-aqui"
   ```

5. **Agregar documentos**
   
   Coloca los siguientes archivos en `data/documents/`:
   - `Horarios.xlsx`
   - `Suma_Gana.pdf`
   - `Preguntas_frecuentes.docx`

## Uso

1. **Ejecutar la aplicación**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Abrir en el navegador**
   
   La aplicación se abrirá automáticamente en `http://localhost:8501`

3. **Interactuar con el chatbot**
   
   - Para clientes nuevos: registrarse con identificación, nombre, teléfono y email
   - Para clientes frecuentes: identificarse con número de identificación
   - Realizar consultas en lenguaje natural

## Validaciones de Datos

### Identificación
- Entre 4 y 11 dígitos numéricos
- No permite duplicados

### Nombre Completo
- Entre 1 y 100 caracteres
- Solo letras, espacios, tildes y ñ

### Teléfono
- Exactamente 10 dígitos
- Debe iniciar por 3 o 6

### Email
- Formato válido con @
- Validación regex completa

## Funcionalidades del QA Engine

- **Procesamiento de documentos**: Extrae texto de Excel, PDF y Word
- **Embeddings semánticos**: Usa `text-embedding-3-small` de OpenAI
- **Búsqueda por similitud**: FAISS vectorstore
- **Respuestas naturales**: GPT-3.5-turbo con prompt engineering
- **Cache inteligente**: Evita reprocesar documentos

## Tecnologías Utilizadas

- **Frontend**: Streamlit
- **Backend**: Python 3.8+
- **Base de datos**: SQLite
- **LLM**: OpenAI GPT-3.5-turbo
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: FAISS
- **Procesamiento**: LangChain
- **Validación**: Pydantic + regex

## Desarrollo

### Estructura de Estados de Conversación

```python
ConversationState:
- WELCOME: Mensaje inicial
- IDENTIFY_USER_TYPE: Nuevo vs frecuente
- EXISTING_USER_ID: Validar ID existente
- NEW_USER_*: Proceso de registro
- CHAT_ACTIVE: Conversación activa
```

### Agregar Nuevas Funcionalidades

1. **Nuevas validaciones**: Editar `chat_core/validators.py`
2. **Nuevos estados**: Modificar `chat_core/chat_manager.py`
3. **Procesamiento de documentos**: Extender `utils/document_processor.py`
4. **Configuración**: Actualizar `config.py`

## Testing

```bash
# Ejecutar tests (cuando se implementen)
python -m pytest tests/

# Validar datos manualmente
python -c "from chat_core.validators import UserValidator; print(UserValidator.validate_telefono('3001234567'))"
```

## Deployment

### Local
```bash
streamlit run streamlit_app.py --server.port 8501
```

### Docker (futuro)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py"]
```

## Consideraciones de Seguridad

- ✅ API keys en archivos de configuración (no en código)
- ✅ Validación robusta de inputs
- ✅ Sanitización de datos de usuario
- ⚠️ HTTPS recomendado para producción
- ⚠️ Rate limiting para API calls

## Limitaciones Conocidas

- Dependiente de conexión a internet (OpenAI API)
- SQLite no recomendado para alta concurrencia
- Cache de embeddings en disco local
- Sin autenticación avanzada

## Próximas Mejoras

- [ ] Tests unitarios y de integración
- [ ] Base de datos PostgreSQL
- [ ] Autenticación con JWT
- [ ] Rate limiting
- [ ] Logging avanzado
- [ ] Métricas y analytics
- [ ] Deploy en cloud

## Contacto

Desarrollado para prueba técnica de Selección - Desarrollador de Soluciones de IA y Automatización.

---

*Última actualización: Diciembre 2024*
