"""
Web search module for Music Usage AI Detector.
Handles SerpAPI integration to search Google results.
"""

import requests
import json
from typing import List, Dict, Optional
import logging

from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSearcher:
    """SerpAPI wrapper for searching Google results."""
    
    def __init__(self):
        """Initialize SerpAPI client."""
        self.api_key = config.serpapi_api_key
        self.base_url = "https://serpapi.com/search"
        logger.info("SerpAPI client initialized successfully")
    
    def search_web(self, song_name: str, artist_name: str, num_results: int = 10) -> List[Dict]:
        """
        Search Google for results related to a song and artist.
        
        Args:
            song_name: Name of the song to search for
            artist_name: Name of the artist to search for
            num_results: Number of results to return (default: 10)
            
        Returns:
            List of dictionaries containing search result information
            
        Raises:
            Exception: If SerpAPI request fails
        """
        # Construct search query
        query = f"{song_name} {artist_name}"
        
        # Parameters for SerpAPI
        params = {
            'api_key': self.api_key,
            'engine': 'google',
            'q': query,
            'num': num_results,
            'hl': 'en',
            'gl': 'us'
        }
        
        try:
            # Make API request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # Parse JSON response
            search_results = response.json()
            
            # Process organic results
            results = []
            if 'organic_results' in search_results:
                for result in search_results['organic_results']:
                    result_info = {
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'snippet': result.get('snippet', ''),
                        'displayed_link': result.get('displayed_link', ''),
                        'position': result.get('position', 0)
                    }
                    results.append(result_info)
            
            logger.info(f"Found {len(results)} web results for query: {query}")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SerpAPI request error: {e}")
            raise Exception(f"SerpAPI request failed: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing SerpAPI response: {e}")
            raise Exception(f"Failed to parse search results: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during web search: {e}")
            raise
    
    def search_news(self, song_name: str, artist_name: str, num_results: int = 5) -> List[Dict]:
        """
        Search Google News for articles related to a song and artist.
        
        Args:
            song_name: Name of the song to search for
            artist_name: Name of the artist to search for
            num_results: Number of news results to return (default: 5)
            
        Returns:
            List of dictionaries containing news result information
        """
        query = f"{song_name} {artist_name}"
        
        params = {
            'api_key': self.api_key,
            'engine': 'google_news',
            'q': query,
            'num': num_results,
            'hl': 'en',
            'gl': 'us'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            search_results = response.json()
            
            results = []
            if 'news_results' in search_results:
                for result in search_results['news_results']:
                    result_info = {
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'snippet': result.get('snippet', ''),
                        'source': result.get('source', ''),
                        'date': result.get('date', ''),
                        'position': result.get('position', 0)
                    }
                    results.append(result_info)
            
            logger.info(f"Found {len(results)} news results for query: {query}")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SerpAPI news search error: {e}")
            raise Exception(f"SerpAPI news search failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during news search: {e}")
            raise

def format_web_results(results: List[Dict]) -> List[Dict]:
    """
    Format web search results for display in the UI.
    
    Args:
        results: List of search result information from SerpAPI
        
    Returns:
        Formatted list of search results
    """
    formatted_results = []
    
    for result in results:
        formatted_result = {
            'title': result['title'],
            'link': result['link'],
            'description': result['snippet'][:200] + '...' if len(result['snippet']) > 200 else result['snippet'],
            'source': 'Web',
            'displayed_link': result.get('displayed_link', result['link']),
            'position': result.get('position', 0)
        }
        
        # Add additional fields if available (for news results)
        if 'source' in result and result['source']:
            formatted_result['news_source'] = result['source']
        if 'date' in result and result['date']:
            formatted_result['date'] = result['date']
        
        formatted_results.append(formatted_result)
    
    return formatted_results
