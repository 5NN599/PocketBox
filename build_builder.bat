@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
set "APP_ICON=%~dp0assets\pocketbox.ico"
set "APP_ICON_DATA=%~dp0assets\pocketbox.ico;assets"
echo [PocketBox] Building the GUI builder with its app icon...
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=py -3.12"
if not exist "%APP_ICON%" (
    echo Missing assets\pocketbox.ico
    pause
    exit /b 1
)
if not exist "build\staging\builder" mkdir "build\staging\builder"
if exist "build\staging\builder\PocketBoxBuilder.exe" del /q "build\staging\builder\PocketBoxBuilder.exe"
if "%PYTHON_EXE%"=="py -3.12" (
    py -3.12 -m PyInstaller --noconfirm --clean --onefile --windowed --name PocketBoxBuilder --distpath "build\staging\builder" --workpath "build\builder" --specpath "build\spec" --icon "%APP_ICON%" --add-data "%APP_ICON_DATA%" --hidden-import pocketbox_format pocketbox_builder.py
) else (
    "%PYTHON_EXE%" -m PyInstaller --noconfirm --clean --onefile --windowed --name PocketBoxBuilder --distpath "build\staging\builder" --workpath "build\builder" --specpath "build\spec" --icon "%APP_ICON%" --add-data "%APP_ICON_DATA%" --hidden-import pocketbox_format pocketbox_builder.py
)
if errorlevel 1 goto :error
if not exist "build\staging\builder\PocketBoxBuilder.exe" goto :error
copy /Y "build\staging\builder\PocketBoxBuilder.exe" "%~dp0PocketBoxBuilder.exe" >nul
if errorlevel 1 goto :error
echo.
echo Builder created: %CD%\PocketBoxBuilder.exe
exit /b 0
:error
echo.
echo Builder build failed. Check Python, PyInstaller, and the absolute resource paths above.
pause
exit /b 1
