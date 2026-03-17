"""
Módulo de generación de PDF para el Detector de Uso de Música.
Crea reportes PDF profesionales con los resultados del análisis.
"""

from fpdf import FPDF
from typing import Dict, List
from datetime import datetime
import io


class PDFReport(FPDF):
    """Clase personalizada para generar reportes PDF."""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        """Encabezado del PDF."""
        # Logo o título
        self.set_font('Arial', 'B', 16)
        self.set_text_color(102, 126, 234)
        self.cell(0, 10, 'Detector de Uso de Música con IA', 0, 1, 'C')
        
        # Subtítulo
        self.set_font('Arial', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Reporte de Análisis de Uso de Canciones', 0, 1, 'C')
        
        # Línea divisoria
        self.set_draw_color(102, 126, 234)
        self.line(10, 30, 200, 30)
        self.ln(10)
        
    def footer(self):
        """Pie de página del PDF."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        
    def chapter_title(self, title: str):
        """Título de sección."""
        self.set_font('Arial', 'B', 14)
        self.set_text_color(102, 126, 234)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)
        
    def chapter_body(self, body: str):
        """Cuerpo de texto."""
        self.set_font('Arial', '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 6, body)
        self.ln()
        
    def add_metric_box(self, label: str, value: str, x: int, y: int, width: int = 45):
        """Agregar caja de métrica."""
        # Caja con fondo gris claro
        self.set_fill_color(240, 240, 240)
        self.set_draw_color(200, 200, 200)
        self.rect(x, y, width, 20, 'DF')
        
        # Etiqueta
        self.set_xy(x, y + 2)
        self.set_font('Arial', '', 8)
        self.set_text_color(100, 100, 100)
        self.cell(width, 5, label, 0, 2, 'C')
        
        # Valor
        self.set_font('Arial', 'B', 12)
        self.set_text_color(102, 126, 234)
        self.cell(width, 8, value, 0, 2, 'C')
        
    def add_category_row(self, category: str, count: int, percentage: float):
        """Agregar fila de categoría."""
        # Color según categoría
        colors = {
            'Uso Directo de Canción': (255, 107, 107),
            'Cover/Interpretación': (78, 205, 196),
            'Uso Promocional': (69, 183, 209),
            'Solo Referencia': (150, 206, 180)
        }
        
        color = colors.get(category, (150, 150, 150))
        
        # Barra de color
        self.set_fill_color(*color)
        self.cell(5, 8, '', 0, 0, 'L', True)
        
        # Nombre de categoría
        self.set_font('Arial', '', 10)
        self.set_text_color(50, 50, 50)
        self.cell(80, 8, f'  {category}', 0, 0, 'L')
        
        # Cantidad
        self.set_font('Arial', 'B', 10)
        self.cell(30, 8, str(count), 0, 0, 'C')
        
        # Porcentaje
        self.set_font('Arial', '', 10)
        self.cell(30, 8, f'{percentage:.1f}%', 0, 1, 'R')
        
    def add_insight_item(self, text: str):
        """Agregar item de hallazgo."""
        self.set_font('Arial', '', 10)
        self.set_text_color(50, 50, 50)
        
        # Bullet point
        self.set_fill_color(102, 126, 234)
        self.cell(3, 6, '', 0, 0, 'L', True)
        self.cell(5, 6, '', 0, 0, 'L')
        
        # Texto
        self.multi_cell(0, 6, text)
        self.ln(2)


def generate_pdf_report(summary: Dict, song_name: str, artist_name: str) -> bytes:
    """
    Generar reporte PDF con el resumen del análisis.
    
    Args:
        summary: Diccionario con el resumen del análisis
        song_name: Nombre de la canción
        artist_name: Nombre del artista
        
    Returns:
        Bytes del PDF generado
    """
    pdf = PDFReport()
    pdf.add_page()
    
    # Información general
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 10, f'"{song_name}" - {artist_name}', 0, 1, 'L')
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f'Fecha del análisis: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'L')
    pdf.ln(10)
    
    # Sección de métricas principales
    pdf.chapter_title('Resumen General')
    
    # Métricas en cajas
    metrics_y = pdf.get_y()
    pdf.add_metric_box('Total de Resultados', str(summary['total_results']), 10, metrics_y)
    pdf.add_metric_box('Usos Directos', str(summary['category_counts'].get('possible_song_usage', 0)), 57, metrics_y)
    pdf.add_metric_box('Covers', str(summary['category_counts'].get('cover', 0)), 104, metrics_y)
    pdf.add_metric_box('Alta Confianza', str(summary['high_confidence_results']), 151, metrics_y)
    
    pdf.ln(25)
    
    # Métricas de riesgo
    high_risk = summary.get('high_risk_count', 0)
    medium_risk = summary.get('medium_risk_count', 0)
    
    pdf.chapter_title('Análisis de Riesgo')
    
    metrics_y = pdf.get_y()
    pdf.add_metric_box('Alto Riesgo', str(high_risk), 10, metrics_y, 60)
    pdf.add_metric_box('Riesgo Medio', str(medium_risk), 75, metrics_y, 60)
    pdf.add_metric_box('Promocional', str(summary['category_counts'].get('promotional_usage', 0)), 140, metrics_y, 60)
    
    pdf.ln(25)
    
    # Sección de desglose por categoría
    pdf.chapter_title('Desglose por Tipo de Uso')
    
    # Encabezados de tabla
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(85, 8, 'Categoría', 0, 0, 'L')
    pdf.cell(30, 8, 'Cantidad', 0, 0, 'C')
    pdf.cell(30, 8, 'Porcentaje', 0, 1, 'R')
    
    # Línea divisoria
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    # Traducciones de categorías
    category_translations = {
        'possible_song_usage': 'Uso Directo de Canción',
        'cover': 'Cover/Interpretación',
        'promotional_usage': 'Uso Promocional',
        'reference_only': 'Solo Referencia'
    }
    
    # Filas de categorías
    for category, count in summary['category_counts'].items():
        percentage = summary['category_percentages'].get(category, 0)
        category_display = category_translations.get(category, category.replace('_', ' ').title())
        pdf.add_category_row(category_display, count, percentage)
    
    pdf.ln(10)
    
    # Sección de AI Executive Report
    if summary.get('ai_report'):
        pdf.add_page()
        pdf.chapter_title('AI Executive Report')
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, summary['ai_report'])
        pdf.ln(10)
    
    # Sección de hallazgos clave
    if summary['insights'] and not summary.get('ai_report'):
        pdf.chapter_title('Hallazgos Clave')
        
        for insight in summary['insights']:
            pdf.add_insight_item(insight)
    
    # Pie de página con información adicional
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 5, 
        'Este reporte fue generado automáticamente por el Detector de Uso de Música con IA. '
        'Los resultados se basan en análisis de búsquedas en YouTube y la web, '
        'clasificados por inteligencia artificial.'
    )
    
    # Retornar PDF como bytes (nueva versión fpdf2 retorna bytearray directamente)
    return bytes(pdf.output(dest='S'))


def get_pdf_download_link(song_name: str, artist_name: str, summary: Dict) -> tuple:
    """
    Generar el PDF y retornar los bytes y nombre de archivo sugerido.
    
    Args:
        song_name: Nombre de la canción
        artist_name: Nombre del artista
        summary: Resumen del análisis
        
    Returns:
        Tupla (bytes del PDF, nombre de archivo sugerido)
    """
    pdf_bytes = generate_pdf_report(summary, song_name, artist_name)
    
    # Crear nombre de archivo seguro
    safe_song = song_name.replace(' ', '_').replace('/', '-').replace('\\', '-')[:30]
    safe_artist = artist_name.replace(' ', '_').replace('/', '-').replace('\\', '-')[:30]
    filename = f"Reporte_{safe_song}_{safe_artist}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return pdf_bytes, filename
