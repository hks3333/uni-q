@echo off
setlocal enabledelayedexpansion

:menu
cls
echo ========================================
echo           RAG System Manager
echo ========================================
echo.
echo 1. Start RAG System
echo 2. Stop RAG System
echo 3. Restart RAG System
echo 4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto start_system
if "%choice%"=="2" goto stop_system
if "%choice%"=="3" goto restart_system
if "%choice%"=="4" goto exit
goto menu

:start_system
echo.
echo Starting RAG System...

REM Check if system is already running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Ollama is already running!
    goto menu
)

tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "uvicorn">NUL
if "%ERRORLEVEL%"=="0" (
    echo FastAPI server is already running!
    goto menu
)

REM Activate virtual environment
call venv\Scripts\activate

REM Start Ollama
start "Ollama" ollama serve

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start FastAPI server
start "FastAPI" python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start Next.js frontend
cd next-frontend
start "Next.js" npm run dev

REM Wait a moment for Next.js to start
timeout /t 8 /nobreak >nul

REM Open browser to localhost:3000
start "" "http://localhost:3000"

echo.
echo System started successfully!
echo - Ollama: http://localhost:11434
echo - FastAPI: http://localhost:8000
echo - Next.js: http://localhost:3000
echo.
pause
goto menu

:stop_system
echo.
echo Stopping RAG System...

REM Stop Next.js processes
echo Stopping Next.js...
taskkill /FI "WINDOWTITLE eq Next.js*" /F >nul 2>&1
taskkill /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq *npm*" /F >nul 2>&1
taskkill /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq *next*" /F >nul 2>&1

REM Stop FastAPI server (uvicorn)
echo Stopping FastAPI...
taskkill /FI "WINDOWTITLE eq FastAPI*" /F >nul 2>&1
taskkill /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *uvicorn*" /F >nul 2>&1
taskkill /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *FastAPI*" /F >nul 2>&1

REM Stop Ollama
echo Stopping Ollama...
taskkill /FI "WINDOWTITLE eq Ollama*" /F >nul 2>&1
taskkill /FI "IMAGENAME eq ollama.exe" /F >nul 2>&1

REM Additional cleanup - kill any remaining processes on the ports
echo Cleaning up ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /PID %%a /F >nul 2>&1

echo System stopped successfully!
pause
goto menu

:restart_system
echo.
echo Restarting RAG System...
call :stop_system
timeout /t 2 /nobreak >nul
call :start_system
goto menu

:exit
echo.
echo Goodbye!
exit /b 0