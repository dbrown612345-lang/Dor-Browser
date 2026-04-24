@echo off
title Dor Browser Environment Installer
color 0B

echo ============================================
echo   Dor Browser + Python + Dependencies Setup
echo ============================================
echo.

echo Checking for Python installation...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found. Installing Python 3.13...
    echo.

    :: Download Python installer
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe -OutFile python_installer.exe"

    :: Install Python silently with pip + PATH
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

    echo Python installed.
    echo.
) ELSE (
    echo Python is already installed.
    echo.
)

echo Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Installing Dor Browser dependencies...
python -m pip install ^
    PyQt6 ^
    PyQt6-WebEngine ^
    PyQt6-Multimedia ^
    yt-dlp ^
    vt-py ^
    openai ^
    requests

echo.
echo ============================================
echo   Installation Complete!
echo   You can now run:  python browser.py
echo ============================================
echo.
pause