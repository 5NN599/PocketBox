@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "SOURCE=%~dp0PocketBox.exe"
set "BUILDER_SOURCE=%~dp0PocketBoxBuilder.exe"
set "ICON_SOURCE=%~dp0assets\pbox_file.ico"
set "INSTALL_DIR=%LOCALAPPDATA%\Programs\PocketBox"
set "DEST=%INSTALL_DIR%\PocketBox.exe"
set "BUILDER_DEST=%INSTALL_DIR%\PocketBoxBuilder.exe"
set "ICON_DEST=%INSTALL_DIR%\PocketBox_File.ico"
set "NO_PAUSE=0"
if /I "%~1"=="/nopause" set "NO_PAUSE=1"

if not exist "%SOURCE%" goto :missing_launcher
if not exist "%BUILDER_SOURCE%" goto :missing_builder
if not exist "%ICON_SOURCE%" goto :missing_icon

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if errorlevel 1 goto :error
copy /Y "%SOURCE%" "%DEST%" >nul
if errorlevel 1 goto :error
copy /Y "%BUILDER_SOURCE%" "%BUILDER_DEST%" >nul
if errorlevel 1 goto :error
copy /Y "%ICON_SOURCE%" "%ICON_DEST%" >nul
if errorlevel 1 goto :error

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0register_pocketbox.ps1"
if errorlevel 1 goto :error

echo.
echo PocketBox launcher and Builder installed for the current Windows user.
echo .pbox double-click handling and its file icon are registered.
if "%NO_PAUSE%"=="0" pause
exit /b 0

:missing_launcher
echo ERROR: PocketBox.exe is missing. Run build_all.bat first.
goto :error
:missing_builder
echo ERROR: PocketBoxBuilder.exe is missing. Run build_all.bat first.
goto :error
:missing_icon
echo ERROR: assets\pbox_file.ico is missing.
goto :error
:error
echo.
echo PocketBox installation or file association failed.
if "%NO_PAUSE%"=="0" pause
exit /b 1
