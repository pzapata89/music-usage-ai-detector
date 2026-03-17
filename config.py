"""
Configuration module for Music Usage AI Detector.
Handles API key loading and configuration settings.
"""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for API keys and settings."""
    
    def __init__(self):
        self.youtube_api_key = self._get_api_key("YOUTUBE_API_KEY")
        self.serpapi_api_key = self._get_api_key("SERPAPI_API_KEY")
        self.openai_api_key = self._get_api_key("OPENAI_API_KEY")
    
    def _get_api_key(self, key_name: str) -> str:
        """
        Get API key from environment variables.
        
        Args:
            key_name: Name of the environment variable
            
        Returns:
            API key string
            
        Raises:
            ValueError: If API key is not found
        """
        api_key = os.getenv(key_name)
        if not api_key:
            raise ValueError(
                f"API key '{key_name}' not found in environment variables. "
                f"Please set it in your .env file or environment."
            )
        return api_key
    
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

# Global configuration instance
config = Config()
