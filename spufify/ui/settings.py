import customtkinter as ctk
import soundcard as sc
from spufify.config import Config
import tkinter.filedialog as filedialog

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Spufify Settings")
        self.geometry("500x600")
        self.resizable(False, False)
        
        self.parent = parent
        self.transient(parent) # Stay on top of main window
        self.grab_set() # Modal
        
        self._init_ui()
        self._load_current_values()

    def _init_ui(self):
        # 1. Footer (Bottom) - Pack first to ensure visibility
        footer = ctk.CTkFrame(self, height=50)
        footer.pack(side="bottom", fill="x")
        
        save_btn = ctk.CTkButton(footer, text="Save & Close", command=self._save)
        save_btn.pack(pady=10)

        # 2. Title (Top)
        title = ctk.CTkLabel(self, text="Settings", font=("Arial", 20, "bold"))
        title.pack(side="top", pady=10)
        
        # 3. Scrollable Frame (Middle - takes remaining space)
        self.scroll = ctk.CTkScrollableFrame(self, width=480)
        self.scroll.pack(padx=10, pady=5, fill="both", expand=True)
        
        # --- Audio Device ---
        ctk.CTkLabel(self.scroll, text="Audio Input Device (Loopback Target)", font=("Arial", 14, "bold")).pack(anchor="w", pady=(10, 0))
        
        self.device_combo = ctk.CTkComboBox(self.scroll, width=400)
        self.device_combo.pack(pady=5)
        self._populate_devices()
        
        # --- Audio Settings ---
        ctk.CTkLabel(self.scroll, text="Audio Format", font=("Arial", 14, "bold")).pack(anchor="w", pady=(15, 0))
        
        # Format
        ctk.CTkLabel(self.scroll, text="Output Format").pack(anchor="w")
        self.format_combo = ctk.CTkComboBox(self.scroll, values=["mp3", "flac", "wav"])
        self.format_combo.pack(anchor="w", pady=5)
        
        # Sample Rate
        ctk.CTkLabel(self.scroll, text="Sample Rate (Hz)").pack(anchor="w")
        self.rate_entry = ctk.CTkEntry(self.scroll)
        self.rate_entry.pack(anchor="w", pady=5)
        
        # Block Size
        ctk.CTkLabel(self.scroll, text="Buffer Block Size (frames)").pack(anchor="w")
        self.block_entry = ctk.CTkEntry(self.scroll)
        self.block_entry.pack(anchor="w", pady=5)
        
        # --- Logic Settings ---
        ctk.CTkLabel(self.scroll, text="Recording Logic", font=("Arial", 14, "bold")).pack(anchor="w", pady=(15, 0))
        
        ctk.CTkLabel(self.scroll, text="Silence Threshold (dB) (e.g. -50)").pack(anchor="w")
        self.silence_entry = ctk.CTkEntry(self.scroll)
        self.silence_entry.pack(anchor="w", pady=5)
        
        # --- Paths ---
        ctk.CTkLabel(self.scroll, text="Storage", font=("Arial", 14, "bold")).pack(anchor="w", pady=(15, 0))
        
        ctk.CTkLabel(self.scroll, text="Output Directory").pack(anchor="w")
        
        path_frame = ctk.CTkFrame(self.scroll)
        path_frame.pack(fill="x", pady=5)
        
        self.path_entry = ctk.CTkEntry(path_frame)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_btn = ctk.CTkButton(path_frame, text="...", width=30, command=self._browse_path)
        browse_btn.pack(side="right")

    def _populate_devices(self):
        # We need loopback devices
        try:
            mics = sc.all_microphones(include_loopback=True)
            # Filter somewhat relevant ones (usually contain the speaker name)
            self.device_names = [m.name for m in mics]
            self.device_combo.configure(values=self.device_names)
        except Exception as e:
            print(f"Error listing devices: {e}")
            self.device_combo.configure(values=["Error enumerating devices"])

    def _browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)

    def _load_current_values(self):
        # Load Config into fields
        self.format_combo.set(Config.OUTPUT_FORMAT)
        self.rate_entry.insert(0, str(Config.SAMPLE_RATE))
        self.block_entry.insert(0, str(Config.BLOCK_SIZE))
        self.silence_entry.insert(0, str(Config.SILENCE_THRESHOLD_DB))
        self.path_entry.insert(0, Config.OUTPUT_DIR)
        
        # Device
        if Config.AUDIO_DEVICE_ID and Config.AUDIO_DEVICE_ID in self.device_names:
            self.device_combo.set(Config.AUDIO_DEVICE_ID)
        else:
            # Default to soundcard default if possible
            try:
                def_mic = sc.default_microphone()
                # Find best match in list
                if def_mic.name in self.device_names:
                    self.device_combo.set(def_mic.name)
                else:
                    self.device_combo.set(self.device_names[0] if self.device_names else "")
            except:
                pass

    def _save(self):
        try:
            # Update Config
            Config.OUTPUT_FORMAT = self.format_combo.get()
            Config.SAMPLE_RATE = int(self.rate_entry.get())
            Config.BLOCK_SIZE = int(self.block_entry.get())
            Config.SILENCE_THRESHOLD_DB = float(self.silence_entry.get())
            Config.OUTPUT_DIR = self.path_entry.get()
            Config.AUDIO_DEVICE_ID = self.device_combo.get()
            
            # Save to disk
            Config.save_settings()
            Config.ensure_directories()
            
            # Hot Reload Audio Engine
            if self.parent.controller and self.parent.controller.recorder:
                # Run in thread to not block UI
                import threading
                threading.Thread(target=self.parent.controller.recorder.restart_audio_engine, daemon=True).start()
            
            # Close
            self.destroy()
            
        except ValueError:
            print("Invalid input values")
