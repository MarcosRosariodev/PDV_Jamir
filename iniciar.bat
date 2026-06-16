@echo off
chcp 65001 > nul
title PDV Jamir — Totem Cliente

cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo  Iniciando PDV Jamir...
python main.py

if %errorlevel% neq 0 (
    echo.
    echo  [ERRO] O sistema encerrou com erro.
    pause
)
