@echo off
setlocal
set "APPDIR=%~dp0"

echo =========================================================
echo   DESINSTALANDO FFX ENCODER GUI
echo =========================================================
echo.

reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\FFX Encoder GUI" /f >nul 2>nul
reg delete "HKCU\Software\Classes\Directory\Background\shell\FFX Encoder GUI" /f >nul 2>nul
reg delete "HKCU\Software\Classes\Directory\shell\FFX Encoder GUI" /f >nul 2>nul

echo Removendo arquivos instalados...
echo A pasta Capas sera preservada, caso exista.

set "FFX_UNINSTALL_DIR=%APPDIR%"
start "" /min powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; $app=$env:FFX_UNINSTALL_DIR; if (Test-Path -LiteralPath $app) { Get-ChildItem -LiteralPath $app -Force | Where-Object { $_.Name -ne 'Capas' } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; if (-not (Test-Path -LiteralPath (Join-Path $app 'Capas'))) { Remove-Item -LiteralPath $app -Force -ErrorAction SilentlyContinue } }"
echo.
echo Desinstalacao iniciada. A pasta Capas sera mantida.
pause
