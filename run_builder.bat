@echo off
setlocal
cd /d "%~dp0"
set "INSTALLED_BUILDER=%LOCALAPPDATA%\Programs\PocketBox\PocketBoxBuilder.exe"
if exist "%INSTALLED_BUILDER%" (
    start "" "%INSTALLED_BUILDER%"
    exit /b 0
)
if exist "%~dp0PocketBoxBuilder.exe" (
    start "" "%~dp0PocketBoxBuilder.exe"
    exit /b 0
)
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0pocketbox_builder.py"
) else (
    py -3.12 "%~dp0pocketbox_builder.py"
)
if errorlevel 1 (
    echo.
    echo Could not launch the Builder. Run build_all.bat first.
    pause
)
