@echo off
REM Activate the virtual environment
call venv\Scripts\activate

REM Start the FastAPI server in a new command window
start cmd /k "ollama serve"

REM Wait a bit to ensure the server starts
ping 127.0.0.1 -n 3 > nul

REM Start the FastAPI server in a new command window
start cmd /k "uvicorn server.fastapi_ingestion_server:app --reload"

REM Wait a bit to ensure the server starts
ping 127.0.0.1 -n 3 > nul

REM Start the Streamlit frontend in another new command window
cd frontend
start cmd /k "streamlit run bot.py"

REM Return to root directory
cd .. 