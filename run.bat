@echo off
cd /d "%~dp0"
echo Launching Spufify...
echo Checking for virtual environment...

if exist venv\Scripts\python.exe (
    echo Virtual environment found.
    echo Starting Application...
    venv\Scripts\python.exe spufify\main.py
) else (
    echo CRITICAL ERROR: venv\Scripts\python.exe not found!
    echo Please run the installation steps again.
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application crashed with error code %ERRORLEVEL%
)

pause
