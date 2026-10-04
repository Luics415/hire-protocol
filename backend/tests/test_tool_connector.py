"""
Pruebas Unitarias del Hub y Buscador de Herramientas (Hire Protocol).
"""

import pytest
from src.tool_connector import ToolConnectorHub
from src.database import DatabaseManager


def test_registered_tools_catalog():
    tools = ToolConnectorHub.get_registered_tools()
    assert len(tools) >= 5
    tool_ids = [t.id for t in tools]
    assert "whatsapp" in tool_ids
    assert "email" in tool_ids
    assert "discord" in tool_ids
    assert "n8n" in tool_ids
    assert "antiphishing" in tool_ids
    assert "duplicates" in tool_ids


def test_tool_search_by_tag_and_keyword():
    # Búsqueda por término whatsapp
    results_ws = ToolConnectorHub.search_tools("whatsapp")
    assert len(results_ws) >= 1
    assert results_ws[0].id == "whatsapp"

    # Búsqueda por término correo / imap
    results_mail = ToolConnectorHub.search_tools("correo")
    assert any(t.id == "email" for t in results_mail)

    # Búsqueda de discord
    results_discord = ToolConnectorHub.search_tools("discord")
    assert any(t.id == "discord" for t in results_discord)

    # Búsqueda de n8n
    results_n8n = ToolConnectorHub.search_tools("n8n")
    assert any(t.id == "n8n" for t in results_n8n)


def test_persistent_setting_storage():
    DatabaseManager.set_setting("test_key_permanent", "val_12345")
    recovered = DatabaseManager.get_setting("test_key_permanent")
    assert recovered == "val_12345"
