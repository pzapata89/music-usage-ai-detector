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
