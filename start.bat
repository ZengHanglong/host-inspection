@echo off
setlocal

echo ============================================
echo   Host Inspection System - Starting...
echo ============================================
echo.

cd /d "%~dp0"

:: Kill old processes
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Frontend*" >nul 2>&1

:: Kill anything on ports 8000 and 5173
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173.*LISTENING"') do taskkill /F /PID %%a >nul 2>&1

timeout /t 1 /nobreak >nul

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 16+
    pause
    exit /b 1
)

echo [1/2] Starting backend on http://localhost:8000
start "Backend" cmd /k "cd /d "%~dp0backend" && python run.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting frontend on http://localhost:5173
start "Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo ============================================
echo   Done!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Close this window anytime.
echo To stop: close the Backend and Frontend windows.
echo.
pause
