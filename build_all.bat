@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title PocketBox v0.3.1 - One-click setup and build

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
set "APP_ICON=%~dp0assets\pocketbox.ico"
set "APP_ICON_DATA=%~dp0assets\pocketbox.ico;assets"

echo ==================================================
echo   PocketBox v0.3.1 - One-click build and installation
echo ==================================================
echo.

echo [1/6] Checking Python 3.12 64-bit...
where py >nul 2>&1
if errorlevel 1 goto :python_missing
py -3.12 -c "import sys,struct; raise SystemExit(0 if sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8 else 1)" >nul 2>&1
if errorlevel 1 goto :python_missing

if not exist "%PYTHON_EXE%" (
    echo [2/6] Creating an isolated project environment...
    py -3.12 -m venv ".venv"
    if errorlevel 1 goto :venv_failed
) else (
    echo [2/6] Checking the existing project environment...
    "%PYTHON_EXE%" -c "import sys,struct; raise SystemExit(0 if sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8 else 1)" >nul 2>&1
    if errorlevel 1 (
        echo Existing .venv does not match Python 3.12 64-bit. Recreating it...
        rmdir /S /Q ".venv"
        if exist ".venv" goto :venv_failed
        py -3.12 -m venv ".venv"
        if errorlevel 1 goto :venv_failed
    )
)

if not exist "%PYTHON_EXE%" goto :venv_failed

echo [3/6] Installing required Python packages...
"%PYTHON_EXE%" -m ensurepip --upgrade >nul 2>&1
"%PYTHON_EXE%" -m pip --version >nul 2>&1
if errorlevel 1 goto :dependencies_failed
"%PYTHON_EXE%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :dependencies_failed

echo.
echo [4/6] Running unit tests...
"%PYTHON_EXE%" -m unittest discover -v
if errorlevel 1 goto :tests_failed

if not exist "%APP_ICON%" goto :assets_missing
if not exist "assets\pbox_file.ico" goto :assets_missing

rem Build to staging folders first. Only copy fully completed EXEs to the project root.
rem PyInstaller spec files live under build\spec, so resource paths MUST be absolute.
echo.
echo [5/6] Building PocketBox.exe and PocketBoxBuilder.exe...
if not exist "build\staging\launcher" mkdir "build\staging\launcher"
if not exist "build\staging\builder" mkdir "build\staging\builder"
if exist "build\staging\launcher\PocketBox.exe" del /q "build\staging\launcher\PocketBox.exe"
if exist "build\staging\builder\PocketBoxBuilder.exe" del /q "build\staging\builder\PocketBoxBuilder.exe"

"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean --onefile --windowed --name PocketBox --distpath "build\staging\launcher" --workpath "build\launcher" --specpath "build\spec" --icon "%APP_ICON%" --hidden-import pocketbox_format pocketbox_runtime.py
if errorlevel 1 goto :launcher_failed
if not exist "build\staging\launcher\PocketBox.exe" goto :launcher_failed
copy /Y "build\staging\launcher\PocketBox.exe" "%~dp0PocketBox.exe" >nul
if errorlevel 1 goto :launcher_failed

"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean --onefile --windowed --name PocketBoxBuilder --distpath "build\staging\builder" --workpath "build\builder" --specpath "build\spec" --icon "%APP_ICON%" --add-data "%APP_ICON_DATA%" --hidden-import pocketbox_format pocketbox_builder.py
if errorlevel 1 goto :builder_failed
if not exist "build\staging\builder\PocketBoxBuilder.exe" goto :builder_failed
copy /Y "build\staging\builder\PocketBoxBuilder.exe" "%~dp0PocketBoxBuilder.exe" >nul
if errorlevel 1 goto :builder_failed

echo.
echo [6/6] Installing the launcher and registering .pbox files for this user...
call "%~dp0install_pocketbox.bat" /nopause
if errorlevel 1 goto :install_failed

echo.
echo ==================================================
echo   SUCCESS - PocketBox is ready!
echo ==================================================
echo.
echo Created in this project folder:
echo   PocketBox.exe
echo   PocketBoxBuilder.exe
echo.
echo Installed launcher location:
echo   %LOCALAPPDATA%\Programs\PocketBox
echo.
echo You can now double-click any .pbox file to run it.
echo Start creating packages with PocketBoxBuilder.exe.
echo.
echo Note: Python 3.12 64-bit and an internet connection are
echo needed for the first build. Later builds reuse .venv.
pause
exit /b 0

:python_missing
echo.
echo ERROR: Python 3.12 64-bit or the Python Launcher (py) was not found.
echo Install Python 3.12 64-bit, enable the Python Launcher, then run this file again.
echo Download: https://www.python.org/downloads/windows/
goto :failed

:venv_failed
echo.
echo ERROR: Could not create or locate the local .venv environment.
goto :failed

:dependencies_failed
echo.
echo ERROR: Dependency installation failed. Check internet access and try again.
goto :failed

:tests_failed
echo.
echo ERROR: PocketBox unit tests failed. No installation was performed.
goto :failed

:assets_missing
echo.
echo ERROR: Required application or .pbox icon is missing from assets\.
goto :failed

:launcher_failed
echo.
echo ERROR: Building PocketBox.exe failed. Check the PyInstaller output above.
goto :failed

:builder_failed
echo.
echo ERROR: Building PocketBoxBuilder.exe failed. Check the PyInstaller output above.
goto :failed

:install_failed
echo.
echo ERROR: The executables were built, but launcher installation/file association failed.
echo You can retry by running install_pocketbox.bat.
goto :failed

:failed
echo.
echo PocketBox one-click build did not finish.
pause
exit /b 1
