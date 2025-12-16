# Spufify

Real-time audio recorder for Spotify on Windows using WASAPI Loopback.

## Audio Quality Settings

### 🎯 AUTO-CONFIGURATION (New!)
Spufify now **automatically detects** your system's optimal audio settings at startup:
- ✅ **Auto-detects sample rate** (48000, 44100, or other native rate)
- ✅ **Auto-detects channels** (stereo/mono based on device)
- ✅ **No manual configuration needed!**

The app tests multiple configurations and uses what works best with your hardware.

### Default Settings
- **Block Size**: 2048 frames (reduces glitches)
- **Output Format**: FLAC (lossless) or MP3 (320kbps CBR)
- **Recording**: 32-bit FLOAT WAV (maximum quality before encoding)

### Troubleshooting Audio Quality Issues

If the recorded audio still sounds bad despite auto-detection:

#### Adjust Settings in App
Open **⚙️ Settings** in Spufify and verify:
- **Audio Device**: Shows your loopback device (e.g., "Speakers (Loopback)")
- **Sample Rate**: 48000 Hz
- **Block Size**: 1 or higher


## Installation

### Option A: Installer (Recommended for End Users)

Download the latest installer from [Releases](https://github.com/AlexAlvarezAlmendros/Spufify/releases):
- `Spufify-Setup-1.0.0.exe` (includes everything: Python, FFmpeg, dependencies)

The installer will:
1. ✅ Install Spufify to Program Files
2. ✅ Bundle FFmpeg (no separate download needed)
3. ✅ Ask for your Spotify API credentials
4. ✅ Create shortcuts on Desktop and Start Menu

**First-time setup**: You'll need Spotify Developer credentials:
1. Go to https://developer.spotify.com/dashboard
2. Create a new app
3. Set Redirect URI to: `http://127.0.0.1:8888/callback`
4. Enter your Client ID and Secret during installation
5. After installation, open Spufify and go to **⚙️ Settings → Spotify Authentication** to authenticate

### Option B: Development Setup

For developers who want to modify the code:

#### Prerequisites
- Windows 10/11
- Python 3.8+
- FFmpeg (must be in PATH) - [Download here](https://github.com/BtbN/FFmpeg-Builds/releases)
- Spotify Developer App credentials

#### Setup
1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `venv\Scripts\pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and add your Spotify credentials:
   ```
   SPOTIPY_CLIENT_ID=your_client_id
   SPOTIPY_CLIENT_SECRET=your_client_secret
   ```
5. Run: `run.bat`
6. Open **⚙️ Settings → Spotify Authentication** and click "Authenticate with Spotify"

#### Building Installer
See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for creating the standalone installer.

## ⚙️ Required System Configuration

### Windows Sound Settings
**Important**: Configure your audio device correctly to avoid quality issues:

1. **Open Sound Control Panel**:
   - Right-click speaker icon in taskbar → "Sound settings" → "More sound settings"
   - Or: `Control Panel → Hardware and Sound → Sound`

2. **Select your playback device** (Speakers/Headphones) → **Properties**

3. **Advanced Tab**:
   - ❌ **Uncheck "Enable audio enhancements"** (may cause distortion)
   - ❌ **Uncheck "Allow applications to take exclusive control"** (prevents Spufify from capturing audio)

4. **Set Volume to 100%**:
   - Windows system volume: **100%**
   - Spotify volume slider: **100%**
   - **Tip**: If you don't want to hear the music while recording, **plug in headphones** without wearing them

### Spotify Settings
**Disable audio transitions** to ensure clean track boundaries:

1. Open **Spotify → Settings**
2. **Audio Quality**:
   - Set to **Very High** (for best source quality)
3. **Playback**:
   - ❌ **Disable "Crossfade"** (crossfade songs)
   - ❌ **Disable "Automix"** (seamless transitions between songs)
   - ❌ **Disable "Gapless playback"** (if available)

**Why?** These features blend songs together, making it impossible to detect track boundaries accurately.

## Usage
 (or from the installed shortcut)
2. **First time**: Go to **⚙️ Settings → Spotify Authentication** and click "Authenticate with Spotify"
   - This opens your browser for OAuth authorization
   - Grant permissions and return to the app
   - Status indicator in header shows "✅ Spotify OK" when authenticated
3. Open Spotify and play music
4. Spufify automatically detects and records each track
5. Use **⏸ Pause Recording** button to stop recording while listening
6. Use **⏸ Pause Recording** button to stop recording while listening
5. Files are saved to `~/Music/Spufify/` with metadata and artwork

## License

MIT