"""
Configuration module for Music Usage AI Detector.
Handles API key loading from environment variables and Streamlit Cloud secrets.
"""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file (for local development)
load_dotenv()

class Config:
    """Configuration class for API keys and settings."""
    
    def __init__(self):
        self.youtube_api_key = self._get_api_key("YOUTUBE_API_KEY")
        self.serpapi_api_key = self._get_api_key("SERPAPI_API_KEY")
        self.openai_api_key = self._get_api_key("OPENAI_API_KEY")
        self.spotify_client_id = self._get_api_key("SPOTIFY_CLIENT_ID")
        self.spotify_client_secret = self._get_api_key("SPOTIFY_CLIENT_SECRET")
        self.login_salt = self._get_api_key("LOGIN_SALT")
        self.login_users = self._get_login_users()
    
    def _get_api_key(self, key_name: str) -> str:
        """
        Get API key from environment variables or Streamlit secrets.
        
        Priority:
        1. Streamlit Cloud secrets (for deployment)
        2. Environment variables from .env file (for local development)
        
        Args:
            key_name: Name of the environment variable
            
        Returns:
            API key string
            
        Raises:
            ValueError: If API key is not found
        """
        api_key = None
        
        # Try Streamlit secrets first (for Streamlit Cloud deployment)
        try:
            import streamlit as st
            api_key = st.secrets.get(key_name)
        except Exception:
            pass
        
        # Fall back to environment variables (for local development)
        if not api_key:
            api_key = os.getenv(key_name)
        
        if not api_key:
            raise ValueError(
                f"API key '{key_name}' not found. "
                f"Please set it in Streamlit Cloud Secrets (for deployment) "
                f"or in your .env file (for local development)."
            )
        return api_key
    
    def _get_login_users(self) -> dict:
        """
        Carga el diccionario usuario->hash desde secrets o variables de entorno.
        Formato env: LOGIN_USER_SACVEN, LOGIN_USER_PEDRO, LOGIN_USER_INVITADO
        """
        users = {}
        user_keys = ['SACVEN', 'Pedro', 'Invitado']

        for username in user_keys:
            env_key = f"LOGIN_USER_{username.upper()}"
            value = None

            try:
                import streamlit as st
                value = st.secrets.get(env_key)
            except Exception:
                pass

            if not value:
                value = os.getenv(env_key)

            if value:
                users[username] = value

        return users

    @property
    def youtube_api_key(self) -> str:
        """Get YouTube API key."""
        return self._youtube_api_key
    
    @youtube_api_key.setter
    def youtube_api_key(self, value: str):
        self._youtube_api_key = value
    
    @property
    def serpapi_api_key(self) -> str:
        """Get SerpAPI key."""
        return self._serpapi_api_key
    
    @serpapi_api_key.setter
    def serpapi_api_key(self, value: str):
        self._serpapi_api_key = value
    
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key."""
        return self._openai_api_key

    @openai_api_key.setter
    def openai_api_key(self, value: str):
        self._openai_api_key = value

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

# Global configuration instance
config = Config()
