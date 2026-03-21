"""
Módulo de análisis de IA para Detector de Uso de Música.
Usa la API de OpenAI para clasificar resultados de búsqueda en categorías de uso.
"""

from openai import OpenAI
from typing import List, Dict, Optional
import logging
import json
import re

from config import config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Límite de análisis por sesión
MAX_ANALISIS = 20

class AIAnalyzer:
    """Wrapper de API de OpenAI para analizar y clasificar resultados de búsqueda."""
    
    # Categorías de clasificación
    CATEGORIES = {
        "possible_song_usage": "Uso Directo de Canción - Uso directo de la canción en contenido",
        "cover": "Cover - Alguien interpretando o cubriendo la canción",
        "promotional_usage": "Uso Promocional - Uso de la canción para promoción o marketing",
        "reference_only": "Solo Referencia - Mencionando la canción pero sin usarla"
    }
    
    def __init__(self):
        """Inicializar cliente de OpenAI."""
        try:
            self.client = OpenAI(api_key=config.openai_api_key)
            self.analysis_count = 0  # Contador de análisis en la sesión actual
            logger.info("Cliente de OpenAI inicializado exitosamente")
        except Exception as e:
            logger.error(f"Error al inicializar cliente de OpenAI: {e}")
            raise
    
    def classify_result(self, title: str, description: str, song_name: str, artist_name: str) -> Dict:
        """
        Clasificar un resultado de búsqueda en categorías de uso.
        
        Args:
            title: Título del resultado de búsqueda
            description: Descripción/snippet del resultado de búsqueda
            song_name: Nombre de la canción buscada
            artist_name: Nombre del artista buscado
            
        Returns:
            Diccionario con el resultado de clasificación y confianza
        """
        # Verificar límite de análisis por sesión
        if self.analysis_count >= MAX_ANALISIS:
            logger.warning(f"Límite de análisis por sesión alcanzado ({MAX_ANALISIS}). Clasificación por defecto.")
            return {
                "category": "reference_only",
                "confidence": 0.5,
                "reasoning": "Límite de análisis alcanzado - clasificación por defecto"
            }
        
        # Create analysis prompt
        prompt = self._create_classification_prompt(title, description, song_name, artist_name)
        
        try:
            # Llamar a API de OpenAI (nueva versión 1.0+)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un experto en analizar cómo se usan las canciones en contenido en línea. Clasifica los resultados con precisión y proporciona razonamientos breves en español."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            # Parsear respuesta (nueva API usa .choices[0].message.content)
            result_text = response.choices[0].message.content.strip()
            classification = self._parse_classification_response(result_text)
            
            # Incrementar contador de análisis
            self.analysis_count += 1
            logger.info(f"Análisis #{self.analysis_count}/{MAX_ANALISIS} realizado: {title} -> {classification['category']}")
            return classification
            
        except Exception as e:
            logger.error(f"Error durante la clasificación de IA: {e}")
            # Retornar clasificación por defecto en caso de error
            return {
                "category": "reference_only",
                "confidence": 0.5,
                "reasoning": "Clasificación fallida - asignando solo referencia por defecto"
            }
    
    def _sanitize_for_prompt(self, text: str, max_length: int = 500) -> str:
        """Truncate and strip control characters to reduce prompt injection risk."""
        if not text:
            return ""
        text = str(text)[:max_length]
        # Remove ASCII control characters except newline and tab
        text = ''.join(c for c in text if c >= ' ' or c in '\n\t')
        return text.strip()

    def _create_classification_prompt(self, title: str, description: str, song_name: str, artist_name: str) -> str:
        """Crear prompt para clasificación de uso de música."""
        safe_title = self._sanitize_for_prompt(title, 200)
        safe_desc = self._sanitize_for_prompt(description, 400)
        safe_song = self._sanitize_for_prompt(song_name, 100)
        safe_artist = self._sanitize_for_prompt(artist_name, 100)
        return f"""
Analiza este resultado de búsqueda y clasifica el tipo de uso de la canción "{safe_song}" de {safe_artist}.

TÍTULO: <data>{safe_title}</data>
DESCRIPCIÓN: <data>{safe_desc}</data>

Categorías posibles:
1. possible_song_usage - Uso directo de la canción en contenido
2. cover - Alguien interpretando o cubriendo la canción
3. promotional_usage - Uso de la canción para promoción o marketing
4. reference_only - Mencionando la canción pero sin usarla

Responde en formato JSON:
{{
    "category": "nombre_categoria",
    "confidence": 0.0-1.0,
    "reasoning": "breve explicación en español"
}}
"""
    
    def _parse_classification_response(self, response_text: str) -> Dict:
        """Parsear respuesta de clasificación de la API."""
        try:
            # Intentar parsear como JSON
            if response_text.startswith('{'):
                result = json.loads(response_text)
                return {
                    "category": result.get("category", "reference_only"),
                    "confidence": float(result.get("confidence", 0.5)),
                    "reasoning": result.get("reasoning", "Sin razonamiento proporcionado")
                }
        except json.JSONDecodeError:
            pass
        
        # Si no es JSON, parsear texto plano
        category = "reference_only"
        confidence = 0.5
        reasoning = response_text
        
        # Buscar categorías en el texto
        for cat in self.CATEGORIES.keys():
            if cat.lower() in response_text.lower():
                category = cat
                break
        
        return {
            "category": category,
            "confidence": confidence,
            "reasoning": reasoning[:200]  # Limitar longitud
        }
    
    def analyze_batch(self, results: List[Dict], song_name: str, artist_name: str) -> List[Dict]:
        """
        Analizar un lote de resultados.
        
        Args:
            results: Lista de resultados a analizar
            song_name: Nombre de la canción
            artist_name: Nombre del artista
            
        Returns:
            Lista de resultados con clasificación agregada
        """
        logger.info(f"Analizando lote de {len(results)} resultados")
        
        classified_results = []
        for result in results:
            try:
                classification = self.classify_result(
                    result.get('title', ''),
                    result.get('description', ''),
                    song_name,
                    artist_name
                )
                
                # Agregar información de clasificación al resultado
                result['ai_category'] = classification['category']
                result['ai_confidence'] = classification['confidence']
                result['ai_reasoning'] = classification['reasoning']
                
                classified_results.append(result)
                
            except Exception as e:
                logger.error(f"Error analizando resultado: {e}")
                # Agregar resultado con clasificación por defecto
                result['ai_category'] = 'reference_only'
                result['ai_confidence'] = 0.5
                result['ai_reasoning'] = 'Error en análisis'
                classified_results.append(result)
        
        logger.info(f"Lote analizado: {len(classified_results)} resultados clasificados")
        return classified_results
    
    def classify_usage_risk(self, title: str, description: str, category: str = "") -> str:
        """
        Clasificar el nivel de riesgo comercial de un resultado.
        
        Args:
            title: Título del resultado
            description: Descripción del resultado
            category: Categoría previamente clasificada (opcional)
            
        Returns:
            Nivel de riesgo: 'LOW', 'MEDIUM', o 'HIGH'
        """
        # Si ya tenemos categoría, podemos inferir riesgo directamente
        risk_mapping = {
            'possible_song_usage': 'HIGH',
            'promotional_usage': 'HIGH',
            'cover': 'MEDIUM',
            'reference_only': 'LOW'
        }
        
        if category and category in risk_mapping:
            return risk_mapping[category]
        
        # Verificar límite de análisis por sesión
        if self.analysis_count >= MAX_ANALISIS:
            logger.warning(f"Límite de análisis por sesión alcanzado ({MAX_ANALISIS}). Riesgo por defecto: LOW.")
            return "LOW"
        
        # Si no hay categoría, usar IA para clasificar
        try:
            prompt = f"""
Analiza este contenido y determina el nivel de riesgo comercial para uso no autorizado de música:

Título: {title}
Descripción: {description}

Evalúa si indica:
- Uso comercial directo (alto riesgo)
- Promoción de eventos o marketing (alto riesgo)
- Cover/interpretación (riesgo medio)
- Solo referencia o mención (bajo riesgo)

Responde únicamente con: HIGH, MEDIUM, o LOW
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un experto en derechos de autor y análisis de uso comercial de música. Clasifica el riesgo de manera conservadora."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            risk_level = response.choices[0].message.content.strip().upper()
            
            # Incrementar contador de análisis
            self.analysis_count += 1
            logger.info(f"Análisis de riesgo #{self.analysis_count}/{MAX_ANALISIS} realizado: {risk_level}")
            
            if risk_level in ['HIGH', 'MEDIUM', 'LOW']:
                return risk_level
            else:
                logger.warning(f"Respuesta de riesgo no válida: {risk_level}")
                return 'LOW'
                
        except Exception as e:
            logger.error(f"Error clasificando riesgo: {e}")
            return 'LOW'

    def generate_summary_report(self, results: List[Dict], song_name: str, artist_name: str) -> Dict:
        """
        Generar resumen estadístico de los resultados clasificados.

        Returns:
            Dict con total_results, category_counts, category_percentages,
            high_confidence_results e insights.
        """
        total = len(results)

        category_counts = {
            'possible_song_usage': 0,
            'cover': 0,
            'promotional_usage': 0,
            'reference_only': 0,
        }
        high_confidence = 0

        for r in results:
            cat = r.get('ai_category', 'reference_only')
            if cat in category_counts:
                category_counts[cat] += 1
            if r.get('ai_confidence', 0) >= 0.7:
                high_confidence += 1

        category_percentages = {
            cat: (count / total * 100) if total > 0 else 0
            for cat, count in category_counts.items()
        }

        insights = []
        usage = category_counts['possible_song_usage']
        covers = category_counts['cover']
        promo = category_counts['promotional_usage']

        if usage > 0:
            insights.append(f"Se detectaron {usage} uso(s) directo(s) potencial(es) de '{song_name}'.")
        if covers > 0:
            insights.append(f"Se encontraron {covers} versión(es) cover o interpretación de la canción.")
        if promo > 0:
            insights.append(f"Hay {promo} resultado(s) con uso promocional o comercial.")
        if total == 0:
            insights.append("No se encontraron resultados para esta búsqueda.")

        return {
            'total_results': total,
            'category_counts': category_counts,
            'category_percentages': category_percentages,
            'high_confidence_results': high_confidence,
            'insights': insights,
        }

    def generate_ai_report(self, results: List[Dict], song_name: str, artist_name: str) -> str:
        """
        Generar un reporte ejecutivo de IA con análisis de copyright.
        
        Args:
            results: Lista de resultados clasificados
            song_name: Nombre de la canción
            artist_name: Nombre del artista
            
        Returns:
            Reporte ejecutivo en formato string (nunca falla, siempre retorna algo)
        """
        # Calcular métricas detalladas
        total_results = len(results)
        youtube_count = sum(1 for r in results if r.get('source') == 'YouTube')
        web_count = sum(1 for r in results if r.get('source') == 'Web')
        usage_count = sum(1 for r in results if r.get('ai_category') == 'possible_song_usage')
        promo_count = sum(1 for r in results if r.get('ai_category') == 'promotional_usage')
        cover_count = sum(1 for r in results if r.get('ai_category') == 'cover')
        reference_count = sum(1 for r in results if r.get('ai_category') == 'reference_only')
        high_risk = sum(1 for r in results if self.classify_usage_risk(
            r.get('title', ''), r.get('description', ''), r.get('ai_category', '')
        ) == 'HIGH')
        medium_risk = sum(1 for r in results if self.classify_usage_risk(
            r.get('title', ''), r.get('description', ''), r.get('ai_category', '')
        ) == 'MEDIUM')
        low_risk = total_results - high_risk - medium_risk
        
        # Crear resumen de datos para el prompt
        categories_summary = f"""
