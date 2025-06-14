"""
Script para procesar los documentos y verificar la extracción de texto
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DOCUMENTS_DIR, HORARIOS_FILE, SUMA_GANA_FILE, PREGUNTAS_FILE
from utils.document_processor import DocumentProcessor
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Procesa todos los documentos y muestra el contenido extraído"""
    
    # Verificar que los archivos existen
    documents = {
        "horarios": str(HORARIOS_FILE),
        "suma_gana": str(SUMA_GANA_FILE), 
        "preguntas_frecuentes": str(PREGUNTAS_FILE)
    }
    
    print("🔍 Verificando archivos de documentos...")
    for name, path in documents.items():
        if os.path.exists(path):
            print(f"✅ {name}: {path}")
        else:
            print(f"❌ {name}: {path} - NO ENCONTRADO")
    
    print("\n📄 Procesando documentos...")
    
    # Procesar cada documento
    processor = DocumentProcessor()
    processed_docs = processor.process_all_documents(documents)
    
    for doc_name, content in processed_docs.items():
        print(f"\n{'='*60}")
        print(f"DOCUMENTO: {doc_name.upper()}")
        print(f"{'='*60}")
        
        if content:
            # Mostrar los primeros 500 caracteres
            preview = content[:500]
            print(f"Contenido (primeros 500 chars):\n{preview}")
            if len(content) > 500:
                print(f"\n... (total: {len(content)} caracteres)")
            
            # Dividir en chunks para verificar
            chunks = processor.split_text_into_chunks(content, chunk_size=800, overlap=100)
            print(f"\n📊 Chunks generados: {len(chunks)}")
            
        else:
            print("❌ No se pudo extraer contenido")

if __name__ == "__main__":
    main()
