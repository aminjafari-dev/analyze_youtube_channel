@echo off
chcp 65001 >nul
echo ========================================
echo YouTube Channel Analyzer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo Starting application...
echo.

REM Run the application
python -m src.main

REM If there's an error, keep the window open
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)