- Total de resultados encontrados: {total_results}
- Resultados de YouTube: {youtube_count}
- Resultados de Web: {web_count}
- Usos directos potenciales: {usage_count}
- Usos promocionales/comerciales: {promo_count}
- Covers o interpretaciones: {cover_count}
- Solo referencias: {reference_count}
- Resultados de alto riesgo: {high_risk}
- Resultados de riesgo medio: {medium_risk}
- Resultados de bajo riesgo: {low_risk}
"""
        
        safe_song = self._sanitize_for_prompt(song_name, 100)
        safe_artist = self._sanitize_for_prompt(artist_name, 100)

        try:
            prompt = f"""
Actúa como un analista experto en derechos de autor evaluando el uso online de la canción "{safe_song}" de {safe_artist}.

DATOS DEL ANÁLISIS:
{categories_summary}

Basándote en estos datos, genera un reporte ejecutivo profesional que incluya:

1. RESUMEN EJECUTIVO (2-3 oraciones sobre el hallazgo principal)
2. NIVEL DE RIESGO GENERAL (Alto/Medio/Bajo con justificación)
3. DISTRIBUCIÓN DE USOS (breve análisis de los tipos de uso encontrados)
4. RECOMENDACIÓN DE ACCIÓN (qué pasos tomar)

