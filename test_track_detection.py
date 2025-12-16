"""
Quick test to verify track change detection is working
Run this while playing Spotify and changing songs
"""
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spufify.api.spotify import SpotifyClient
from spufify.config import Config

print("=" * 60)
print("TRACK CHANGE DETECTION TEST")
print("=" * 60)
print("\nPlay a song in Spotify, then skip to the next one...")
print("Press Ctrl+C to stop\n")

try:
    spotify = SpotifyClient()
    last_track_id = None
    
    while True:
        track = spotify.get_current_track()
        
        if track:
            if track['is_ad']:
                print(f"[AD] Advertisement detected")
            elif not track['is_playing']:
                print(f"[PAUSED] {track['title']}")
            else:
                current_id = track['track_id']
                
                if current_id != last_track_id:
                    if last_track_id is not None:
                        print(f"\n✓ TRACK CHANGED!")
                    print(f"[NOW PLAYING] {track['artist']} - {track['title']}")
                    print(f"  Track ID: {current_id}")
                    last_track_id = current_id
                else:
                    # Same track, just show progress
                    progress = track['progress_ms'] / 1000
                    duration = track['duration_ms'] / 1000
                    print(f"  Progress: {progress:.0f}s / {duration:.0f}s", end='\r')
        else:
            print("[IDLE] No music playing", end='\r')
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n\nTest stopped.")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
