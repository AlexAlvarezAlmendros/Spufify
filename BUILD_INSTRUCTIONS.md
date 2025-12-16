# Building Spufify Installer

This guide explains how to create a standalone Windows installer for Spufify.

## Prerequisites

### 1. Development Environment
- Windows 10/11 (64-bit)
- Python 3.8+ with venv
- Git

### 2. Required Software

#### PyInstaller (included in requirements)
Already installed if you followed setup:
```bash
venv\Scripts\pip install pyinstaller
```

#### Inno Setup 6
Download and install from: https://jrsoftware.org/isdl.php
- Choose **Unicode** version (recommended)
- Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

#### FFmpeg
1. Download FFmpeg from: https://github.com/BtbN/FFmpeg-Builds/releases
2. Get the `ffmpeg-master-latest-win64-gpl.zip` (or similar)
3. Extract the zip file
4. Copy these files to `ffmpeg\` folder in project root:
   - `bin\ffmpeg.exe`
   - `bin\ffprobe.exe`

Your project structure should look like:
```
Spufify/
├── ffmpeg/
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── assets/
│   ├── icon.ico
│   └── icon.png
├── spufify/
├── spufify.spec
├── installer.iss
└── build_installer.bat
```

## Build Process

### Option A: Automated Build (Recommended)

Simply run the build script:
```bash
build_installer.bat
```

This script will:
1. ✅ Check prerequisites
2. ✅ Clean previous builds
3. ✅ Build executable with PyInstaller
4. ✅ Create installer with Inno Setup
5. ✅ Output final installer to `dist\installer\`

### Option B: Manual Build

If you prefer to run steps manually:

#### Step 1: Build with PyInstaller
```bash
venv\Scripts\pyinstaller spufify.spec --noconfirm
```

This creates `dist\Spufify\` folder with:
- `Spufify.exe` (main executable)
- All Python dependencies
- Assets and data files

#### Step 2: Verify FFmpeg is ready
Ensure `ffmpeg\ffmpeg.exe` and `ffmpeg\ffprobe.exe` exist in project root.

#### Step 3: Compile Installer
```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

## Output

After successful build, you'll find:
```
dist/
├── Spufify/              (PyInstaller output - portable version)
└── installer/
    └── Spufify-Setup-1.0.0.exe  (Final installer)
```

## Installer Features

The generated installer (`Spufify-Setup-1.0.0.exe`) includes:

### ✨ Automatic Configuration
- Prompts user for Spotify API credentials during installation
- Creates `.env` file automatically with user's credentials
- Adds FFmpeg to system PATH

### 📦 Bundled Components
- Spufify executable (no Python needed)
- FFmpeg (no separate download)
- Icon and assets

### 🎯 Installation Options
- Desktop shortcut (optional)
- Start menu entry
- Custom installation directory

### 🔧 Smart Uninstaller
- Asks if user wants to keep recorded music
- Removes application files
- Cleans up registry entries

## Testing the Installer

### Before Distribution:
1. **Test on Clean VM**: Install on a Windows VM without Python/FFmpeg
2. **Test Installation Path**: Try both Program Files and custom paths
3. **Test Credentials**: Enter valid Spotify credentials during setup
4. **Verify Shortcuts**: Check desktop and start menu icons work
5. **Test Recording**: Record a song to ensure everything works
6. **Test Uninstall**: Run uninstaller and verify cleanup

### Common Issues:

#### "FFmpeg not found"
- Ensure `ffmpeg\ffmpeg.exe` exists before building
- Verify installer.iss `[Files]` section includes FFmpeg

#### "Import Error" when running
- Missing hidden import in `spufify.spec`
- Add to `hiddenimports` list in spec file

#### Icon not showing
- Ensure `assets\icon.ico` is a valid ICO file (multiple sizes)
- Verify icon path in both `spufify.spec` and `installer.iss`

## Advanced Customization

### Change Version Number
Edit `installer.iss`:
```pascal
#define MyAppVersion "1.0.0"  // Change here
```

### Add More Files
Edit `installer.iss` `[Files]` section:
```pascal
Source: "path\to\file"; DestDir: "{app}"; Flags: ignoreversion
```

### Modify Installation Wizard
Edit `installer.iss` `[Code]` section to add custom pages or logic.

### Reduce Installer Size
Edit `spufify.spec`:
- Add more packages to `excludes` list (e.g., `'tkinter'`)
- Disable UPX compression if it causes issues: `upx=False`

## Distribution

### Recommended Platforms:
- **GitHub Releases**: Upload `Spufify-Setup-1.0.0.exe` as release asset
- **Microsoft Store**: Use MSIX packaging (requires additional setup)
- **Direct Download**: Host on website with SHA256 checksum

### Security Notes:
⚠️ **Do NOT include your personal `.env` file in builds**
- The installer creates a template `.env` with placeholders
- Users must add their own Spotify credentials

### Release Checklist:
- [ ] Update version in `installer.iss`
- [ ] Update CHANGELOG.md
- [ ] Test installer on clean Windows VM
- [ ] Generate SHA256 hash: `certutil -hashfile Spufify-Setup-1.0.0.exe SHA256`
- [ ] Create GitHub release with installer and hash
- [ ] Update README.md with download link

## Troubleshooting Build Issues

### PyInstaller Errors

**"Module not found" errors:**
```bash
# Add to spufify.spec hiddenimports
hiddenimports=['missing_module_name']
```

**Executable crashes immediately:**
```bash
# Build with console to see errors
# Edit spufify.spec: console=True
venv\Scripts\pyinstaller spufify.spec --noconfirm
```

### Inno Setup Errors

**"File not found" during compilation:**
- Check all `Source:` paths in `installer.iss` are correct
- Ensure `dist\Spufify\` exists (run PyInstaller first)

**"Access denied" during installation:**
- Run installer as Administrator
- Check `PrivilegesRequired=admin` in `installer.iss`

## Further Reading

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [Code Signing for Windows](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
