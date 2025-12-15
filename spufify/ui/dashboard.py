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
        self.title("Spufify Recorder")
        self.geometry("600x400")
        self.resizable(False, False)
        
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
        
        # Status
        self.status_label = ctk.CTkLabel(self.main_frame, text="STATUS: WAITING", font=("Roboto Mono", 12), text_color="#3B8ED0")
        self.status_label.grid(row=3, column=0, pady=20)
        
        # --- Footer ---
        self.footer_frame = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.footer_frame.grid(row=2, column=0, sticky="ew")
        
        self.rec_indicator = ctk.CTkProgressBar(self.footer_frame, orientation="horizontal") 
        self.rec_indicator.pack(fill="x", padx=0, pady=0)
        self.rec_indicator.set(0) # Logic to pulse this if recording?
        
        self.current_cover_url = None
        self.start_controller()

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
        
        self.status_label.configure(text=f"STATUS: {state}")
        
        if state == "RECORDING":
            self.status_label.configure(text_color="#2CC985") # Green
            self.rec_indicator.configure(progress_color="#2CC985")
            self.rec_indicator.set(1.0) # Full bar or pulsing
        elif state == "PAUSED":
            self.status_label.configure(text_color="#E0A82E") # Yellow
            self.rec_indicator.configure(progress_color="#E0A82E")
            self.rec_indicator.set(0.0)
        else:
            self.status_label.configure(text_color="#3B8ED0") # Blue
            self.rec_indicator.set(0.0)
            
        if track:
            self.title_label.configure(text=track['title'])
            self.artist_label.configure(text=track['artist'])
            
            # Cover Art
            if track.get('cover_url') != self.current_cover_url:
                self.current_cover_url = track['cover_url']
                self._load_image(self.current_cover_url)
        else:
             self.title_label.configure(text="Paused / Not Playing")

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
