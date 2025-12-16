import customtkinter as ctk
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading

class Dashboard(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        
        # Window setup
        self.title("Spufify")
        self.geometry("600x630")
        self.resizable(True, True)
        self.minsize(500, 500)
        
        # Theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # --- Header ---
        self.header_frame = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.logo_label = ctk.CTkLabel(self.header_frame, text="Spufify", font=("Roboto Medium", 20))
        self.logo_label.pack(side="left", padx=20, pady=10)
        
        # --- Main Content ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Album Art
        self.art_label = ctk.CTkLabel(self.main_frame, text="[No Image]", width=200, height=200, fg_color="gray20", corner_radius=10)
        self.art_label.grid(row=0, column=0, pady=(20, 10))
        
        # Track Info
        self.title_label = ctk.CTkLabel(self.main_frame, text="Waiting for Spotify...", font=("Roboto Medium", 18))
        self.title_label.grid(row=1, column=0, pady=5)
        
        self.artist_label = ctk.CTkLabel(self.main_frame, text="", font=("Roboto", 14), text_color="gray")
        self.artist_label.grid(row=2, column=0, pady=0)
        
        # Duration
        self.duration_label = ctk.CTkLabel(self.main_frame, text="", font=("Roboto Mono", 11), text_color="gray60")
        self.duration_label.grid(row=3, column=0, pady=2)
        
        # Status
        self.status_label = ctk.CTkLabel(self.main_frame, text="STATUS: WAITING", font=("Roboto Mono", 12), text_color="#3B8ED0")
        self.status_label.grid(row=4, column=0, pady=10)
        
        # Record/Pause Button
        self.record_btn = ctk.CTkButton(
            self.main_frame,
            text="⏺ Start Recording",
            width=200,
            height=35,
            font=("Roboto Medium", 13),
            command=self.toggle_recording
        )
        self.record_btn.grid(row=5, column=0, pady=10)
        
        # --- Footer ---
        self.footer_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.footer_frame.grid(row=2, column=0, sticky="ew")
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.footer_frame, orientation="horizontal", height=8)
        self.progress_bar.pack(fill="x", padx=20, pady=(10, 5))
        self.progress_bar.set(0)
        
        # Time Label
        self.time_label = ctk.CTkLabel(
            self.footer_frame,
            text="0:00 / 0:00",
            font=("Roboto Mono", 11),
            text_color="gray70"
        )
        self.time_label.pack(pady=(0, 5))
        
        # Info Button (left side)
        self.info_btn = ctk.CTkButton(self.footer_frame, text="Info", width=10, command=self.open_info)
        self.info_btn.pack(side="left", padx=5, pady=5)
        
        # Settings Button (right side)
        self.settings_btn = ctk.CTkButton(self.footer_frame, text="⚙️", width=40, command=self.open_settings)
        self.settings_btn.pack(side="right", padx=10, pady=5)
        
        self.current_cover_url = None
        self.settings_window = None
        self.info_window = None
        self.start_controller()
    
    def toggle_recording(self):
        """Toggle manual recording pause/resume"""
        if self.controller.user_paused:
            self.controller.manual_resume()
        else:
            self.controller.manual_pause()
    
    def _format_time(self, ms):
        """Convert milliseconds to M:SS format"""
        if not ms:
            return "0:00"
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            from spufify.ui.settings import SettingsWindow # Lazy import to avoid circular dep
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()
    
    def open_info(self):
        if self.info_window is None or not self.info_window.winfo_exists():
            from spufify.ui.info import InfoWindow # Lazy import to avoid circular dep
            self.info_window = InfoWindow(self)
        else:
            self.info_window.focus()

    def start_controller(self):
        # Pass callback to controller
        self.controller.ui_callback = self.update_ui
        self.controller.start()
        
    def update_ui(self, status):
        # This is called from background thread, so we must schedule update on main thread
        # CustomTkinter usually handles this gracefully or we use .after
        
        self.after(0, lambda: self._update_ui_internal(status))
        
    def _update_ui_internal(self, status):
        state = status['state']
        track = status['track']
        
        # Enhanced status text with format info
        from spufify.config import Config
        status_text = f"STATUS: {state}"
        if state == "RECORDING" and track:
            status_text += f" • {Config.OUTPUT_FORMAT.upper()}"
        elif state == "PAUSED" and track and track.get('is_ad'):
            status_text += " • Ad detected"
        
        self.status_label.configure(text=status_text)
        
        # Update button text based on state
        if self.controller.user_paused:
            self.record_btn.configure(text="⏺ Resume Recording")
        else:
            self.record_btn.configure(text="⏸ Pause Recording")
        
        if state == "RECORDING":
            self.status_label.configure(text_color="#2CC985") # Green
            self.progress_bar.configure(progress_color="#2CC985")
        elif state == "PAUSED":
            self.status_label.configure(text_color="#E0A82E") # Yellow
            self.progress_bar.configure(progress_color="#E0A82E")
        else:
            self.status_label.configure(text_color="#3B8ED0") # Blue
            self.progress_bar.configure(progress_color="#3B8ED0")
            
        if track:
            self.title_label.configure(text=track['title'])
            self.artist_label.configure(text=track['artist'])
            
            # Duration display
            if track.get('duration_ms'):
                duration_str = self._format_time(track['duration_ms'])
                self.duration_label.configure(text=f"Duration: {duration_str}")
                
                # Progress bar and time display
                progress_ms = track.get('progress_ms', 0)
                duration_ms = track['duration_ms']
                
                if duration_ms > 0:
                    progress_fraction = progress_ms / duration_ms
                    self.progress_bar.set(progress_fraction)
                    
                    current_time = self._format_time(progress_ms)
                    total_time = self._format_time(duration_ms)
                    self.time_label.configure(text=f"{current_time} / {total_time}")
            else:
                self.duration_label.configure(text="")
                self.progress_bar.set(0)
                self.time_label.configure(text="0:00 / 0:00")
            
            # Cover Art
            if track.get('cover_url') != self.current_cover_url:
                self.current_cover_url = track['cover_url']
                self._load_image(self.current_cover_url)
        else:
            self.title_label.configure(text="Waiting for Spotify...")
            self.artist_label.configure(text="")
            self.duration_label.configure(text="")
            self.progress_bar.set(0)
            self.time_label.configure(text="0:00 / 0:00")

    def _load_image(self, url):
        def _fetch():
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    img_data = BytesIO(resp.content)
                    pil_image = Image.open(img_data)
                    pil_image = pil_image.resize((200, 200), Image.Resampling.LANCZOS)
                    ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(200, 200))
                    
                    self.after(0, lambda: self.art_label.configure(text="", image=ctk_image))
            except Exception as e:
                print(f"Error loading image: {e}")
        
        threading.Thread(target=_fetch, daemon=True).start()

    def on_closing(self):
        self.controller.stop()
        self.destroy()
