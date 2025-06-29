@echo off
echo Starting RAG System...

REM Activate virtual environment
call venv\Scripts\activate

REM Start Ollama
start "Ollama" ollama serve

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start FastAPI server
start "FastAPI" python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start Next.js frontend
cd next-frontend
start "Next.js" npm run dev

echo System started!
pause 