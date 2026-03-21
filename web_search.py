"""
Web search module for Music Usage AI Detector.
Handles SerpAPI integration to search Google results.
"""

import requests
import json
from typing import List, Dict, Optional, Set
import logging
import time

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
    
    def search_web(self, song_name: str, artist_name: str, max_results: int = 60) -> List[Dict]:
        """
        Search Google using multiple query variations with SerpAPI.
        
        Args:
            song_name: Name of the song to search for
            artist_name: Name of the artist to search for
            max_results: Maximum number of unique results to return (default: 60)
            
        Returns:
            List of dictionaries containing search result information (deduplicated)
        """
        # Query variations to detect different types of usage
        query_variations = [
            f"{song_name} {artist_name}",
            f"{song_name} {artist_name} cover",
            f"{song_name} {artist_name} lyrics",
            f"{song_name} {artist_name} meaning",
            f"{song_name} {artist_name} review",
            f"{song_name} {artist_name} live performance",
            f"{song_name} {artist_name} remix"
        ]
        
        all_results = []
        seen_urls: Set[str] = set()
        seen_titles: Set[str] = set()
        
        logger.info(f"Starting multi-query web search for '{song_name}' by '{artist_name}'")
        logger.info(f"Will execute {len(query_variations)} query variations")
        
        for query_index, query in enumerate(query_variations, 1):
            try:
                logger.info(f"Web query {query_index}/{len(query_variations)}: {query}")
                
                # Fetch results for this query
                query_results = self._fetch_web_results(query, num_results=20)
                
                # Deduplicate and add new results
                new_count = 0
                for result in query_results:
                    url = result.get('link', '').strip()
                    title = result.get('title', '').lower().strip()
                    
                    # Skip if we've seen this URL
                    if url in seen_urls:
                        continue
                    
                    # Skip if we've seen a very similar title
                    if self._is_similar_web_title(title, seen_titles):
                        continue
                    
                    # Add to results
                    seen_urls.add(url)
                    seen_titles.add(title)
                    all_results.append(result)
                    new_count += 1
                    
                    # Check if we've reached max results
                    if len(all_results) >= max_results:
                        logger.info(f"Reached target of {max_results} unique web results")
                        break
                
                logger.info(f"Web query {query_index}: Found {new_count} new unique results (Total: {len(all_results)})")
                
                # Rate limit protection - wait between queries
                if query_index < len(query_variations) and len(all_results) < max_results:
                    time.sleep(0.5)
                
                # Break if we have enough results
                if len(all_results) >= max_results:
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"SerpAPI request error for query '{query}': {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error for web query '{query}': {e}")
                continue
        
        logger.info(f"Web search complete: {len(all_results)} unique results found")
        return all_results
    
    def _fetch_web_results(self, query: str, num_results: int = 20) -> List[Dict]:
        """
        Fetch web results for a single query from SerpAPI.
        
        Args:
            query: Search query string
            num_results: Number of results to fetch
            
        Returns:
            List of result dictionaries
        """
        params = {
            'api_key': self.api_key,
            'engine': 'google',
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

            return results

        except Exception as e:
            # Avoid logging the full exception as it may contain the API key in the URL
            status = getattr(getattr(e, 'response', None), 'status_code', 'N/A')
            logger.error(f"Error fetching web results: {type(e).__name__} status={status}")
            return []
    
    def _is_similar_web_title(self, title: str, seen_titles: Set[str]) -> bool:
        """
        Check if a web title is similar to already seen titles.
        
        Args:
            title: Title to check
            seen_titles: Set of previously seen titles
            
        Returns:
            True if similar title found, False otherwise
        """
        # Normalize title
        normalized = title.lower().strip()
        
        # Direct match
        if normalized in seen_titles:
            return True
        
        # Check similarity with seen titles
        for seen in seen_titles:
            if self._calculate_title_similarity(normalized, seen) > 0.85:
                return True
        
        return False
    
    def _calculate_title_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two title strings.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not str1 or not str2:
            return 0.0
        
        # Character-based similarity
        set1 = set(str1)
        set2 = set(str2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
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
            # Avoid logging the full exception as it may contain the API key in the URL
            status = getattr(getattr(e, 'response', None), 'status_code', 'N/A')
            logger.error(f"SerpAPI news search error: {type(e).__name__} status={status}")
            raise Exception(f"SerpAPI news search failed")
        except Exception as e:
            logger.error(f"Unexpected error during news search: {type(e).__name__}")
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
