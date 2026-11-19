@echo off
setlocal
cd /d "%~dp0"
echo ===============================================
echo   Agentic AI Course Organizer - Setup and Run
echo ===============================================
echo.
python --version
if errorlevel 1 (
  echo Python was not found. Install Python 3.10+ and enable Add Python to PATH.
  pause
  exit /b 1
)
echo.
echo Installing required packages...
python -m pip install --upgrade pip
if errorlevel 1 goto failed
python -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Starting application at http://127.0.0.1:8002/
echo Open the integrated Academic AI Assistant from the main dashboard at http://127.0.0.1:8002/
echo Keep this window open while using the application.
python -m uvicorn course_organizer.main:app --host 127.0.0.1 --port 8002
pause
exit /b 0
:failed
echo.
echo Setup failed. Read the error above, check your internet connection, and try again.
pause
exit /b 1
