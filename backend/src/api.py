"""
Servidor API REST (FastAPI) para Integración con N8N y Webhooks.
Provee endpoints para análisis de correos, ejecución de comandos de WhatsApp y gestión de duplicados.
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from contextlib import asynccontextmanager
from .email_parser import EmailParser, ParsedEmail
from .phishing_detector import PhishingDetector
from .job_classifier import JobClassifier
from .duplicate_finder import DuplicateFinder
from .command_handler import CommandHandler
from .database import DatabaseManager
from .notifier import Notifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    DatabaseManager.init_db()
    yield


app = FastAPI(
    title="Hire Protocol API",
    description="Motor local en Python para análisis forense de correos, detección de phishing y seguimiento de postulaciones conectado a n8n.",
    version="1.0.0",
    lifespan=lifespan
)


# Modelos Pydantic para validación de datos
class EmailAnalysisRequest(BaseModel):
    sender: str = Field(..., description="Dirección o nombre del remitente (From)")
    recipient: Optional[str] = Field("", description="Destinatario (To)")
    subject: str = Field(..., description="Asunto del correo")
    text: Optional[str] = Field("", description="Cuerpo en texto plano")
    html: Optional[str] = Field("", description="Cuerpo en formato HTML")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Cabeceras crudas opcionales")
    spf_pass: Optional[bool] = Field(None, description="Resultado de verificación SPF")
    dkim_pass: Optional[bool] = Field(None, description="Resultado de verificación DKIM")


class WhatsAppCommandRequest(BaseModel):
    message: str = Field(..., description="Texto del comando enviado por el usuario (ej: !resumen)")
    sender_number: Optional[str] = Field("", description="Número de teléfono remitente")


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Email Security & Job Tracker Engine",
        "version": "1.0.0",
        "endpoints": [
            "/analyze-email",
            "/whatsapp-command",
            "/duplicates/scan",
            "/duplicates/clean",
            "/status",
            "/credentials"
        ]
    }


@app.get("/credentials")
def check_credentials():
    """Diagnóstico seguro del estado de vinculación de credenciales y cuentas locales."""
    from .config import get_credentials_status
    return get_credentials_status()


@app.get("/status")
def get_system_status():
    """Retorna métricas del sistema, estadísticas y estado del modo silencio."""
    stats = DatabaseManager.get_summary_stats()
    is_silenced = DatabaseManager.is_silenced()
    return {
        "status": "healthy",
        "silence_mode_active": is_silenced,
        "database_stats": stats
    }


@app.post("/analyze-email")
def analyze_email_endpoint(payload: EmailAnalysisRequest):
    """
    Endpoint principal consumido por el nodo HTTP Request de n8n.
    Analiza phishing, clasifica vacantes, persiste en SQLite y despacha alertas.
    """
    # 1. Comprobar si el remitente o dominio está en lista negra (!ignorar)
    if DatabaseManager.is_blacklisted(payload.sender):
        return {
            "route": "IGNORED",
            "message": f"Remitente '{payload.sender}' ignorado por lista negra personal.",
            "action_taken": "SILENT_DROP"
        }

    # 2. Parsear el correo y extraer strings, hipervínculos y tokens
    parsed = EmailParser.parse_dict({
        "sender": payload.sender,
        "recipient": payload.recipient,
        "subject": payload.subject,
        "body_plain": payload.text,
        "body_html": payload.html,
        "headers": payload.headers,
        "spf_pass": payload.spf_pass,
        "dkim_pass": payload.dkim_pass
    })

    # 3. Ejecutar Motor de Seguridad y Phishing
    phishing_result = PhishingDetector.analyze(parsed)
    phishing_dict = asdict(phishing_result)

    # 4. Clasificar si es una Postulación Laboral
    job_metadata = JobClassifier.classify(parsed)
    job_dict = asdict(job_metadata)

    # 5. Manejo de Rutas y Persistencia
    bundle_data = {
        "email": {
            "sender": parsed.sender,
            "sender_name": parsed.sender_name,
            "sender_domain": parsed.sender_domain,
            "subject": parsed.subject,
            "recipient": parsed.recipient
        },
        "security": phishing_dict,
        "job_metadata": job_dict
    }

    whatsapp_response = None
    discord_response = None

    if phishing_result.verdict in ["PHISHING", "SUSPICIOUS"]:
        # Guardar registro en tabla de cuarentena
        DatabaseManager.save_quarantine_log({
            "sender": parsed.sender,
            "subject": parsed.subject,
            "score": phishing_result.score,
            "verdict": phishing_result.verdict,
            "indicators": [asdict(i) for i in phishing_result.indicators],
            "body_sha256": phishing_result.body_sha256,
            "quarantine_path": phishing_result.quarantine_path
        })

        # Alerta crítica a WhatsApp si es Phishing severo
        alert_msg = Notifier.format_whatsapp_threat_message(bundle_data)
        whatsapp_response = Notifier.send_whatsapp(alert_msg)
        discord_response = Notifier.send_discord_log(bundle_data)

        return {
            "route": "PHISHING",
            "verdict": phishing_result.verdict,
            "score": phishing_result.score,
            "is_quarantined": True,
            "quarantine_file": phishing_result.quarantine_path,
            "whatsapp_alert": whatsapp_response,
            "discord_log": discord_response,
            "data": bundle_data
        }

    elif job_metadata.is_job_related:
        # Guardar en base de datos de postulaciones
        app_id = DatabaseManager.save_job_application({
            "company_name": job_metadata.company_name,
            "role_title": job_metadata.role_title,
            "platform": job_metadata.platform,
            "stage": job_metadata.stage,
            "salary": job_metadata.salary,
            "modality": job_metadata.modality,
            "tech_stack": job_metadata.tech_stack,
            "subject": parsed.subject,
            "sender": parsed.sender,
            "action_required": job_metadata.action_required,
            "action_description": job_metadata.action_description
        })

        # Enviar notificación formateada a WhatsApp
        job_msg = Notifier.format_whatsapp_job_message(bundle_data)
        whatsapp_response = Notifier.send_whatsapp(job_msg)
        discord_response = Notifier.send_discord_log(bundle_data)

        return {
            "route": "JOB_UPDATE",
            "application_id": app_id,
            "stage": job_metadata.stage,
            "company": job_metadata.company_name,
            "role": job_metadata.role_title,
            "whatsapp_notification": whatsapp_response,
            "discord_log": discord_response,
            "data": bundle_data
        }

    else:
        # Correo normal sin relevancia laboral ni amenazas
        return {
            "route": "NORMAL",
            "message": "Correo analizado. Sin relevancia de postulaciones ni amenazas de phishing.",
            "data": bundle_data
        }


@app.post("/whatsapp-command")
def whatsapp_command_endpoint(payload: WhatsAppCommandRequest):
    """
    Endpoint para procesar mensajes y comandos entrantes desde WhatsApp vía Webhook de n8n.
    """
    reply_text = CommandHandler.handle_command(payload.message)
    return {
        "status": "success",
        "command_received": payload.message,
        "reply": reply_text
    }


@app.post("/duplicates/scan")
def scan_duplicates_endpoint():
    """Ejecuta el escaneo de archivos duplicados por hashes y genera el reporte JSON."""
    report = DuplicateFinder.scan_directory()
    return asdict(report)


@app.post("/duplicates/clean")
def clean_duplicates_endpoint():
    """Aísla archivos duplicados liberando espacio en disco de forma segura."""
    result = DuplicateFinder.clean_duplicates()
    return result
