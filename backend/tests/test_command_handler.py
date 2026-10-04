"""
Pruebas Unitarias del Gestor de Comandos Interactivos de WhatsApp.
"""

import pytest
from src.command_handler import CommandHandler
from src.database import DatabaseManager


def test_command_ayuda():
    reply = CommandHandler.handle_command("!ayuda")
    assert "COMANDOS DEL ASISTENTE" in reply
    assert "!resumen" in reply
    assert "!pendientes" in reply
    assert "!analizar" in reply


def test_command_resumen():
    reply = CommandHandler.handle_command("!resumen")
    assert "RESUMEN DE TUS POSTULACIONES" in reply
    assert "Total Postulaciones" in reply


def test_command_ignorar_blacklist():
    reply = CommandHandler.handle_command("!ignorar spammer-recruiters.com")
    assert "añadido a tu lista negra" in reply or "se encontraba previamente" in reply
    assert DatabaseManager.is_blacklisted("spammer-recruiters.com") is True


def test_command_analizar_phishing():
    phish_text = "!analizar Gana $5000 al dia dando likes a videos contactar por telegram wa.me/12345"
    reply = CommandHandler.handle_command(phish_text)
    assert "ALERTA CRÍTICA" in reply or "ADVERTENCIA" in reply
    assert "SHA-256" in reply


def test_command_silencio():
    reply = CommandHandler.handle_command("!silencio 1")
    assert "MODO SILENCIO ACTIVADO" in reply
    assert DatabaseManager.is_silenced() is True
