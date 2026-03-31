"""
Aplicación principal de Streamlit para Detector de Uso de Música con IA.
Proporciona la interfaz de usuario para buscar y analizar el uso de canciones.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict
import time
import logging
import html

from youtube_search import YouTubeSearcher, format_youtube_results
from web_search import WebSearcher, format_web_results
from ai_analysis import AIAnalyzer, format_classification_display
from config import config
from pdf_generator import get_pdf_download_link
from login import show_login, logout
from song_metadata import get_song_metadata, SongCandidate
from quick_search import search_links

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Detector de Uso de Música con IA",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para diseño profesional
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        text-align: center;
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    .result-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e5e7eb;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .result-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    }
    
    .category-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-right: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .possible-song-usage { 
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(238, 90, 111, 0.3);
    }
    
    .cover { 
        background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(68, 160, 141, 0.3);
    }
    
    .promotional-usage { 
        background: linear-gradient(135deg, #45b7d1 0%, #96c93d 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(150, 201, 61, 0.3);
    }
    
    .reference-only { 
        background: linear-gradient(135deg, #96ceb4 0%, #ffecd2 100%);
        color: #374151;
        box-shadow: 0 2px 4px rgba(150, 206, 180, 0.3);
    }
    
    .confidence-score {
        font-size: 0.875rem;
        color: #6b7280;
        font-weight: 500;
        background: #f3f4f6;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
    }
    
    .summary-metric {
        text-align: center;
        padding: 1.5rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .summary-metric:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    .search-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .search-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
    }
    
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .section-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .insight-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
        border-left: 4px solid #60a5fa;
        padding: 1rem;
        border-radius: 0 12px 12px 0;
        margin-bottom: 0.75rem;
        color: #ffffff;
        font-weight: 500;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .video-meta, .web-meta {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #6b7280;
        font-size: 0.875rem;
        margin-top: 0.5rem;
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .ai-reasoning {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #8b5cf6;
        margin-top: 1rem;
        font-style: italic;
        color: #4b5563;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Inicializar variables de estado de la sesión de Streamlit."""
    # Estado del flujo dual (nuevas variables)
    if 'mode' not in st.session_state:
        st.session_state.mode = 'idle'
    if 'song_candidates' not in st.session_state:
        st.session_state.song_candidates = []
    if 'quick_links' not in st.session_state:
        st.session_state.quick_links = []
    if 'selected_candidate_idx' not in st.session_state:
        st.session_state.selected_candidate_idx = 0
    if 'user_query' not in st.session_state:
        st.session_state.user_query = ''
    # Estado existente (sin cambios)
    if 'search_results' not in st.session_state:
        st.session_state.search_results = {
            'youtube': [],
            'web': [],
            'summary': None
        }
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False
    if 'loading' not in st.session_state:
        st.session_state.loading = False

def display_header():
    """Mostrar el encabezado de la aplicación."""
    st.markdown('<h1 class="main-header">🎵 Detector de Uso de Música con IA</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Descubre cómo se están usando las canciones en internet con análisis impulsado por inteligencia artificial</p>', unsafe_allow_html=True)
    st.markdown("---")

def display_search_form():
    """Mostrar el formulario de búsqueda con campo único."""
    st.markdown("### 🔍 Busca una canción")

    with st.form("search_form"):
        user_query = st.text_input(
            "🎵 Nombre de la canción",
            placeholder="Ej: Despacito, La Bamba, Bohemian Rhapsody...",
            help="Ingresa el nombre de la canción. Identificaremos el artista automáticamente.",
        )
        submitted = st.form_submit_button(
            "🔍 Buscar",
            type="primary",
            use_container_width=True,
        )
        return submitted, user_query

