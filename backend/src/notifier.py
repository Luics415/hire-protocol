"""
Módulo Despachador de Notificaciones para WhatsApp y Discord.
Aplica formato enriquecido, gestión de prioridades y respeto al modo silencio.
"""

import requests
from typing import Dict, Any, Optional
from .config import (
    WHATSAPP_PROVIDER, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
    TWILIO_WHATSAPP_FROM, USER_WHATSAPP_NUMBER, DISCORD_WEBHOOK_URL
)
from .database import DatabaseManager


class Notifier:
    """Despachador central de alertas hacia WhatsApp y canal de bitácora en Discord."""

    @classmethod
    def format_whatsapp_job_message(cls, data: Dict[str, Any]) -> str:
        """Genera el mensaje formateado para WhatsApp de una postulación."""
        job = data.get("job_metadata", {})
        email_data = data.get("email", {})
        security = data.get("security", {})

        salary_line = f"\n💰 *Salario*: {job.get('salary')}" if job.get("salary") else ""
        modality_line = f"\n🏠 *Modalidad*: {job.get('modality')}" if job.get("modality") else ""
        stack_line = f"\n🛠️ *Stack*: {', '.join(job.get('tech_stack', []))}" if job.get("tech_stack") else ""

        action_section = ""
        if job.get("action_required"):
            action_section = (
                "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ *ACCIÓN REQUERIDA*: {job.get('action_description')}"
            )

        return (
            f"{job.get('stage_emoji', '💼')} *ACTUALIZACIÓN DE POSTULACIÓN*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏢 *Empresa*: {job.get('company_name')}\n"
            f"🎯 *Posición*: {job.get('role_title')}\n"
            f"📌 *Etapa*: {job.get('stage_label')}\n"
            f"🌐 *Plataforma*: {job.get('platform')}{salary_line}{modality_line}{stack_line}\n"
            f"💬 *Asunto*: {email_data.get('subject', '')}\n"
            f"🔒 *Seguridad*: Verificado (Score Phishing: {security.get('score', 0)}/10){action_section}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "ℹ️ _Este correo NO ha sido respondido automáticamente._"
        )

    @classmethod
    def format_whatsapp_threat_message(cls, data: Dict[str, Any]) -> str:
        """Genera alerta crítica de seguridad para WhatsApp si se detecta phishing."""
        security = data.get("security", {})
        email_data = data.get("email", {})

        indicators_text = ""
        for ind in security.get("indicators", []):
            indicators_text += f"\n  • *{ind['category']}*: {ind['description']}"

        return (
            "🚨 *ALERTA DE SEGURIDAD: CORREO SOSPECHOSO DETECTADO*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Nivel de Riesgo*: {security.get('score')}/10.0 ({security.get('verdict')})\n"
            f"👤 *Remitente*: {email_data.get('sender')}\n"
            f"💬 *Asunto*: {email_data.get('subject')}\n"
            f"🔍 *Patrones Detectados*:{indicators_text}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔒 *Firma SHA-256*: `{security.get('body_sha256', '')[:16]}...`\n"
            "🛑 *Acción*: Correo aislado en cuarentena. No abras ningún enlace."
        )

    @classmethod
    def send_whatsapp(cls, message_text: str) -> Dict[str, Any]:
        """Envía el mensaje a WhatsApp según el proveedor configurado o simula si está en modo mock."""
        # Verificar si el usuario activó !silencio
        if DatabaseManager.is_silenced():
            return {
                "sent": False,
                "reason": "Modo silencio activo en este momento. Alerta retenida.",
                "provider": WHATSAPP_PROVIDER
            }

        if WHATSAPP_PROVIDER == "twilio" and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and USER_WHATSAPP_NUMBER:
            try:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
                payload = {
                    "From": TWILIO_WHATSAPP_FROM,
                    "To": f"whatsapp:{USER_WHATSAPP_NUMBER}",
                    "Body": message_text
                }
                res = requests.post(url, data=payload, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=10)
                return {"sent": res.status_code in [200, 201], "status_code": res.status_code, "provider": "twilio"}
            except Exception as e:
                return {"sent": False, "error": str(e), "provider": "twilio"}

        # Modo Mock / Local (para pruebas sin requerir API keys externas)
        return {
            "sent": True,
            "provider": "mock",
            "message_preview": message_text[:120] + "...",
            "full_message": message_text
        }

    @classmethod
    def send_discord_log(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Envía un registro técnico detallado con Embed a Discord si el webhook está configurado."""
        if not DISCORD_WEBHOOK_URL:
            return {"sent": False, "reason": "DISCORD_WEBHOOK_URL no configurado"}

        security = data.get("security", {})
        job = data.get("job_metadata", {})
        email_data = data.get("email", {})

        # Color según estado: Verde (Seguro/Oferta), Azul (Entrevista), Amarillo (Sospechoso), Rojo (Phishing)
        verdict = security.get("verdict", "SAFE")
        if verdict == "PHISHING":
            color = 0xED4245  # Rojo
        elif verdict == "SUSPICIOUS":
            color = 0xFEE75C  # Amarillo
        elif job.get("stage") == "OFERTA":
            color = 0x57F287  # Verde brillante
        elif job.get("stage") in ["ENTREVISTA", "PRUEBA_TECNICA"]:
            color = 0x5865F2  # Azul Discord
        else:
            color = 0x95A5A6  # Gris

        fields = [
            {"name": "Remitente", "value": email_data.get("sender", "N/A"), "inline": True},
            {"name": "Plataforma / ATS", "value": job.get("platform", "N/A"), "inline": True},
            {"name": "Etapa", "value": f"{job.get('stage_emoji', '')} {job.get('stage_label', 'N/A')}", "inline": True},
            {"name": "Empresa", "value": job.get("company_name", "N/A"), "inline": True},
            {"name": "Puesto", "value": job.get("role_title", "N/A"), "inline": True},
            {"name": "Score Phishing", "value": f"{security.get('score', 0)}/10.0 ({verdict})", "inline": True},
        ]

        if job.get("salary"):
            fields.append({"name": "Salario Detectado", "value": job.get("salary"), "inline": True})
        if job.get("modality"):
            fields.append({"name": "Modalidad", "value": job.get("modality"), "inline": True})
        if job.get("tech_stack"):
            fields.append({"name": "Stack Tecnológico", "value": ", ".join(job.get("tech_stack")), "inline": False})

        embed = {
            "title": f"Registro de Correo: {email_data.get('subject', 'Sin Asunto')}",
            "color": color,
            "fields": fields,
            "footer": {"text": f"SHA-256: {security.get('body_sha256', 'N/A')[:24]}..."},
        }

        try:
            res = requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}, timeout=8)
            return {"sent": res.status_code == 204, "status_code": res.status_code}
        except Exception as e:
            return {"sent": False, "error": str(e)}
