import os
import json
import pickle
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

import config
from utils.document_processor import DocumentProcessor


class QAEngine:
    """Motor de QA mejorado para respuestas precisas del chatbot"""
    
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.qa_chain = None
        self.documents_processed = False
        self.conversation_history = []
        
        # Rutas de cache
        self.vectorstore_path = config.EMBEDDINGS_DIR / "vectorstore"
        self.metadata_path = config.EMBEDDINGS_DIR / "metadata.json"
        
        # Configuración optimizada
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.retrieval_k = 4
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Inicializa los componentes de OpenAI de forma segura"""
        try:
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY no configurada")
            
            # Inicializar embeddings
            self.embeddings = OpenAIEmbeddings(
                model=config.EMBEDDING_MODEL,
                openai_api_key=config.OPENAI_API_KEY
            )
            
            # Inicializar LLM con configuración mejorada
            self.llm = ChatOpenAI(
                model=config.OPENAI_MODEL,
                temperature=0.2,  # Más preciso
                max_tokens=1200,  # Respuestas más completas
                openai_api_key=config.OPENAI_API_KEY
            )
            
            # Cargar vectorstore si existe
            self._load_vectorstore()
            
        except Exception as e:
            logging.error(f"Error inicializando componentes: {str(e)}")
    
    def _create_optimized_text_splitter(self):
        """Crea un text splitter optimizado"""
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ";", ":", " ", ""]
        )
    
    def _enhance_document_metadata(self, doc: Document, source: str, chunk_id: int) -> Document:
        """Agrega metadata mejorada y más específica a los documentos"""
        content = doc.page_content.lower()
        
        # Detectar tipo de contenido con mayor precisión
        content_type = "general"
        keywords = []
        specificity_score = 0
        
        # Horarios - detectar patrones específicos
        if any(word in content for word in ["horario", "hora", "abierto", "cerrado"]):
            content_type = "horarios"
            keywords.extend(["horarios", "tiempo", "apertura", "cierre"])
            # Bonus si tiene días específicos o horas específicas
            if any(day in content for day in ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]):
                specificity_score += 0.3
            if any(hour in content for hour in ["am", "pm", ":"]):
                specificity_score += 0.2
                
        # Promociones - detectar específicamente Suma y Gana
        elif any(word in content for word in ["suma", "gana", "puntos", "promoción", "descuento"]):
            content_type = "promociones"
            keywords.extend(["ofertas", "descuentos", "promociones", "puntos", "suma_gana"])
            if "suma" in content and "gana" in content:
                specificity_score += 0.4
            if "punto" in content:
                specificity_score += 0.2
                
        # Preguntas frecuentes
        elif any(word in content for word in ["pregunta", "respuesta", "cómo", "qué", "consulta"]):
            content_type = "preguntas_frecuentes"
            keywords.extend(["ayuda", "información", "consultas", "servicios"])
            if "?" in content:
                specificity_score += 0.2
        
        doc.metadata.update({
            "source": source,
            "chunk_id": chunk_id,
            "content_type": content_type,
            "keywords": keywords,
            "length": len(doc.page_content),
            "specificity_score": specificity_score
        })
        
        return doc
    
    def process_documents(self, force_reload: bool = False) -> bool:
        """Procesa los documentos con mejoras pero de forma estable"""
        if self.documents_processed and not force_reload:
            return True
        
        try:
            # Definir rutas de documentos
            document_paths = {
                "horarios": str(config.HORARIOS_FILE),
                "suma_gana": str(config.SUMA_GANA_FILE),
                "preguntas_frecuentes": str(config.PREGUNTAS_FILE)
            }
            
            # Procesar documentos con el procesador estándar
            logging.info("Procesando documentos...")
            processed_docs = DocumentProcessor.process_all_documents(document_paths)
            
            # Crear text splitter
            text_splitter = self._create_optimized_text_splitter()
            
            # Crear documentos para LangChain
            documents = []
            for doc_name, content in processed_docs.items():
                if content.strip():
                    # Dividir en chunks
                    chunks = text_splitter.split_text(content)
                    
                    for i, chunk in enumerate(chunks):
                        doc = Document(
                            page_content=chunk,
                            metadata={}
                        )
                        # Enriquecer metadata
                        doc = self._enhance_document_metadata(doc, doc_name, i)
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
        """Crea la cadena de QA con prompts mejorados"""
        if not self.vectorstore:
            return
        
        # Prompt mejorado y específico
        prompt_template = """Eres un asistente virtual del supermercado. Tu función es INFORMAR y RESPONDER PREGUNTAS basándote en la información de los documentos del supermercado.

