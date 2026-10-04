"""
Pruebas Unitarias del Clasificador de Postulaciones y Extractor de Vacantes (Regex).
"""

import pytest
from src.email_parser import EmailParser
from src.job_classifier import JobClassifier


def test_classify_linkedin_job_application():
    email = EmailParser.parse_dict({
        "sender": "jobs-noreply@linkedin.com",
        "subject": "Tu postulación para Backend Python Engineer en Rappi",
        "text": "Hemos recibido tu postulación para la vacante de Backend Python Engineer. Salario: $3,500 - $5,000 USD mensuales. Modalidad: 100% Remoto. Requisitos: Python, Docker, AWS y PostgreSQL.",
        "html": ""
    })

    result = JobClassifier.classify(email)
    assert result.is_job_related is True
    assert "LinkedIn" in result.platform
    assert result.stage == "POSTULACION_ENVIADA"
    assert result.company_name.lower() == "rappi"
    assert "Python" in result.role_title or "Backend" in result.role_title
    assert result.salary is not None
    assert "USD" in result.salary or "3,500" in result.salary
    assert "Remoto" in result.modality
    assert "Python" in result.tech_stack
    assert "AWS" in result.tech_stack
    assert "Docker" in result.tech_stack


def test_classify_interview_invitation():
    email = EmailParser.parse_dict({
        "sender": "recruiting@greenhouse.io",
        "subject": "Invitación a entrevista con el Hiring Manager - Nubank",
        "text": "Queremos agendar una entrevista técnica contigo para el rol de Fullstack Developer. Por favor selecciona tu horario en meet.google.com/abc-xyz.",
        "html": ""
    })

    result = JobClassifier.classify(email)
    assert result.is_job_related is True
    assert result.stage == "ENTREVISTA"
    assert result.action_required is True


def test_classify_technical_challenge():
    email = EmailParser.parse_dict({
        "sender": "no-reply@hackerrank.net",
        "subject": "Evaluación técnica de programación para Mercado Libre",
        "text": "Tienes una prueba técnica asignada en HackerRank. Tienes 48 horas para completar el desafío de código.",
        "html": ""
    })

    result = JobClassifier.classify(email)
    assert result.is_job_related is True
    assert result.stage == "PRUEBA_TECNICA"
    assert result.action_required is True


def test_classify_rejection():
    email = EmailParser.parse_dict({
        "sender": "talent@startup.io",
        "subject": "Actualización sobre tu candidatura",
        "text": "Agradecemos tu tiempo e interés. Hemos decidido avanzar con otros candidatos cuyo perfil se alinea más a la etapa actual.",
        "html": ""
    })

    result = JobClassifier.classify(email)
    assert result.is_job_related is True
    assert result.stage == "RECHAZO"
    assert result.action_required is False
