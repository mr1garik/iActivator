@echo off
REM Build iActivator.exe for Windows (run on Windows, Python 3.9+ from python.org).
cd /d "%~dp0"
if not exist .venv python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt -c constraints.txt
.venv\Scripts\python build.py
echo.
echo Done: dist\iActivator.exe
pause
