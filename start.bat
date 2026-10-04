@echo off
chcp 65001 >nul
title Hire Protocol - Local Security & Career Agent Launcher

echo ======================================================================
echo   🛡️  HIRE PROTOCOL - LOCAL AGENT ^& TOOL HUB
echo   Agente Inteligente de Postulaciones, Antiphishing y Orquestador n8n
echo ======================================================================
echo.

:: 1. Verificar Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python no está instalado o no se encuentra en el PATH.
    echo Por favor instala Python 3.10+ desde https://www.python.org/
    pause
    exit /b 1
)

:: 2. Crear entorno virtual si no existe
if not exist "backend\.venv" (
    echo [PASO 1/3] Creando entorno virtual Python en backend\.venv...
    python -m venv backend\.venv
)

:: 3. Instalar dependencias si no existen paquetes
if not exist "backend\.venv\Lib\site-packages\fastapi" (
    echo [PASO 2/3] Instalando dependencias en el entorno virtual...
    call backend\.venv\Scripts\pip install -r backend\requirements.txt
)

:: 4. Inicializar archivo de variables de entorno si no existe
if not exist "backend\.env" (
    if exist ".env.example" (
        echo [PASO 3/3] Inicializando backend\.env desde .env.example...
        copy .env.example backend\.env >nul
    )
)

echo.
echo ======================================================================
echo   Selecciona una opción de Hire Protocol:
echo ======================================================================
echo   [1] Abrir Hub Interactivo ^& Buscador de Herramientas (Recomendado)
echo   [2] Iniciar Servidor Directamente (FastAPI en http://127.0.0.1:8000)
echo   [3] Ver Estado Seguro de Credenciales Locales (--credentials)
echo   [4] Ejecutar Suite de Pruebas (pytest)
echo   [5] Ejecutar Laboratorio Demo (test_lab.py)
echo   [6] Iniciar n8n nativamente (npx n8n)
echo   [0] Salir
echo ======================================================================
set /p opt="Opción elegida [1]: "

if "%opt%"=="" set opt=1
if "%opt%"=="1" goto hub
if "%opt%"=="2" goto serve
if "%opt%"=="3" goto creds
if "%opt%"=="4" goto test
if "%opt%"=="5" goto lab
if "%opt%"=="6" goto n8n
if "%opt%"=="0" exit /b 0

:hub
echo.
call backend\.venv\Scripts\python backend\run_service.py
goto end

:serve
echo.
echo [INFO] Iniciando microservicio FastAPI de Hire Protocol...
call backend\.venv\Scripts\python backend\run_service.py --serve
goto end

:creds
echo.
call backend\.venv\Scripts\python backend\run_service.py --credentials
pause
goto end

:test
echo.
call backend\.venv\Scripts\python -m pytest -v backend\tests
pause
goto end

:lab
echo.
call backend\.venv\Scripts\python backend\test_lab.py
pause
goto end

:n8n
echo.
echo [INFO] Lanzando n8n (http://localhost:5678)...
npx n8n
goto end

:end
