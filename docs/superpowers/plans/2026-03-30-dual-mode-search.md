# Búsqueda Dual (Quick Search + Análisis Profundo) — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar un modo de Búsqueda Rápida que auto-identifica canción/artista via Spotify, muestra hasta 3 candidatos con 10 links cada uno, y ofrece un botón por candidato para lanzar el Análisis Profundo existente con reporte ejecutivo prominente y descargable en PDF.

**Architecture:** Dos módulos nuevos (`song_metadata.py`, `quick_search.py`) se agregan sin tocar los módulos existentes. `app.py` se refactoriza a un flujo de 3 estados (`idle` → `quick_results` → `deep_analysis`) con input único. El `perform_search()` existente se reutiliza íntegramente para el modo profundo.

**Tech Stack:** Spotify Web API (Client Credentials flow), OpenAI `gpt-4o-mini` (fallback), `requests` (ya en requirements), Streamlit >= 1.28, módulos existentes de YouTube/SerpAPI.

---

## Estructura de archivos

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `song_metadata.py` | Crear | Identificar canción/artista desde texto libre via Spotify + fallback OpenAI |
| `quick_search.py` | Crear | Obtener top 10 links de YouTube y web sin clasificación IA |
| `config.py` | Modificar | Agregar `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` |
| `app.py` | Modificar | Flujo nuevo, input único, fix PDF, UI en español |
| `requirements.txt` | Modificar | Agregar `pytest>=7.0` |
| `tests/conftest.py` | Crear | Variables de entorno mock para todos los tests |
| `tests/test_song_metadata.py` | Crear | Tests de Spotify search + fallback OpenAI |
| `tests/test_quick_search.py` | Crear | Tests de `search_links()` |

---

### Task 1: Agregar credenciales Spotify a config.py y requirements.txt

**Files:**
- Modify: `config.py:17-21`
- Modify: `requirements.txt`

- [ ] **Step 1: Agregar `pytest` a `requirements.txt`**

```text
# Agregar al final de requirements.txt:
pytest>=7.0
```

- [ ] **Step 2: Agregar claves Spotify al `__init__` de `Config` en `config.py`**

Insertar después de la línea `self.openai_api_key = self._get_api_key("OPENAI_API_KEY")` (línea 20):

```python
        self.spotify_client_id = self._get_api_key("SPOTIFY_CLIENT_ID")
        self.spotify_client_secret = self._get_api_key("SPOTIFY_CLIENT_SECRET")
```

- [ ] **Step 3: Agregar las propiedades getter/setter para Spotify**

Insertar después del setter de `openai_api_key` (después de la línea `self._openai_api_key = value`):

```python
    @property
    def spotify_client_id(self) -> str:
        """Get Spotify Client ID."""
        return self._spotify_client_id

    @spotify_client_id.setter
    def spotify_client_id(self, value: str):
        self._spotify_client_id = value

    @property
    def spotify_client_secret(self) -> str:
        """Get Spotify Client Secret."""
        return self._spotify_client_secret

    @spotify_client_secret.setter
    def spotify_client_secret(self, value: str):
        self._spotify_client_secret = value
```

- [ ] **Step 4: Agregar las variables al archivo `.env`**

