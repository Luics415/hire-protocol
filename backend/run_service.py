"""
Punto de Entrada Principal (Runner & CLI).
Permite arrancar el servidor FastAPI para n8n o ejecutar utilidades directas por consola.
"""

import sys
import argparse
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

from src.config import API_HOST, API_PORT
from src.database import DatabaseManager
from src.duplicate_finder import DuplicateFinder
from src.command_handler import CommandHandler


def main():
    parser = argparse.ArgumentParser(description="Email Security & Job Tracker Runner")
    parser.add_argument("--serve", action="store_true", help="Inicia el servidor API FastAPI para n8n")
    parser.add_argument("--host", default=API_HOST, help=f"Host del servidor (por defecto: {API_HOST})")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"Puerto del servidor (por defecto: {API_PORT})")
    parser.add_argument("--scan-duplicates", action="store_true", help="Ejecuta escáner de archivos duplicados por hash")
    parser.add_argument("--clean-duplicates", action="store_true", help="Limpia archivos duplicados a carpeta de backup")
    parser.add_argument("--cmd", type=str, help="Prueba un comando de WhatsApp (ej: --cmd '!resumen')")

    args = parser.parse_args()

    # Si no se pasan argumentos, por defecto arrancar el servidor
    if len(sys.argv) == 1 or args.serve:
        print(f"🚀 Iniciando Email Security API en http://{args.host}:{args.port}")
        print("📡 Listo para recibir peticiones de los nodos de n8n.")
        uvicorn.run("src.api:app", host=args.host, port=args.port, reload=True)
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
        print(f"🤖 Ejecutando comando: {args.cmd}")
        reply = CommandHandler.handle_command(args.cmd)
        print("\n--- Respuesta enviada a WhatsApp ---")
        print(reply)
        print("-------------------------------------")


if __name__ == "__main__":
    main()