El tono debe ser profesional, objetivo y útil para organizaciones de copyright.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un analista senior de derechos de autor en una organización de protección musical. Proporciona reportes ejecutivos claros, accionables y basados en datos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            report = response.choices[0].message.content.strip()
            logger.info(f"Reporte ejecutivo generado exitosamente para {song_name}")
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte ejecutivo con IA: {e}")
            # Siempre retornar reporte fallback, nunca fallar
            return self._generate_fallback_report(
                song_name, artist_name, total_results, youtube_count, web_count,
                usage_count, cover_count, promo_count, high_risk, medium_risk, low_risk
            )
    
    def _generate_fallback_report(self, song_name: str, artist_name: str, 
                                   total_results: int, youtube_count: int, web_count: int,
                                   usage_count: int, cover_count: int, promo_count: int,
                                   high_risk: int, medium_risk: int, low_risk: int) -> str:
        """
        Generar reporte fallback detallado cuando la IA falla.
        
        Args:
            song_name, artist_name: Información de la canción
            Various counts: Métricas del análisis
            
        Returns:
            Reporte estructurado en formato string
        """
        # Determinar nivel de riesgo
        if high_risk > 5:
            risk_level = "ALTO"
            risk_assessment = f"Se detectaron {high_risk} usos de alto riesgo que requieren atención inmediata."
            recommendation = "Recomendación: Revisar urgentemente los usos de alto riesgo. Considerar acciones de protección de derechos de autor."
        elif high_risk > 2 or medium_risk > 5:
            risk_level = "MEDIO"
            risk_assessment = f"Se encontraron {high_risk} usos de alto riesgo y {medium_risk} de riesgo medio. Requiere monitoreo."
            recommendation = "Recomendación: Monitorear los usos detectados. Evaluar si requieren licenciamiento o acción legal."
        else:
            risk_level = "BAJO"
            risk_assessment = f"Mayoría de resultados son de bajo riesgo ({low_risk}). Uso limitado detectado."
            recommendation = "Recomendación: Monitoreo estándar. No se detectaron usos comerciales significativos."
        
        # Generar resumen de uso
        usage_summary = []
        if usage_count > 0:
            usage_summary.append(f"{usage_count} uso(s) directo(s) potencial(es)")
        if cover_count > 0:
            usage_summary.append(f"{cover_count} versión(es) cover")
        if promo_count > 0:
            usage_summary.append(f"{promo_count} uso(s) promocional(es)")
        
        usage_text = ", ".join(usage_summary) if usage_summary else "solo referencias y menciones"
        
        fallback_report = f"""## AI Executive Report

### Executive Summary
Análisis de "{song_name}" de {artist_name} encontró **{total_results} resultados totales** ({youtube_count} de YouTube, {web_count} de la web). Se detectaron {usage_text}.

### Key Findings
| Métrica | Valor |
|---------|-------|
| **Total de Resultados** | {total_results} |
| **Resultados YouTube** | {youtube_count} |
| **Resultados Web** | {web_count} |
| **Usos Directos Potenciales** | {usage_count} |
| **Versiones Cover** | {cover_count} |
| **Usos Promocionales** | {promo_count} |
| **Alto Riesgo** | {high_risk} |
| **Riesgo Medio** | {medium_risk} |
| **Bajo Riesgo** | {low_risk} |

### Risk Assessment
**Nivel: {risk_level}**

{risk_assessment}

### Recommendation
{recommendation}

---
*Nota: Este es un reporte de fallback generado automáticamente. El análisis detallado con IA no estuvo disponible, pero los datos mostrados son precisos basados en la búsqueda realizada.*"""
        
        logger.info(f"Reporte fallback generado para {song_name}")
        return fallback_report

def format_classification_display(category: str, confidence: float, reasoning: str) -> str:
    """
    Formatear información de clasificación para mostrar en la interfaz.
    
    Args:
        category: Categoría de clasificación
        confidence: Puntaje de confianza (0-1)
        reasoning: Razonamiento de la clasificación
        
    Returns:
        String formateado para mostrar
    """
    category_translations = {
        'possible_song_usage': 'Uso Directo de Canción',
        'cover': 'Cover/Interpretación',
        'promotional_usage': 'Uso Promocional',
        'reference_only': 'Solo Referencia'
    }
    
    display_name = category_translations.get(category, category.replace('_', ' ').title())
    confidence_pct = int(confidence * 100)
    
    return f"**{display_name}** (Confianza: {confidence_pct}%)\n\n{reasoning}"
