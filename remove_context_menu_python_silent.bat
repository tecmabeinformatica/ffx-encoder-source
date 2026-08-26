@echo off
reg import "%~dp0remove_context_menu_python.reg" >nul
if errorlevel 1 (
    echo ERRO: nao foi possivel remover o menu de contexto Python.
    pause
    exit /b 1
)
echo Menu de contexto Python removido com sucesso.
pause

