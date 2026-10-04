"""
Módulo de Configuración Central del Analizador de Correos y Seguridad.
Gestiona rutas del sistema de archivos, umbrales de detección y variables de entorno.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno si existe un archivo .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

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

# Configuración de Notificaciones
WHATSAPP_PROVIDER = os.getenv("WHATSAPP_PROVIDER", "mock")  # 'twilio', 'meta', 'mock'
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
USER_WHATSAPP_NUMBER = os.getenv("USER_WHATSAPP_NUMBER", "")

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Configuración del Microservicio
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
