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
