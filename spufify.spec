# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Spufify
Creates a standalone Windows executable with all dependencies
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get project root
project_root = os.path.abspath(SPECPATH)

block_cipher = None

# Collect all data files from customtkinter (themes, fonts, etc.)
customtkinter_datas = collect_data_files('customtkinter')

# Collect hidden imports
hidden_imports = [
    'soundcard',
    'numpy',
    'spotipy',
    'pydub',
    'mutagen',
    'customtkinter',
    'pywinauto',
    'PIL',
    'dotenv',
    'requests',
    'urllib3',
    'certifi',
]

# Add all submodules
hidden_imports += collect_submodules('spufify')
hidden_imports += collect_submodules('customtkinter')

a = Analysis(
    ['spufify\\main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        # Include assets (icon)
        ('assets\\icon.ico', 'assets'),
        ('assets\\icon.png', 'assets'),
        # Include .env.example for reference
        ('.env.example', '.'),
        # Include customtkinter data files
        *customtkinter_datas,
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Spufify',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\\icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Spufify',
)
