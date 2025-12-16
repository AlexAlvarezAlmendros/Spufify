import customtkinter as ctk

class InfoWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Setup Guide - Spufify")
        self.geometry("650x700")
        self.resizable(True, True)
        self.minsize(500, 600)
        
        self.parent = parent
        self.transient(parent)  # Stay on top of main window
        self.grab_set()  # Modal
        
        self._init_ui()

    def _init_ui(self):
        # Header
        header = ctk.CTkFrame(self, height=60, corner_radius=0)
        header.pack(side="top", fill="x")
        
        title = ctk.CTkLabel(
            header, 
            text="⚙️ Required Configuration", 
            font=("Roboto Medium", 22)
        )
        title.pack(pady=15)
        
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, width=620)
        scroll.pack(padx=15, pady=(10, 15), fill="both", expand=True)
        
        # === WINDOWS AUDIO SETTINGS ===
        self._add_section_title(scroll, "🪟 Windows Sound Settings")
        
        self._add_text(scroll, 
            "Configure your audio device correctly to avoid quality issues:",
            bold=True
        )
        
        self._add_numbered_step(scroll, "1", 
            "Open Sound Control Panel:\n"
            "   • Right-click speaker icon in taskbar → \"Sound settings\" → \"More sound settings\"\n"
            "   • Or: Control Panel → Hardware and Sound → Sound"
        )
        
        self._add_numbered_step(scroll, "2", 
            "Select your playback device (Speakers/Headphones) → Properties"
        )
        
        self._add_numbered_step(scroll, "3", 
            "Advanced Tab:\n"
            "   ❌ Uncheck \"Enable audio enhancements\"\n"
            "   ❌ Uncheck \"Allow applications to take exclusive control\""
        )
        
        self._add_numbered_step(scroll, "4", 
            "Set Volume to 100%:\n"
            "   • Windows system volume: 100%\n"
            "   • Spotify volume slider: 100%"
        )
        
        self._add_tip(scroll, 
            "💡 Tip: If you don't want to hear the music while recording, "
            "plug in headphones without wearing them"
        )
        
        self._add_divider(scroll)
        
        # === SPOTIFY SETTINGS ===
        self._add_section_title(scroll, "🎵 Spotify Settings")
        
        self._add_text(scroll, 
            "Disable audio transitions to ensure clean track boundaries:",
            bold=True
        )
        
        self._add_numbered_step(scroll, "1", 
            "Open Spotify → Settings (gear icon)"
        )
        
        self._add_numbered_step(scroll, "2", 
            "Audio Quality:\n"
            "   ✅ Set to \"Very High\" (for best source quality)"
        )
        
        self._add_numbered_step(scroll, "3", 
            "Playback:\n"
            "   ❌ Disable \"Crossfade\" (crossfade songs)\n"
            "   ❌ Disable \"Automix\" (seamless transitions)\n"
            "   ❌ Disable \"Gapless playback\" (if available)"
        )
        
        self._add_warning(scroll,
            "⚠️ Why disable these?\n"
            "These features blend songs together, making it impossible to "
            "detect track boundaries accurately."
        )
        
        self._add_divider(scroll)
        
        # === USAGE TIPS ===
        self._add_section_title(scroll, "🎯 Usage Tips")
        
        self._add_bullet(scroll, 
            "• Use the ⏸ Pause Recording button to stop recording while listening"
        )
        
        self._add_bullet(scroll, 
            "• The progress bar shows real-time song position"
        )
        
        self._add_bullet(scroll, 
            "• Recordings are automatically saved to ~/Music/Spufify/"
        )
        
        self._add_bullet(scroll, 
            "• Metadata and artwork are embedded automatically"
        )
        
        # Footer
        footer = ctk.CTkFrame(self, height=50, corner_radius=0)
        footer.pack(side="bottom", fill="x")
        
        close_btn = ctk.CTkButton(
            footer, 
            text="Got it!", 
            width=200,
            height=35,
            command=self.destroy
        )
        close_btn.pack(pady=10)
    
    def _add_section_title(self, parent, text):
        label = ctk.CTkLabel(
            parent, 
            text=text, 
            font=("Roboto Medium", 18),
            anchor="w"
        )
        label.pack(anchor="w", pady=(15, 10), padx=10)
    
    def _add_text(self, parent, text, bold=False):
        font = ("Roboto Medium", 12) if bold else ("Roboto", 12)
        label = ctk.CTkLabel(
            parent, 
            text=text, 
            font=font,
            anchor="w",
            justify="left",
            wraplength=580
        )
        label.pack(anchor="w", pady=5, padx=10)
    
    def _add_numbered_step(self, parent, number, text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5, padx=10)
        
        # Number badge
        num_label = ctk.CTkLabel(
            frame, 
            text=number, 
            font=("Roboto Medium", 14),
            width=30,
            height=30,
            fg_color="#2CC985",
            corner_radius=15
        )
        num_label.pack(side="left", padx=(0, 10))
        
        # Step text
        text_label = ctk.CTkLabel(
            frame, 
            text=text, 
            font=("Roboto", 12),
            anchor="w",
            justify="left",
            wraplength=540
        )
        text_label.pack(side="left", fill="x", expand=True)
    
    def _add_bullet(self, parent, text):
        label = ctk.CTkLabel(
            parent, 
            text=text, 
            font=("Roboto", 12),
            anchor="w",
            justify="left",
            wraplength=560
        )
        label.pack(anchor="w", pady=3, padx=20)
    
    def _add_tip(self, parent, text):
        frame = ctk.CTkFrame(parent, fg_color="#3B8ED0", corner_radius=8)
        frame.pack(fill="x", pady=10, padx=10)
        
        label = ctk.CTkLabel(
            frame, 
            text=text, 
            font=("Roboto", 11),
            anchor="w",
            justify="left",
            wraplength=580,
            text_color="white"
        )
        label.pack(pady=10, padx=15)
    
    def _add_warning(self, parent, text):
        frame = ctk.CTkFrame(parent, fg_color="#E0A82E", corner_radius=8)
        frame.pack(fill="x", pady=10, padx=10)
        
        label = ctk.CTkLabel(
            frame, 
            text=text, 
            font=("Roboto", 11),
            anchor="w",
            justify="left",
            wraplength=580,
            text_color="white"
        )
        label.pack(pady=10, padx=15)
    
    def _add_divider(self, parent):
        divider = ctk.CTkFrame(parent, height=2, fg_color="gray30")
        divider.pack(fill="x", pady=15, padx=10)
