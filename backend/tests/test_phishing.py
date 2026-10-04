"""
Pruebas Unitarias del Motor de Detección de Phishing.
"""

import pytest
from src.email_parser import EmailParser
from src.phishing_detector import PhishingDetector


def test_legitimate_email_is_safe():
    email = EmailParser.parse_dict({
        "sender": "reclutamiento@mercadolibre.com",
        "subject": "Tu postulación para Backend Developer",
        "text": "Hola, hemos recibido tu postulación. Revisaremos tu CV y te contactaremos en los próximos días.",
        "html": "<p>Hola, hemos recibido tu postulación.</p>"
    })

    result = PhishingDetector.analyze(email)
    assert result.verdict == "SAFE"
    assert result.score < 4.0
    assert not result.is_quarantined


def test_phishing_urgency_and_credential_harvest():
    email = EmailParser.parse_dict({
        "sender": "seguridad@banc0-alerta.com",
        "subject": "URGENTE: Cuenta suspendida - Verifique su identidad en 24 horas",
        "text": "Su cuenta será cerrada inmediatamente por acceso no autorizado. Ingrese su contraseña y actualice sus datos bancarios de inmediato.",
        "html": ""
    })

    result = PhishingDetector.analyze(email)
    assert result.verdict in ["PHISHING", "SUSPICIOUS"]
    assert result.score >= 5.0
    # Verifica que detectó urgencia y credenciales
    categories = [i.category for i in result.indicators]
    assert "Urgencia Psicológica" in categories
    assert "Recolección de Credenciales" in categories


def test_phishing_link_spoofing():
    email = EmailParser.parse_dict({
        "sender": "notificaciones@linkedin-fake.com",
        "subject": "Nueva oferta de empleo disponible",
        "text": "",
        "html": '<p>Ver vacante en <a href="http://192.168.1.50/malicious-login">https://www.linkedin.com/jobs/12345</a></p>'
    })

    result = PhishingDetector.analyze(email)
    assert result.score >= 4.0
    categories = [i.category for i in result.indicators]
    assert "Hipervínculo Engañoso (Spoofing)" in categories or "Alojamiento Sospechoso" in categories


def test_telegram_job_scam_detection():
    email = EmailParser.parse_dict({
        "sender": "rrhh@oportunidad-global.net",
        "subject": "Trabajo fácil desde casa - Gana $5000 al día",
        "text": "Trabajo fácil desde casa sin experiencia dando likes a videos. Deposito de garantía reembolsable. Escríbeme al whatsapp wa.me/5211234567 o contactar por telegram.",
        "html": ""
    })

    result = PhishingDetector.analyze(email)
    categories = [i.category for i in result.indicators]
    assert "Estafa Laboral / Oferta Falsa" in categories
    assert result.score >= 4.0