def run_quick_search(user_query: str):
    """Ejecutar búsqueda rápida: identifica canción y obtiene links sin clasificación IA."""
    with st.spinner("🔍 Identificando canción y obteniendo links..."):
        try:
            candidates = get_song_metadata(user_query)
        except Exception as e:
            st.error("❌ No pudimos identificar la canción. Intenta con un nombre más específico.")
            logger.error(f"Error identificando canción '{user_query}': {e}")
            return

        quick_links = []
        youtube_failed_any = False
        web_failed_any = False
        for candidate in candidates:
            links_data = search_links(candidate.song_name, candidate.artist_name)
            quick_links.append(links_data)
            if links_data.get("youtube_failed"):
                youtube_failed_any = True
            if links_data.get("web_failed"):
                web_failed_any = True

        if youtube_failed_any:
            st.warning("⚠️ No se pudieron cargar los videos de YouTube.")
        if web_failed_any:
            st.warning("⚠️ No se pudieron cargar los resultados web.")

        st.session_state.song_candidates = candidates
        st.session_state.quick_links = quick_links
        st.session_state.mode = 'quick_results'
        st.session_state.search_performed = False
        logger.info(
            f"Búsqueda rápida completada: '{user_query}' → {len(candidates)} candidato(s)"
        )

def display_quick_results():
    """Mostrar tarjetas de candidatos con links y botón de análisis profundo."""
    candidates = st.session_state.song_candidates
    quick_links = st.session_state.quick_links

    if not candidates:
        st.warning("⚠️ No se encontraron canciones para tu búsqueda.")
        return

    st.markdown("---")
    st.markdown("### 🎵 Canciones encontradas")

    cols = st.columns(len(candidates))
    for i, candidate in enumerate(candidates):
        with cols[i]:
            st.markdown(f"#### 🎵 {html.escape(candidate.song_name)}")
            st.markdown(f"👤 **{html.escape(candidate.artist_name)}**")
            if candidate.album:
                st.markdown(f"💿 _{html.escape(candidate.album)}_")
            st.markdown("---")

            links_data = quick_links[i] if i < len(quick_links) else {"links": []}
            yt_links = [l for l in links_data["links"] if l["type"] == "YouTube"]
            web_links = [l for l in links_data["links"] if l["type"] == "Web"]

            if yt_links:
                st.markdown("**📺 Videos de YouTube**")
                for link in yt_links[:10]:
                    safe_url = (
                        link["url"]
                        if link["url"].startswith(("https://", "http://"))
                        else "#"
                    )
                    safe_title = html.escape(str(link["title"]))
                    st.markdown(f"- [{safe_title}]({safe_url})")
            else:
                st.caption("Sin resultados de YouTube.")

            if web_links:
                st.markdown("**🌐 Resultados Web**")
                for link in web_links[:10]:
                    safe_url = (
                        link["url"]
                        if link["url"].startswith(("https://", "http://"))
                        else "#"
                    )
                    safe_title = html.escape(str(link["title"]))
                    st.markdown(f"- [{safe_title}]({safe_url})")
            else:
                st.caption("Sin resultados web.")

            st.markdown("---")

            already_analyzed = (
                st.session_state.mode == 'deep_analysis'
                and st.session_state.selected_candidate_idx == i
            )
            if already_analyzed:
                st.success("✅ Análisis profundo ejecutado")
            else:
                if st.button(
                    "🔬 Ejecutar Análisis Profundo",
                    key=f"deep_btn_{i}",
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state.selected_candidate_idx = i
                    st.session_state.mode = 'deep_analysis'
                    with st.spinner("🤖 Ejecutando análisis profundo..."):
                        success = perform_search(candidate.song_name, candidate.artist_name)
                        if success:
                            st.session_state.search_performed = True
                    st.rerun()

def perform_search(song_name: str, artist_name: str):
    """Realizar la búsqueda en YouTube y la web."""
    try:
        # Inicializar buscadores
        youtube_searcher = YouTubeSearcher()
        web_searcher = WebSearcher()
        ai_analyzer = AIAnalyzer()
        
        # Seguimiento de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Buscar en YouTube
        status_text.text("🔍 Buscando en YouTube (múltiples consultas)...")
        progress_bar.progress(20)
        youtube_results = youtube_searcher.search_videos(song_name, artist_name, max_results=100)
        formatted_youtube = format_youtube_results(youtube_results)
        
        # Buscar en la web
        status_text.text(f"🌐 Buscando en la web... ({len(formatted_youtube)} resultados de YouTube encontrados)")
        progress_bar.progress(40)
        web_results = web_searcher.search_web(song_name, artist_name, max_results=60)
        formatted_web = format_web_results(web_results)
        
        # Análisis con IA
        status_text.text("🤖 Analizando resultados con inteligencia artificial...")
        progress_bar.progress(60)
        
        # Analizar resultados de YouTube
        classified_youtube = ai_analyzer.analyze_batch(formatted_youtube, song_name, artist_name)
        progress_bar.progress(75)
        
        # Analizar resultados de la web
        classified_web = ai_analyzer.analyze_batch(formatted_web, song_name, artist_name)
        progress_bar.progress(85)
        
        # Generar resumen
        all_results = classified_youtube + classified_web
        summary = ai_analyzer.generate_summary_report(all_results, song_name, artist_name)
        
        # Clasificar riesgo para cada resultado
        status_text.text("⚠️ Evaluando niveles de riesgo...")
        for result in all_results:
            result['risk_level'] = ai_analyzer.classify_usage_risk(
                result.get('title', ''),
                result.get('description', ''),
                result.get('ai_category', '')
            )
        
        progress_bar.progress(95)
        
        # Generar reporte ejecutivo de IA
        status_text.text("📝 Generando reporte ejecutivo...")
        ai_report = ai_analyzer.generate_ai_report(all_results, song_name, artist_name)
        
        # Calcular métricas de riesgo
        high_risk_count = sum(1 for r in all_results if r.get('risk_level') == 'HIGH')
        medium_risk_count = sum(1 for r in all_results if r.get('risk_level') == 'MEDIUM')
        
        # Almacenar resultados en el estado de la sesión
        st.session_state.search_results = {
            'youtube': classified_youtube,
            'web': classified_web,
            'youtube_count': len(classified_youtube),
            'web_count': len(classified_web),
            'summary': summary,
            'ai_report': ai_report,
            'high_risk_count': high_risk_count,
            'medium_risk_count': medium_risk_count,
            'song_name': song_name,
            'artist_name': artist_name
        }
        
        progress_bar.progress(100)
        status_text.text("✅ ¡Búsqueda completada exitosamente!")
        time.sleep(1)
        status_text.empty()
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error durante la búsqueda: {str(e)}")
        logger.error(f"Error de búsqueda: {e}")
        return False

def display_results():
    """Mostrar los resultados de la búsqueda."""
    results = st.session_state.search_results
    
    if not results['youtube'] and not results['web']:
        st.info("🔍 No se encontraron resultados. Intenta con diferentes términos de búsqueda.")
        return
    
    # Mostrar Reporte Ejecutivo IA primero
    if results.get('ai_report'):
        st.markdown("---")
        st.subheader("🤖 Reporte Ejecutivo de IA")
        st.info(results['ai_report'])
        st.markdown("---")

    # Mostrar resumen con métricas de riesgo
    if results['summary']:
        display_summary(
            results['summary'],
            results.get('song_name', 'Desconocida'),
            results.get('artist_name', 'Desconocido'),
            results.get('high_risk_count', 0),
            results.get('medium_risk_count', 0),
            results.get('youtube_count', 0),
            results.get('web_count', 0),
            ai_report=results.get('ai_report', '')
        )
    
    # Mostrar resultados de YouTube
    if results['youtube']:
        st.markdown("## 📺 Resultados de YouTube")
        display_result_cards(results['youtube'], 'youtube')
    
    # Mostrar resultados de la web
    if results['web']:
        st.markdown("## 🌐 Resultados de la Web")
        display_result_cards(results['web'], 'web')

def display_summary(summary: Dict, song_name: str = "", artist_name: str = "",
                    high_risk: int = 0, medium_risk: int = 0,
                    youtube_count: int = 0, web_count: int = 0,
                    ai_report: str = ""):
    """Mostrar el resumen del análisis con métricas de riesgo."""
    st.markdown("## 📊 Dashboard de Métricas")
    
    # Métricas de fuentes de datos
    st.markdown("### 📈 Fuentes de Datos")
    col_sources = st.columns(3)
    with col_sources[0]:
        st.metric("Resultados YouTube", youtube_count)
    with col_sources[1]:
        st.metric("Resultados Web", web_count)
    with col_sources[2]:
        st.metric("Total de Resultados", summary['total_results'])
    
    st.markdown("---")
    
    # Métricas principales de análisis
    st.markdown("### 🔍 Análisis de Uso")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Usos Potenciales", summary['category_counts'].get('possible_song_usage', 0))

    with col2:
        covers = summary['category_counts'].get('cover', 0)
        st.metric("Covers", covers)

    with col3:
        st.metric("Resultados Riesgo Alto", high_risk)

    # Métricas secundarias
    col4, col5, col6 = st.columns(3)

    with col4:
        promo = summary['category_counts'].get('promotional_usage', 0)
        st.metric("Uso Promocional", promo)

    with col5:
        st.metric("Riesgo Medio", medium_risk)

    with col6:
        reference = summary['category_counts'].get('reference_only', 0)
        st.metric("Solo Referencias", reference)
    
    st.markdown("---")
    
    # Botón de descarga de PDF
    if song_name and artist_name:
        col_download, col_spacer = st.columns([1, 3])
        with col_download:
            try:
                # Crear summary extendido para PDF
                summary_for_pdf = summary.copy()
                summary_for_pdf['high_risk_count'] = high_risk
                summary_for_pdf['medium_risk_count'] = medium_risk
                summary_for_pdf['ai_report'] = ai_report
                pdf_bytes, filename = get_pdf_download_link(song_name, artist_name, summary_for_pdf)
                st.download_button(
                    label="Descargar Reporte PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    width='stretch',
                    type="primary"
                )
            except Exception as e:
                logger.error(f"Error generando PDF: {e}")
                st.error("❌ Error al generar el PDF")
        st.markdown("---")
    
    # Desglose por categoría
    st.markdown("### 📈 Desglose por Tipo de Uso")
    
    categories_data = []
    for category, count in summary['category_counts'].items():
        percentage = summary['category_percentages'].get(category, 0)
        # Traducir categorías
        category_translations = {
            'possible_song_usage': 'Uso Directo de Canción',
            'cover': 'Cover/Interpretación',
            'promotional_usage': 'Uso Promocional',
            'reference_only': 'Solo Referencia'
        }
        categories_data.append({
            'Categoría': category_translations.get(category, category.replace('_', ' ').title()),
            'Cantidad': count,
            'Porcentaje': f"{percentage:.1f}%"
        })
    
    df_categories = pd.DataFrame(categories_data)
    st.dataframe(df_categories, use_container_width=True, hide_index=True)
    
    # Insights
    if summary['insights']:
        st.markdown("### 💡 Hallazgos Clave")
        for insight in summary['insights']:
            st.markdown(f'<div class="insight-card">{html.escape(str(insight))}</div>', unsafe_allow_html=True)

def display_result_cards(results: List[Dict], source_type: str):
    """Mostrar tarjetas individuales de resultados con nivel de riesgo."""
    # Traducciones de categorías
    category_translations = {
        'possible_song_usage': 'Uso Directo de Canción',
        'cover': 'Cover/Interpretación',
        'promotional_usage': 'Uso Promocional',
        'reference_only': 'Solo Referencia'
    }
    
    # Categorías CSS válidas (whitelist)
    valid_css_classes = {'possible-song-usage', 'cover', 'promotional-usage', 'reference-only'}

    for i, result in enumerate(results):
        with st.container():
            # Estilo de badge de categoría
            category = result.get('ai_category', 'reference_only')
            confidence = result.get('ai_confidence', 0.5)
            risk_level = result.get('risk_level', 'LOW')

            # Validar category_class contra whitelist para evitar inyección CSS
            category_class = category.replace('_', '-')
            if category_class not in valid_css_classes:
                category_class = 'reference-only'
            category_display = category_translations.get(category, 'Solo Referencia')

            # Mostrar nivel de riesgo con colores
            if risk_level == 'HIGH':
                st.error(f"⚠️ RIESGO ALTO - {category_display}")
            elif risk_level == 'MEDIUM':
                st.warning(f"⚡ RIESGO MEDIO - {category_display}")
            else:
                st.success(f"✅ RIESGO BAJO - {category_display}")

            # Escapar todos los datos externos antes de insertar en HTML
            safe_title = html.escape(str(result.get('title', '')))
            safe_desc = html.escape(str(result.get('description', '')))
            safe_reasoning = html.escape(str(result.get('ai_reasoning', 'Análisis no disponible')))
            safe_category_display = html.escape(category_display)

            # Validar esquema de URL para prevenir inyección javascript:
            raw_link = result.get('link', '#')
            safe_link = raw_link if raw_link.startswith(('https://', 'http://')) else '#'

            # Tarjeta de resultado
            st.markdown(f"""
            <div class="result-card">
                <h4 style="margin-bottom: 0.5rem;">
                    <a href="{safe_link}" target="_blank" rel="noopener noreferrer" style="color: #1f2937; text-decoration: none; font-weight: 600;">
                        {safe_title}
                    </a>
                </h4>
                <p style="color: #6b7280; margin-bottom: 1rem;">{safe_desc}</p>
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                    <span class="category-badge {category_class}">{safe_category_display}</span>
                    <span class="confidence-score">🎯 Confianza: {int(confidence * 100)}%</span>
                    <span class="risk-badge" style="font-weight: bold; color: {'#dc2626' if risk_level == 'HIGH' else '#ea580c' if risk_level == 'MEDIUM' else '#16a34a'};">{'RIESGO ALTO' if risk_level == 'HIGH' else 'RIESGO MEDIO' if risk_level == 'MEDIUM' else 'RIESGO BAJO'}</span>
                </div>
                <div class="ai-reasoning">
                    <strong>🤖 Análisis IA:</strong> {safe_reasoning}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Metadatos adicionales para diferentes fuentes
            if source_type == 'youtube' and 'channel' in result:
                safe_channel = html.escape(str(result['channel']))
                st.markdown(f'<div class="video-meta">📺 Canal: {safe_channel} | 🎬 YouTube</div>', unsafe_allow_html=True)
            elif source_type == 'web' and 'displayed_link' in result:
                safe_displayed = html.escape(str(result['displayed_link']))
                st.markdown(f'<div class="web-meta">🔗 {safe_displayed} | 🌐 Web</div>', unsafe_allow_html=True)
            
            st.markdown("---")

def display_sidebar():
    """Mostrar información en la barra lateral."""
    st.sidebar.markdown("## ℹ️ Acerca de")
    st.sidebar.markdown("""
    Esta herramienta te ayuda a:
    - Encontrar usos de canciones en YouTube
    - Descubrir menciones en la web
    - Clasificar tipos de uso con IA
    - Generar reportes detallados
    """)
    
    st.sidebar.markdown("## 🏷️ Categorías de Clasificación")
    st.sidebar.markdown("""
    - **🎵 Uso Directo**: Uso directo de la canción
    - **🎤 Cover**: Versiones o interpretaciones
    - **📢 Promocional**: Uso en marketing
    - **📝 Referencia**: Solo menciones
    """)
    
    st.sidebar.markdown("## ⚙️ Configuración")
    st.sidebar.markdown(f"""
    **Estado de APIs:**
    ✅ API de YouTube
    ✅ API de SerpAPI
    ✅ API de OpenAI
    """)

    st.sidebar.markdown("---")
    username = st.session_state.get('username', '')
    st.sidebar.markdown(f"👤 **{username}**")
    if st.sidebar.button("Cerrar sesión", use_container_width=True):
        logout()

def main():
    """Función principal de la aplicación."""
    if not show_login():
        st.stop()

    initialize_session_state()
    display_header()
    display_sidebar()

    submitted, user_query = display_search_form()

    if submitted:
        if not user_query.strip():
            st.warning("⚠️ Por favor ingresa el nombre de una canción.")
        else:
            # Resetear estado de búsqueda anterior
            st.session_state.user_query = user_query.strip()
            st.session_state.mode = 'idle'
            st.session_state.search_performed = False
            run_quick_search(user_query.strip())
            st.rerun()

    if st.session_state.mode in ('quick_results', 'deep_analysis'):
        display_quick_results()

    if st.session_state.mode == 'deep_analysis' and st.session_state.search_performed:
        display_results()

if __name__ == "__main__":
    main()
