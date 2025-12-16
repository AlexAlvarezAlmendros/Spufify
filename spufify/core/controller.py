import time
import threading
import logging
from spufify.api.spotify import SpotifyClient
from spufify.config import Config
# from spufify.core.recorder import Recorder # formatting circular dependency, will handle with signals or injection

logger = logging.getLogger(__name__)

class Controller:
    """
    Module B: The Brain
    Manages the state of the application based on Spotify status.
    """
    
    STATES = ["WAITING", "RECORDING", "PAUSED", "PROCESSING"]

    def __init__(self, recorder_ref=None, ui_callback_ref=None):
        self.spotify = SpotifyClient()
        self.recorder = recorder_ref
        self.ui_callback = ui_callback_ref
        
        self.state = "WAITING"
        self.current_track = None
        self.last_poll_time = 0
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._ev_loop, daemon=True)
        self.thread.start()
        logger.info("Controller started, polling Spotify API every 1 second.")

    def stop(self):
        logger.info("Stopping controller...")
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            if self.thread.is_alive():
                logger.warning("Controller thread did not stop cleanly")
        logger.info("Controller stopped.")

    def _ev_loop(self):
        while self.running:
            self.tick()
            time.sleep(1) # Poll interval
            
    def tick(self):
        try:
            track_info = self.spotify.get_current_track()
            
            # Send info to UI if callback exists
            if self.ui_callback:
                status_pkg = {
                    'state': self.state,
                    'track': track_info
                }
                try:
                    self.ui_callback(status_pkg)
                except Exception as e:
                    logger.error(f"Error in UI callback: {e}")

            if not track_info:
                self._handle_no_music()
                return

            if track_info['is_ad']:
                self._handle_ad()
            elif not track_info['is_playing']:
                self._handle_paused_playback()
            else:
                self._handle_playing_track(track_info)

        except Exception as e:
            logger.error(f"Controller tick error: {e}", exc_info=True)

    def _set_state(self, new_state):
        if self.state != new_state:
            logger.info(f"State Change: {self.state} -> {new_state}")
            self.state = new_state
            
            # Notify Recorder
            if self.recorder:
                try:
                    if new_state == "RECORDING":
                        self.recorder.resume_recording()
                    elif new_state == "PAUSED":
                        self.recorder.pause_recording()
                    elif new_state == "WAITING":
                        self.recorder.stop_recording()
                except Exception as e:
                    logger.error(f"Error notifying recorder of state change: {e}")

    def _handle_no_music(self):
        if self.state != "WAITING":
            self._set_state("WAITING")

    def _handle_ad(self):
        if self.state == "RECORDING":
            self._set_state("PAUSED")
            
    def _handle_paused_playback(self):
         if self.state == "RECORDING":
            self._set_state("PAUSED")

    def _handle_playing_track(self, track_info):
        # If we were waiting or paused, start recording
        if self.state in ["WAITING", "PAUSED"]:
            self.current_track = track_info
            # If we were WAITING, we might need to initialize a new session
            # For now, simple transition
            self._set_state("RECORDING")
            if self.recorder:
                # Provide metadata for tagging
                self.recorder.set_current_metadata(track_info)

        # If currently recording, check if track changed
        elif self.state == "RECORDING":
            if self.current_track and track_info['track_id'] != self.current_track['track_id']:
                logger.info(f"Track Changed: {self.current_track['title']} -> {track_info['title']}")
                # Finish previous
                if self.recorder:
                    try:
                        logger.debug("Calling recorder.finish_track()...")
                        self.recorder.finish_track() # Saves the file
                        logger.debug("finish_track() completed")
                    except Exception as e:
                        logger.error(f"Error finishing track: {e}", exc_info=True)
                
                # Start new
                self.current_track = track_info
                if self.recorder:
                    self.recorder.set_current_metadata(track_info)
                    self.recorder.resume_recording() # Ensure we are recording
            else:
                # Same track still playing - this is normal
                pass
