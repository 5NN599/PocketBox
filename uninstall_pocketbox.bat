@echo off
setlocal
reg delete "HKCU\Software\Classes\.pbox" /f >nul 2>nul
reg delete "HKCU\Software\Classes\PocketBox.Container" /f >nul 2>nul
rmdir /S /Q "%LOCALAPPDATA%\Programs\PocketBox" 2>nul
rmdir /S /Q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\PocketBox" 2>nul
rmdir /S /Q "%APPDATA%\PocketBox" 2>nul
echo PocketBox file association, launcher, file icon, and saved language preference removed for this Windows user.
pause
