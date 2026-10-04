"""
Clasificador de Postulaciones Laborales y Extractor con Expresiones Regulares (Regex).
Detecta dominios de bolsas de trabajo, ATS, etapas de contratación, salario, modalidad y stack.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from .email_parser import ParsedEmail


@dataclass
class JobApplicationMetadata:
    is_job_related: bool
    platform: str                    # 'LinkedIn', 'Indeed', 'Computrabajo', 'OCC', 'ATS Directo', etc.
    company_name: str
    role_title: str
    stage: str                       # 'POSTULACION_ENVIADA', 'ENTREVISTA', 'PRUEBA_TECNICA', 'OFERTA', 'RECHAZO', 'OTRO'
    stage_label: str
    stage_emoji: str
    salary: Optional[str] = None     # Ej: "$3,500 - $4,500 USD" o "50,000 MXN"
    modality: Optional[str] = None   # 'Remoto', 'Híbrido', 'Presencial'
    tech_stack: List[str] = field(default_factory=list)
    action_required: bool = False
    action_description: str = ""


class JobClassifier:
    """Clasificador inteligente de procesos de selección y postulaciones."""

    # 1. Dominios de Bolsas de Trabajo y Redes Profesionales
    JOB_BOARD_DOMAINS = {
        "linkedin.com": "LinkedIn Jobs",
        "indeed.com": "Indeed",
        "computrabajo.com": "CompuTrabajo",
        "occ.com.mx": "OCCMundial",
        "glassdoor.com": "Glassdoor",
        "talent.com": "Talent.com",
        "ziprecruiter.com": "ZipRecruiter",
        "infojobs.net": "InfoJobs",
        "welcometothejungle.com": "Welcome to the Jungle",
        "bumeran.com.mx": "Bumeran",
        "getonbrd.com": "Get on Board",
        "torre.ai": "Torre"
    }

    # 2. Dominios de Sistemas ATS (Applicant Tracking Systems) y RRHH
    ATS_DOMAINS = {
        "greenhouse.io": "Greenhouse ATS",
        "lever.co": "Lever ATS",
        "myworkday.com": "Workday",
        "workday.com": "Workday",
        "smartrecruiters.com": "SmartRecruiters",
        "ashbyhq.com": "Ashby",
        "bamboohr.com": "BambooHR",
        "workable.com": "Workable",
        "taleo.net": "Oracle Taleo",
        "breezy.hr": "Breezy HR",
        "jobvite.com": "Jobvite",
        "recruitee.com": "Recruitee"
    }

    # 3. Regex de Etapas del Proceso de Selección
    REGEX_STAGE_OFFER = re.compile(
        r"(?i)\b("
        r"oferta laboral|propuesta de empleo|propuesta econ[oó]mica|carta oferta|carta de oferta|"
        r"felicidades por tu selecci[oó]n|te queremos en el equipo|formal job offer|offer letter|"
        r"pleased to offer you the position"
        r")\b"
    )

    REGEX_STAGE_INTERVIEW = re.compile(
        r"(?i)\b("
        r"invitaci[oó]n a entrevista|agendar (una )?(llamada|reuni[oó]n|entrevista)|"
        r"coordinar entrevista|entrevista con el equipo|entrevista inicial|entrevista con rh|"
        r"entrevista con el hiring manager|schedule an interview|invitation to interview|"
        r"first round interview|calendly\.com|meet\.google\.com|zoom\.us"
        r")\b"
    )

    REGEX_STAGE_TECH_TEST = re.compile(
        r"(?i)\b("
        r"prueba t[eé]cnica|evaluaci[oó]n t[eé]cnica|desaf[ií]o de c[oó]digo|cuestionario t[eé]cnico|"
        r"hackerrank|codility|leetcode|codesignal|testdome|take-home challenge|"
        r"technical assessment|coding challenge|ejercicio pr[aá]ctico de desarrollo"
        r")\b"
    )

    REGEX_STAGE_REJECTION = re.compile(
        r"(?i)\b("
        r"no continuaremos con tu proceso|hemos decidido avanzar con otros candidatos|"
        r"no fuiste seleccionado|proceso finalizado|desafortunadamente|guardaremos tu cv|"
        r"agradecemos tu inter[eé]s, sin embargo|we regret to inform you|"
        r"decided to pursue other candidates|position has been closed"
        r")\b"
    )

    REGEX_STAGE_RECEIVED = re.compile(
        r"(?i)\b("
        r"hemos recibido tu postulaci[oó]n|confirmaci[oó]n de postulaci[oó]n|gracias por postularte|"
        r"tu solicitud ha sido enviada|postulaci[oó]n exitosa|recibimos tu candidatura|"
        r"application received|thank you for applying|we received your application|"
        r"application submitted"
        r")\b"
    )

    # 4. Regex para Extracción de Salario
    REGEX_SALARY = re.compile(
        r"(?i)(?:salario|sueldo|remuneraci[oó]n|compensaci[oó]n|salary|compensation)?\s*:?\s*"
        r"(?:(?:usd|\$|€|mxn)\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d+)?)\s*(?:-|a|to)\s*(?:usd|\$|€|mxn)?\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d+)?)\s*(?:usd|mxn|eur|d[oó]lares|pesos)?|"
        r"(?:usd|\$|€|mxn)\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d+)?)\s*(?:usd|mxn|eur|d[oó]lares|pesos)?(?:\s*(?:mensuales|anuales|al mes|netos|brutos|/mo|/yr|per month|per year))?)"
    )

    # 5. Regex para Extracción de Modalidad Laboral
    REGEX_MODALITY_REMOTE = re.compile(r"(?i)\b(remoto|remote|100%\s*remoto|home office|teletrabajo|full remote)\b")
    REGEX_MODALITY_HYBRID = re.compile(r"(?i)\b(h[ií]brido|hybrid|mixto|\d\s*d[ií]as\s*en\s*oficina)\b")
    REGEX_MODALITY_ONSITE = re.compile(r"(?i)\b(presencial|on-site|onsite|en sitio|en oficina)\b")

    # 6. Catálogo de Tecnologías y Stack Común
    TECH_KEYWORDS = [
        "python", "fastapi", "django", "flask", "javascript", "typescript", "react", "next.js",
        "node.js", "express", "vue", "angular", "aws", "gcp", "azure", "docker", "kubernetes",
        "sql", "postgresql", "mysql", "mongodb", "redis", "kafka", "terraform", "ci/cd",
        "git", "linux", "c#", ".net", "java", "spring boot", "golang", "go", "php", "laravel"
    ]

    @classmethod
    def identify_platform(cls, sender_domain: str, full_text: str) -> Tuple[bool, str]:
        """Verifica si el correo proviene de una bolsa de empleo, ATS o canal de selección."""
        domain_lower = sender_domain.lower()

        # Comprobar bolsas de trabajo
        for domain, name in cls.JOB_BOARD_DOMAINS.items():
            if domain in domain_lower:
                return True, name

        # Comprobar ATS corporativos
        for domain, name in cls.ATS_DOMAINS.items():
            if domain in domain_lower:
                return True, name

        # Comprobar si el remitente tiene palabras clave de reclutamiento (ej: jobs@empresa.com)
        if re.search(r"(?i)\b(jobs|careers|talent|recruiting|reclutamiento|rh|hr)@", sender_domain):
            return True, "Contacto Directo Reclutamiento"

        # Comprobar menciones explícitas de plataformas en el cuerpo
        if "linkedin.com/jobs" in full_text.lower():
            return True, "LinkedIn (Enlace)"
        if "indeed.com" in full_text.lower():
            return True, "Indeed (Enlace)"

        return False, "Correo Corporativo"

    @classmethod
    def extract_salary(cls, text: str) -> Optional[str]:
        """Extrae con expresiones regulares menciones de salario o rango salarial."""
        match = cls.REGEX_SALARY.search(text)
        if match:
            found = match.group(0).strip()
            # Validar que no sea un número falso o fecha
            if any(char.isdigit() for char in found) and len(found) >= 3:
                return found
        return None

    @classmethod
    def extract_modality(cls, text: str) -> Optional[str]:
        """Detecta la modalidad de trabajo (Remoto, Híbrido, Presencial)."""
        if cls.REGEX_MODALITY_REMOTE.search(text):
            return "Remoto (100% Home Office)"
        if cls.REGEX_MODALITY_HYBRID.search(text):
            return "Híbrido"
        if cls.REGEX_MODALITY_ONSITE.search(text):
            return "Presencial"
        return "No especificada"

    @classmethod
    def extract_tech_stack(cls, text: str) -> List[str]:
        """Extrae tecnologías mencionadas en el texto usando límites de palabra."""
        found_stack = []
        text_lower = text.lower()
        for tech in cls.TECH_KEYWORDS:
            # Buscar con word boundaries (\b) para no confundir 'go' con 'good'
            pattern = rf"\b{re.escape(tech)}\b"
            if re.search(pattern, text_lower):
                found_stack.append(tech.title() if tech not in ["aws", "gcp", "sql", "ci/cd"] else tech.upper())
        return list(dict.fromkeys(found_stack))  # eliminar duplicados preservando orden

    @classmethod
    def extract_company_and_role(cls, email_obj: ParsedEmail, platform: str) -> Tuple[str, str]:
        """Extrae el nombre de la empresa y el título de la vacante usando heurísticas y strings."""
        subject = email_obj.subject
        clean_subject = subject.strip()
        company = email_obj.sender_name
        role = "Desarrollador / Posición Técnica"

        # 1. Patrón en subject: "... - [Rol] en [Empresa]" o "[Etapa] - [Rol] en [Empresa]"
        match_dash = re.search(r"-\s*([A-Za-z0-9\s\.\+#/]+?)\s+(?:en|at|con)\s+([A-Za-z0-9\s\.\-]+)$", clean_subject, re.IGNORECASE)
        if match_dash:
            role = match_dash.group(1).strip()
            company = match_dash.group(2).strip()
            return company, role

        # 2. Patrón en subject: "[postulación|entrevista|vacante] [para] [Rol] en [Empresa]"
        match1 = re.search(r"(?i)(?:postulaci[oó]n|solicitud|vacante|entrevista|evaluaci[oó]n)\s+(?:t[eé]cnica\s+)?(?:para|a|de)?\s*(.*?)\s+(?:en|at|con|para)\s+([^-\|:]+)", clean_subject)
        if match1:
            extracted_role = match1.group(1).strip()
            extracted_company = match1.group(2).strip()
            if extracted_role:
                role = extracted_role
            if extracted_company:
                company = extracted_company
            return company, role

        # 3. Patrón simple: "... en [Empresa]" al final del asunto
        match_en = re.search(r"(?i)\s+(?:en|at|con)\s+([A-Za-z0-9\s\.\-]+)$", clean_subject)
        if match_en:
            company = match_en.group(1).strip()

        # 4. Si el nombre de la empresa parece genérico de correo (ej: 'talent-acquisition', 'no-reply', 'jobs')
        generic_names = ["talent-acquisition", "no-reply", "noreply", "jobs", "careers", "recruiting", "rh", "hr", "notificaciones"]
        if company.lower().strip() in generic_names or company.lower().strip() == email_obj.sender.split("@")[0].lower():
            # Intentar inferir de firma o cuerpo
            sig_match = re.search(r"\|\s*([A-Za-z0-9\s]+)$", email_obj.clean_text, re.MULTILINE)
            if sig_match:
                company = sig_match.group(1).strip()
            else:
                # Inferir del dominio si no es un ATS público
                domain_parts = email_obj.sender_domain.split(".")
                if len(domain_parts) >= 2 and domain_parts[0] not in ["gmail", "outlook", "hotmail", "yahoo"]:
                    root_name = domain_parts[0]
                    if root_name == "mercadolibre":
                        company = "Mercado Libre"
                    elif root_name == "nubank":
                        company = "Nubank"
                    elif root_name == "globant":
                        company = "Globant"
                    else:
                        company = root_name.capitalize()

        # 5. Si viene de una bolsa de empleo genérica, extraer del cuerpo
        if company.lower() in ["linkedin", "indeed", "computrabajo", "occmundial"]:
            body_match = re.search(r"(?i)(?:postulaste a|aplicaste a|candidatura para)\s+([A-Za-z0-9\s\.\+]+?)\s+(?:en|at)\s+([A-Za-z0-9\s\.\-]+)", email_obj.clean_text[:600])
            if body_match:
                role = body_match.group(1).strip()
                company = body_match.group(2).strip()

        return company, role

    @classmethod
    def classify(cls, email_obj: ParsedEmail) -> JobApplicationMetadata:
        """Clasifica el correo y extrae todos los metadatos relevantes de la postulación."""
        full_text = f"{email_obj.subject}\n{email_obj.clean_text}"
        is_job_domain, platform = cls.identify_platform(email_obj.sender_domain, full_text)

        # Detectar la etapa del proceso con Regex
        if cls.REGEX_STAGE_OFFER.search(full_text):
            stage = "OFERTA"
            stage_label = "¡Oferta Laboral Recibida!"
            stage_emoji = "🎉"
            action_req = True
            action_desc = "Revisar términos económicos y responder carta oferta."
        elif cls.REGEX_STAGE_TECH_TEST.search(full_text):
            stage = "PRUEBA_TECNICA"
            stage_label = "Evaluación / Desafío Técnico"
            stage_emoji = "💻"
            action_req = True
            action_desc = "Revisar fecha límite y resolver prueba técnica."
        elif cls.REGEX_STAGE_INTERVIEW.search(full_text):
            stage = "ENTREVISTA"
            stage_label = "Invitación a Entrevista"
            stage_emoji = "🗓️"
            action_req = True
            action_desc = "Agendar espacio en Calendly / responder horarios disponibles."
        elif cls.REGEX_STAGE_REJECTION.search(full_text):
            stage = "RECHAZO"
            stage_label = "Candidatura Finalizada / Descarte"
            stage_emoji = "❌"
            action_req = False
            action_desc = "Proceso concluido sin acción requerida."
        elif cls.REGEX_STAGE_RECEIVED.search(full_text):
            stage = "POSTULACION_ENVIADA"
            stage_label = "Confirmación de Postulación Enviada"
            stage_emoji = "📨"
            action_req = False
            action_desc = "Postulación registrada en sistema del reclutador."
        else:
            stage = "OTRO"
            stage_label = "Actualización General de Empleo"
            stage_emoji = "💼"
            action_req = False
            action_desc = "Revisar detalles en caso de ser necesario."

        # Es laboral si viene de dominio de empleo O si encaja con regex de etapas clave
        is_job = is_job_domain or (stage != "OTRO")

        company, role = cls.extract_company_and_role(email_obj, platform)
        salary = cls.extract_salary(full_text)
        modality = cls.extract_modality(full_text)
        tech_stack = cls.extract_tech_stack(full_text)

        return JobApplicationMetadata(
            is_job_related=is_job,
            platform=platform,
            company_name=company,
            role_title=role,
            stage=stage,
            stage_label=stage_label,
            stage_emoji=stage_emoji,
            salary=salary,
            modality=modality,
            tech_stack=tech_stack,
            action_required=action_req,
            action_description=action_desc
        )
