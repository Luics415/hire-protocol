#!/usr/bin/env bash
# ======================================================================
#   🛡️  JOB SECURITY & APPLICATION TRACKING AGENT - LAUNCHER
#   Script de inicio universal para Linux y macOS
# ======================================================================

set -e

echo "======================================================================"
echo "  🛡️  JOB SECURITY & APPLICATION TRACKING AGENT"
echo "  Agente Local de Empleo, Antiphishing y Orquestador n8n"
echo "======================================================================"
echo ""

# 1. Detectar Python
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo "[ERROR] Python 3 no se encuentra instalado en el sistema."
    echo "Por favor instala Python 3.10+ para continuar."
    exit 1
fi

# 2. Crear entorno virtual si no existe
if [ ! -d "backend/.venv" ]; then
    echo "[PASO 1/3] Creando entorno virtual Python en backend/.venv..."
    $PYTHON_BIN -m venv backend/.venv
fi

# 3. Instalar dependencias si no están instaladas
if [ ! -f "backend/.venv/bin/pytest" ] && [ ! -d "backend/.venv/lib" ]; then
    echo "[PASO 2/3] Instalando dependencias en el entorno virtual..."
    ./backend/.venv/bin/pip install --upgrade pip
    ./backend/.venv/bin/pip install -r backend/requirements.txt
fi

# 4. Inicializar archivo de variables de entorno si no existe
if [ ! -f "backend/.env" ]; then
    if [ -f ".env.example" ]; then
        echo "[PASO 3/3] Inicializando backend/.env desde .env.example..."
        cp .env.example backend/.env
    fi
fi

echo ""
echo "======================================================================"
echo "  Selecciona una opción:"
echo "======================================================================"
echo "  [1] Iniciar Servidor Backend (FastAPI en http://127.0.0.1:8000)"
echo "  [2] Asistente de Licencias y Credenciales (--configure)"
echo "  [3] Ver Estado de Credenciales Locales (--credentials)"
echo "  [4] Ejecutar Suite de Pruebas (pytest)"
echo "  [5] Ejecutar Laboratorio Demo (test_lab.py)"
echo "  [6] Iniciar n8n nativamente (npx n8n)"
echo "  [0] Salir"
echo "======================================================================"
read -p "Opción elegida [1]: " opt
opt=${opt:-1}

case "$opt" in
    1)
        echo ""
        echo "[INFO] Iniciando microservicio FastAPI..."
        ./backend/.venv/bin/python backend/run_service.py --serve
        ;;
    2)
        echo ""
        ./backend/.venv/bin/python backend/run_service.py --configure
        ;;
    3)
        echo ""
        ./backend/.venv/bin/python backend/run_service.py --credentials
        ;;
    4)
        echo ""
        ./backend/.venv/bin/python -m pytest -v backend/tests
        ;;
    5)
        echo ""
        ./backend/.venv/bin/python backend/test_lab.py
        ;;
    6)
        echo ""
        echo "[INFO] Lanzando n8n (http://localhost:5678)..."
        npx n8n
        ;;
    0)
        exit 0
        ;;
    *)
        echo "Opción no válida."
        exit 1
        ;;
esac
