"""
Punto de Entrada Principal (Runner & CLI) de Hire Protocol.
Despliega el Hub interactivo con buscador de herramientas,
gestor de credenciales persistentes (SQLite + .env) y servidor FastAPI.
"""

import sys
import argparse
import subprocess
import uvicorn
from pathlib import Path

# Asegurar codificación UTF-8 en terminales Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Asegurar que 'src' esté en el path de Python
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import API_HOST, API_PORT, ENV_FILE, get_credentials_status
from src.database import DatabaseManager
from src.duplicate_finder import DuplicateFinder
from src.command_handler import CommandHandler
from src.tool_connector import ToolConnectorHub


def start_server(host=API_HOST, port=API_PORT):
    """Inicia el servidor REST de Hire Protocol con FastAPI y Uvicorn."""
    print(f"\n🚀 Iniciando Hire Protocol API en http://{host}:{port}")
    print("📡 Listo para recibir peticiones de los nodos de n8n y webhooks.")
    print(f"🔐 Archivo de configuración local activo: {ENV_FILE}")
    uvicorn.run("src.api:app", host=host, port=port, reload=True)


def run_tests_and_lab():
    """Ejecuta la suite de pruebas unitarias y el laboratorio interactivo."""
    print("\n🧪 Ejecutando pruebas unitarias con pytest...")
    subprocess.run([sys.executable, "-m", "pytest", "-v", "tests"], check=False)
    print("\n🔬 Ejecutando laboratorio de demostración end-to-end...")
    subprocess.run([sys.executable, "test_lab.py"], check=False)


def main():
    parser = argparse.ArgumentParser(description="Hire Protocol - Local Security & Career Agent Runner")
    parser.add_argument("--hub", action="store_true", help="Abre el Hub interactivo con buscador de herramientas")
    parser.add_argument("--serve", action="store_true", help="Inicia el servidor API FastAPI directamente")
    parser.add_argument("--host", default=API_HOST, help=f"Host del servidor (por defecto: {API_HOST})")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"Puerto del servidor (por defecto: {API_PORT})")
    parser.add_argument("--configure", action="store_true", help="Asistente interactivo para vincular licencias y credenciales")
    parser.add_argument("--credentials", action="store_true", help="Muestra el estado seguro de credenciales configuradas")
    parser.add_argument("--scan-duplicates", action="store_true", help="Ejecuta escáner de archivos duplicados por hash")
    parser.add_argument("--clean-duplicates", action="store_true", help="Limpia archivos duplicados a carpeta de backup")
    parser.add_argument("--cmd", type=str, help="Prueba un comando de WhatsApp (ej: --cmd '!resumen')")

    args = parser.parse_args()

    # Si se pasa un comando específico
    if args.serve:
        start_server(args.host, args.port)
    elif args.configure:
        ToolConnectorHub.configure_whatsapp()
    elif args.credentials:
        status = get_credentials_status()
        print("\n🔐 ESTADO DE HERRAMIENTAS Y CUENTAS LOCALES (Hire Protocol):")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for k, v in status.items():
            print(f"  • {k}: {v}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    elif args.scan_duplicates:
        print("🔍 Escaneando archivos y calculando hashes MD5/SHA-256 en bloques...")
        report = DuplicateFinder.scan_directory()
        print(f"\n📊 Archivos escaneados: {report.total_files_scanned}")
        print(f"📁 Archivos únicos: {report.unique_files_count}")
        print(f"📑 Grupos duplicados: {report.duplicate_groups_count}")
        print(f"💾 Espacio recuperable: {report.total_wasted_mb} MB ({report.total_wasted_bytes:,} bytes)")
        for g in report.groups:
            print(f"  • SHA-256: {g.sha256[:16]}... | Original: {g.canonical_file}")
            for d in g.duplicate_files:
                print(f"    - Duplicado: {d}")
    elif args.clean_duplicates:
        print("🧹 Ejecutando aislamiento de archivos duplicados...")
        res = DuplicateFinder.clean_duplicates()
        print(res["message"])
    elif args.cmd:
        print(f"🤖 Ejecutando comando en Hire Protocol: {args.cmd}")
        reply = CommandHandler.handle_command(args.cmd)
        print("\n--- Respuesta enviada a WhatsApp ---")
        print(reply)
        print("-------------------------------------")
    else:
        # Por defecto al ejecutar sin banderas: Desplegar el Buscador y Hub interactivo
        action = ToolConnectorHub.display_hub_menu()
        if action == "serve":
            start_server(args.host, args.port)
        elif action == "test":
            run_tests_and_lab()


if __name__ == "__main__":
    main()
