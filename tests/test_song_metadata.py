from song_metadata import SongCandidate
import json
import song_metadata
from unittest.mock import patch, MagicMock


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
