import os

# Deben estar antes de que cualquier import active Config()
os.environ.setdefault("YOUTUBE_API_KEY", "test_yt_key")
os.environ.setdefault("SERPAPI_API_KEY", "test_serp_key")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")
os.environ.setdefault("LOGIN_SALT", "test_salt")
os.environ.setdefault("SPOTIFY_CLIENT_ID", "test_spotify_id")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test_spotify_secret")
