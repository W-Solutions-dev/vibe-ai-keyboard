@echo off
REM Windows Setup Script for Speech-to-Text Keyboard (CMD version)
REM For users who prefer cmd.exe over PowerShell

echo === Speech-to-Text Keyboard Setup for Windows ===
echo.

REM Check Python
echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Show Python version
python --version

REM Create virtual environment
if exist venv (
    echo Virtual environment already exists
) else (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
echo This may take several minutes...
pip install -r requirements.txt

REM Create logs directory
if not exist logs mkdir logs

REM Run tests
echo.
echo Running component tests...
python test_setup.py

echo.
echo === Setup Complete! ===
echo.
echo To use the speech-to-text keyboard:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Run the program: python speech_to_keyboard.py
echo.
echo Press F9 to toggle listening on/off
echo Press Ctrl+C to exit
echo.
pause 