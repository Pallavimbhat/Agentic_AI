@echo off
setlocal
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe DEMO_ALL_14_LABS.py
) else (
  python DEMO_ALL_14_LABS.py
)
pause
