import soundcard as sc
import numpy as np
import threading
import time
import queue
import soundfile as sf
import os
import logging
import warnings
from spufify.config import Config
from spufify.core.processor import Processor

# Suppress soundcard discontinuity warnings (cosmetic, doesn't affect recording quality)
warnings.filterwarnings('ignore', category=sc.SoundcardRuntimeWarning, message='data discontinuity in recording')

logger = logging.getLogger(__name__)


class Recorder:
    """
    Module A: Audio Capture
    Captures loopback audio and manages buffers.
    """
    def __init__(self):
        self.recording = False
        self.paused = False
        self.buffer_queue = queue.Queue()
        self.capture_thread = None
        self.processing_thread = None
        self.current_metadata = None
        self.processor = Processor()
        
        # We'll use a temp file to store the raw WAV while recording a track
        self.current_temp_file = os.path.join(Config.OUTPUT_DIR, "temp_recording.wav")
        self._sf_file = None
        self._file_lock = threading.RLock()  # Reentrant lock for nested calls
        
        # Auto-detected audio parameters (will be set in _capture_loop)
        self.actual_sample_rate = Config.SAMPLE_RATE
        self.actual_channels = Config.CHANNELS

    def start_capture_thread(self):
        """Starts the background thread that reads from soundcard."""
        if self.capture_thread and self.capture_thread.is_alive():
            return
        
        self.recording = True # Keep thread alive
        self.paused = True # Start paused until Controller says resume
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Also start processing thread (writer)
        self.processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processing_thread.start()
        logger.info("Capture threads started.")

    def resume_recording(self):
        # Always try to open a new file when resuming
        self._open_wav_file()
        self.paused = False
        logger.info("Recording resumed.")

    def pause_recording(self):
        self.paused = True
        logger.info("Recording paused.")

    def stop_recording(self):
        self.paused = True
        # Don't kill thread, just wait in paused state usually, 
        # but for full stop we can set recording=False
        pass

    def restart_audio_engine(self):
        """
        Restarts the capture and processing threads to apply new settings (Device, Sample Rate, etc.)
        """
        logger.info("Restarting audio engine...")
        self.recording = False
        self.paused = True
        
        # Wait for threads to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
            if self.capture_thread.is_alive():
                logger.warning("Capture thread did not terminate cleanly")
            
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
            if self.processing_thread.is_alive():
                logger.warning("Processing thread did not terminate cleanly")
            
        # Restart
        self.start_capture_thread()
        logger.info("Audio engine restarted successfully.")

    def set_current_metadata(self, metadata):
        self.current_metadata = metadata

    def finish_track(self):
        """
        Closes current WAV, triggers processing (Module C), and prepares for next.
        """
        logger.debug("finish_track() called - starting cleanup")
        self.pause_recording()
        
        # Give a moment for _process_loop to finish any pending writes
        time.sleep(0.15)
        
        # Clear the queue (don't try to write, too risky for deadlock)
        cleared = 0
        while not self.buffer_queue.empty():
            try:
                self.buffer_queue.get_nowait()
                cleared += 1
            except:
                break
        if cleared > 0:
            logger.debug(f"Cleared {cleared} pending chunks from queue")
        
        self._close_wav_file()
        logger.debug("finish_track() - file closed, processing...")
        
        if self.current_metadata:
            # TRIGGER MODULE C (Processor)
            # We rename temp to a specific temp name for this track to avoid collisions if next track starts fast
            
            temp_track_path = os.path.join(Config.OUTPUT_DIR, f"temp_{int(time.time())}.wav")
            
            if os.path.exists(self.current_temp_file):
                # Process all files regardless of size
                try:
                    file_size = os.path.getsize(self.current_temp_file)
                    
                    # Only skip completely empty files (0 bytes)
                    if file_size > 0:
                        try:
                            # Must verify file is closed before renaming
                            if self._sf_file and not self._sf_file.closed:
                                self._sf_file.close()
                                
                            os.rename(self.current_temp_file, temp_track_path)
                            # Offload to processor with actual sample rate
                            self.processor.process_track(temp_track_path, self.current_metadata, self.actual_sample_rate)
                            logger.info(f"Track handed off to processor: {self.current_metadata['title']} ({file_size/1024:.1f} KB)")
                        except Exception as e:
                            logger.error(f"Error handing off file: {e}", exc_info=True)
                    else:
                        logger.warning("File is empty (0 bytes), discarded.")
                except Exception as e:
                     logger.error(f"File check error: {e}", exc_info=True)
            
        # Ready for next
        pass

    def _open_wav_file(self):
        with self._file_lock:
            # Close any existing file first
            if self._sf_file:
                logger.debug("Closing existing file before opening new one")
                self._close_wav_file()
            
            try:
                # Use SoundFile to write 32-bit FLOAT WAV with auto-detected parameters
                self._sf_file = sf.SoundFile(
                    self.current_temp_file, 
                    mode='w', 
                    samplerate=self.actual_sample_rate,  # Use detected, not config
                    channels=self.actual_channels,        # Use detected, not config
                    subtype='FLOAT'
                )
                logger.info(f"✓ New WAV file opened: {self.actual_sample_rate}Hz, {self.actual_channels}ch")
            except Exception as e:
                logger.error(f"Error opening WAV: {e}", exc_info=True)

    def _close_wav_file(self):
        with self._file_lock:
            if self._sf_file:
                try:
                    self._sf_file.close()
                    logger.debug("WAV file closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing WAV file: {e}")
                finally:
                    self._sf_file = None

    def _detect_optimal_settings(self, device):
        """
        Auto-detect the optimal sample rate and channels for the device.
        Tests multiple configurations and returns the best working one.
        """
        # Priority order for sample rates (most common to least)
        test_rates = [48000, 44100, 96000, 192000, 32000, 22050, 16000]
        
        logger.info(f"Auto-detecting optimal settings for: {device.name}")
        
        # Get device channels (usually 2 for stereo)
        optimal_channels = min(device.channels, 2)  # Use 2 max, even if device supports more
        
        # Test sample rates
        for rate in test_rates:
            try:
                # Try to create a recorder with this sample rate
                with device.recorder(samplerate=rate, channels=optimal_channels) as rec:
                    # If we get here, this configuration works
                    logger.info(f"✓ Detected working configuration: {rate} Hz, {optimal_channels} channels")
                    return rate, optimal_channels
            except Exception as e:
                logger.debug(f"✗ {rate} Hz not supported: {e}")
                continue
        
        # Fallback to config values if nothing works
        logger.warning(f"Could not auto-detect, using config defaults: {Config.SAMPLE_RATE} Hz")
        return Config.SAMPLE_RATE, Config.CHANNELS

    def _capture_loop(self):
        # finding default loopback
        # NOTE: 'sc.get_microphone' with include_loopback=True on Windows often finds loopbacks.
        # But specifically we want the default system loopback.
        # id usually is a complex string.
        
        try:
            # Start recording with a block size
            # We assume default speaker loopback is desired.
            mic = sc.default_speaker() # This is sending audio TO speaker.
            # To record loopback, we often need sc.get_microphone(id=..., include_loopback=True)
            # sc.default_microphone() usually gives the physical mic.
            
            # For Windows Loopback via soundcard library:
            # We need to find the loopback device corresponding to default speaker.
            mics = sc.all_microphones(include_loopback=True)
            loopback_mic = None
            
            # 1. Try Configured Device
            if Config.AUDIO_DEVICE_ID:
                for m in mics:
                    if m.name == Config.AUDIO_DEVICE_ID:
                         loopback_mic = m
                         logger.info(f"Using configured device: {m.name}")
                         break
            
            # 2. Auto-detect if not found or not configured
            if not loopback_mic:
                 # Simple heuristic: look for 'Loopback' or match the default speaker name
                 try:
                     default_spk = sc.default_speaker()
                     logger.info(f"System Default Speaker: {default_spk.name}")
                     
                     for m in mics:
                          if m.isloopback and default_spk.name in m.name: # Try to match default speaker
                              loopback_mic = m
                              logger.info(f"Auto-selected Loopback matching default: {m.name}")
                              break 
                     
                     # Fallback to ANY loopback
                     if not loopback_mic:
                         for m in mics:
                             if m.isloopback:
                                 loopback_mic = m
                                 logger.info(f"Using first available loopback: {m.name}")
                                 break
                 except Exception as e:
                     logger.error(f"Error detecting default speaker: {e}")

            if not loopback_mic:
                logger.error("No loopback device found! Using default mic (WILL BE WRONG).")
                loopback_mic = sc.default_microphone()

            logger.info(f"Recording from: {loopback_mic.name}")

            # AUTO-DETECT optimal settings for this device
            self.actual_sample_rate, self.actual_channels = self._detect_optimal_settings(loopback_mic)
            
            # Use detected settings (not config values which may not match hardware)
            with loopback_mic.recorder(samplerate=self.actual_sample_rate, channels=self.actual_channels) as recorder:
                logger.info(f"Recording at: {self.actual_sample_rate} Hz, {self.actual_channels} channels, Block: {Config.BLOCK_SIZE}")
                logger.info(f"📊 Audio Quality: {'Lossless' if Config.OUTPUT_FORMAT == 'flac' else f'{Config.OUTPUT_FORMAT.upper()}'}")
                
                while self.recording:
                    try:
                        # Read block
                        data = recorder.record(numframes=Config.BLOCK_SIZE)
                        
                        if not self.paused:
                            self.buffer_queue.put(data)
                    except Exception as e:
                        logger.error(f"Error reading audio block: {e}")
                        time.sleep(0.1)  # Prevent tight loop on error
                        
        except Exception as e:
            logger.critical(f"Capture thread crashed: {e}", exc_info=True)

    def _process_loop(self):
        logger.info("Audio processing loop started.")
        while self.recording:
            try:
                data = self.buffer_queue.get(timeout=1)
                
                # Thread-safe write with lock
                with self._file_lock:
                    if self._sf_file and not self._sf_file.closed:
                        try:
                            self._sf_file.write(data)
                        except (AssertionError, TypeError) as e:
                            # File closed/invalid during track change - this is normal, skip chunk
                            logger.debug(f"Skipped write (track changing): {type(e).__name__}")
                        except Exception as e:
                            # Other unexpected errors
                            logger.warning(f"Write error: {e}")
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Unexpected error in write loop: {e}", exc_info=True)
        logger.info("Audio processing loop stopped.")
