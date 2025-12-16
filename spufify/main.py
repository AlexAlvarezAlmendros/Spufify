import os
import sys
import logging

print("Loading Spufify modules...")

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
# Monkeypatch for soundcard compatibility with Numpy 2.0+
# FORCE replace because Numpy 2.0 still has fromstring but it errors on binary data
np.fromstring = np.frombuffer

# Ensure cache path is writable and absolute
os.environ["SPOTIPY_CACHE_PATH"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".spotify_cache")

from spufify.config import Config
from spufify.core.controller import Controller
from spufify.core.recorder import Recorder
from spufify.ui.dashboard import Dashboard
import subprocess
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_ffmpeg():
    """Verify FFmpeg is available in PATH"""
    if not shutil.which('ffmpeg'):
        logger.error("FFmpeg not found in PATH. Please install FFmpeg and add it to system PATH.")
        return False
    logger.info("FFmpeg found.")
    return True

def check_spotify_credentials():
    """Verify Spotify credentials are configured"""
    if not Config.SPOTIPY_CLIENT_ID or not Config.SPOTIPY_CLIENT_SECRET:
        logger.error("Spotify credentials not configured. Please create a .env file with SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET.")
        return False
    logger.info("Spotify credentials configured.")
    return True

def main():
    try:
        logger.info("Spufify starting...")
        
        # Pre-flight checks
        if not check_ffmpeg():
            input("Press Enter to exit...")
            return
        
        if not check_spotify_credentials():
            input("Press Enter to exit...")
            return
        
        Config.ensure_directories()
        
        # 1. Initialize Core
        recorder = Recorder()
        controller = Controller(recorder_ref=recorder)
        
        # Start Recorder Thread (starts paused)
        recorder.start_capture_thread()
        
        # 2. Initialize UI
        app = Dashboard(controller)
        
        # Handle graceful exit
        def on_closing():
            logger.info("Shutting down...")
            try:
                controller.stop()
                recorder.recording = False
                recorder.paused = True
                # Give threads time to cleanup
                import time
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
            finally:
                app.destroy()
        
        app.protocol("WM_DELETE_WINDOW", on_closing)
        
        app.mainloop()
    except Exception as e:
        logger.critical(f"CRITICAL ERROR: {e}", exc_info=True)

if __name__ == "__main__":
    main()
