import os
import json
import pickle
from typing import List, Dict, Optional, Tuple
import numpy as np
from pathlib import Path
import logging

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

import config
from utils.document_processor import DocumentProcessor


class QAEngine:
    """Motor de preguntas y respuestas usando embeddings y LLM"""
    
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.qa_chain = None
        self.documents_processed = False
        
        # Rutas de cache
        self.vectorstore_path = config.EMBEDDINGS_DIR / "vectorstore"
        self.metadata_path = config.EMBEDDINGS_DIR / "metadata.json"
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Inicializa los componentes de OpenAI"""
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY no configurada")
        
        # Inicializar embeddings
        self.embeddings = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            openai_api_key=config.OPENAI_API_KEY
        )
        
        # Inicializar LLM
        self.llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS,
            openai_api_key=config.OPENAI_API_KEY
        )
        
        # Cargar vectorstore si existe
        self._load_vectorstore()
    
    def _load_vectorstore(self) -> bool:
        """
        Carga el vectorstore desde cache si existe
        
        Returns:
            bool: True si se cargó exitosamente
        """
        try:
            if self.vectorstore_path.exists() and self.metadata_path.exists():
                # Cargar vectorstore
                self.vectorstore = FAISS.load_local(
                    str(self.vectorstore_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                
                # Cargar metadata
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                self.documents_processed = True
                logging.info(f"Vectorstore cargado con {metadata.get('num_documents', 0)} documentos")
                
                # Crear cadena de QA
                self._create_qa_chain()
                return True
                
        except Exception as e:
            logging.error(f"Error cargando vectorstore: {str(e)}")
        
        return False
    
    def _save_vectorstore(self, num_docs: int):
        """
        Guarda el vectorstore en cache
        
        Args:
            num_docs: Número de documentos procesados
        """
        try:
            # Crear directorio si no existe
            config.EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
            
            # Guardar vectorstore
            self.vectorstore.save_local(str(self.vectorstore_path))
            
            # Guardar metadata
            metadata = {
                "num_documents": num_docs,
                "created_at": str(Path().cwd()),
                "model": config.EMBEDDING_MODEL
            }
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
            logging.info("Vectorstore guardado exitosamente")
            
        except Exception as e:
            logging.error(f"Error guardando vectorstore: {str(e)}")
    
    def process_documents(self, force_reload: bool = False) -> bool:
        """
        Procesa los documentos y crea embeddings
        
        Args:
            force_reload: Forzar reprocesamiento aunque ya exista cache
            
        Returns:
            bool: True si se procesaron exitosamente
        """
        if self.documents_processed and not force_reload:
            return True
        
        try:
            # Definir rutas de documentos
            document_paths = {
                "horarios": str(config.HORARIOS_FILE),
                "suma_gana": str(config.SUMA_GANA_FILE),
                "preguntas_frecuentes": str(config.PREGUNTAS_FILE)
            }
            
            # Procesar documentos
            logging.info("Procesando documentos...")
            processed_docs = DocumentProcessor.process_all_documents(document_paths)
            
            # Crear documentos para LangChain
            documents = []
            for doc_name, content in processed_docs.items():
                if content.strip():
                    # Dividir en chunks
                    chunks = DocumentProcessor.split_text_into_chunks(content)
                    
                    for i, chunk in enumerate(chunks):
                        doc = Document(
                            page_content=chunk,
                            metadata={
                                "source": doc_name,
                                "chunk_id": i,
                                "total_chunks": len(chunks)
                            }
                        )
                        documents.append(doc)
            
            if not documents:
                logging.error("No se pudieron procesar documentos")
                return False
            
            # Crear vectorstore
            logging.info(f"Creando embeddings para {len(documents)} chunks...")
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            
            # Guardar en cache
            self._save_vectorstore(len(documents))
            
            # Crear cadena de QA
            self._create_qa_chain()
            
            self.documents_processed = True
            logging.info("Documentos procesados exitosamente")
            return True
            
        except Exception as e:
            logging.error(f"Error procesando documentos: {str(e)}")
            return False
    
    def _create_qa_chain(self):
        """Crea la cadena de QA con el prompt personalizado"""
        if not self.vectorstore:
            return
        
        # Prompt personalizado
        prompt_template = """Eres un asistente virtual amigable de un supermercado. 
        Usa la siguiente información para responder la pregunta del cliente de manera natural y conversacional.

        Información disponible:
        {context}

        Pregunta del cliente: {question}

        Instrucciones:
        - Responde de manera amigable y natural
        - Si la información no está disponible, indica que no cuentas con esa información
        - Sugiere contactar al servicio al cliente si no puedes ayudar
        - Mantén un tono profesional pero cercano

        Respuesta:"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Crear retriever
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # Top 3 documentos más similares
        )
        
        # Crear cadena de QA
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
    
    def ask_question(self, question: str) -> Tuple[str, List[str]]:
        """
        Responde una pregunta usando el motor de QA
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            Tuple[str, List[str]]: (respuesta, fuentes_utilizadas)
        """
        if not self.qa_chain:
            if not self.process_documents():
                return "Lo siento, no puedo procesar tu consulta en este momento. Por favor contacta al servicio al cliente.", []
        
        try:
            # Hacer la consulta
            result = self.qa_chain({"query": question})
            
            # Extraer respuesta
            answer = result["result"]
            
            # Extraer fuentes
            sources = []
            if "source_documents" in result:
                for doc in result["source_documents"]:
                    source = doc.metadata.get("source", "documento")
                    if source not in sources:
                        sources.append(source)
            
            return answer, sources
            
        except Exception as e:
            logging.error(f"Error procesando pregunta: {str(e)}")
            return "Lo siento, hubo un error procesando tu consulta. Por favor intenta de nuevo o contacta al servicio al cliente.", []
    
    def get_similar_questions(self, question: str, k: int = 3) -> List[Dict]:
        """
        Obtiene preguntas similares del vectorstore
        
        Args:
            question: Pregunta de referencia
            k: Número de resultados similares
            
        Returns:
            Lista de documentos similares con metadata
        """
        if not self.vectorstore:
            return []
        
        try:
            docs = self.vectorstore.similarity_search(question, k=k)
            
            similar = []
            for doc in docs:
                similar.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "chunk_id": doc.metadata.get("chunk_id", 0)
                })
            
            return similar
            
        except Exception as e:
            logging.error(f"Error buscando preguntas similares: {str(e)}")
            return []
    
    def reset_vectorstore(self):
        """Elimina el cache y fuerza reprocesamiento"""
        try:
            if self.vectorstore_path.exists():
                import shutil
                shutil.rmtree(self.vectorstore_path)
            
            if self.metadata_path.exists():
                self.metadata_path.unlink()
            
            self.vectorstore = None
            self.qa_chain = None
            self.documents_processed = False
            
            logging.info("Cache de vectorstore eliminado")
            
        except Exception as e:
            logging.error(f"Error eliminando cache: {str(e)}")
