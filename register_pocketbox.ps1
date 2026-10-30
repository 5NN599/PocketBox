$ErrorActionPreference = 'Stop'
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\PocketBox'
$launcher = Join-Path $installDir 'PocketBox.exe'
$fileIcon = Join-Path $installDir 'PocketBox_File.ico'
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw "PocketBox launcher not found: $launcher"
}
if (-not (Test-Path -LiteralPath $fileIcon -PathType Leaf)) {
    throw "PocketBox file icon not found: $fileIcon"
}

$extensionKey = 'HKCU:\Software\Classes\.pbox'
$classKey = 'HKCU:\Software\Classes\PocketBox.Container'
New-Item -Path $extensionKey -Force | Out-Null
Set-Item -Path $extensionKey -Value 'PocketBox.Container'
New-Item -Path $classKey -Force | Out-Null
Set-Item -Path $classKey -Value 'PocketBox Package'
New-Item -Path (Join-Path $classKey 'DefaultIcon') -Force | Out-Null
Set-Item -Path (Join-Path $classKey 'DefaultIcon') -Value ('"' + $fileIcon + '"')
$openCommandKey = Join-Path $classKey 'shell\open\command'
New-Item -Path $openCommandKey -Force | Out-Null
$placeholder = [char]37 + '1'
$openCommand = '"' + $launcher + '" "' + $placeholder + '"'
Set-Item -Path $openCommandKey -Value $openCommand
# Add a Start Menu shortcut for the GUI packager.
$startMenuDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\PocketBox'
New-Item -Path $startMenuDir -ItemType Directory -Force | Out-Null
$shortcutPath = Join-Path $startMenuDir 'PocketBox Builder.lnk'
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $installDir 'PocketBoxBuilder.exe'
$shortcut.WorkingDirectory = $installDir
$shortcut.IconLocation = $launcher + ',0'
$shortcut.Save()

# Ask Windows Explorer to refresh file associations and icon cache.
Add-Type -Namespace PocketBox -Name ShellNotify -MemberDefinition '[System.Runtime.InteropServices.DllImport("shell32.dll")] public static extern void SHChangeNotify(uint eventId, uint flags, System.IntPtr item1, System.IntPtr item2);'
[PocketBox.ShellNotify]::SHChangeNotify(0x08000000, 0x0000, [System.IntPtr]::Zero, [System.IntPtr]::Zero)

Write-Host 'Registered .pbox files for the current Windows user.'
Write-Host "Launcher: $launcher"
Write-Host "File icon: $fileIcon"
Write-Host "Start Menu shortcut: $shortcutPath"
