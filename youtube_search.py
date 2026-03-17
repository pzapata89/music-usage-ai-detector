"""
YouTube search module for Music Usage AI Detector.
Handles YouTube Data API integration to search for videos.
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional, Set
import logging
import time

from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeSearcher:
    """YouTube API wrapper for searching videos."""
    
    def __init__(self):
        """Initialize YouTube API client."""
        try:
            self.youtube = build('youtube', 'v3', developerKey=config.youtube_api_key)
            logger.info("YouTube API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API client: {e}")
            raise
    
    def search_videos(self, song_name: str, artist_name: str, max_results: int = 100) -> List[Dict]:
        """
        Search YouTube for videos using multiple query variations with pagination.
        
        Args:
            song_name: Name of the song to search for
            artist_name: Name of the artist to search for
            max_results: Maximum number of unique results to return (default: 100)
            
        Returns:
            List of dictionaries containing video information (deduplicated)
        """
        # Query variations to detect different types of usage
        query_variations = [
            f"{song_name} {artist_name}",
            f"{song_name} {artist_name} cover",
            f"{song_name} {artist_name} live",
            f"{song_name} {artist_name} performance",
            f"{song_name} {artist_name} remix",
            f"{song_name} {artist_name} karaoke",
            f"{song_name} {artist_name} band"
        ]
        
        all_videos = []
        seen_video_ids: Set[str] = set()
        seen_titles: Set[str] = set()
        
        logger.info(f"Starting multi-query YouTube search for '{song_name}' by '{artist_name}'")
        logger.info(f"Will execute {len(query_variations)} query variations")
        
        for query_index, query in enumerate(query_variations, 1):
            try:
                logger.info(f"Query {query_index}/{len(query_variations)}: {query}")
                
                # Fetch results for this query with pagination
                query_results = self._fetch_query_results(query, max_per_query=50)
                
                # Deduplicate and add new results
                new_count = 0
                for video in query_results:
                    video_id = video.get('video_id')
                    title = video.get('title', '').lower().strip()
                    
                    # Skip if we've seen this video ID
                    if video_id in seen_video_ids:
                        continue
                    
                    # Skip if we've seen a very similar title (fuzzy dedup)
                    if self._is_similar_title(title, seen_titles):
                        continue
                    
                    # Add to results
                    seen_video_ids.add(video_id)
                    seen_titles.add(title)
                    all_videos.append(video)
                    new_count += 1
                    
                    # Check if we've reached max results
                    if len(all_videos) >= max_results:
                        logger.info(f"Reached target of {max_results} unique videos")
                        break
                
                logger.info(f"Query {query_index}: Found {new_count} new unique videos (Total: {len(all_videos)})")
                
                # Rate limit protection - wait between queries
                if query_index < len(query_variations) and len(all_videos) < max_results:
                    time.sleep(1)
                
                # Break if we have enough results
                if len(all_videos) >= max_results:
                    break
                    
            except HttpError as e:
                logger.error(f"YouTube API error for query '{query}': {e}")
                # Continue with next query - don't fail completely
                continue
            except Exception as e:
                logger.error(f"Unexpected error for query '{query}': {e}")
                continue
        
        logger.info(f"YouTube search complete: {len(all_videos)} unique videos found")
        return all_videos
    
    def _fetch_query_results(self, query: str, max_per_query: int = 50) -> List[Dict]:
        """
        Fetch results for a single query with pagination.
        
        Args:
            query: Search query string
            max_per_query: Maximum results to fetch per query
            
        Returns:
            List of video dictionaries
        """
        videos = []
        next_page_token = None
        pages_fetched = 0
        max_pages = 2  # Limit to 2 pages per query (100 max results)
        
        while len(videos) < max_per_query and pages_fetched < max_pages:
            try:
                # Build request
                request_params = {
                    'q': query,
                    'part': 'id,snippet',
                    'maxResults': min(50, max_per_query - len(videos)),
                    'type': 'video',
                    'order': 'relevance'
                }
                
                if next_page_token:
                    request_params['pageToken'] = next_page_token
                
                # Execute search
                search_response = self.youtube.search().list(**request_params).execute()
                
                # Process results
                for item in search_response.get('items', []):
                    video_info = {
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'link': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                        'video_id': item['id']['videoId'],
                        'channel_title': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'thumbnail_url': item['snippet']['thumbnails']['default']['url']
                    }
                    videos.append(video_info)
                
                pages_fetched += 1
                
                # Check for next page
                next_page_token = search_response.get('nextPageToken')
                if not next_page_token:
                    break
                    
                # Small delay between pages
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching page {pages_fetched + 1}: {e}")
                break
        
        return videos
    
    def _is_similar_title(self, title: str, seen_titles: Set[str]) -> bool:
        """
        Check if a title is similar to already seen titles (fuzzy deduplication).
        
        Args:
            title: Title to check
            seen_titles: Set of previously seen titles
            
        Returns:
            True if similar title found, False otherwise
        """
        # Normalize title for comparison
        normalized = title.lower().strip()
        
        # Direct match
        if normalized in seen_titles:
            return True
        
        # Check for similar titles (remove common suffixes/prefixes)
        common_variations = [' (official video)', ' (official)', ' (music video)', 
                            ' (audio)', ' (lyrics)', ' - audio', ' - lyrics',
                            ' (hd)', ' [official]', ' (live)']
        
        base_title = normalized
        for variant in common_variations:
            base_title = base_title.replace(variant, '').strip()
        
        for seen in seen_titles:
            seen_base = seen
            for variant in common_variations:
                seen_base = seen_base.replace(variant, '').strip()
            
            # If base titles are very similar (80% match)
            if self._calculate_similarity(base_title, seen_base) > 0.8:
                return True
        
        return False
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate simple similarity between two strings.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not str1 or not str2:
            return 0.0
        
        # Simple character-based similarity
        set1 = set(str1)
        set2 = set(str2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary containing video details or None if not found
        """
        try:
            video_response = self.youtube.videos().list(
                part='statistics,contentDetails',
                id=video_id
            ).execute()
            
            if not video_response['items']:
                return None
            
            video = video_response['items'][0]
            return {
                'view_count': int(video['statistics'].get('viewCount', 0)),
                'like_count': int(video['statistics'].get('likeCount', 0)),
                'comment_count': int(video['statistics'].get('commentCount', 0)),
                'duration': video['contentDetails'].get('duration', '')
            }
            
        except HttpError as e:
            logger.error(f"Error fetching video details for {video_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching video details: {e}")
            return None

def format_youtube_results(videos: List[Dict]) -> List[Dict]:
    """
    Format YouTube results for display in the UI.
    
    Args:
        videos: List of video information from YouTube API
        
    Returns:
        Formatted list of video results
    """
    formatted_results = []
    
    for video in videos:
        formatted_result = {
            'title': video['title'],
            'link': video['link'],
            'description': video['description'][:200] + '...' if len(video['description']) > 200 else video['description'],
            'source': 'YouTube',
            'channel': video['channel_title'],
            'published_at': video['published_at'],
            'video_id': video['video_id']
        }
        formatted_results.append(formatted_result)
    
    return formatted_results
