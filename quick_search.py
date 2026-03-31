"""
Módulo de búsqueda rápida de links.
Obtiene hasta 10 resultados de YouTube y 10 de la web sin clasificación de IA,
usando una única query enriquecida 'canción artista'.
"""
import logging
from typing import Dict, List

from web_search import WebSearcher
from youtube_search import YouTubeSearcher

logger = logging.getLogger(__name__)


def search_links(song_name: str, artist_name: str) -> Dict:
    """
    Obtiene hasta 10 links de YouTube y 10 de la web para una canción.

    Reutiliza los buscadores existentes con una sola query enriquecida,
    sin el loop de múltiples variaciones del Análisis Profundo.

    Args:
        song_name: Nombre de la canción identificada.
        artist_name: Nombre del artista identificado.

    Returns:
        Dict con keys: song (str), artist (str),
        links (List[Dict] con keys type/title/url).
    """
    query = f"{song_name} {artist_name}"
    links: List[Dict] = []

    try:
        yt = YouTubeSearcher()
        videos = yt._fetch_query_results(query, max_per_query=10)
        for v in videos:
            links.append({"type": "YouTube", "title": v["title"], "url": v["link"]})
        logger.info(
            f"Quick links YouTube: {len(videos)} resultado(s) para '{song_name}' de '{artist_name}'"
        )
    except Exception as e:
        logger.error(f"YouTube falló en búsqueda rápida: {e}")

    try:
        web = WebSearcher()
        results = web._fetch_web_results(query, num_results=10)
        for r in results:
            links.append({"type": "Web", "title": r["title"], "url": r["link"]})
        logger.info(
            f"Quick links Web: {len(results)} resultado(s) para '{song_name}' de '{artist_name}'"
        )
    except Exception as e:
        logger.error(f"SerpAPI falló en búsqueda rápida: {e}")

    return {"song": song_name, "artist": artist_name, "links": links}
