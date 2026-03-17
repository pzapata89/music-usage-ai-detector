"""
YouTube search module for Music Usage AI Detector.
Handles YouTube Data API integration to search for videos.
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional
import logging

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
    
    def search_videos(self, song_name: str, artist_name: str, max_results: int = 10) -> List[Dict]:
        """
        Search YouTube for videos related to a song and artist.
        
        Args:
            song_name: Name of the song to search for
            artist_name: Name of the artist to search for
            max_results: Maximum number of results to return (default: 10)
            
        Returns:
            List of dictionaries containing video information
            
        Raises:
            HttpError: If YouTube API request fails
        """
        # Construct search query
        query = f"{song_name} {artist_name}"
        
        try:
            # Execute search request
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=max_results,
                type='video',
                order='relevance'
            ).execute()
            
            # Process results
            videos = []
            for item in search_response['items']:
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
            
            logger.info(f"Found {len(videos)} YouTube videos for query: {query}")
            return videos
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise Exception(f"YouTube API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during YouTube search: {e}")
            raise
    
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
