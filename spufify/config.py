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
    SAMPLE_RATE = 48000  # Changed to 48000 to match Windows WASAPI native rate
    CHANNELS = 2
    BLOCK_SIZE = 1  # Small block for low latency (larger values cause distortion)
    
    # Output Format (mp3, flac, wav)
    OUTPUT_FORMAT = "flac"
    
    # Paths
    OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Music", "Spufify")
    
    # Logic
    SILENCE_THRESHOLD_DB = -50
    MIN_SILENCE_DURATION_SEC = 2.0
    
    # Audio Device ID (full string name from soundcard)
    AUDIO_DEVICE_ID = None 

    @classmethod
    def load_settings(cls):
        settings_path = os.path.join(cls.OUTPUT_DIR, "settings.json") # Save inside Spufify folder for portability? Or User Home? Let's use OUTPUT_DIR parent? No, AppData or Home.
        # Let's use Config.OUTPUT_DIR for now as it's the main folder user sees.
        settings_path = os.path.join(os.path.dirname(cls.OUTPUT_DIR), ".spufify_settings.json")
        
        if os.path.exists(settings_path):
            try:
                import json
                with open(settings_path, 'r') as f:
                    data = json.load(f)
                    
                cls.SAMPLE_RATE = data.get("SAMPLE_RATE", cls.SAMPLE_RATE)
                cls.CHANNELS = data.get("CHANNELS", cls.CHANNELS)
                cls.BLOCK_SIZE = data.get("BLOCK_SIZE", cls.BLOCK_SIZE)
                cls.OUTPUT_FORMAT = data.get("OUTPUT_FORMAT", cls.OUTPUT_FORMAT)
                cls.OUTPUT_DIR = data.get("OUTPUT_DIR", cls.OUTPUT_DIR)
                cls.SILENCE_THRESHOLD_DB = data.get("SILENCE_THRESHOLD_DB", cls.SILENCE_THRESHOLD_DB)
                cls.MIN_SILENCE_DURATION_SEC = data.get("MIN_SILENCE_DURATION_SEC", cls.MIN_SILENCE_DURATION_SEC)
                cls.AUDIO_DEVICE_ID = data.get("AUDIO_DEVICE_ID", cls.AUDIO_DEVICE_ID)
                
                # Ensure directories if output dir changed
                cls.ensure_directories()
            except Exception as e:
                print(f"[Config] Error loading settings: {e}")

    @classmethod
    def save_settings(cls):
        settings_path = os.path.join(os.path.dirname(cls.OUTPUT_DIR), ".spufify_settings.json")
        try:
            import json
            data = {
                "SAMPLE_RATE": cls.SAMPLE_RATE,
                "CHANNELS": cls.CHANNELS,
                "BLOCK_SIZE": cls.BLOCK_SIZE,
                "OUTPUT_FORMAT": cls.OUTPUT_FORMAT,
                "OUTPUT_DIR": cls.OUTPUT_DIR,
                "SILENCE_THRESHOLD_DB": cls.SILENCE_THRESHOLD_DB,
                "MIN_SILENCE_DURATION_SEC": cls.MIN_SILENCE_DURATION_SEC,
                "AUDIO_DEVICE_ID": cls.AUDIO_DEVICE_ID
            }
            with open(settings_path, 'w') as f:
                json.dump(data, f, indent=4)
            print("[Config] Settings saved.")
        except Exception as e:
            print(f"[Config] Error saving settings: {e}")

    @staticmethod
    def ensure_directories():
        if not os.path.exists(Config.OUTPUT_DIR):
            os.makedirs(Config.OUTPUT_DIR)

# Load settings on module import (after definition)
Config.load_settings()
