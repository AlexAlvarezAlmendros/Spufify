@echo off
cd /d "%~dp0"

if exist venv\Scripts\pythonw.exe (
    start "" venv\Scripts\pythonw.exe spufify\main.py
) else (
    echo CRITICAL ERROR: venv\Scripts\pythonw.exe not found!
    echo Please run the installation steps again.
    pause
)
