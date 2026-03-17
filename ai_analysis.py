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
        # Create analysis prompt
        prompt = self._create_classification_prompt(title, description, song_name, artist_name)
        
        try:
            # Llamar a API de OpenAI (nueva versión 1.0+)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en analizar cómo se usan las canciones en contenido en línea. Clasifica los resultados con precisión y proporciona razonamientos breves en español."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            # Parsear respuesta (nueva API usa .choices[0].message.content)
            result_text = response.choices[0].message.content.strip()
            classification = self._parse_classification_response(result_text)
            
            logger.info(f"Resultado clasificado: {title} -> {classification['category']}")
            return classification
            
        except Exception as e:
            logger.error(f"Error durante la clasificación de IA: {e}")
            # Retornar clasificación por defecto en caso de error
            return {
                "category": "reference_only",
                "confidence": 0.5,
                "reasoning": "Clasificación fallida - asignando solo referencia por defecto"
            }
    
    def analyze_batch(self, results: List[Dict], song_name: str, artist_name: str) -> List[Dict]:
        """
        Clasificar múltiples resultados de búsqueda.
        
        Args:
            results: Lista de diccionarios de resultados de búsqueda
            song_name: Nombre de la canción buscada
            artist_name: Nombre del artista buscado
            
        Returns:
            Lista de resultados con información de clasificación agregada
        """
        classified_results = []
        
        for result in results:
            classification = self.classify_result(
                result['title'],
                result['description'],
                song_name,
                artist_name
            )
            
            # Add classification to result
            result_with_classification = result.copy()
            result_with_classification.update({
                'ai_category': classification['category'],
                'ai_confidence': classification['confidence'],
                'ai_reasoning': classification['reasoning']
            })
            
            classified_results.append(result_with_classification)
        
        return classified_results
    
    def generate_summary_report(self, classified_results: List[Dict], song_name: str, artist_name: str) -> Dict:
        """
        Generar un reporte resumen del análisis.
        
        Args:
            classified_results: Lista de resultados de búsqueda clasificados
            song_name: Nombre de la canción
            artist_name: Nombre del artista
            
        Returns:
            Diccionario con estadísticas resumen y hallazgos
        """
        # Count categories
        category_counts = {}
        total_results = len(classified_results)
        
        for result in classified_results:
            category = result.get('ai_category', 'reference_only')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate percentages
        category_percentages = {}
        for category, count in category_counts.items():
            category_percentages[category] = (count / total_results) * 100 if total_results > 0 else 0
        
        # Generate insights
        insights = self._generate_insights(category_counts, category_percentages, song_name, artist_name)
        
        summary = {
            'song_name': song_name,
            'artist_name': artist_name,
            'total_results': total_results,
            'category_counts': category_counts,
            'category_percentages': category_percentages,
            'insights': insights,
            'high_confidence_results': len([r for r in classified_results if r.get('ai_confidence', 0) > 0.8])
        }
        
        return summary
    
    def _create_classification_prompt(self, title: str, description: str, song_name: str, artist_name: str) -> str:
        """Crear el prompt de clasificación para OpenAI."""
        categories_text = "\n".join([f"- {k}: {v}" for k, v in self.CATEGORIES.items()])
        
        prompt = f"""
Analiza este resultado de búsqueda y clasifica cómo se está usando la canción "{song_name}" de {artist_name}.

Título: {title}
Descripción: {description}

Categorías:
{categories_text}

Por favor responde en este formato exacto:
Category: [nombre_de_categoria]
Confidence: [0.0-1.0]
Reasoning: [explicación breve en español]

Sé objetivo y basa tu análisis únicamente en el título y descripción proporcionados.
"""
        return prompt
    
    def _parse_classification_response(self, response_text: str) -> Dict:
        """Parsear la respuesta de OpenAI en datos estructurados."""
        # Valores por defecto
        result = {
            "category": "reference_only",
            "confidence": 0.5,
            "reasoning": "No se pudo parsear la respuesta"
        }
        
        try:
            # Extraer categoría
            category_match = re.search(r'Category:\s*(\w+)', response_text, re.IGNORECASE)
            if category_match:
                category = category_match.group(1).lower()
                # Validar categoría
                if category in self.CATEGORIES:
                    result["category"] = category
            
            # Extraer confianza
            confidence_match = re.search(r'Confidence:\s*([0-9.]+)', response_text)
            if confidence_match:
                confidence = float(confidence_match.group(1))
                result["confidence"] = min(max(confidence, 0.0), 1.0)
            
            # Extraer razonamiento
            reasoning_match = re.search(r'Reasoning:\s*(.+)', response_text, re.IGNORECASE)
            if reasoning_match:
                result["reasoning"] = reasoning_match.group(1).strip()
            
        except Exception as e:
            logger.error(f"Error al parsear respuesta de clasificación: {e}")
        
        return result
    
    def _generate_insights(self, counts: Dict, percentages: Dict, song_name: str, artist_name: str) -> List[str]:
        """Generar hallazgos a partir de los resultados de clasificación."""
        insights = []
        
        # Tipo de uso más común
        if counts:
            most_common = max(counts.items(), key=lambda x: x[1])
            category_name = self.CATEGORIES.get(most_common[0], most_common[0])
            insights.append(f"Uso más común: {category_name} ({most_common[1]} resultados)")
        
        # Detección de uso alto
        possible_usage_count = counts.get('possible_song_usage', 0)
        if possible_usage_count > 0:
            insights.append(f"Se encontraron {possible_usage_count} uso(s) directo(s) posible(s) de la canción")
        
        # Detección de covers
        cover_count = counts.get('cover', 0)
        if cover_count > 0:
            insights.append(f"Se encontraron {cover_count} versión(es) cover")
        
        # Uso promocional
        promo_count = counts.get('promotional_usage', 0)
        if promo_count > 0:
            insights.append(f"Se encontraron {promo_count} uso(s) promocional(es)")
        
        # Evaluación general
        total_usage = possible_usage_count + promo_count
        if total_usage > 5:
            insights.append("Alta actividad detectada - la canción parece ser ampliamente utilizada")
        elif total_usage > 2:
            insights.append("Actividad moderada detectada - la canción tiene uso notable")
        elif total_usage > 0:
            insights.append("Baja actividad detectada - uso limitado encontrado")
        else:
            insights.append("No se detectó uso directo - solo referencias encontradas")
        
        return insights
    
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
        
        if category in risk_mapping:
            return risk_mapping[category]
        
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
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en derechos de autor y análisis de uso comercial de música. Clasifica el riesgo de manera conservadora."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().upper()
            
            if 'HIGH' in result:
                return 'HIGH'
            elif 'MEDIUM' in result or 'MID' in result:
                return 'MEDIUM'
            else:
                return 'LOW'
                
        except Exception as e:
            logger.error(f"Error clasificando riesgo: {e}")
            return 'LOW'
    
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
        
        try:
            prompt = f"""
Actúa como un analista experto en derechos de autor evaluando el uso online de la canción "{song_name}" de {artist_name}.

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
        Cadena formateada para mostrar
    """
    category_display = category.replace('_', ' ').title()
    confidence_percent = int(confidence * 100)
    
    return f"**{category_display}** ({confidence_percent}% de confianza)\n{reasoning}"
