@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [PocketBox] Preparing a local Python 3.12 environment...
where py >nul 2>&1
if errorlevel 1 goto :error
py -3.12 -c "import sys,struct; raise SystemExit(0 if sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8 else 1)" >nul 2>&1
if errorlevel 1 goto :error
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv ".venv"
if errorlevel 1 goto :error
"%~dp0.venv\Scripts\python.exe" -m ensurepip --upgrade >nul 2>&1
"%~dp0.venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :error
echo.
echo Setup complete. You can now run build_all.bat.
pause
exit /b 0
:error
echo.
echo Setup failed. Check Python 3.12 64-bit and internet access.
pause
exit /b 1
