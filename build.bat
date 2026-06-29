@echo off
chcp 65001 > nul
echo ================================================
echo   PDV Jamir — Build para Distribuicao
echo ================================================
echo.

cd /d "%~dp0"

echo [1/4] Instalando dependencias de build...
pip install customtkinter pyinstaller darkdetect --quiet
if %ERRORLEVEL% neq 0 (
    echo ERRO ao instalar dependencias.
    pause
    exit /b 1
)

echo [2/4] Limpando builds anteriores...
if exist "dist\PDV_Jamir_Totem" rmdir /s /q "dist\PDV_Jamir_Totem"
if exist "dist\PDV_Jamir_Admin" rmdir /s /q "dist\PDV_Jamir_Admin"
if exist "build" rmdir /s /q "build"

echo [3/4] Empacotando Totem (tela do cliente)...
pyinstaller pdv_totem.spec --noconfirm
if %ERRORLEVEL% neq 0 (
    echo ERRO ao empacotar o Totem.
    pause
    exit /b 1
)

echo [4/4] Empacotando Painel Admin...
pyinstaller pdv_admin.spec --noconfirm
if %ERRORLEVEL% neq 0 (
    echo ERRO ao empacotar o Admin.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Build concluido com sucesso!
echo.
echo   Totem : dist\PDV_Jamir_Totem\PDV_Jamir_Totem.exe
echo   Admin : dist\PDV_Jamir_Admin\PDV_Jamir_Admin.exe
echo.
echo   Copie a pasta dist\ inteira para o PC do cliente.
echo ================================================
pause
