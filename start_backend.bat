@echo off
title CampusGPT Backend
color 0A
echo.
echo  ======================================
echo   CampusGPT Backend Startup
echo  ======================================
echo.

cd /d "%~dp0backend"

REM Check Python 3.12
python --version 2>&1 | findstr "3.12" >nul
if errorlevel 1 (
    echo [ERROR] Python 3.12 not found!
    echo.
    echo Please install Python 3.12 from:
    echo https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe
    echo.
    echo Make sure to check "Add python.exe to PATH" during install.
    pause
    exit /b 1
)

echo [1/4] Python 3.12 found
echo.

REM Create venv if it doesn't exist
if not exist "venv\Scripts\activate.bat" (
    echo [2/4] Creating virtual environment...
    python -m venv venv
) else (
    echo [2/4] Virtual environment already exists
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo [3/4] Installing dependencies (first time takes ~2 min)...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed. Check your internet connection.
    pause
    exit /b 1
)
echo Dependencies installed.
echo.

REM Init database if it doesn't exist
if not exist "campusgpt.db" (
    echo [4/4] Creating database with demo data...
    python init_db.py
) else (
    echo [4/4] Database already exists
)

echo.
echo  ======================================
echo   Backend running at:
echo   http://localhost:8000
echo   API Docs: http://localhost:8000/api/docs
echo  ======================================
echo.

REM Start server
uvicorn app.main:app --reload --port 8000

pause
