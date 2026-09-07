@echo off
rem Atalho da equipe: clique duas vezes para abrir o assistente de aportes.
rem Nao precisa de terminal, nem de Claude Code, nem de conta em lugar nenhum.
title Assistente de Aportes - Escrituracao
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo   O ambiente ainda nao foi instalado nesta maquina.
  echo   Siga o INSTALAR.md, na pasta do projeto.
  echo.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" "scripts\abrir.py"

if errorlevel 1 (
  echo.
  echo   O assistente parou com erro. Copie a mensagem acima e mostre
  echo   para o responsavel pelo projeto.
  echo.
  pause
)