INFORMACIÓN DISPONIBLE:
{context}

PREGUNTA DEL CLIENTE: {question}

INSTRUCCIONES IMPORTANTES:
- Proporciona información ESPECÍFICA y DETALLADA cuando esté disponible en los documentos
- Si hay horarios específicos, menciónalos exactamente como aparecen
- Si hay promociones específicas del programa "Suma y Gana", menciona claramente que pertenecen a ese programa
- Tu función es INFORMAR sobre servicios, NO realizarlos directamente
- Usa frases como "puedes", "está disponible", "la información indica" en lugar de "te ayudo con"
- Responde SOLO lo que se pregunta, no agregues información de otros temas
- Si preguntan sobre horarios, NO menciones promociones
- Si preguntan sobre promociones, NO menciones horarios
- Sé específico con datos como horarios, precios, porcentajes, condiciones
- Mantén un tono amigable pero enfócate en dar información precisa

RESPUESTA:"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Crear retriever optimizado con filtros
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.retrieval_k}
        )
        
        # Crear cadena de QA
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
    
    def ask_question(self, question: str, user_context: Dict = None) -> Tuple[str, List[str], Dict]:
        """
        Responde una pregunta de forma mejorada pero estable
        """
        if not self.qa_chain:
            if not self.process_documents():
                return "Lo siento, no puedo procesar tu consulta en este momento. Por favor contacta al servicio al cliente.", [], {}
        
        try:
            # Enriquecer la pregunta con contexto de conversación
            enriched_question = self._add_conversation_context(question)
            
            # Hacer la consulta
            result = self.qa_chain({"query": enriched_question})
            
            # Extraer respuesta
            answer = result["result"]
            
            # Calcular score de calidad básico
            quality_score = self._calculate_quality_score(result, question)
            
            # Extraer fuentes de manera más precisa y relevante
            sources = []
            question_lower = question.lower()
            
            if "source_documents" in result:
                source_relevance = {}
                
                for doc in result["source_documents"]:
                    source = doc.metadata.get("source", "documento")
                    content = doc.page_content.lower()
                    content_type = doc.metadata.get("content_type", "general")
                    
                    # Determinar relevancia específica según el tipo de pregunta
                    relevance = 0
                    
                    # Preguntas sobre horarios
                    if any(word in question_lower for word in ["horario", "hora", "abierto", "cerrado", "cuándo"]):
                        if source == "horarios" or content_type == "horarios":
                            relevance = 1.0
                        elif any(word in content for word in ["horario", "hora", "abierto", "cerrado"]):
                            relevance = 0.5
                    
                    # Preguntas sobre promociones/Suma y Gana
                    elif any(word in question_lower for word in ["promoción", "descuento", "oferta", "suma", "gana", "puntos"]):
                        if source == "suma_gana" or content_type == "promociones":
                            relevance = 1.0
                        elif any(word in content for word in ["promoción", "descuento", "suma", "gana", "puntos"]):
                            relevance = 0.5
                    
                    # Preguntas generales o de ayuda
                    elif any(word in question_lower for word in ["ayuda", "pueden", "puedo", "qué", "cómo"]):
                        if source == "preguntas_frecuentes" or content_type == "preguntas_frecuentes":
                            relevance = 1.0
                        else:
                            relevance = 0.3
                    
                    # Si el documento tiene contenido relevante a la pregunta específica
                    else:
                        question_words = set(question_lower.split())
                        content_words = set(content.split())
                        word_overlap = len(question_words.intersection(content_words))
                        if word_overlap > 0:
                            relevance = min(word_overlap / len(question_words), 1.0)
                    
                    # Solo incluir fuentes con relevancia significativa
                    if relevance > 0.3:
                        source_relevance[source] = max(source_relevance.get(source, 0), relevance)
                
                # Ordenar por relevancia y tomar máximo 2 fuentes más relevantes
                sources = sorted(source_relevance.keys(), key=lambda x: source_relevance[x], reverse=True)[:2]
            
            # Guardar en historial
            self.conversation_history.append({
                "question": question,
                "answer": answer,
                "sources": sources
            })
            
            # Metadata
            metadata = {
                "quality_score": quality_score,
                "sources_used": len(sources),
                "response_length": len(answer)
            }
            
            return answer, sources, metadata
            
        except Exception as e:
            logging.error(f"Error procesando pregunta: {str(e)}")
            return "Lo siento, hubo un error procesando tu consulta. Por favor intenta de nuevo.", [], {"quality_score": 0.0, "sources_used": 0}
    
    def _add_conversation_context(self, question: str) -> str:
        """Agrega contexto de conversación SOLO si es relevante y relacionado"""
        # No usar contexto conversacional para evitar interferencias
        # Cada pregunta debe ser tratada de forma independiente para mayor precisión
        return question
    
    def _calculate_quality_score(self, result: Dict, original_question: str) -> float:
        """Calcula un score de calidad básico"""
        score = 0.0
        
        # Score basado en fuentes
        if "source_documents" in result and result["source_documents"]:
            score += 0.4
            if len(result["source_documents"]) > 1:
                score += 0.2
        
        # Score basado en longitud de respuesta
        answer_length = len(result["result"])
        if 50 < answer_length < 800:
            score += 0.3
        
        # Score basado en palabras clave relevantes
        answer_lower = result["result"].lower()
        question_lower = original_question.lower()
        
        relevant_words = ["horario", "promoción", "descuento", "oferta", "supermercado", "cliente"]
        for word in relevant_words:
            if word in question_lower and word in answer_lower:
                score += 0.05
        
        return min(score, 1.0)
    
    def get_context_aware_suggestions(self, question: str) -> List[str]:
        """Genera sugerencias contextuales específicas sobre información disponible"""
        suggestions = []
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["horario", "hora", "abierto"]):
            suggestions.extend([
                "¿Necesitas información sobre horarios de días específicos?",
                "¿Te interesa conocer horarios de sucursales particulares?"
            ])
        elif any(word in question_lower for word in ["promoción", "descuento", "oferta"]):
            suggestions.extend([
                "¿Quieres conocer más detalles del programa Suma y Gana?",
                "¿Te interesa información sobre cómo redimir puntos?"
            ])
        elif any(word in question_lower for word in ["ayuda", "ayudar", "servicio"]):
            suggestions.extend([
                "Puedo informarte sobre horarios de atención",
                "Puedo darte información sobre el programa Suma y Gana"
            ])
        else:
            suggestions.extend([
                "¿Necesitas información sobre horarios de atención?",
                "¿Te interesa conocer sobre nuestras promociones?"
            ])
        
        return suggestions[:2]
    
    def _load_vectorstore(self) -> bool:
        """Carga el vectorstore desde cache"""
        try:
            if self.vectorstore_path.exists() and self.metadata_path.exists():
                self.vectorstore = FAISS.load_local(
                    str(self.vectorstore_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                self.documents_processed = True
                logging.info(f"Vectorstore cargado con {metadata.get('num_documents', 0)} documentos")
                
                self._create_qa_chain()
                return True
                
        except Exception as e:
            logging.error(f"Error cargando vectorstore: {str(e)}")
        
        return False
    
    def _save_vectorstore(self, num_docs: int):
        """Guarda el vectorstore en cache"""
        try:
            config.EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
            
            self.vectorstore.save_local(str(self.vectorstore_path))
            
            metadata = {
                "num_documents": num_docs,
                "created_at": datetime.now().isoformat(),
                "model": config.EMBEDDING_MODEL,
                "version": "qa_engine_v2.0_stable"
            }
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
            logging.info("Vectorstore guardado exitosamente")
            
        except Exception as e:
            logging.error(f"Error guardando vectorstore: {str(e)}")
    
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
