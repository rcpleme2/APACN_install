@echo off
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   BUILD - APACN Nota Parana
echo ============================================================
echo.

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo        Instale em https://python.org e marque "Add to PATH".
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] %PY_VER%

:: Instala dependencias de build
echo.
echo [1/4] Instalando dependencias...
pip install --quiet --upgrade pyinstaller playwright python-dotenv
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas.

:: Instala Chromium
echo.
echo [2/4] Verificando Chromium (pode demorar na primeira vez)...
playwright install chromium
if errorlevel 1 (
    echo [ERRO] Falha ao instalar Chromium.
    pause
    exit /b 1
)
echo [OK] Chromium pronto.

:: Gera o executavel com PyInstaller
echo.
echo [3/4] Empacotando com PyInstaller...
if exist dist\APACN rmdir /s /q dist\APACN
if exist build\APACN rmdir /s /q build\APACN

pyinstaller apacn.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERRO] PyInstaller falhou. Verifique as mensagens acima.
    pause
    exit /b 1
)
echo [OK] Executavel gerado em dist\APACN\

:: Gera o instalador com Inno Setup
echo.
echo [4/4] Gerando instalador com Inno Setup...

set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe
if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 5\ISCC.exe

if not defined ISCC (
    echo [AVISO] Inno Setup nao encontrado.
    echo         Baixe em: https://jrsoftware.org/isdl.php
    echo         Apos instalar, execute build.bat novamente.
    echo.
    echo         O executavel standalone esta disponivel em:
    echo         dist\APACN\APACN.exe
    pause
    exit /b 0
)

if not exist dist\installer mkdir dist\installer
"%ISCC%" installer.iss
if errorlevel 1 (
    echo [ERRO] Inno Setup falhou. Verifique as mensagens acima.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD CONCLUIDO COM SUCESSO!
echo ============================================================
echo.
echo   Instalador : dist\installer\APACN_Setup_v1.0.exe
echo   Executavel : dist\APACN\APACN.exe  (pasta standalone)
echo.
pause
