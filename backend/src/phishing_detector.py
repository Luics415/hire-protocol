"""
Motor de Detección de Phishing y Ciberamenazas.
Aplica manipulación de cadenas (strings), expresiones regulares (regex) avanzadas,
hashing criptográfico (MD5/SHA-256) y gestión de archivos de cuarentena.
"""

import re
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict

from .email_parser import ParsedEmail
from .config import QUARANTINE_DIR, PHISHING_THRESHOLD_WARNING, PHISHING_THRESHOLD_CRITICAL


@dataclass
class ThreatIndicator:
    category: str
    description: str
    weight: float
    matched_text: str = ""


@dataclass
class PhishingAnalysisResult:
    score: float
    verdict: str  # 'SAFE', 'SUSPICIOUS', 'PHISHING'
    indicators: List[ThreatIndicator]
    body_sha256: str
    url_hashes: List[Dict[str, str]]
    is_quarantined: bool
    quarantine_path: str = ""


class PhishingDetector:
    """Analizador de seguridad heurístico con regex, hashing y cuarentena en disco."""

    # 1. Regex de Urgencia Psicológica e Intimidación
    REGEX_URGENCY = re.compile(
        r"(?i)\b("
        r"urgente|inmediatamente|acci[oó]n inmediata|cuenta suspendida|suspensi[oó]n definitiva|"
        r"bloqueo de cuenta|acceso no autorizado|verifique su identidad|evite la cancelaci[oó]n|"
        r"plazo l[ií]mite|24 horas|48 horas|multa|seguridad comprometida|alerta crítica|"
        r"urgent|immediate action|account suspended|verify your identity|unauthorized activity|"
        r"limited time|security alert|action required"
        r")\b"
    )

    # 2. Regex de Extracción de Credenciales y Trampas Financieras
    REGEX_CREDENTIAL_HARVEST = re.compile(
        r"(?i)\b("
        r"ingrese su contrase[ñn]a|restablecer credenciales|iniciar sesi[oó]n aqu[ií]|"
        r"actualice sus datos bancarios|verificar tarjeta|c[oó]digo de seguridad|cvv|"
        r"token de seguridad|confirmar pin|clabe interbancaria|transferencia retenida|"
        r"enter password|reset credentials|confirm credit card|banking details|verify pin"
        r")\b"
    )

    # 3. Regex de Estafas de Falso Empleo (Telegram / Cripto / Pagos previos)
    REGEX_JOB_SCAMS = re.compile(
        r"(?i)\b("
        r"gana (?:\$\s*\d+|\d+\s*d[oó]lares) al d[ií]a|trabajo f[aá]cil desde casa|sin experiencia|"
        r"da likes a videos|inversi[oó]n inicial requerida|pago por adelantado|deposito de garant[ií]a|"
        r"contactar por telegram|escr[ií]beme al whatsapp de recursos humanos|t\.me/|wa\.me/|"
        r"gana dinero viendo videos|paquete de bienvenida previo pago|cryptocurrency investment"
        r")\b"
    )

    # 4. Regex para URLs sospechosas, IPs crudas y dominios dinámicos gratuitos
    REGEX_SUSPICIOUS_URL = re.compile(
        r"https?://("
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # Dirección IP directa en lugar de dominio
        r"[\w\.-]+\.(ngrok-free\.app|ngrok\.io|duckdns\.org|000webhostapp\.com|firebaseapp\.com|pages\.dev|glitch\.me|surge\.sh)"
        r")",
        re.IGNORECASE
    )

    # 5. Lista de Marcas Notorias para Detección de Typosquatting
    POPULAR_BRANDS = [
        "paypal", "netflix", "microsoft", "google", "amazon", "apple",
        "linkedin", "santander", "bbva", "banorte", "hsbc", "mercado libre"
    ]

    # 6. Base local de Hashes SHA-256 conocidos como maliciosos (Threat Intel local)
    MALICIOUS_HASHES_DB = {
        # Hashes de prueba para simulación
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "8f448b29f074d284f3ab6660f588c2263d8ff114e9f54668b5a0b77626920199"
    }

    @classmethod
    def compute_sha256(cls, text: str) -> str:
        """Genera hash SHA-256 de una cadena de texto."""
        return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

    @classmethod
    def compute_md5(cls, text: str) -> str:
        """Genera hash MD5 rápido para firmas secundarias."""
        return hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()

    @classmethod
    def detect_typosquatting(cls, domain: str) -> Tuple[bool, str]:
        """Detecta dominios que imitan marcas reales usando números o letras cambiadas (ej: paypa1.com)."""
        domain_lower = domain.lower()
        
        # Mapeos de sustitución comunes (leetspeak)
        normalized = domain_lower.replace("0", "o").replace("1", "l").replace("3", "e").replace("5", "s").replace("8", "b")

        for brand in cls.POPULAR_BRANDS:
            # Si el dominio normalizado contiene la marca pero el original no coincide exactamente con el dominio oficial
            if brand in normalized and brand not in domain_lower:
                return True, f"Suplantación tipográfica de '{brand}' detectada en '{domain}'"
            # O si contiene guiones sospechosos como 'banco-seguro-verificacion.com'
            if brand in domain_lower and ("-" in domain_lower or "login" in domain_lower or "verify" in domain_lower):
                # Si no es el dominio raíz oficial
                if not (domain_lower.endswith(f".{brand}.com") or domain_lower == f"{brand}.com"):
                    return True, f"Dominio engañoso que utiliza la marca legítima '{brand}': '{domain}'"

        return False, ""

    @classmethod
    def analyze(cls, email_obj: ParsedEmail) -> PhishingAnalysisResult:
        """Ejecuta el análisis forense integral del correo con regex, strings y hashes."""
        indicators: List[ThreatIndicator] = []
        score = 0.0

        full_text = f"{email_obj.subject}\n{email_obj.clean_text}"
        body_sha256 = cls.compute_sha256(full_text)

        # A. Análisis con Expresiones Regulares: Urgencia / Intimidación
        urgency_matches = [m.group(0) for m in cls.REGEX_URGENCY.finditer(full_text)]
        if urgency_matches:
            weight = min(len(urgency_matches) * 1.5, 3.5)
            indicators.append(ThreatIndicator(
                category="Urgencia Psicológica",
                description=f"Patrones de presión o intimidación detectados ({len(urgency_matches)} ocurrencias)",
                weight=weight,
                matched_text=", ".join(set(urgency_matches[:5]))
            ))
            score += weight

        # B. Análisis con Expresiones Regulares: Solicitud de Credenciales
        cred_matches = [m.group(0) for m in cls.REGEX_CREDENTIAL_HARVEST.finditer(full_text)]
        if cred_matches:
            weight = min(len(cred_matches) * 2.0, 4.0)
            indicators.append(ThreatIndicator(
                category="Recolección de Credenciales",
                description="Intento de solicitud de contraseñas, PIN o datos bancarios confidenciales",
                weight=weight,
                matched_text=", ".join(set(cred_matches[:4]))
            ))
            score += weight

        # C. Análisis con Expresiones Regulares: Estafas de Empleo Falso (Telegram/Cripto)
        scam_matches = [m.group(0) for m in cls.REGEX_JOB_SCAMS.finditer(full_text)]
        if scam_matches:
            weight = min(len(scam_matches) * 2.5, 4.5)
            indicators.append(ThreatIndicator(
                category="Estafa Laboral / Oferta Falsa",
                description="Promesas de ingresos irreales, pagos por adelantado o desvío a Telegram",
                weight=weight,
                matched_text=", ".join(set(scam_matches[:3]))
            ))
            score += weight

        # D. Análisis de Hipervínculos Engañosos (Href Mismatches)
        url_hashes = []
        for link in email_obj.hyperlinks:
            # Calcular hash SHA-256 de la URL para comparación en bloque
            url_sha256 = cls.compute_sha256(link.target_url)
            url_hashes.append({"url": link.target_url, "sha256": url_sha256})

            # Comprobar si el hash está en la base maliciosa local
            if url_sha256 in cls.MALICIOUS_HASHES_DB:
                score += 5.0
                indicators.append(ThreatIndicator(
                    category="URL en Lista Negra",
                    description=f"El enlace coincide con firma criptográfica maliciosa conocida",
                    weight=5.0,
                    matched_text=link.target_url
                ))

            # Mismatch visual (El texto dice google.com pero el enlace va a sitio malicioso)
            if link.is_mismatched:
                score += 3.5
                indicators.append(ThreatIndicator(
                    category="Hipervínculo Engañoso (Spoofing)",
                    description=f"El texto visible '{link.visible_text}' discrepa del destino real '{link.target_url}'",
                    weight=3.5,
                    matched_text=f"{link.visible_text} -> {link.target_url}"
                ))

            # Detección de IP cruda o servicio gratuito sospechoso
            if cls.REGEX_SUSPICIOUS_URL.search(link.target_url):
                score += 2.5
                indicators.append(ThreatIndicator(
                    category="Alojamiento Sospechoso",
                    description=f"Enlace hacia dirección IP cruda o dominio dinámico de túnel/phishing",
                    weight=2.5,
                    matched_text=link.target_url
                ))

        # E. Detección de Typosquatting en el Remitente
        is_typo, typo_msg = cls.detect_typosquatting(email_obj.sender_domain)
        if is_typo:
            score += 3.0
            indicators.append(ThreatIndicator(
                category="Suplantación de Identidad (Typosquatting)",
                description=typo_msg,
                weight=3.0,
                matched_text=email_obj.sender_domain
            ))

        # F. Comprobación de Fallos de Autenticación (SPF / DKIM)
        if email_obj.spf_pass is False or email_obj.dkim_pass is False:
            score += 2.0
            indicators.append(ThreatIndicator(
                category="Fallo de Autenticación de Correo",
                description="Las cabeceras SPF o DKIM fallaron, sugiriendo spoofing del servidor remitente",
                weight=2.0,
                matched_text=f"SPF: {email_obj.spf_pass}, DKIM: {email_obj.dkim_pass}"
            ))

        # Normalizar Score máximo a 10.0
        final_score = round(min(score, 10.0), 1)

        # Determinar Veredicto
        if final_score >= PHISHING_THRESHOLD_CRITICAL:
            verdict = "PHISHING"
        elif final_score >= PHISHING_THRESHOLD_WARNING:
            verdict = "SUSPICIOUS"
        else:
            verdict = "SAFE"

        # G. Manejo de Archivo de Cuarentena (Files)
        is_quarantined = False
        quarantine_file_path = ""
        if verdict in ("PHISHING", "SUSPICIOUS"):
            is_quarantined = True
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_filename = f"threat_{timestamp_str}_{body_sha256[:10]}.json"
            quarantine_file_path = str(QUARANTINE_DIR / quarantine_filename)

            quarantine_data = {
                "timestamp": datetime.now().isoformat(),
                "verdict": verdict,
                "score": final_score,
                "sender": email_obj.sender,
                "subject": email_obj.subject,
                "body_sha256": body_sha256,
                "indicators": [asdict(i) for i in indicators],
                "raw_text_preview": full_text[:500]
            }

            with open(quarantine_file_path, "w", encoding="utf-8") as qf:
                json.dump(quarantine_data, qf, indent=2, ensure_ascii=False)

        return PhishingAnalysisResult(
            score=final_score,
            verdict=verdict,
            indicators=indicators,
            body_sha256=body_sha256,
            url_hashes=url_hashes,
            is_quarantined=is_quarantined,
            quarantine_path=quarantine_file_path
        )
