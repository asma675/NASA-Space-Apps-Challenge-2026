@echo off
cd /d "%~dp0"
echo ============================================
echo PARALLAX BLINDSPOT - GLOBAL INVESTIGATION EDITION
 echo ============================================
echo Open http://127.0.0.1:8765
py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765 --reload
pause
