@echo off
cd /d "%~dp0"
echo.
echo ==========================================================
echo  PARALLAX BLINDSPOT - EARTH SYSTEMS / WORLD 2026
 echo ==========================================================
echo  Original Observatory: http://127.0.0.1:8777/
echo  New Earth Systems hub: http://127.0.0.1:8777/earth
echo  NASA World Explorer: http://127.0.0.1:8777/explore
echo.
echo Installing Python requirements if necessary...
py -m pip install -r backend\requirements.txt
if errorlevel 1 (
  echo Installation failed. Check Python and Internet connectivity.
  pause
  exit /b 1
)
echo.
echo Starting the app on port 8777 to avoid older BLINDSPOT copies...
if exist .env (
  echo Loading existing .env settings for optional original NASA FIRMS features...
  py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8777 --reload --env-file .env
) else (
  py -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8777 --reload
)
pause
