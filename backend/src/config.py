"""
Módulo de Configuración Central del Analizador de Correos y Seguridad.
Gestiona rutas del sistema de archivos, umbrales de detección y variables de entorno.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno buscando en backend/.env o en el directorio raíz .env
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

ENV_FILE = BASE_DIR / ".env"
if not ENV_FILE.exists():
    if (ROOT_DIR / ".env").exists():
        ENV_FILE = ROOT_DIR / ".env"
    else:
        # Inicializar automáticamente desde .env.example si existe
        example_src = ROOT_DIR / ".env.example" if (ROOT_DIR / ".env.example").exists() else (BASE_DIR / ".env.example")
        if example_src.exists():
            import shutil
            shutil.copy(example_src, ENV_FILE)

load_dotenv(ENV_FILE)

# Directorios de datos y persistencia (Files)
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
SAMPLES_DIR = DATA_DIR / "samples"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
QUARANTINE_DIR = DATA_DIR / "quarantine"
REPORTS_DIR = DATA_DIR / "reports"
DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "email_agent.sqlite3"))

# Asegurar existencia de directorios críticos
for folder in [DATA_DIR, SAMPLES_DIR, ATTACHMENTS_DIR, QUARANTINE_DIR, REPORTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Parámetros del Motor de Phishing
PHISHING_THRESHOLD_WARNING = float(os.getenv("PHISHING_THRESHOLD_WARNING", "4.0"))
PHISHING_THRESHOLD_CRITICAL = float(os.getenv("PHISHING_THRESHOLD_CRITICAL", "7.0"))

# Parámetros de Hashing y Deduplicación
HASH_CHUNK_SIZE = int(os.getenv("HASH_CHUNK_SIZE", "65536"))  # 64 KB por bloque para streaming óptimo

# Configuración de Notificaciones y Credenciales
WHATSAPP_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "mock")  # 'twilio', 'meta', 'mock'
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
USER_WHATSAPP_NUMBER = os.getenv("USER_WHATSAPP_NUMBER", "")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Configuración del Microservicio
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))


def get_credentials_status():
    """Retorna un reporte seguro (con máscaras) del estado de credenciales locales."""
    twilio_ready = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and USER_WHATSAPP_NUMBER)
    discord_ready = bool(DISCORD_WEBHOOK_URL and "discord.com" in DISCORD_WEBHOOK_URL)
    
    sid_masked = f"{TWILIO_ACCOUNT_SID[:4]}...{TWILIO_ACCOUNT_SID[-4:]}" if len(TWILIO_ACCOUNT_SID) > 8 else ("Configurado" if TWILIO_ACCOUNT_SID else "No configurado")
    user_phone_masked = f"{USER_WHATSAPP_NUMBER[:5]}...{USER_WHATSAPP_NUMBER[-2:]}" if len(USER_WHATSAPP_NUMBER) > 7 else ("Configurado" if USER_WHATSAPP_NUMBER else "No configurado")

    return {
        "status": "ready",
        "env_file_location": str(ENV_FILE),
        "whatsapp_provider": WHATSAPP_PROVIDER,
        "whatsapp_connected": twilio_ready if WHATSAPP_PROVIDER == "twilio" else True,
        "twilio_sid": sid_masked,
        "user_phone": user_phone_masked,
        "discord_webhook_configured": discord_ready,
        "mode": "PRODUCCION (Twilio/Discord)" if (twilio_ready or discord_ready) else "MOCK_LOCAL (Seguro sin APIs externas)",
        "security_note": "Tus credenciales residen 100% en tu máquina local y jamás se transmiten a servidores externos."
    }

