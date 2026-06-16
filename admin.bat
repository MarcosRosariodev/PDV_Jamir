@echo off
chcp 65001 > nul
title PDV Jamir — Painel Admin

cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo  Abrindo painel administrativo...
echo  (O servidor principal deve estar rodando)
echo.
python admin\admin_app.py

if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] Painel encerrou com erro.
    pause
)
