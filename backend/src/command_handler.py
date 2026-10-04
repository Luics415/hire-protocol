"""
Módulo de Gestión de Comandos Interactivos Bidireccionales para WhatsApp.
Procesa comandos del usuario (!estado, !pendientes, !resumen, !analizar, !duplicados, !limpiar, etc.)
y retorna mensajes amigables con emojis y formato Markdown de WhatsApp.
"""

import re
from typing import Dict, Any
from .database import DatabaseManager
from .phishing_detector import PhishingDetector
from .email_parser import EmailParser
from .duplicate_finder import DuplicateFinder


class CommandHandler:
    """Intérprete de comandos interactivos enviados por el usuario."""

    @classmethod
    def handle_command(cls, raw_message: str) -> str:
        """Punto de entrada principal para resolver comandos de WhatsApp."""
        if not raw_message or not raw_message.strip().startswith("!"):
            return cls._help_message()

        tokens = raw_message.strip().split(maxsplit=1)
        command = tokens[0].lower()
        args = tokens[1].strip() if len(tokens) > 1 else ""

        if command == "!resumen":
            return cls._cmd_resumen()
        elif command == "!estado":
            return cls._cmd_estado(args)
        elif command == "!pendientes":
            return cls._cmd_pendientes()
        elif command == "!rechazos":
            return cls._cmd_rechazos()
        elif command == "!ignorar":
            return cls._cmd_ignorar(args)
        elif command == "!analizar":
            return cls._cmd_analizar(args)
        elif command == "!cuarentena":
            return cls._cmd_cuarentena()
        elif command == "!duplicados":
            return cls._cmd_duplicados()
        elif command == "!limpiar":
            return cls._cmd_limpiar()
        elif command == "!silencio":
            return cls._cmd_silencio(args)
        elif command in ["!ayuda", "!help", "!comandos"]:
            return cls._help_message()
        else:
            return f"❌ Comando `{command}` no reconocido.\nEscribe `!ayuda` para ver la lista de comandos disponibles."

    @classmethod
    def _cmd_resumen(cls) -> str:
        stats = DatabaseManager.get_summary_stats()
        return (
            "📊 *RESUMEN DE TUS POSTULACIONES*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💼 *Total Postulaciones*: {stats['total_postulaciones']}\n"
            f"🗓️ *Entrevistas*: {stats['entrevistas']}\n"
            f"💻 *Pruebas Técnicas*: {stats['pruebas_tecnicas']}\n"
            f"🎉 *Ofertas Recibidas*: {stats['ofertas']}\n"
            f"❌ *Procesos Cerrados*: {stats['rechazos']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛡️ *Amenazas/Phishing Bloqueadas*: {stats['amenazas_bloqueadas']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 _Tip: Escribe `!pendientes` para ver qué tareas tienes por entregar._"
        )

    @classmethod
    def _cmd_estado(cls, company_query: str) -> str:
        if not company_query:
            return "⚠️ Debes indicar el nombre de la empresa.\n_Ejemplo:_ `!estado MercadoLibre`"

        app = DatabaseManager.get_application_by_company(company_query)
        if not app:
            return f"🔍 No encontré ninguna postulación registrada con el nombre *'{company_query}'*."

        salary_info = f"\n💰 *Salario*: {app['salary']}" if app.get("salary") else ""
        modality_info = f"\n🏠 *Modalidad*: {app['modality']}" if app.get("modality") else ""

        return (
            f"🏢 *ESTADO DE PROCESO: {app['company'].upper()}*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Puesto*: {app['role']}\n"
            f"📌 *Etapa Actual*: {app['stage']}\n"
            f"🌐 *Plataforma*: {app['platform']}\n"
            f"📅 *Último Correo*: {app['received_at']}{salary_info}{modality_info}\n"
            f"💬 *Asunto*: {app['subject']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ *Acción requerida*: {app.get('action_description') or 'Ninguna por ahora.'}"
        )

    @classmethod
    def _cmd_pendientes(cls) -> str:
        items = DatabaseManager.get_pending_actions()
        if not items:
            return "✨ *¡Todo al día!* No tienes pruebas técnicas ni entrevistas pendientes de respuesta."

        msg = "⏳ *POSTULACIONES PENDIENTES DE ACCIÓN*\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, it in enumerate(items, 1):
            msg += (
                f"{i}. *{it['company']}* ({it['role']})\n"
                f"   📌 Etapa: {it['stage']}\n"
                f"   ⚡ Tarea: {it.get('action_description') or 'Responder al reclutador'}\n"
                f"   📅 Recibido: {it['received_at']}\n\n"
            )
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n_Usa `!estado <empresa>` para más detalles._"
        return msg.strip()

    @classmethod
    def _cmd_rechazos(cls) -> str:
        rejections = DatabaseManager.get_rejections()
        if not rejections:
            return "🎯 No tienes ningún descarte registrado en este momento."

        msg = "❌ *ÚLTIMOS PROCESOS CONCLUIDOS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for r in rejections:
            msg += f"• *{r['company']}* - {r['role']} ({r['received_at'][:10]})\n"
        msg += "\n_¡Ánimo! Lo bueno está por llegar._ 💪"
        return msg

    @classmethod
    def _cmd_ignorar(cls, pattern: str) -> str:
        if not pattern:
            return "⚠️ Indica qué remitente o dominio deseas bloquear.\n_Ejemplo:_ `!ignorar spam-jobs.com`"

        success = DatabaseManager.add_to_blacklist(pattern)
        if success:
            return f"🚫 Remitente o dominio *'{pattern}'* añadido a tu lista negra personal.\nNo volverás a recibir notificaciones de sus correos."
        else:
            return f"ℹ️ *'{pattern}'* ya se encontraba previamente en tu lista negra."

    @classmethod
    def _cmd_analizar(cls, content: str) -> str:
        if not content:
            return "⚠️ Debes pegar el texto o URL sospechosa a analizar.\n_Ejemplo:_ `!analizar Hola somos de Amazon gana 5000 al dia dando likes`"

        # Simular objeto ParsedEmail para pasarlo al detector de phishing
        parsed = EmailParser.parse_dict({
            "sender": "whatsapp-user-scan@external",
            "subject": "Análisis Manual Solicitado por Usuario",
            "text": content,
            "html": ""
        })

        res = PhishingDetector.analyze(parsed)

        if res.verdict == "PHISHING":
            header = "🚨 *¡ALERTA CRÍTICA: FRAUDE / PHISHING CONFIRMADO!*"
            color = "🔴"
        elif res.verdict == "SUSPICIOUS":
            header = "⚠️ *ADVERTENCIA: PATRONES SOSPECHOSOS DETECTADOS*"
            color = "🟡"
        else:
            header = "✅ *RESULTADO: CONTENIDO APARENTEMENTE SEGURO*"
            color = "🟢"

        indicators_text = ""
        for ind in res.indicators:
            indicators_text += f"\n• *{ind.category}*: {ind.description} (Coincidencia: _{ind.matched_text}_)"

        return (
            f"{header}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{color} *Nivel de Riesgo*: {res.score}/10.0 ({res.verdict})\n"
            f"🔍 *Indicadores Forenses*:{indicators_text if indicators_text else ' Ninguno detectado.'}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔒 *Huella Digital (SHA-256)*: `{res.body_sha256[:16]}...`\n"
            f"🛑 *Recomendación*: {'No proporciones contraseñas ni depósitos de dinero.' if res.score >= 4.0 else 'Texto sin riesgos evidentes detectados.'}"
        )

    @classmethod
    def _cmd_cuarentena(cls) -> str:
        items = DatabaseManager.get_recent_quarantines()
        if not items:
            return "🛡️ *Bandeja de Cuarentena Limpia*: No hay correos maliciosos retenidos recientemente."

        msg = "☣️ *CORREOS RETENIDOS EN CUARENTENA*\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        for q in items:
            msg += (
                f"• [{q['verdict']}] *{q['sender']}*\n"
                f"  💬 Asunto: {q['subject'][:40]}\n"
                f"  ⚠️ Riesgo: {q['score']}/10.0 | 📅 {q['timestamp'][:19]}\n\n"
            )
        msg += "_Estos correos han sido aislados para tu seguridad._"
        return msg.strip()

    @classmethod
    def _cmd_duplicados(cls) -> str:
        report = DuplicateFinder.scan_directory()
        if not report.groups:
            return "✨ *Todo ordenado*: No se detectaron archivos duplicados en la carpeta de adjuntos."

        msg = (
            "📁 *REPORTE DE ARCHIVOS DUPLICADOS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Archivos escaneados*: {report.total_files_scanned}\n"
            f"📑 *Grupos de duplicados*: {report.duplicate_groups_count}\n"
            f"💾 *Espacio desperdiciado*: {report.total_wasted_mb} MB ({report.total_wasted_bytes:,} bytes)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        for g in report.groups[:3]:
            msg += f"• Archivo: `{g.canonical_file.split('/')[-1].split(chr(92))[-1]}` ({len(g.duplicate_files)} copias redundantes)\n"

        msg += "\n💡 _Para aislar y liberar este espacio, envía:_ `!limpiar`"
        return msg

    @classmethod
    def _cmd_limpiar(cls) -> str:
        result = DuplicateFinder.clean_duplicates()
        if result["files_removed"] == 0:
            return "✨ No había archivos duplicados pendientes de limpiar."

        return (
            "🧹 *LIMPIEZA DE ARCHIVOS COMPLETADA*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🗑️ *Archivos aislados*: {result['files_removed']}\n"
            f"💾 *Espacio recuperado*: {result['freed_mb']} MB\n"
            f"📂 *Carpeta de resguardo*: `{result.get('backup_folder', '')}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Los archivos originales se mantienen intactos."
        )

    @classmethod
    def _cmd_silencio(cls, args: str) -> str:
        hours = 2.0
        if args:
            match = re.search(r"(\d+(?:\.\d+)?)", args)
            if match:
                hours = float(match.group(1))

        until_time = DatabaseManager.set_silence_mode(hours)
        return (
            f"🔕 *MODO SILENCIO ACTIVADO*\n"
            f"No te enviaré notificaciones de WhatsApp hasta las *{until_time}* ({hours} horas).\n"
            f"Los correos y postulaciones se seguirán analizando y guardando en segundo plano."
        )

    @classmethod
    def _help_message(cls) -> str:
        return (
            "🤖 *COMANDOS DEL ASISTENTE DE POSTULACIONES*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💼 *Control de Empleo:*\n"
            "  • `!resumen` : Resumen general de postulaciones\n"
            "  • `!pendientes` : Tareas o pruebas por entregar\n"
            "  • `!estado <empresa>` : Estado del proceso de una empresa\n"
            "  • `!rechazos` : Procesos que ya finalizaron\n"
            "  • `!ignorar <empresa/email>` : Bloquear notificaciones de un remitente\n\n"
            "🛡️ *Seguridad & Anti-estafas:*\n"
            "  • `!analizar <texto/enlace>` : Escanear mensaje sospechoso\n"
            "  • `!cuarentena` : Ver amenazas retenidas\n\n"
            "🧹 *Archivos & Mantenimiento:*\n"
            "  • `!duplicados` : Buscar archivos y CVs repetidos\n"
            "  • `!limpiar` : Mover duplicados a carpeta de resguardo\n"
            "  • `!silencio [horas]` : Pausar alertas (ej. `!silencio 3`)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
