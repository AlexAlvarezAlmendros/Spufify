import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import os
import logging
from spufify.config import Config

logger = logging.getLogger(__name__)

class SpotifyClient:
    def __init__(self):
        # We need a scope that allows reading playback state
        self.scope = "user-read-playback-state user-read-currently-playing"
        self.retry_count = 0
        self.max_retries = 3
        
        # Initialize Spotipy
        # Note: In a real app we might need to handle the browser auth flow gracefully.
        # For now, we assume standard flow with a redirect URI (e.g., http://localhost:8888/callback)
        try:
            cache_handler = spotipy.CacheFileHandler(cache_path=os.path.join(Config.OUTPUT_DIR, '.spotify_token_cache'))
            
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=Config.SPOTIPY_CLIENT_ID,
                client_secret=Config.SPOTIPY_CLIENT_SECRET,
                redirect_uri=Config.SPOTIPY_REDIRECT_URI,
                scope=self.scope,
                cache_handler=cache_handler,
                open_browser=True # Allow browser auth on first run
            ))
            logger.info("Spotify client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            raise

    def get_current_track(self):
        """
        Fetches current playback info.
        Returns a dict with relevant metadata or None if nothing playing.
        """
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
