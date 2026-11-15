@echo off
cd /d "%~dp0"
echo ============================================
echo PARALLAX BLINDSPOT - NASA GLOBAL INVESTIGATION EDITION
echo ============================================
echo Starting historical-data dashboard at http://127.0.0.1:8765
if exist .env (
  py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload --env-file .env
) else (
  py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload
)
pause
