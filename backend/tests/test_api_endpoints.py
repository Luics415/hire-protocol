"""
Pruebas de Integración End-to-End de los Endpoints de la API FastAPI.
Simula el comportamiento exacto de los nodos HTTP Request de n8n.
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient
from src.api import app
from src.config import SAMPLES_DIR
from src.database import DatabaseManager

client = TestClient(app)


def test_api_status_endpoint():
    DatabaseManager.clear_silence_mode()
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database_stats" in data


def test_api_analyze_interview_sample():
    sample_file = SAMPLES_DIR / "sample_01_interview_mercadolibre.json"
    with open(sample_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    response = client.post("/analyze-email", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["route"] == "JOB_UPDATE"
    assert res["stage"] == "ENTREVISTA"
    assert "Mercado Libre" in res["company"]
    assert res["whatsapp_notification"]["sent"] is True
    assert res["data"]["job_metadata"]["salary"] is not None
    assert "Remoto" in res["data"]["job_metadata"]["modality"]
    assert "Python" in res["data"]["job_metadata"]["tech_stack"]


def test_api_analyze_phishing_sample():
    sample_file = SAMPLES_DIR / "sample_04_phishing_account_suspension.json"
    with open(sample_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    response = client.post("/analyze-email", json=payload)
    assert response.status_code == 200
    res = response.json()

    assert res["route"] == "PHISHING"
    assert res["score"] >= 4.0
    assert res["is_quarantined"] is True
    assert Path(res["quarantine_file"]).exists()


def test_api_whatsapp_command_endpoint():
    # Test !resumen
    response = client.post("/whatsapp-command", json={"message": "!resumen"})
    assert response.status_code == 200
    res = response.json()
    assert "RESUMEN DE TUS POSTULACIONES" in res["reply"]

    # Test !estado Mercado Libre
    response_estado = client.post("/whatsapp-command", json={"message": "!estado Mercado Libre"})
    assert response_estado.status_code == 200
    res_estado = response_estado.json()
    assert "MERCADO LIBRE" in res_estado["reply"]
    assert "ENTREVISTA" in res_estado["reply"]
