"""
Módulo de Extracción y Procesamiento de Cadenas (Strings) y Archivos (Files) de Correos.
Procesa formatos .eml, texto plano y payloads estructurados JSON.
"""

import email
from email import policy
from email.parser import BytesParser
import re
import html
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .config import ATTACHMENTS_DIR


@dataclass
class Hyperlink:
    visible_text: str
    target_url: str
    is_mismatched: bool = False


@dataclass
class AttachmentInfo:
    filename: str
    content_type: str
    size_bytes: int
    local_path: Optional[str] = None
    md5_hash: str = ""
    sha256_hash: str = ""


@dataclass
class ParsedEmail:
    sender: str
    sender_domain: str
    sender_name: str
    recipient: str
    subject: str
    date_str: str
    raw_headers: Dict[str, str] = field(default_factory=dict)
    body_plain: str = ""
    body_html: str = ""
    clean_text: str = ""
    hyperlinks: List[Hyperlink] = field(default_factory=list)
    attachments: List[AttachmentInfo] = field(default_factory=list)
    spf_pass: Optional[bool] = None
    dkim_pass: Optional[bool] = None


class EmailParser:
    """Clase especializada en manipular cadenas (strings) y archivos para extraer datos de correos."""

    @staticmethod
    def extract_domain(email_address: str) -> str:
        """Extrae y normaliza el dominio de una dirección de correo."""
        if not email_address:
            return ""
        # Extraer usando regex el contenido dentro de <> o la dirección cruda
        match = re.search(r"[\w\.-]+@([\w\.-]+\.\w+)", email_address)
        if match:
            return match.group(1).lower().strip()
        return ""

    @staticmethod
    def extract_sender_name(email_address: str) -> str:
        """Extrae el nombre visible del remitente."""
        if not email_address:
            return ""
        # Formato: "Nombre del Remitente" <correo@dominio.com>
        match = re.search(r"^(.*?)\s*<.*?>$", email_address)
        if match:
            clean_name = match.group(1).replace('"', '').replace("'", '').strip()
            if clean_name:
                return clean_name
        return email_address.split("@")[0]

    @staticmethod
    def html_to_clean_text(html_content: str) -> str:
        """Limpia etiquetas HTML, decodifica entidades y normaliza espacios en blanco."""
        if not html_content:
            return ""
        
        # Eliminar bloques de script y style
        cleaned = re.sub(r"<(script|style).*?>.*?</\1>", " ", html_content, flags=re.DOTALL | re.IGNORECASE)
        # Reemplazar saltos de línea HTML por saltos de línea estándar
        cleaned = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", cleaned, flags=re.IGNORECASE)
        # Eliminar cualquier etiqueta HTML remanente
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        # Decodificar entidades HTML (ej: &nbsp; &amp; &lt;)
        cleaned = html.unescape(cleaned)
        # Normalizar espacios repetidos pero preservando saltos de línea legibles
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.splitlines()]
        return "\n".join([line for line in lines if line])

    @classmethod
    def extract_hyperlinks(cls, html_content: str) -> List[Hyperlink]:
        """Extrae hipervínculos comparando texto visible con URL destino para detectar spoofing."""
        hyperlinks: List[Hyperlink] = []
        if not html_content:
            return hyperlinks

        # Regex para capturar etiquetas <a href="...">texto</a>
        pattern = re.compile(r'<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
        
        for match in pattern.finditer(html_content):
            raw_url = match.group(1).strip()
            raw_text = cls.html_to_clean_text(match.group(2)).strip()

            # Comprobar si el texto visible se hace pasar por una URL diferente
            # Ej: texto dice "https://paypal.com/login" pero href es "http://phish-site.ru"
            is_mismatched = False
            visible_url_match = re.search(r"https?://([\w\.-]+)", raw_text, re.IGNORECASE)
            target_url_match = re.search(r"https?://([\w\.-]+)", raw_url, re.IGNORECASE)

            if visible_url_match and target_url_match:
                visible_domain = visible_url_match.group(1).lower()
                target_domain = target_url_match.group(1).lower()
                if visible_domain != target_domain:
                    is_mismatched = True

            hyperlinks.append(Hyperlink(
                visible_text=raw_text,
                target_url=raw_url,
                is_mismatched=is_mismatched
            ))

        return hyperlinks

    @classmethod
    def parse_eml_file(cls, file_path: Path) -> ParsedEmail:
        """Parsea un archivo físico .eml del sistema de archivos."""
        with open(file_path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)

        sender = msg.get("From", "")
        sender_domain = cls.extract_domain(sender)
        sender_name = cls.extract_sender_name(sender)
        recipient = msg.get("To", "")
        subject = msg.get("Subject", "(Sin Asunto)")
        date_str = msg.get("Date", "")

        # Cabeceras de autenticación (SPF / DKIM)
        auth_results = msg.get("Authentication-Results", "").lower()
        spf_pass = "spf=pass" in auth_results if auth_results else None
        dkim_pass = "dkim=pass" in auth_results if auth_results else None

        body_plain = ""
        body_html = ""
        attachments: List[AttachmentInfo] = []

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                content_type = part.get_content_type()

                if "attachment" in content_disposition:
                    filename = part.get_filename() or "adjunto_desconocido.bin"
                    payload = part.get_payload(decode=True) or b""
                    
                    # Guardar archivo adjunto
                    save_path = ATTACHMENTS_DIR / filename
                    with open(save_path, "wb") as af:
                        af.write(payload)

                    attachments.append(AttachmentInfo(
                        filename=filename,
                        content_type=content_type,
                        size_bytes=len(payload),
                        local_path=str(save_path)
                    ))
                elif content_type == "text/plain":
                    body_plain += part.get_content()
                elif content_type == "text/html":
                    body_html += part.get_content()
        else:
            payload = msg.get_content()
            if msg.get_content_type() == "text/html":
                body_html = payload
            else:
                body_plain = payload

        # Generar texto limpio
        clean_text = body_plain if body_plain else cls.html_to_clean_text(body_html)
        hyperlinks = cls.extract_hyperlinks(body_html)

        return ParsedEmail(
            sender=sender,
            sender_domain=sender_domain,
            sender_name=sender_name,
            recipient=recipient,
            subject=subject,
            date_str=date_str,
            raw_headers=dict(msg.items()),
            body_plain=body_plain,
            body_html=body_html,
            clean_text=clean_text,
            hyperlinks=hyperlinks,
            attachments=attachments,
            spf_pass=spf_pass,
            dkim_pass=dkim_pass
        )

    @classmethod
    def parse_dict(cls, data: Dict[str, Any]) -> ParsedEmail:
        """Crea una estructura ParsedEmail desde un payload JSON de n8n o webhook."""
        sender = data.get("sender") or data.get("from", "")
        sender_domain = cls.extract_domain(sender)
        sender_name = cls.extract_sender_name(sender)
        recipient = data.get("recipient") or data.get("to", "")
        subject = data.get("subject", "")
        date_str = data.get("date", "")
        
        body_plain = data.get("body_plain") or data.get("text", "")
        body_html = data.get("body_html") or data.get("html", "")
        
        clean_text = body_plain if body_plain else cls.html_to_clean_text(body_html)
        hyperlinks = cls.extract_hyperlinks(body_html)

        # Si vienen URLs explícitas en texto plano, capturarlas
        url_matches = re.findall(r"https?://[^\s<>\"']+", clean_text)
        for url in url_matches:
            if not any(h.target_url == url for h in hyperlinks):
                hyperlinks.append(Hyperlink(visible_text=url, target_url=url, is_mismatched=False))

        return ParsedEmail(
            sender=sender,
            sender_domain=sender_domain,
            sender_name=sender_name,
            recipient=recipient,
            subject=subject,
            date_str=date_str,
            raw_headers=data.get("headers", {}),
            body_plain=body_plain,
            body_html=body_html,
            clean_text=clean_text,
            hyperlinks=hyperlinks,
            attachments=[],
            spf_pass=data.get("spf_pass"),
            dkim_pass=data.get("dkim_pass")
        )
