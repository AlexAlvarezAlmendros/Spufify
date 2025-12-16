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

### Prerequisites
- Windows 10/11
- Python 3.8+
- FFmpeg (must be in PATH)
- Spotify Developer App credentials

### Setup
1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `venv\Scripts\pip install -r requirements.txt`
4. Create `.env` file with Spotify credentials:
   ```
   SPOTIPY_CLIENT_ID=your_client_id
   SPOTIPY_CLIENT_SECRET=your_client_secret
   ```
5. Run: `run.bat`

## Usage

1. Launch Spufify
2. Open Spotify and play music
3. Spufify automatically detects and records each track
4. Files are saved to `~/Music/Spufify/` with metadata and artwork

## License

MIT