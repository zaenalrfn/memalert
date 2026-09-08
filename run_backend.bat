@echo off
echo Starting Solana Memecoin Tracker Backend (FastAPI)...
cd /d %~dp0
if not exist "backend\venv" (
    echo Creating Python virtual environment...
    python -m venv backend\venv
)
call backend\venv\Scripts\activate.bat
pip install -r backend\requirements.txt --quiet
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
