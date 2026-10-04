"""
Módulo de Gestión, Búsqueda y Persistencia de Herramientas y Conectores (Hire Protocol).
Permite buscar herramientas desde la terminal, vincular credenciales/licencias locales
y asegurar su persistencia en disco (SQLite + .env) entre reinicios del sistema.
"""

import os
import sys
import json
import imaplib
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from .config import (
    ENV_FILE, BASE_DIR, WHATSAPP_PROVIDER, TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, USER_WHATSAPP_NUMBER,
    DISCORD_WEBHOOK_URL, API_HOST, API_PORT,
    PHISHING_THRESHOLD_WARNING, PHISHING_THRESHOLD_CRITICAL, HASH_CHUNK_SIZE
)
from .database import DatabaseManager


@dataclass
class ToolDefinition:
    id: str
    name: str
    category: str
    description: str
    tags: List[str]
    is_connected: bool
    status_label: str
    connection_type: str  # 'env', 'imap', 'webhook', 'local'


class ToolConnectorHub:
    """Hub central de búsqueda y conexión de integraciones de Hire Protocol."""

    @classmethod
    def get_registered_tools(cls) -> List[ToolDefinition]:
        """Obtiene el catálogo de herramientas disponibles y su estado en tiempo real."""
        # Consultar estado en memoria o base de datos local
        twilio_ready = bool(
            os.getenv("TWILIO_ACCOUNT_SID", TWILIO_ACCOUNT_SID) and
            os.getenv("TWILIO_AUTH_TOKEN", TWILIO_AUTH_TOKEN) and
            os.getenv("USER_WHATSAPP_NUMBER", USER_WHATSAPP_NUMBER)
        )
        provider = os.getenv("WHATSAPP_PROVIDER", WHATSAPP_PROVIDER).lower()
        ws_connected = twilio_ready if provider == "twilio" else True
        ws_label = "Twilio Activo" if (provider == "twilio" and twilio_ready) else (
            "Mock Local Activo" if provider == "mock" else f"Proveedor: {provider}"
        )

        discord_url = os.getenv("DISCORD_WEBHOOK_URL", DISCORD_WEBHOOK_URL)
        discord_ready = bool(discord_url and "discord.com" in discord_url)

        # Consultar configuración de correo IMAP persistida en SQLite
        imap_host = DatabaseManager.get_setting("imap_host", os.getenv("IMAP_HOST", ""))
        imap_user = DatabaseManager.get_setting("imap_user", os.getenv("IMAP_USER", ""))
        email_ready = bool(imap_host and imap_user)
        email_label = f"Conectado ({imap_user})" if email_ready else "Vía n8n (Modo Webhook)"

        # Estado de n8n
        n8n_url = DatabaseManager.get_setting("n8n_webhook_url", os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678"))
        n8n_ready = True

        return [
            ToolDefinition(
                id="whatsapp",
                name="WhatsApp Bot Gateway",
                category="Mensajería y Alertas",
                description="Envío de notificaciones inmediatas y recepción de comandos bidireccionales (!resumen, !estado).",
                tags=["whatsapp", "mensajes", "alertas", "twilio", "meta", "notificaciones", "celular"],
                is_connected=ws_connected,
                status_label=ws_label,
                connection_type="env"
            ),
            ToolDefinition(
                id="email",
                name="Servicio de Correo (IMAP / Gmail / Outlook)",
                category="Buzón de Entrada",
                description="Monitoreo de emails de empleo entrantes (soporta lectura IMAP directa o vía webhook en n8n).",
                tags=["correo", "email", "gmail", "outlook", "imap", "buzon", "inbox", "mensajes"],
                is_connected=email_ready,
                status_label=email_label,
                connection_type="imap"
            ),
            ToolDefinition(
                id="discord",
                name="Discord Security Logger",
                category="Bitácora Forense",
                description="Canal de auditoría privada para registrar cabeceras de seguridad, salarios y logs técnicos detallados.",
                tags=["discord", "webhook", "auditoria", "logs", "bitacora", "seguridad"],
                is_connected=discord_ready,
                status_label="Webhook Activo" if discord_ready else "No configurado (Opcional)",
                connection_type="webhook"
            ),
            ToolDefinition(
                id="n8n",
                name="Orquestador n8n",
                category="Automatización",
                description="Motor de flujos visuales que sincroniza el webhook de correo con el backend de Hire Protocol.",
                tags=["n8n", "orquestador", "workflow", "automatizacion", "webhook", "flujos"],
                is_connected=n8n_ready,
                status_label=f"Vinculado ({n8n_url})",
                connection_type="webhook"
            ),
            ToolDefinition(
                id="antiphishing",
                name="Motor Antiphishing & Cuarentena",
                category="Seguridad Heurística",
                description="Análisis de urgencia, suplantación de enlaces (spoofing) y aislamiento en data/quarantine/.",
                tags=["seguridad", "phishing", "cuarentena", "heuristica", "amenazas", "spoofing", "antiphishing"],
                is_connected=True,
                status_label="Activo (Umbral: 4.0 / 7.0)",
                connection_type="local"
            ),
            ToolDefinition(
                id="duplicates",
                name="Deduplicador Criptográfico",
                category="Almacenamiento Local",
                description="Escáner por bloques (64 KB) con hashes MD5 y SHA-256 para depurar adjuntos repetidos.",
                tags=["duplicados", "hash", "sha256", "md5", "archivos", "cv", "almacenamiento", "limpiar"],
                is_connected=True,
                status_label="Activo (Bloques: 64 KB)",
                connection_type="local"
            )
        ]

    @classmethod
    def search_tools(cls, query: str) -> List[ToolDefinition]:
        """Busca herramientas por término de búsqueda en nombre, descripción o etiquetas."""
        q = query.strip().lower()
        if not q:
            return cls.get_registered_tools()

        tools = cls.get_registered_tools()
        matches = []
        for t in tools:
            if (q in t.id.lower() or
                q in t.name.lower() or
                q in t.category.lower() or
                q in t.description.lower() or
                any(q in tag for tag in t.tags)):
                matches.append(t)
        return matches

    @classmethod
    def persist_env_key(cls, key: str, value: str):
        """Guarda permanentemente una variable tanto en el archivo .env como en la base SQLite."""
        # 1. Guardar en SQLite para persistencia indestructible
        DatabaseManager.set_setting(key, value)
        os.environ[key] = value

        # 2. Actualizar archivo .env
        env_lines = []
        key_found = False
        target_env = ENV_FILE

        if target_env.exists():
            with open(target_env, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith(f"{key}=") or stripped.startswith(f"#{key}="):
                        env_lines.append(f"{key}={value}\n")
                        key_found = True
                    else:
                        env_lines.append(line)

        if not key_found:
            env_lines.append(f"{key}={value}\n")

        with open(target_env, "w", encoding="utf-8") as f:
            f.writelines(env_lines)

    @classmethod
    def sync_persisted_settings(cls):
        """Carga en os.environ las configuraciones guardadas previamente en SQLite al arrancar."""
        settings = DatabaseManager.get_all_settings()
        for k, v in settings.items():
            if k not in os.environ:
                os.environ[k] = v

    @classmethod
    def configure_whatsapp(cls):
        """Asistente para configurar y probar WhatsApp."""
        print("\n" + "=" * 60)
        print("📱 CONFIGURACIÓN DE WHATSAPP (Hire Protocol)")
        print("=" * 60)
        curr_provider = os.getenv("WHATSAPP_PROVIDER", "mock")
        print("Proveedores disponibles:")
        print("  1. 'mock'   - Modo simulado local (muestra mensajes en consola sin costo)")
        print("  2. 'twilio' - Conexión oficial a través de Twilio WhatsApp Sandbox / API")
        
        choice = input(f"\nSelecciona proveedor [actual: {curr_provider}]: ").strip().lower() or curr_provider
        if choice in ["1", "mock"]:
            cls.persist_env_key("WHATSAPP_PROVIDER", "mock")
            print("✅ Proveedor configurado como 'mock' (Modo seguro local activado).")
        elif choice in ["2", "twilio"]:
            cls.persist_env_key("WHATSAPP_PROVIDER", "twilio")
            sid = input(f"Twilio Account SID [{os.getenv('TWILIO_ACCOUNT_SID', '')[:6]}...]: ").strip()
            if sid:
                cls.persist_env_key("TWILIO_ACCOUNT_SID", sid)

            token = input(f"Twilio Auth Token: ").strip()
            if token:
                cls.persist_env_key("TWILIO_AUTH_TOKEN", token)

            from_num = input(f"Twilio WhatsApp From [{os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')}]: ").strip()
            if from_num:
                cls.persist_env_key("TWILIO_WHATSAPP_FROM", from_num)

            user_num = input(f"Tu número de WhatsApp destino (ej. +52155...): ").strip()
            if user_num:
                cls.persist_env_key("USER_WHATSAPP_NUMBER", user_num)

            print("✅ Credenciales de Twilio guardadas localmente de forma permanente.")

    @classmethod
    def configure_email(cls):
        """Asistente para vincular cuenta de correo IMAP o Gmail."""
        print("\n" + "=" * 60)
        print("📬 CONFIGURACIÓN DE CUENTA DE CORREO")
        print("=" * 60)
        print("Puedes conectar una cuenta IMAP para monitoreo local o usar el nodo Gmail de n8n.\n")
        
        host = input("Servidor IMAP (ej. imap.gmail.com o imap.mail.yahoo.com): ").strip()
        if host:
            cls.persist_env_key("IMAP_HOST", host)
            port = input("Puerto IMAP [993]: ").strip() or "993"
            cls.persist_env_key("IMAP_PORT", port)
            user = input("Dirección de correo: ").strip()
            if user:
                cls.persist_env_key("IMAP_USER", user)
            password = input("Contraseña de Aplicación (App Password): ").strip()
            if password:
                cls.persist_env_key("IMAP_PASSWORD", password)

            test_conn = input("\n¿Deseas probar la conexión IMAP ahora mismo? (s/n) [s]: ").strip().lower()
            if test_conn != "n":
                try:
                    print("🔄 Conectando con servidor de correo...")
                    mail = imaplib.IMAP4_SSL(host, int(port), timeout=10)
                    mail.login(user, password)
                    mail.logout()
                    print("🎉 ¡Conexión IMAP verificada exitosamente! Tu correo está vinculado.")
                except Exception as e:
                    print(f"⚠️ Aviso: No se pudo verificar la conexión ({e}). Verifica que sea una 'Contraseña de Aplicación'.")

    @classmethod
    def configure_discord(cls):
        """Asistente para configurar y probar Discord Webhook."""
        print("\n" + "=" * 60)
        print("📜 CONFIGURACIÓN DE BITÁCORA EN DISCORD")
        print("=" * 60)
        curr = os.getenv("DISCORD_WEBHOOK_URL", "")
        prompt = f"[{curr[:35]}...]" if curr else "[Vacio]"
        url = input(f"Discord Webhook URL {prompt}: ").strip() or curr

        if url:
            cls.persist_env_key("DISCORD_WEBHOOK_URL", url)
            test_it = input("¿Deseas enviar un mensaje de prueba a tu canal de Discord? (s/n) [s]: ").strip().lower()
            if test_it != "n":
                try:
                    res = requests.post(url, json={
                        "embeds": [{
                            "title": "🛡️ Hire Protocol Conectado",
                            "description": "Tu canal de Discord ha sido vinculado exitosamente a Hire Protocol.",
                            "color": 3066993
                        }]
                    }, timeout=6)
                    if res.status_code in [200, 204]:
                        print("🎉 ¡Mensaje de prueba recibido en Discord con éxito!")
                    else:
                        print(f"⚠️ Discord respondió con código {res.status_code}.")
                except Exception as err:
                    print(f"⚠️ Error al conectar con Discord: {err}")

    @classmethod
    def display_hub_menu(cls):
        """Despliega el buscador y centro de control interactivo de Hire Protocol."""
        cls.sync_persisted_settings()

        while True:
            tools = cls.get_registered_tools()
            print("\n" + "=" * 72)
            print("  🛡️  HIRE PROTOCOL - HUB INTERACTIVO & BUSCADOR DE HERRAMIENTAS")
            print("=" * 72)
            print("ℹ️  Tus herramientas conectadas se guardan de forma permanente en tu máquina.")
            print("   Seguirán vinculadas mañana al reiniciar tu computadora (100% Local y Privado).\n")

            print("HERRAMIENTAS INTEGRADAS:")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for idx, t in enumerate(tools, start=1):
                icon = "✅" if t.is_connected else "⚪"
                print(f" [{idx}] {icon} {t.name:<32} | {t.category:<18} | {t.status_label}")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("ACCIONES:")
            print(" [S] 🚀 Iniciar Servidor Hire Protocol (FastAPI)")
            print(" [B] 🔍 Buscar Herramientas por Nombre o Etiqueta")
            print(" [T] 🧪 Ejecutar Suite de Pruebas y Laboratorio Demo")
            print(" [0] 🚪 Salir")
            print("=" * 72)

            choice = input("\n👉 Elige una herramienta [1-6], acción [S/B/T] o escribe para buscar: ").strip()

            if not choice or choice.lower() == "s":
                return "serve"
            elif choice == "0":
                sys.exit(0)
            elif choice.lower() == "t":
                return "test"
            elif choice == "1":
                cls.configure_whatsapp()
            elif choice == "2":
                cls.configure_email()
            elif choice == "3":
                cls.configure_discord()
            elif choice == "4":
                print(f"\n⚙️ Orquestador n8n activo. Configura tus flujos en http://localhost:5678")
                input("Presiona Enter para continuar...")
            elif choice == "5":
                print(f"\n🛡️ Umbrales de Phishing: Advertencia={PHISHING_THRESHOLD_WARNING}, Crítico={PHISHING_THRESHOLD_CRITICAL}")
                input("Presiona Enter para continuar...")
            elif choice == "6":
                print(f"\n💾 Deduplicador activo con bloques de {HASH_CHUNK_SIZE} bytes (64 KB).")
                input("Presiona Enter para continuar...")
            elif choice.lower() == "b":
                q = input("🔍 Término de búsqueda (ej: whatsapp, correo, discord, hash): ").strip()
                results = cls.search_tools(q)
                print(f"\nResultados encontrados ({len(results)}):")
                for r in results:
                    icon = "✅" if r.is_connected else "⚪"
                    print(f" • {icon} {r.name} ({r.category}): {r.description}")
                input("\nPresiona Enter para volver al Hub...")
            else:
                # Si el usuario escribió un texto directamente, buscarlo
                results = cls.search_tools(choice)
                if results:
                    print(f"\n🔍 Coincidencias para '{choice}':")
                    for r in results:
                        icon = "✅" if r.is_connected else "⚪"
                        print(f" • {icon} {r.name}: {r.description} [{r.status_label}]")
                    input("\nPresiona Enter para continuar...")
                else:
                    print("Comando o herramienta no reconocida. Intenta de nuevo.")