Agregar en tu `.env` (obtener credenciales en https://developer.spotify.com/dashboard → crear app → copiar Client ID y Client Secret):

```
SPOTIFY_CLIENT_ID=tu_client_id_aqui
SPOTIFY_CLIENT_SECRET=tu_client_secret_aqui
```

- [ ] **Step 5: Verificar que config carga correctamente**

```bash
python -c "from config import config; print('Spotify ID:', config.spotify_client_id[:8] + '...')"
```

Salida esperada: `Spotify ID: <primeros_8_chars>...`

- [ ] **Step 6: Instalar pytest**

```bash
pip install pytest>=7.0
```

- [ ] **Step 7: Commit**

```bash
git add config.py requirements.txt
git commit -m "feat: agregar credenciales de Spotify a config"
```

---

### Task 2: Crear tests/conftest.py y esqueleto de song_metadata.py

**Files:**
- Create: `tests/conftest.py`
- Create: `song_metadata.py`
- Create: `tests/test_song_metadata.py`

- [ ] **Step 1: Crear `tests/conftest.py`**

```python
# tests/conftest.py
import os

# Deben estar antes de que cualquier import active Config()
os.environ.setdefault("YOUTUBE_API_KEY", "test_yt_key")
os.environ.setdefault("SERPAPI_API_KEY", "test_serp_key")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")
os.environ.setdefault("LOGIN_SALT", "test_salt")
os.environ.setdefault("SPOTIFY_CLIENT_ID", "test_spotify_id")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test_spotify_secret")
```

- [ ] **Step 2: Escribir el test de `SongCandidate` (fallará primero)**

```python
# tests/test_song_metadata.py
from song_metadata import SongCandidate


def test_song_candidate_fields():
    candidate = SongCandidate(
        song_name="Despacito",
        artist_name="Luis Fonsi",
        album="Vida",
        spotify_id="abc123",
        confidence=1.0,
    )
    assert candidate.song_name == "Despacito"
    assert candidate.artist_name == "Luis Fonsi"
    assert candidate.album == "Vida"
    assert candidate.spotify_id == "abc123"
    assert candidate.confidence == 1.0
```

- [ ] **Step 3: Ejecutar test para verificar que falla**

```bash
python -m pytest tests/test_song_metadata.py::test_song_candidate_fields -v
```

Salida esperada: `ImportError: cannot import name 'SongCandidate' from 'song_metadata'`

- [ ] **Step 4: Crear `song_metadata.py` con el dataclass `SongCandidate`**

```python
# song_metadata.py
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
```

- [ ] **Step 5: Ejecutar test para verificar que pasa**

```bash
python -m pytest tests/test_song_metadata.py::test_song_candidate_fields -v
```

Salida esperada: `PASSED`

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py song_metadata.py tests/test_song_metadata.py
git commit -m "feat: agregar SongCandidate y conftest de tests"
```

---

### Task 3: Implementar SpotifyClient en song_metadata.py

**Files:**
- Modify: `song_metadata.py`
- Modify: `tests/test_song_metadata.py`

- [ ] **Step 1: Agregar tests de SpotifyClient al final de `tests/test_song_metadata.py`**

```python
# Agregar al final de tests/test_song_metadata.py
import json
import song_metadata
from unittest.mock import patch, MagicMock


def test_spotify_get_token():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"access_token": "token_abc"}
    mock_resp.raise_for_status = MagicMock()

    with patch("song_metadata.requests.post", return_value=mock_resp) as mock_post:
        client = song_metadata.SpotifyClient()
        token = client._get_token()

    assert token == "token_abc"
    mock_post.assert_called_once()
    assert mock_post.call_args.kwargs["headers"]["Authorization"].startswith("Basic ")


