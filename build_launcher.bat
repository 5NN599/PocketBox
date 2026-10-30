@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
set "APP_ICON=%~dp0assets\pocketbox.ico"
echo [PocketBox] Building the shared .pbox launcher with its app icon...
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=py -3.12"
if not exist "%APP_ICON%" (
    echo Missing assets\pocketbox.ico
    pause
    exit /b 1
)
if not exist "build\staging\launcher" mkdir "build\staging\launcher"
if exist "build\staging\launcher\PocketBox.exe" del /q "build\staging\launcher\PocketBox.exe"
if "%PYTHON_EXE%"=="py -3.12" (
    py -3.12 -m PyInstaller --noconfirm --clean --onefile --windowed --name PocketBox --distpath "build\staging\launcher" --workpath "build\launcher" --specpath "build\spec" --icon "%APP_ICON%" --hidden-import pocketbox_format pocketbox_runtime.py
) else (
    "%PYTHON_EXE%" -m PyInstaller --noconfirm --clean --onefile --windowed --name PocketBox --distpath "build\staging\launcher" --workpath "build\launcher" --specpath "build\spec" --icon "%APP_ICON%" --hidden-import pocketbox_format pocketbox_runtime.py
)
if errorlevel 1 goto :error
if not exist "build\staging\launcher\PocketBox.exe" goto :error
copy /Y "build\staging\launcher\PocketBox.exe" "%~dp0PocketBox.exe" >nul
if errorlevel 1 goto :error
echo.
echo Launcher created: %CD%\PocketBox.exe
echo App icon embedded in PocketBox.exe.
exit /b 0
:error
echo.
echo Launcher build failed. Check Python, PyInstaller, and the absolute icon path above.
pause
exit /b 1
