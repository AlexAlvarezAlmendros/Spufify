import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Spotify Credentials (to be loaded from env or user input)
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID", "")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "")
    SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    
    # Audio Settings
    # 48000Hz is the standard for Windows Audio Engine (WASAPI) shared mode.
    # Using 44100Hz causes resampling artifacts or robotic sound on loopback.
    SAMPLE_RATE = 44100
    CHANNELS = 2
    BLOCK_SIZE = 2048
    
    # Output Format (mp3, flac, wav)
    OUTPUT_FORMAT = "flac"
    
    # Paths
    OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Music", "Spufify")
    
    # Logic
    SILENCE_THRESHOLD_DB = -50
    MIN_SILENCE_DURATION_SEC = 2.0
    
    @staticmethod
    def ensure_directories():
        if not os.path.exists(Config.OUTPUT_DIR):
            os.makedirs(Config.OUTPUT_DIR)
