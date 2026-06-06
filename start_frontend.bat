@echo off
title CampusGPT Frontend
color 0B
echo.
echo  ======================================
echo   CampusGPT Frontend Startup
echo  ======================================
echo.

cd /d "%~dp0frontend"

REM Check node
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Please install from: https://nodejs.org
    pause
    exit /b 1
)

echo [1/3] Node.js found

REM Copy env file if missing
if not exist ".env.local" (
    echo [2/3] Creating .env.local...
    copy .env.example .env.local
) else (
    echo [2/3] .env.local already exists
)

REM Install if node_modules missing
if not exist "node_modules" (
    echo [3/3] Installing npm packages (first time ~30 sec)...
    npm install
) else (
    echo [3/3] node_modules already installed
)

echo.
echo  ======================================
echo   Frontend running at:
echo   http://localhost:5173
echo  ======================================
echo.

npm run dev

pause
