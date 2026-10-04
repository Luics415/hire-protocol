"""
Punto de Entrada Principal (Runner & CLI).
Permite arrancar el servidor FastAPI para n8n o ejecutar utilidades directas por consola.
Incluye asistente interactivo de credenciales locales y diagnóstico de cuentas.
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

from src.config import API_HOST, API_PORT, ENV_FILE, get_credentials_status
from src.database import DatabaseManager
from src.duplicate_finder import DuplicateFinder
from src.command_handler import CommandHandler


def run_interactive_configuration():
    """Asistente interactivo por consola para vincular credenciales y licencias locales."""
    print("=" * 70)
    print("🔐 ASISTENTE INTERACTIVO DE CREDENCIALES Y CUENTAS LOCALES")
    print("=" * 70)
    print("ℹ️  Tus claves y licencias se guardan exclusivamente en tu archivo .env local.")
    print("   El agente opera 100% en tu máquina y nunca comparte tus datos con la nube.\n")

    from src.config import (
        WHATSAPP_PROVIDER, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
        TWILIO_WHATSAPP_FROM, USER_WHATSAPP_NUMBER, DISCORD_WEBHOOK_URL
    )

    print("1️⃣  PROVEEDOR DE MENSAJERÍA WHATSAPP:")
    print("   • 'mock': Modo simulado en consola (ideal para pruebas locales sin costo)")
    print("   • 'twilio': Conexión con API de Twilio WhatsApp")
    print("   • 'meta': Conexión con WhatsApp Business Cloud API")
    provider = input(f"   Selecciona proveedor [{WHATSAPP_PROVIDER}]: ").strip() or WHATSAPP_PROVIDER

    account_sid = TWILIO_ACCOUNT_SID
    auth_token = TWILIO_AUTH_TOKEN
    from_number = TWILIO_WHATSAPP_FROM
    user_number = USER_WHATSAPP_NUMBER

    if provider.lower() == "twilio":
        print("\n2️⃣  CREDENCIALES DE TWILIO:")
        prompt_sid = f"[{account_sid[:6]}...]" if account_sid else "[Vacío]"
        account_sid = input(f"   Twilio Account SID {prompt_sid}: ").strip() or account_sid

        prompt_token = f"[{auth_token[:4]}...]" if auth_token else "[Vacío]"
        auth_token = input(f"   Twilio Auth Token {prompt_token}: ").strip() or auth_token

        from_number = input(f"   Twilio WhatsApp Remitente [{from_number}]: ").strip() or from_number

        prompt_user = f"[{user_number}]" if user_number else "[Ej: +5215500000000]"
        user_number = input(f"   Tu número de WhatsApp personal {prompt_user}: ").strip() or user_number

    print("\n3️⃣  BITÁCORA TÉCNICA EN DISCORD (Opcional):")
    prompt_discord = f"[{DISCORD_WEBHOOK_URL[:30]}...]" if DISCORD_WEBHOOK_URL else "[Opcional]"
    discord_url = input(f"   Webhook URL de Discord {prompt_discord}: ").strip() or DISCORD_WEBHOOK_URL

    env_content = f"""# =====================================================================
# VARIABLES DE ENTORNO: EMAIL SECURITY & JOB TRACKER AGENT (LOCAL)
# =====================================================================

# Servidor API FastAPI
API_HOST={API_HOST}
API_PORT={API_PORT}

# Proveedor de WhatsApp: 'mock' (local testing), 'twilio' o 'meta'
WHATSAPP_PROVIDER={provider.lower()}

# Configuración Twilio WhatsApp (Credenciales locales)
TWILIO_ACCOUNT_SID={account_sid}
TWILIO_AUTH_TOKEN={auth_token}
TWILIO_WHATSAPP_FROM={from_number}
USER_WHATSAPP_NUMBER={user_number}

# Bitácora de Registro en Discord (Opcional)
DISCORD_WEBHOOK_URL={discord_url}

# Umbrales Heurísticos de Phishing (0.0 a 10.0)
PHISHING_THRESHOLD_WARNING=4.0
PHISHING_THRESHOLD_CRITICAL=7.0

# Tamaño de bloque de lectura para hashing criptográfico (64 KB)
HASH_CHUNK_SIZE=65536
"""
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(env_content)

    print("\n✅ ¡Credenciales locales guardadas con éxito en:")
    print(f"   📁 {ENV_FILE}")
    print("\n🔒 Este archivo está protegido y jamás se subirá a Git.")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Email Security & Job Tracker Runner")
    parser.add_argument("--serve", action="store_true", help="Inicia el servidor API FastAPI para n8n")
    parser.add_argument("--host", default=API_HOST, help=f"Host del servidor (por defecto: {API_HOST})")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"Puerto del servidor (por defecto: {API_PORT})")
    parser.add_argument("--configure", action="store_true", help="Asistente interactivo para vincular licencias y credenciales locales")
    parser.add_argument("--credentials", action="store_true", help="Muestra el estado seguro de credenciales configuradas")
    parser.add_argument("--scan-duplicates", action="store_true", help="Ejecuta escáner de archivos duplicados por hash")
    parser.add_argument("--clean-duplicates", action="store_true", help="Limpia archivos duplicados a carpeta de backup")
    parser.add_argument("--cmd", type=str, help="Prueba un comando de WhatsApp (ej: --cmd '!resumen')")

    args = parser.parse_args()

    if args.configure:
        run_interactive_configuration()
    elif args.credentials:
        status = get_credentials_status()
        print("\n🔐 ESTADO DE CREDENCIALES Y CUENTAS LOCALES:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for k, v in status.items():
            print(f"  • {k}: {v}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
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
    else:
        # Por defecto arrancar el servidor
        print(f"🚀 Iniciando Email Security API en http://{args.host}:{args.port}")
        print("📡 Listo para recibir peticiones de los nodos de n8n.")
        print(f"🔐 Archivo de credenciales activo: {ENV_FILE}")
        uvicorn.run("src.api:app", host=args.host, port=args.port, reload=True)


if __name__ == "__main__":
    main()
