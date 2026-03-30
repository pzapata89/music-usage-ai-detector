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
