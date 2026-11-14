@echo off
REM Build iActivator for Windows (run on Windows, Python 3.12 from python.org; Inno Setup 6 for the installer).
cd /d "%~dp0"
if not exist .venv python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt -c constraints.txt
.venv\Scripts\python build.py
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
  for /f "tokens=3 delims= " %%v in ('findstr __version__ iactivator\__init__.py') do "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" /DAppVersion=%%~v installer\iActivator.iss
) else (
  echo Inno Setup 6 not found - the installer is skipped. https://jrsoftware.org/isdl.php
)
powershell -NoProfile -Command "Compress-Archive -Force -Path dist\iActivator -DestinationPath dist\iActivator-windows-portable.zip"
echo.
echo Done: dist\iActivator-windows-setup.exe and dist\iActivator-windows-portable.zip
pause
