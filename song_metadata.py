"""
Módulo de identificación de canciones.
Usa Spotify API (Client Credentials) para identificar canción y artista desde
texto libre del usuario. Fallback a OpenAI si Spotify falla o no retorna resultados.
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from typing import List, Optional

import requests
from openai import OpenAI

from config import config

logger = logging.getLogger(__name__)

_SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
_SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"

# Singleton para reutilizar token de Spotify durante la sesión
_spotify_client: Optional["SpotifyClient"] = None


@dataclass
class SongCandidate:
    song_name: str
    artist_name: str
    album: str
    spotify_id: str      # vacío si proviene del fallback de OpenAI
    confidence: float    # 1.0 para Spotify, ~0.8 para OpenAI fallback


class SpotifyClient:
    """Cliente de Spotify con caché de token de sesión."""

    def __init__(self) -> None:
        self._token: Optional[str] = None

    def _get_token(self) -> str:
        if self._token:
            return self._token
        credentials = f"{config.spotify_client_id}:{config.spotify_client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        response = requests.post(
            _SPOTIFY_TOKEN_URL,
            headers={"Authorization": f"Basic {encoded}"},
            data={"grant_type": "client_credentials"},
        )
        response.raise_for_status()
        self._token = response.json()["access_token"]
        return self._token

    def search_tracks(self, query: str, limit: int = 3) -> List[SongCandidate]:
        token = self._get_token()
        response = requests.get(
            _SPOTIFY_SEARCH_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "type": "track", "limit": limit},
        )
        response.raise_for_status()
        items = response.json().get("tracks", {}).get("items", [])
        return [
            SongCandidate(
                song_name=item["name"],
                artist_name=", ".join(a["name"] for a in item["artists"]),
                album=item["album"]["name"],
                spotify_id=item["id"],
                confidence=1.0,
            )
            for item in items
        ]


def _openai_fallback(user_input: str) -> List[SongCandidate]:
    """Identifica canción usando OpenAI cuando Spotify no está disponible."""
    client = OpenAI(api_key=config.openai_api_key)
    safe_input = user_input[:200].replace('"', "'")
    prompt = (
        f'Identifica las 3 canciones más probables para la búsqueda: "{safe_input}".\n'
        "Responde SOLO con un array JSON válido, sin texto adicional:\n"
        '[{"song_name": "...", "artist_name": "...", "album": "..."}, ...]'
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.3,
    )
    text = response.choices[0].message.content.strip()
    # Eliminar bloques de código markdown si están presentes
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)
    return [
        SongCandidate(
            song_name=item["song_name"],
            artist_name=item["artist_name"],
            album=item.get("album", ""),
            spotify_id="",
            confidence=0.8,
        )
        for item in data[:3]
    ]


def get_song_metadata(user_input: str) -> List[SongCandidate]:
    """
    Identifica canción y artista a partir de texto libre del usuario.

    Intenta Spotify primero (Client Credentials, sin login de usuario).
    Si Spotify falla o retorna 0 resultados, usa OpenAI como fallback.

    Args:
        user_input: Texto libre del usuario (ej: "Despacito", "la bamba")

    Returns:
        Lista de hasta 3 SongCandidate ordenados por relevancia.

    Raises:
        Exception: Si tanto Spotify como OpenAI fallan.
    """
    global _spotify_client
    logger.info(f"Búsqueda rápida iniciada: '{user_input}'")

    try:
        if _spotify_client is None:
            _spotify_client = SpotifyClient()
        candidates = _spotify_client.search_tracks(user_input, limit=3)
        if candidates:
            logger.info(f"Spotify identificó {len(candidates)} candidato(s) para '{user_input}'")
            return candidates
        logger.warning(
            f"Spotify retornó 0 resultados para '{user_input}', usando fallback OpenAI"
        )
    except Exception as e:
        logger.warning(f"Spotify falló para '{user_input}': {e}, usando fallback OpenAI")

    return _openai_fallback(user_input)
