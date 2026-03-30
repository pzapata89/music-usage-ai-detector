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