def test_spotify_get_token_caches():
    """Token se reutiliza en llamadas sucesivas sin nueva solicitud HTTP."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"access_token": "token_cached"}
    mock_resp.raise_for_status = MagicMock()

    with patch("song_metadata.requests.post", return_value=mock_resp) as mock_post:
        client = song_metadata.SpotifyClient()
        client._get_token()
        client._get_token()  # segunda llamada — no debe hacer HTTP

    assert mock_post.call_count == 1


def test_spotify_search_tracks():
    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "tok"}
    mock_token_resp.raise_for_status = MagicMock()

    mock_search_resp = MagicMock()
    mock_search_resp.json.return_value = {
        "tracks": {
            "items": [
                {
                    "id": "spotify_id_1",
                    "name": "Despacito",
                    "artists": [{"name": "Luis Fonsi"}, {"name": "Daddy Yankee"}],
                    "album": {"name": "Vida"},
                }
            ]
        }
    }
    mock_search_resp.raise_for_status = MagicMock()

    with patch("song_metadata.requests.post", return_value=mock_token_resp):
        with patch("song_metadata.requests.get", return_value=mock_search_resp):
            client = song_metadata.SpotifyClient()
            candidates = client.search_tracks("Despacito", limit=3)

    assert len(candidates) == 1
    assert candidates[0].song_name == "Despacito"
    assert candidates[0].artist_name == "Luis Fonsi, Daddy Yankee"
    assert candidates[0].album == "Vida"
    assert candidates[0].spotify_id == "spotify_id_1"
    assert candidates[0].confidence == 1.0
```

- [ ] **Step 2: Ejecutar tests para verificar que fallan**

```bash
python -m pytest tests/test_song_metadata.py -v -k "spotify"
```

Salida esperada: `AttributeError: module 'song_metadata' has no attribute 'SpotifyClient'`

- [ ] **Step 3: Implementar `SpotifyClient` en `song_metadata.py`**

Agregar después del dataclass `SongCandidate`:

```python
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
```

- [ ] **Step 4: Ejecutar tests para verificar que pasan**

```bash
python -m pytest tests/test_song_metadata.py -v -k "spotify"
```

Salida esperada: 3 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add song_metadata.py tests/test_song_metadata.py
git commit -m "feat: implementar SpotifyClient con caché de token"
```

---

### Task 4: Implementar get_song_metadata() con fallback a OpenAI

**Files:**
- Modify: `song_metadata.py`
- Modify: `tests/test_song_metadata.py`

- [ ] **Step 1: Agregar tests de `get_song_metadata` al final de `tests/test_song_metadata.py`**

```python
# Agregar al final de tests/test_song_metadata.py
import pytest
from song_metadata import get_song_metadata


def test_get_song_metadata_spotify_success():
    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "tok"}
    mock_token_resp.raise_for_status = MagicMock()

    mock_search_resp = MagicMock()
    mock_search_resp.json.return_value = {
        "tracks": {
            "items": [
                {
                    "id": "id1",
                    "name": "La Bamba",
                    "artists": [{"name": "Ritchie Valens"}],
                    "album": {"name": "Ritchie Valens"},
                }
            ]
        }
    }
    mock_search_resp.raise_for_status = MagicMock()

    song_metadata._spotify_client = None  # resetear singleton
    with patch("song_metadata.requests.post", return_value=mock_token_resp):
        with patch("song_metadata.requests.get", return_value=mock_search_resp):
            candidates = get_song_metadata("La Bamba")

    assert len(candidates) == 1
    assert candidates[0].song_name == "La Bamba"
    assert candidates[0].confidence == 1.0


def test_get_song_metadata_spotify_empty_falls_back_to_openai():
    """Spotify retorna 0 resultados → fallback silencioso a OpenAI."""
    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "tok"}
    mock_token_resp.raise_for_status = MagicMock()

    mock_search_resp = MagicMock()
    mock_search_resp.json.return_value = {"tracks": {"items": []}}
    mock_search_resp.raise_for_status = MagicMock()

    mock_openai_resp = MagicMock()
    mock_openai_resp.choices[0].message.content = json.dumps([
        {"song_name": "Canción Desconocida", "artist_name": "Artista Desconocido", "album": ""}
    ])

    song_metadata._spotify_client = None
    with patch("song_metadata.requests.post", return_value=mock_token_resp):
        with patch("song_metadata.requests.get", return_value=mock_search_resp):
            with patch("song_metadata.OpenAI") as MockOpenAI:
                MockOpenAI.return_value.chat.completions.create.return_value = mock_openai_resp
                candidates = get_song_metadata("xyzabc123")

    assert len(candidates) == 1
    assert candidates[0].song_name == "Canción Desconocida"
    assert candidates[0].spotify_id == ""
    assert candidates[0].confidence == 0.8


def test_get_song_metadata_spotify_exception_falls_back_to_openai():
    """Spotify lanza excepción → fallback a OpenAI."""
    mock_openai_resp = MagicMock()
    mock_openai_resp.choices[0].message.content = json.dumps([
        {"song_name": "Bohemian Rhapsody", "artist_name": "Queen", "album": "A Night at the Opera"}
    ])

    song_metadata._spotify_client = None
    with patch("song_metadata.requests.post", side_effect=Exception("connection error")):
        with patch("song_metadata.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.return_value = mock_openai_resp
            candidates = get_song_metadata("Bohemian Rhapsody")

    assert len(candidates) == 1
    assert candidates[0].song_name == "Bohemian Rhapsody"
    assert candidates[0].confidence == 0.8


def test_get_song_metadata_both_fail_raises():
    """Si tanto Spotify como OpenAI fallan, se propaga la excepción."""
    song_metadata._spotify_client = None
    with patch("song_metadata.requests.post", side_effect=Exception("spotify caído")):
        with patch("song_metadata.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.side_effect = Exception("openai caído")
            with pytest.raises(Exception):
                get_song_metadata("test")
```

- [ ] **Step 2: Ejecutar tests para verificar que fallan**

```bash
python -m pytest tests/test_song_metadata.py -v -k "get_song_metadata"
```

Salida esperada: `ImportError: cannot import name 'get_song_metadata'`

- [ ] **Step 3: Agregar `_openai_fallback()` y `get_song_metadata()` al final de `song_metadata.py`**

```python
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
```

- [ ] **Step 4: Ejecutar todos los tests de song_metadata**

```bash
python -m pytest tests/test_song_metadata.py -v
```

Salida esperada: 7 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add song_metadata.py tests/test_song_metadata.py
git commit -m "feat: implementar get_song_metadata con fallback a OpenAI"
```

---

### Task 5: Crear quick_search.py

**Files:**
- Create: `quick_search.py`
- Create: `tests/test_quick_search.py`

- [ ] **Step 1: Escribir tests de `search_links()`**

```python
# tests/test_quick_search.py
from unittest.mock import patch, MagicMock
from quick_search import search_links


def _yt_video(n: int) -> dict:
    return {
        "title": f"Video {n}",
        "link": f"https://www.youtube.com/watch?v=id{n}",
        "video_id": f"id{n}",
        "description": "",
        "channel_title": "Canal Test",
        "published_at": "2024-01-01T00:00:00Z",
    }


def _web_result(n: int) -> dict:
    return {
        "title": f"Resultado Web {n}",
        "link": f"https://example.com/result{n}",
        "snippet": "descripción de prueba",
        "displayed_link": f"example.com/result{n}",
        "position": n,
    }


def test_search_links_returns_correct_structure():
    yt_videos = [_yt_video(i) for i in range(3)]
    web_results = [_web_result(i) for i in range(3)]

    with patch("quick_search.YouTubeSearcher") as MockYT:
        MockYT.return_value._fetch_query_results.return_value = yt_videos
        with patch("quick_search.WebSearcher") as MockWeb:
            MockWeb.return_value._fetch_web_results.return_value = web_results
            result = search_links("Despacito", "Luis Fonsi")

    assert result["song"] == "Despacito"
    assert result["artist"] == "Luis Fonsi"
    assert len([l for l in result["links"] if l["type"] == "YouTube"]) == 3
    assert len([l for l in result["links"] if l["type"] == "Web"]) == 3


def test_search_links_uses_enriched_query():
    """Verifica que se usa la query combinada 'canción artista'."""
    with patch("quick_search.YouTubeSearcher") as MockYT:
        MockYT.return_value._fetch_query_results.return_value = []
        with patch("quick_search.WebSearcher") as MockWeb:
            MockWeb.return_value._fetch_web_results.return_value = []
            search_links("La Bamba", "Ritchie Valens")

    MockYT.return_value._fetch_query_results.assert_called_once_with(
        "La Bamba Ritchie Valens", max_per_query=10
    )
    MockWeb.return_value._fetch_web_results.assert_called_once_with(
        "La Bamba Ritchie Valens", num_results=10
    )


def test_search_links_youtube_failure_returns_web_only():
    web_results = [_web_result(i) for i in range(2)]

    with patch("quick_search.YouTubeSearcher") as MockYT:
        MockYT.return_value._fetch_query_results.side_effect = Exception("YouTube caído")
        with patch("quick_search.WebSearcher") as MockWeb:
            MockWeb.return_value._fetch_web_results.return_value = web_results
            result = search_links("test", "artista")

    assert len(result["links"]) == 2
    assert all(l["type"] == "Web" for l in result["links"])


def test_search_links_both_fail_returns_empty_links():
    with patch("quick_search.YouTubeSearcher") as MockYT:
        MockYT.return_value._fetch_query_results.side_effect = Exception("YT caído")
        with patch("quick_search.WebSearcher") as MockWeb:
            MockWeb.return_value._fetch_web_results.side_effect = Exception("SerpAPI caído")
            result = search_links("test", "artista")

    assert result["links"] == []
    assert result["song"] == "test"
    assert result["artist"] == "artista"
```

- [ ] **Step 2: Ejecutar tests para verificar que fallan**

```bash
python -m pytest tests/test_quick_search.py -v
```

Salida esperada: `ImportError: No module named 'quick_search'`

- [ ] **Step 3: Crear `quick_search.py`**

```python
# quick_search.py
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
```

- [ ] **Step 4: Ejecutar tests para verificar que pasan**

```bash
python -m pytest tests/test_quick_search.py -v
```

Salida esperada: 4 tests `PASSED`

- [ ] **Step 5: Ejecutar toda la suite**

```bash
python -m pytest tests/ -v
```

Salida esperada: 11 tests `PASSED` (7 song_metadata + 4 quick_search)

- [ ] **Step 6: Commit**

```bash
git add quick_search.py tests/test_quick_search.py
git commit -m "feat: implementar search_links en quick_search.py"
```

---

### Task 6: app.py — imports + session state + formulario único

**Files:**
- Modify: `app.py:13-17` (imports)
- Modify: `app.py:213-224` (initialize_session_state)
- Modify: `app.py:232-259` (display_search_form)

- [ ] **Step 1: Actualizar imports en `app.py` (líneas 13–17)**

Reemplazar el bloque de imports existente con:

```python
from youtube_search import YouTubeSearcher, format_youtube_results
from web_search import WebSearcher, format_web_results
from ai_analysis import AIAnalyzer, format_classification_display
from config import config
from pdf_generator import get_pdf_download_link
from login import show_login, logout
from song_metadata import get_song_metadata, SongCandidate
from quick_search import search_links
```

- [ ] **Step 2: Reemplazar `initialize_session_state()` (líneas 213–224)**

```python
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
```

- [ ] **Step 3: Reemplazar `display_search_form()` (líneas 232–259)**

```python
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
```

- [ ] **Step 4: Verificar que la app inicia sin errores de importación**

```bash
python -c "import app" 2>&1 | head -5
```

Salida esperada: sin errores (la importación de módulos Streamlit en modo CLI puede generar warnings menores, eso es normal).

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: reemplazar formulario doble con input único y actualizar session state"
```

---

### Task 7: app.py — run_quick_search() + display_quick_results()

**Files:**
- Modify: `app.py` — agregar dos funciones nuevas después de `display_search_form()`

- [ ] **Step 1: Agregar `run_quick_search()` después de `display_search_form()` en `app.py`**

```python
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
        for candidate in candidates:
            links_data = search_links(candidate.song_name, candidate.artist_name)
            quick_links.append(links_data)

        st.session_state.song_candidates = candidates
        st.session_state.quick_links = quick_links
        st.session_state.mode = 'quick_results'
        st.session_state.search_performed = False
        logger.info(
            f"Búsqueda rápida completada: '{user_query}' → {len(candidates)} candidato(s)"
        )
```

- [ ] **Step 2: Agregar `display_quick_results()` después de `run_quick_search()` en `app.py`**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: agregar run_quick_search y display_quick_results"
```

---

### Task 8: app.py — main(), fix PDF, reporte prominente, traducciones

**Files:**
- Modify: `app.py` — `main()`, `display_results()`, `display_summary()`, `display_result_cards()`, `display_sidebar()`

- [ ] **Step 1: Reemplazar `main()` (líneas 589–621)**

```python
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
```

- [ ] **Step 2: Actualizar la firma de `display_summary()` — agregar parámetro `ai_report`**

Reemplazar la línea de definición de `display_summary()` (línea 383):

```python
def display_summary(summary: Dict, song_name: str = "", artist_name: str = "",
                    high_risk: int = 0, medium_risk: int = 0,
                    youtube_count: int = 0, web_count: int = 0,
                    ai_report: str = ""):
```

- [ ] **Step 3: Corregir el bloque de descarga PDF dentro de `display_summary()` (alrededor de línea 433)**

Reemplazar el bloque `if song_name and artist_name:` completo (que incluye `col_download`, `col_spacer`, `summary_for_pdf` y el botón):

```python
    if song_name and artist_name:
        col_download, col_spacer = st.columns([1, 3])
        with col_download:
            try:
                summary_for_pdf = summary.copy()
                summary_for_pdf['high_risk_count'] = high_risk
                summary_for_pdf['medium_risk_count'] = medium_risk
                summary_for_pdf['ai_report'] = ai_report  # fix: incluir reporte en PDF
                pdf_bytes, filename = get_pdf_download_link(song_name, artist_name, summary_for_pdf)
                st.download_button(
                    label="⬇️ Descargar Reporte PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    width='stretch',
                    type="primary",
                )
            except Exception as e:
                logger.error(f"Error generando PDF: {e}")
                st.error("❌ Error al generar el PDF")
        st.markdown("---")
```

- [ ] **Step 4: Traducir etiquetas de métricas en `display_summary()` (alrededor de líneas 391–428)**

Reemplazar el bloque de métricas (desde `st.markdown("### 📈 Fuentes de Datos")` hasta antes del botón PDF):

```python
    # Métricas de fuentes de datos
    st.markdown("### 📈 Fuentes de Datos")
    col_sources = st.columns(3)
    with col_sources[0]:
        st.metric("Resultados de YouTube", youtube_count)
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
        st.metric("Covers", summary['category_counts'].get('cover', 0))
    with col3:
        st.metric("Resultados de Alto Riesgo", high_risk)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Uso Promocional", summary['category_counts'].get('promotional_usage', 0))
    with col5:
        st.metric("Riesgo Medio", medium_risk)
    with col6:
        st.metric("Referencias", summary['category_counts'].get('reference_only', 0))
```

- [ ] **Step 5: Reemplazar `display_results()` (líneas 346–381)**

```python
def display_results():
    """Mostrar los resultados del análisis profundo."""
    results = st.session_state.search_results

    if not results['youtube'] and not results['web']:
        st.info("🔍 No se encontraron resultados. Intenta con términos de búsqueda diferentes.")
        return

    # Reporte Ejecutivo de IA — siempre primero y prominente
    if results.get('ai_report'):
        st.markdown("---")
        st.markdown("## 🤖 Reporte Ejecutivo de IA")
        st.info(results['ai_report'])
        st.markdown("---")

    # Dashboard de métricas y descarga PDF
    if results['summary']:
        display_summary(
            results['summary'],
            results.get('song_name', 'Desconocida'),
            results.get('artist_name', 'Desconocido'),
            results.get('high_risk_count', 0),
            results.get('medium_risk_count', 0),
            results.get('youtube_count', 0),
            results.get('web_count', 0),
            results.get('ai_report', ''),  # nuevo parámetro para PDF
        )

    if results['youtube']:
        st.markdown("## 📺 Resultados de YouTube")
        display_result_cards(results['youtube'], 'youtube')

    if results['web']:
        st.markdown("## 🌐 Resultados de la Web")
        display_result_cards(results['web'], 'web')
```

- [ ] **Step 6: Traducir "AI Analysis:" en `display_result_cards()` (alrededor de línea 540)**

Reemplazar la línea dentro del HTML template de la tarjeta:

```python
# Buscar esta línea en display_result_cards():
#   <strong>🤖 AI Analysis:</strong> {safe_reasoning}
# Reemplazar con:
#   <strong>🤖 Análisis de IA:</strong> {safe_reasoning}
```

El bloque completo de markdown a actualizar (dentro del `st.markdown(f"""...""")`):

```python
                <div class="ai-reasoning">
                    <strong>🤖 Análisis de IA:</strong> {safe_reasoning}
                </div>
```

- [ ] **Step 7: Agregar Spotify al estado de APIs en `display_sidebar()` (alrededor de línea 575)**

Reemplazar el bloque de estado de APIs:

```python
    st.sidebar.markdown("## ⚙️ Configuración")
    st.sidebar.markdown("""
**Estado de las APIs:**
✅ API de YouTube
✅ API de SerpAPI
✅ API de OpenAI
✅ API de Spotify
""")
```

- [ ] **Step 8: Prueba manual completa end-to-end**

```bash
streamlit run app.py
```

Verificar el flujo completo:
1. Iniciar sesión con credenciales existentes
2. Ingresar "Despacito" → clic en "🔍 Buscar"
3. Verificar que aparecen 1–3 tarjetas con canción/artista/álbum y links
4. Verificar que cada tarjeta muestra hasta 10 videos YouTube y 10 resultados web
5. Clic en "🔬 Ejecutar Análisis Profundo" en una tarjeta
6. Verificar que aparece el **Reporte Ejecutivo de IA** en caja azul prominente
7. Verificar que el botón "⬇️ Descargar Reporte PDF" genera un PDF que incluye el reporte ejecutivo
8. Verificar que todas las etiquetas de la UI están en español latinoamericano

- [ ] **Step 9: Commit final**

```bash
git add app.py
git commit -m "feat: flujo dual completo — quick search, análisis profundo con reporte prominente y PDF corregido"
```
