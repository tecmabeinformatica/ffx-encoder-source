@echo off
setlocal
set "APPDIR=%~dp0"

echo =========================================================
echo   DESINSTALANDO FFX ENCODER 1.0 FINAL
echo =========================================================
echo.

reg delete "HKCU\Software\Classes\Directory\Background\shell\FFX Encoder 3.0" /f >nul 2>nul
reg delete "HKCU\Software\Classes\Directory\shell\FFX Encoder 3.0" /f >nul 2>nul
reg delete "HKCU\Software\Classes\Directory\Background\shell\FFX Encoder" /f >nul 2>nul
reg delete "HKCU\Software\Classes\Directory\shell\FFX Encoder" /f >nul 2>nul
reg delete "HKCU\Software\Classes\Directory\Background\shell\FFX Encoder Python 3" /f >nul 2>nul
reg delete "HKCU\Software\Classes\Directory\shell\FFX Encoder Python 3" /f >nul 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\FFX Encoder 3.0" /f >nul 2>nul

echo Menu de contexto removido.
echo Removendo arquivos instalados...
echo A pasta Capas sera preservada, caso exista.

set "CLEANUP=%TEMP%\ffx_encoder_uninstall_%RANDOM%.bat"
> "%CLEANUP%" echo @echo off
>> "%CLEANUP%" echo timeout /t 2 /nobreak ^>nul
>> "%CLEANUP%" echo if exist "%APPDIR%_internal" rmdir /s /q "%APPDIR%_internal"
>> "%CLEANUP%" echo del /q "%APPDIR%FFX Encoder 3.0.exe" ^>nul 2^>nul
>> "%CLEANUP%" echo del /q "%APPDIR%FFX Encoder Aqui.exe" ^>nul 2^>nul
>> "%CLEANUP%" echo del /q "%APPDIR%ffx.dat" ^>nul 2^>nul
>> "%CLEANUP%" echo del /q "%APPDIR%LEIA-ME.txt" ^>nul 2^>nul
>> "%CLEANUP%" echo del /q "%APPDIR%install_context_menu_python.reg" ^>nul 2^>nul
>> "%CLEANUP%" echo del /q "%APPDIR%install_context_menu_python_silent.bat" ^>nul 2^>nul
>> "%CLEANUP%" echo del /q "%APPDIR%remove_context_menu_python.reg" ^>nul 2^>nul
>> "%CLEANUP%" echo del /q "%APPDIR%remove_context_menu_python_silent.bat" ^>nul 2^>nul
>> "%CLEANUP%" echo del /q "%APPDIR%FFX Encoder Guia Completo *.pdf" ^>nul 2^>nul
>> "%CLEANUP%" echo del /q "%APPDIR%FFX Encoder * Notas da Versao.pdf" ^>nul 2^>nul
>> "%CLEANUP%" echo del /q "%APPDIR%Desinstalar FFX Encoder.bat" ^>nul 2^>nul
>> "%CLEANUP%" echo dir /b "%APPDIR%" ^| findstr /v /i /x "Capas" ^>nul 2^>nul
>> "%CLEANUP%" echo if errorlevel 1 if not exist "%APPDIR%Capas" rmdir /q "%APPDIR%" ^>nul 2^>nul
>> "%CLEANUP%" echo del "%%~f0" ^>nul 2^>nul

start "" /min cmd /c "%CLEANUP%"
echo.
echo Desinstalacao iniciada. A pasta Capas sera mantida para futuras versoes.
pause
