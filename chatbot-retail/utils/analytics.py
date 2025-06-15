import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import config
from collections import Counter
import re

class AnalyticsManager:
    """Manejo de analytics y estadísticas del chatbot"""
    
    def __init__(self):
        self.db_path = config.DATABASE_PATH
    
    def get_conversation_stats(self, days=30):
        """Obtiene estadísticas de conversaciones"""
        with sqlite3.connect(self.db_path) as conn:
            # Conversaciones por día
            query_daily = """
                SELECT DATE(timestamp) as fecha, COUNT(*) as total_conversaciones
                FROM conversaciones 
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY DATE(timestamp)
                ORDER BY fecha
            """.format(days)
            
            df_daily = pd.read_sql_query(query_daily, conn)
            
            # Tipos de consulta más frecuentes
            query_types = """
                SELECT tipo_consulta, COUNT(*) as total
                FROM conversaciones 
                WHERE timestamp >= datetime('now', '-{} days')
                AND tipo_consulta IS NOT NULL
                GROUP BY tipo_consulta
                ORDER BY total DESC
            """.format(days)
            
            df_types = pd.read_sql_query(query_types, conn)
            
            # Usuarios más activos
            query_users = """
                SELECT u.nombre_completo, COUNT(c.id) as total_mensajes
                FROM usuarios u
                JOIN conversaciones c ON u.id = c.usuario_id
                WHERE c.timestamp >= datetime('now', '-{} days')
                GROUP BY u.id, u.nombre_completo
                ORDER BY total_mensajes DESC
                LIMIT 10
            """.format(days)
            
            df_users = pd.read_sql_query(query_users, conn)
            
            return df_daily, df_types, df_users
    
    def get_word_frequency(self, days=30, limit=20):
        """Analiza frecuencia de palabras en mensajes de usuarios"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT mensaje_usuario
                FROM conversaciones 
                WHERE timestamp >= datetime('now', '-{} days')
            """.format(days)
            
            df = pd.read_sql_query(query, conn)
            
            # Procesar texto
            all_text = ' '.join(df['mensaje_usuario'].astype(str))
            
            # Limpiar y tokenizar
            words = re.findall(r'\b[a-záéíóúñü]{3,}\b', all_text.lower())
            
            # Filtrar palabras comunes
            stop_words = {'que', 'para', 'con', 'una', 'por', 'del', 'las', 'los', 
                         'está', 'son', 'como', 'más', 'pero', 'sus', 'sus', 'uno',
                         'sobre', 'todo', 'también', 'después', 'hasta', 'otro',
                         'cuando', 'muy', 'sin', 'entre', 'ser', 'hay', 'donde',
                         'hola', 'gracias', 'buenos', 'días', 'buenas', 'tardes'}
            
            filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
            
            # Contar frecuencias
            word_freq = Counter(filtered_words).most_common(limit)
            
            return pd.DataFrame(word_freq, columns=['palabra', 'frecuencia'])
    
    def get_hourly_distribution(self, days=30):
        """Obtiene distribución de conversaciones por hora"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT 
                    CAST(strftime('%H', timestamp) AS INTEGER) as hora,
                    COUNT(*) as total_conversaciones
                FROM conversaciones 
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY hora
                ORDER BY hora
            """.format(days)
            
            return pd.read_sql_query(query, conn)
    
    def get_user_engagement_metrics(self):
        """Obtiene métricas de engagement de usuarios"""
        with sqlite3.connect(self.db_path) as conn:
            # Usuarios registrados vs anónimos
            query_registration = """
                SELECT 
                    CASE 
                        WHEN usuario_id IS NULL THEN 'Anónimo'
                        ELSE 'Registrado'
                    END as tipo_usuario,
                    COUNT(*) as total_conversaciones
                FROM conversaciones
                GROUP BY tipo_usuario
            """
            
            df_registration = pd.read_sql_query(query_registration, conn)
            
            # Promedio de mensajes por usuario
            query_avg = """
                SELECT AVG(mensajes_por_usuario) as promedio_mensajes
                FROM (
                    SELECT COUNT(*) as mensajes_por_usuario
                    FROM conversaciones
                    WHERE usuario_id IS NOT NULL
                    GROUP BY usuario_id
                )
            """
            
            avg_result = pd.read_sql_query(query_avg, conn)
            avg_messages = avg_result['promedio_mensajes'].iloc[0] if not avg_result.empty else 0
            # Asegurar que avg_messages no sea None
            avg_messages = avg_messages if avg_messages is not None else 0
            
            return df_registration, avg_messages
    
    def render_analytics_dashboard(self):
        """Renderiza el dashboard completo de analytics"""
        st.markdown("# 📊 Analytics Dashboard")
        st.markdown("---")
        
        # Período fijo de análisis (30 días)
        days_filter = 30
        
        # Sidebar para información
        with st.sidebar:
            st.markdown("### 📈 Métricas Generales (Últimos 30 días)")
            
            # Métricas rápidas
            with sqlite3.connect(self.db_path) as conn:
                # Total conversaciones
                total_conv = pd.read_sql_query(
                    f"SELECT COUNT(*) as total FROM conversaciones WHERE timestamp >= datetime('now', '-{days_filter} days')",
                    conn
                )['total'].iloc[0]
                
                # Total usuarios únicos
                total_users = pd.read_sql_query(
                    f"SELECT COUNT(DISTINCT usuario_id) as total FROM conversaciones WHERE timestamp >= datetime('now', '-{days_filter} days') AND usuario_id IS NOT NULL",
                    conn
                )['total'].iloc[0]
                
                # Promedio diario
                avg_daily = total_conv / days_filter if days_filter > 0 else 0
            
            st.metric("Conversaciones", total_conv)
            st.metric("Usuarios Únicos", total_users)
            st.metric("Promedio Diario", f"{avg_daily:.1f}")
        
        # Tabs principales
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Tendencias", "💬 Conversaciones", "👥 Usuarios", "🔍 Palabras Clave", "🔧 Debug"])
        
        with tab1:
            self._render_trends_tab(days_filter)
        
        with tab2:
            self._render_conversations_tab(days_filter)
        
        with tab3:
            self._render_users_tab(days_filter)
        
        with tab4:
            self._render_words_tab(days_filter)
            
        with tab5:
            self.show_debug_info()
    
    def _render_trends_tab(self, days):
        """Renderiza la pestaña de tendencias"""
        st.markdown("## 📈 Tendencias de Uso")
        
        # Obtener datos
        df_daily, df_types, df_users = self.get_conversation_stats(days)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de conversaciones por día
            if not df_daily.empty:
                fig_daily = px.line(
                    df_daily, 
                    x='fecha', 
                    y='total_conversaciones',
                    title='Conversaciones por Día',
                    markers=True
                )
                fig_daily.update_layout(
                    xaxis_title="Fecha",
                    yaxis_title="Número de Conversaciones"
                )
                st.plotly_chart(fig_daily, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar tendencias diarias")
        
        with col2:
            # Distribución por horas
            df_hourly = self.get_hourly_distribution(days)
            if not df_hourly.empty:
                fig_hourly = px.bar(
                    df_hourly,
                    x='hora',
                    y='total_conversaciones',
                    title='Distribución de Conversaciones por Hora'
                )
                fig_hourly.update_layout(
                    xaxis_title="Hora del Día",
                    yaxis_title="Número de Conversaciones"
                )
                st.plotly_chart(fig_hourly, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar distribución horaria")
    
    def _render_conversations_tab(self, days):
        """Renderiza la pestaña de análisis de conversaciones"""
        st.markdown("## 💬 Análisis de Conversaciones")
        
        df_daily, df_types, df_users = self.get_conversation_stats(days)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Tipos de consulta
            if not df_types.empty:
                fig_types = px.pie(
                    df_types,
                    values='total',
                    names='tipo_consulta',
                    title='Distribución de Tipos de Consulta'
                )
                st.plotly_chart(fig_types, use_container_width=True)
            else:
                st.info("No hay datos de tipos de consulta")
        
        with col2:
            # Engagement metrics
            df_registration, avg_messages = self.get_user_engagement_metrics()
            if not df_registration.empty:
                fig_engagement = px.bar(
                    df_registration,
                    x='tipo_usuario',
                    y='total_conversaciones',
                    title='Usuarios Registrados vs Anónimos',
                    color='tipo_usuario'
                )
                st.plotly_chart(fig_engagement, use_container_width=True)
                
                st.metric(
                    "Promedio mensajes por usuario registrado",
                    f"{avg_messages:.1f}"
                )
            else:
                st.info("No hay datos de engagement")
    
    def _render_users_tab(self, days):
        """Renderiza la pestaña de análisis de usuarios"""
        st.markdown("## 👥 Análisis de Usuarios")
        
        df_daily, df_types, df_users = self.get_conversation_stats(days)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Top usuarios más activos
            if not df_users.empty:
                fig_users = px.bar(
                    df_users.head(10),
                    x='total_mensajes',
                    y='nombre_completo',
                    orientation='h',
                    title='Top 10 Usuarios Más Activos'
                )
                fig_users.update_layout(
                    xaxis_title="Número de Mensajes",
                    yaxis_title="Usuario"
                )
                st.plotly_chart(fig_users, use_container_width=True)
            else:
                st.info("No hay datos de usuarios registrados")
        
        with col2:
            # Tabla de usuarios
            if not df_users.empty:
                st.markdown("### 📋 Detalle de Usuarios")
                st.dataframe(
                    df_users,
                    column_config={
                        "nombre_completo": "Usuario",
                        "total_mensajes": "Mensajes"
                    },
                    hide_index=True
                )
    
    def _render_words_tab(self, days):
        """Renderiza la pestaña de análisis de palabras"""
        st.markdown("## 🔍 Análisis de Palabras Clave")
        
        df_words = self.get_word_frequency(days, limit=30)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if not df_words.empty:
                # Word cloud style bar chart
                fig_words = px.bar(
                    df_words.head(20),
                    x='frecuencia',
                    y='palabra',
                    orientation='h',
                    title='Top 20 Palabras Más Frecuentes',
                    color='frecuencia',
                    color_continuous_scale='viridis'
                )
                fig_words.update_layout(
                    xaxis_title="Frecuencia",
                    yaxis_title="Palabra",
                    yaxis={'categoryorder': 'total ascending'}
                )
                st.plotly_chart(fig_words, use_container_width=True)
            else:
                st.info("No hay suficientes datos de conversaciones para analizar palabras")
        
        with col2:
            if not df_words.empty:
                st.markdown("### 📝 Tabla de Frecuencias")
                st.dataframe(
                    df_words.head(15),
                    column_config={
                        "palabra": "Palabra",
                        "frecuencia": "Frecuencia"
                    },
                    hide_index=True
                )
                
                # Insights automáticos
                st.markdown("### 💡 Insights")
                top_word = df_words.iloc[0]['palabra']
                top_freq = df_words.iloc[0]['frecuencia']
                
                st.write(f"• La palabra más frecuente es **'{top_word}'** ({top_freq} veces)")
                st.write(f"• Se analizaron {len(df_words)} palabras únicas")
                
                # Categorías automáticas
                product_words = ['producto', 'precio', 'oferta', 'descuento', 'promoción']
                service_words = ['horario', 'atención', 'servicio', 'ayuda', 'soporte']
                
                products_found = df_words[df_words['palabra'].isin(product_words)]
                services_found = df_words[df_words['palabra'].isin(service_words)]
                
                if not products_found.empty:
                    st.write("🛒 **Consultas sobre productos detectadas**")
                
                if not services_found.empty:
                    st.write("🛠️ **Consultas sobre servicios detectadas**")
    
    def show_debug_info(self):
        """Muestra información de debug sobre el estado de la base de datos"""
        st.subheader("🔍 Información de Debug")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total de usuarios
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            total_usuarios = cursor.fetchone()[0]
            
            # Total de conversaciones
            cursor.execute("SELECT COUNT(*) FROM conversaciones")
            total_conversaciones = cursor.fetchone()[0]
            
            # Conversaciones con usuario vs anónimas
            cursor.execute("""
                SELECT 
                    CASE WHEN usuario_id IS NULL THEN 'Anónimo' ELSE 'Registrado' END as tipo,
                    COUNT(*) as total
                FROM conversaciones 
                GROUP BY tipo
            """)
            conv_por_tipo = dict(cursor.fetchall())
            
            # Últimas conversaciones
            cursor.execute("""
                SELECT c.mensaje_usuario, c.timestamp, u.nombre_completo, c.usuario_id
                FROM conversaciones c
                LEFT JOIN usuarios u ON c.usuario_id = u.id
                ORDER BY c.timestamp DESC
                LIMIT 10
            """)
            ultimas_conversaciones = cursor.fetchall()
            
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Total Usuarios", total_usuarios)
        
        with col2:
            st.metric("💬 Total Conversaciones", total_conversaciones)
            
        with col3:
            anon = conv_por_tipo.get('Anónimo', 0)
            reg = conv_por_tipo.get('Registrado', 0)
            st.metric("📊 Registrados vs Anónimos", f"{reg}/{anon}")
        
        if ultimas_conversaciones:
            st.subheader("📝 Últimas 10 Conversaciones")
            conv_data = []
            for conv in ultimas_conversaciones:
                mensaje, timestamp, nombre, user_id = conv
                usuario = nombre if nombre else f"Anónimo (ID:{user_id})" if user_id else "Anónimo"
                conv_data.append({
                    "Timestamp": timestamp,
                    "Usuario": usuario,
                    "Mensaje": mensaje[:100] + "..." if len(mensaje) > 100 else mensaje
                })
            
            st.dataframe(pd.DataFrame(conv_data), use_container_width=True)
        else:
            st.info("No hay conversaciones registradas aún.")
            st.markdown("""
            **💡 Sugerencia:** Prueba hacer algunas preguntas al chatbot para ver cómo se registran las conversaciones:
            - Haz una pregunta como usuario anónimo
            - Regístrate como usuario y haz otra pregunta
            - Revisa aquí para ver cómo se almacenan los datos
            """)
