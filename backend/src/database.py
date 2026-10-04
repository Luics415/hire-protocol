"""
Módulo de Persistencia Local SQLite.
Gestiona el historial de postulaciones, lista negra de remitentes spam, registros de cuarentena y preferencias.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .config import DB_PATH


class DatabaseManager:
    """Administrador de persistencia SQLite para el agente de correos."""

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls):
        """Inicializa las tablas de la base de datos si no existen."""
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de postulaciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    role TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    salary TEXT,
                    modality TEXT,
                    tech_stack TEXT,
                    received_at TEXT NOT NULL,
                    subject TEXT,
                    sender TEXT,
                    action_required INTEGER DEFAULT 0,
                    action_description TEXT,
                    status TEXT DEFAULT 'ACTIVA'
                )
            """)

            # Tabla de registros en cuarentena (Phishing / Amenazas)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quarantine_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    subject TEXT,
                    score REAL,
                    verdict TEXT,
                    indicators TEXT,
                    body_sha256 TEXT,
                    file_path TEXT
                )
            """)

            # Tabla de lista negra personal (!ignorar)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ignored_senders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT UNIQUE NOT NULL,
                    added_at TEXT NOT NULL
                )
            """)

            # Tabla de configuración y preferencias (!silencio)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.commit()

    @classmethod
    def save_job_application(cls, app_data: Dict[str, Any]) -> int:
        """Guarda o actualiza el estado de una postulación."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO job_applications (
                    company, role, platform, stage, salary, modality, tech_stack,
                    received_at, subject, sender, action_required, action_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app_data.get("company_name", "Desconocida"),
                app_data.get("role_title", "Desarrollador"),
                app_data.get("platform", "General"),
                app_data.get("stage", "POSTULACION_ENVIADA"),
                app_data.get("salary"),
                app_data.get("modality"),
                json.dumps(app_data.get("tech_stack", [])),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                app_data.get("subject", ""),
                app_data.get("sender", ""),
                1 if app_data.get("action_required") else 0,
                app_data.get("action_description", "")
            ))
            conn.commit()
            return cursor.lastrowid

    @classmethod
    def get_summary_stats(cls) -> Dict[str, Any]:
        """Obtiene resumen numérico para el comando !resumen."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM job_applications")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM job_applications WHERE stage = 'ENTREVISTA'")
            interviews = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM job_applications WHERE stage = 'PRUEBA_TECNICA'")
            tech_tests = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM job_applications WHERE stage = 'OFERTA'")
            offers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM job_applications WHERE stage = 'RECHAZO'")
            rejections = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM quarantine_logs")
            threats_blocked = cursor.fetchone()[0]

            return {
                "total_postulaciones": total,
                "entrevistas": interviews,
                "pruebas_tecnicas": tech_tests,
                "ofertas": offers,
                "rechazos": rejections,
                "amenazas_bloqueadas": threats_blocked
            }

    @classmethod
    def get_application_by_company(cls, company_query: str) -> Optional[Dict[str, Any]]:
        """Busca el último registro de una empresa para el comando !estado <empresa>."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM job_applications
                WHERE company LIKE ? OR subject LIKE ?
                ORDER BY id DESC LIMIT 1
            """, (f"%{company_query}%", f"%{company_query}%"))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    @classmethod
    def get_pending_actions(cls) -> List[Dict[str, Any]]:
        """Obtiene postulaciones que requieren acción del usuario para !pendientes."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM job_applications
                WHERE action_required = 1 AND stage NOT IN ('RECHAZO')
                ORDER BY id DESC LIMIT 5
            """)
            return [dict(r) for r in cursor.fetchall()]

    @classmethod
    def get_rejections(cls) -> List[Dict[str, Any]]:
        """Obtiene lista de procesos rechazados para !rechazos."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT company, role, received_at FROM job_applications
                WHERE stage = 'RECHAZO'
                ORDER BY id DESC LIMIT 5
            """)
            return [dict(r) for r in cursor.fetchall()]

    @classmethod
    def add_to_blacklist(cls, pattern: str) -> bool:
        """Agrega un remitente o dominio a la lista negra personal (!ignorar)."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO ignored_senders (pattern, added_at)
                    VALUES (?, ?)
                """, (pattern.lower().strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    @classmethod
    def is_blacklisted(cls, sender_or_domain: str) -> bool:
        """Comprueba si un remitente o dominio está en lista negra."""
        cls.init_db()
        target = sender_or_domain.lower()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pattern FROM ignored_senders")
            patterns = [r[0] for r in cursor.fetchall()]
            for p in patterns:
                if p in target:
                    return True
        return False

    @classmethod
    def save_quarantine_log(cls, q_data: Dict[str, Any]):
        """Registra un evento de correo malicioso puesto en cuarentena."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quarantine_logs (
                    timestamp, sender, subject, score, verdict, indicators, body_sha256, file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                q_data.get("timestamp", datetime.now().isoformat()),
                q_data.get("sender", ""),
                q_data.get("subject", ""),
                q_data.get("score", 0.0),
                q_data.get("verdict", "PHISHING"),
                json.dumps(q_data.get("indicators", [])),
                q_data.get("body_sha256", ""),
                q_data.get("quarantine_path", "")
            ))
            conn.commit()

    @classmethod
    def get_recent_quarantines(cls, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene las amenazas recientes para el comando !cuarentena."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, sender, subject, score, verdict FROM quarantine_logs
                ORDER BY id DESC LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    @classmethod
    def set_silence_mode(cls, hours: float) -> str:
        """Activa modo silencio por X horas."""
        cls.init_db()
        until_dt = datetime.now() + timedelta(hours=hours)
        until_str = until_dt.strftime("%Y-%m-%d %H:%M:%S")
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value) VALUES ('silence_until', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (until_str,))
            conn.commit()
        return until_str

    @classmethod
    def is_silenced(cls) -> bool:
        """Verifica si el modo silencio está activo en este momento."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'silence_until'")
            row = cursor.fetchone()
            if row:
                try:
                    until_dt = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                    return datetime.now() < until_dt
                except ValueError:
                    return False
        return False

    @classmethod
    def clear_silence_mode(cls):
        """Desactiva el modo silencio y limpia la configuración."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM settings WHERE key = 'silence_until'")
            conn.commit()

    @classmethod
    def set_setting(cls, key: str, value: str):
        """Guarda permanentemente una clave de configuración en SQLite."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))
            conn.commit()

    @classmethod
    def get_setting(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Recupera un valor de configuración almacenado permanentemente."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    @classmethod
    def get_all_settings(cls) -> Dict[str, str]:
        """Recupera todas las configuraciones guardadas en la base de datos."""
        cls.init_db()
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {r[0]: r[1] for r in cursor.fetchall()}


