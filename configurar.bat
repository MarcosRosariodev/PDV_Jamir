@echo off
chcp 65001 > nul
title PDV Jamir — Configuração

echo.
echo  ╔══════════════════════════════════════╗
echo  ║     PDV Jamir — Instalação           ║
echo  ╚══════════════════════════════════════╝
echo.

:: Verifica Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRO] Python não encontrado!
    echo  Baixe em: https://www.python.org/downloads/
    echo  Marque a opção "Add Python to PATH" na instalação.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo  Python: %%i

:: Cria ambiente virtual
if not exist ".venv" (
    echo.
    echo  Criando ambiente virtual...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo  [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
    echo  Ambiente virtual criado.
)

:: Ativa ambiente virtual
call .venv\Scripts\activate.bat

:: Instala dependências
echo.
echo  Instalando dependências...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo  [ERRO] Falha ao instalar dependências.
    pause
    exit /b 1
)
echo  Dependências instaladas com sucesso!

:: Inicializa banco de dados
echo.
echo  Configurando banco de dados...
python database\db.py
if %errorlevel% neq 0 (
    echo  [AVISO] Possível erro na configuração do banco.
)

echo.
echo  ╔══════════════════════════════════════╗
echo  ║  Instalação concluída!               ║
echo  ║                                      ║
echo  ║  Para iniciar o sistema use:         ║
echo  ║    iniciar.bat                       ║
echo  ║                                      ║
echo  ║  Para o painel admin:                ║
echo  ║    admin.bat                         ║
echo  ╚══════════════════════════════════════╝
echo.
pause
