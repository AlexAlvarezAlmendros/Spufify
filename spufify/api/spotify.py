import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import os
import logging
from spufify.config import Config

logger = logging.getLogger(__name__)

class SpotifyClient:
    def __init__(self, auto_authenticate=False):
        # We need a scope that allows reading playback state
        self.scope = "user-read-playback-state user-read-currently-playing"
        self.retry_count = 0
        self.max_retries = 3
        self.sp = None
        self.auth_manager = None
        
        # Initialize Spotipy
        # Note: In a real app we might need to handle the browser auth flow gracefully.
        # For now, we assume standard flow with a redirect URI (e.g., http://localhost:8888/callback)
        try:
            cache_handler = spotipy.CacheFileHandler(cache_path=os.path.join(Config.OUTPUT_DIR, '.spotify_token_cache'))
            
            self.auth_manager = SpotifyOAuth(
                client_id=Config.SPOTIPY_CLIENT_ID,
                client_secret=Config.SPOTIPY_CLIENT_SECRET,
                redirect_uri=Config.SPOTIPY_REDIRECT_URI,
                scope=self.scope,
                cache_handler=cache_handler,
                open_browser=auto_authenticate # Only open browser if explicitly requested
            )
            
            # Only initialize Spotify client if we have valid credentials
            if Config.SPOTIPY_CLIENT_ID and Config.SPOTIPY_CLIENT_SECRET:
                # Check if we have a valid cached token or if auto_authenticate is True
                if auto_authenticate or self.is_authenticated():
                    self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                    logger.info("Spotify client initialized successfully.")
                else:
                    logger.warning("Spotify client initialized but not authenticated. Please authenticate via Settings.")
            else:
                logger.warning("Spotify credentials not configured. Please set them in .env file.")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            # Don't raise - allow app to start without Spotify
    
    def is_authenticated(self):
        """Check if we have a valid cached token"""
        try:
            if not self.auth_manager:
                return False
            token_info = self.auth_manager.get_cached_token()
            return token_info is not None
        except Exception as e:
            logger.error(f"Error checking authentication: {e}")
            return False
    
    def authenticate(self):
        """Manually trigger authentication flow - opens browser"""
        try:
            if not self.auth_manager:
                raise Exception("Auth manager not initialized. Check your credentials in .env file.")
            
            # Force browser authentication
            self.auth_manager.open_browser = True
            token_info = self.auth_manager.get_access_token(as_dict=False)
            
            if token_info:
                self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                logger.info("Spotify authentication successful!")
                return True
            else:
                logger.error("Failed to get access token")
                return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def get_auth_url(self):
        """Get the authorization URL for manual authentication"""
        try:
            if not self.auth_manager:
                return None
            return self.auth_manager.get_authorize_url()
        except Exception as e:
            logger.error(f"Error getting auth URL: {e}")
            return None

    def get_current_track(self):
        """
        Fetches current playback info.
        Returns a dict with relevant metadata or None if nothing playing.
        """
        if not self.sp:
            logger.warning("Spotify client not initialized. Please authenticate via Settings.")
            return None
            
        for attempt in range(self.max_retries):
            try:
                current = self.sp.current_playback()
                
                # Reset retry counter on success
                self.retry_count = 0
                
                if not current or not current.get('item'):
                    return None

                # Check if it's an ad
                # Spotify API says 'currently_playing_type' can be 'track', 'episode', 'ad', 'unknown'
                track_type = current.get('currently_playing_type')
                is_playing = current.get('is_playing')
                
                if track_type == 'ad':
                    return {
                        'is_ad': True,
                        'is_playing': is_playing,
                        'title': 'Advertisement',
                        'artist': 'Spotify',
                    }

                item = current['item']
                artists = ", ".join([artist['name'] for artist in item['artists']])
                title = item['name']
                album = item['album']['name']
                cover_url = item['album']['images'][0]['url'] if item['album']['images'] else None
                duration_ms = item['duration_ms']
                progress_ms = current['progress_ms']
                track_id = item['id']

                return {
                    'is_ad': False,
                    'is_playing': is_playing,
                    'title': title,
                    'artist': artists,
                    'album': album,
                    'cover_url': cover_url,
                    'duration_ms': duration_ms,
                    'progress_ms': progress_ms,
                    'track_id': track_id
                }
            except spotipy.exceptions.SpotifyException as e:
                logger.warning(f"Spotify API error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch Spotify data after {self.max_retries} attempts")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error fetching Spotify data: {e}", exc_info=True)
                return None
