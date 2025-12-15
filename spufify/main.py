import os
import sys
print("Loading Spufify modules...")

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
# Monkeypatch for soundcard compatibility with Numpy 2.0+
# FORCE replace because Numpy 2.0 still has fromstring but it errors on binary data
np.fromstring = np.frombuffer

import os
# Ensure cache path is writable and absolute
os.environ["SPOTIPY_CACHE_PATH"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".spotify_cache")

from spufify.config import Config
from spufify.core.controller import Controller
from spufify.core.recorder import Recorder
from spufify.ui.dashboard import Dashboard

def main():
    try:
        print("Spufify starting...")
        Config.ensure_directories()
        
        # 1. Initialize Core
        recorder = Recorder()
        controller = Controller(recorder_ref=recorder)
        
        # Start Recorder Thread (starts paused)
        recorder.start_capture_thread()
        
        # 2. Initialize UI
        app = Dashboard(controller)
        
        # Handle graceful exit
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        app.mainloop()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
