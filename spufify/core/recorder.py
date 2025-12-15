import soundcard as sc
import numpy as np
import threading
import time
import queue
import wave
import os
from spufify.config import Config
from spufify.core.processor import Processor


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
        self._wav_file_handle = None

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
        print("[Recorder] Capture threads started.")

    def resume_recording(self):
        if not self._wav_file_handle:
            self._open_wav_file()
        self.paused = False
        print("[Recorder] Resumed.")

    def pause_recording(self):
        self.paused = True
        print("[Recorder] Paused.")

    def stop_recording(self):
        self.paused = True
        # Don't kill thread, just wait in paused state usually, 
        # but for full stop we can set recording=False
        pass

    def set_current_metadata(self, metadata):
        self.current_metadata = metadata

    def finish_track(self):
        """
        Closes current WAV, triggers processing (Module C), and prepares for next.
        """
        self.pause_recording()
        self._close_wav_file()
        
        if self.current_metadata:
            # TRIGGER MODULE C (Processor)
            # We rename temp to a specific temp name for this track to avoid collisions if next track starts fast
            
            temp_track_path = os.path.join(Config.OUTPUT_DIR, f"temp_{int(time.time())}.wav")
            
            if os.path.exists(self.current_temp_file):
                # Check if file has meaningful size (avoid empty files from quick skips)
                if os.path.getsize(self.current_temp_file) > 100000: # ~0.5 sec
                    try:
                        os.rename(self.current_temp_file, temp_track_path)
                        # Offload to processor
                        self.processor.process_track(temp_track_path, self.current_metadata)
                    except Exception as e:
                        print(f"[Recorder] Error handing off file: {e}")
                else:
                    print("[Recorder] File too short, discarded.")
            
        # Ready for next
        pass

    def _open_wav_file(self):
        self._close_wav_file() # Ensure closed
        try:
            self._wav_file_handle = wave.open(self.current_temp_file, 'wb')
            self._wav_file_handle.setnchannels(Config.CHANNELS)
            self._wav_file_handle.setsampwidth(2) # 16 bit
            self._wav_file_handle.setframerate(Config.SAMPLE_RATE)
        except Exception as e:
            print(f"[Recorder] Error opening WAV: {e}")

    def _close_wav_file(self):
        if self._wav_file_handle:
            self._wav_file_handle.close()
            self._wav_file_handle = None

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
            
            # Simple heuristic: look for 'Loopback' or match the default speaker name
            default_spk = sc.default_speaker()
            for m in mics:
                 if m.isloopback:
                     loopback_mic = m
                     break # Take first loopback found
            
            if not loopback_mic:
                print("[Recorder] No loopback device found! Using default mic (MAY BE WRONG).")
                loopback_mic = sc.default_microphone()

            print(f"[Recorder] Recording from: {loopback_mic.name}")

            # Reverting: soundcard requires samplerate argument.
            # User set Config.SAMPLE_RATE manually to match their hardware.
            with loopback_mic.recorder(samplerate=Config.SAMPLE_RATE, channels=Config.CHANNELS) as recorder:
                actual_rate = Config.SAMPLE_RATE 
                print(f"[Recorder] Recording at: {actual_rate} Hz")
                
                while self.recording:
                    # Read block
                    data = recorder.record(numframes=Config.BLOCK_SIZE)
                    
                    if not self.paused:
                        self.buffer_queue.put(data)
                        
        except Exception as e:
            print(f"[Recorder] Capture Crashed: {e}")

    def _process_loop(self):
        while self.recording:
            try:
                data = self.buffer_queue.get(timeout=1)
                if self._wav_file_handle:
                    # data is numpy array floats [-1.0, 1.0] usually
                    # Wave needs 16-bit PCM bytes
                    # Convert float32 to int16
                    audio_data = (data * 32767).astype(np.int16)
                    self._wav_file_handle.writeframes(audio_data.tobytes())
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Recorder] Write Error: {e}")
