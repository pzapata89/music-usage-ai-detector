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
