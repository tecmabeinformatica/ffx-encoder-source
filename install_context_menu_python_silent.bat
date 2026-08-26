@echo off
reg import "%~dp0install_context_menu_python.reg" >nul
if errorlevel 1 (
    echo ERRO: nao foi possivel instalar o menu de contexto Python.
    pause
    exit /b 1
)
echo Menu de contexto Python instalado com sucesso.
pause

