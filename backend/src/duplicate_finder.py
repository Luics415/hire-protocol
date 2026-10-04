"""
Módulo de Búsqueda y Gestión de Archivos Duplicados mediante Hashing Criptográfico.
Optimizado para rendimiento mediante pre-filtrado por tamaño y lectura por bloques (chunks).
"""

import os
import shutil
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict

from .config import HASH_CHUNK_SIZE, REPORTS_DIR, ATTACHMENTS_DIR


@dataclass
class FileHashInfo:
    file_path: str
    file_name: str
    size_bytes: int
    md5: str
    sha256: str


@dataclass
class DuplicateGroup:
    sha256: str
    size_bytes: int
    canonical_file: str
    duplicate_files: List[str]
    wasted_bytes: int


@dataclass
class DuplicateScanReport:
    timestamp: str
    target_directory: str
    total_files_scanned: int
    unique_files_count: int
    duplicate_groups_count: int
    total_wasted_bytes: int
    total_wasted_mb: float
    groups: List[DuplicateGroup]


class DuplicateFinder:
    """Buscador y limpiador forense de archivos duplicados basado en hashes."""

    @classmethod
    def calculate_hashes(cls, file_path: Path, chunk_size: int = HASH_CHUNK_SIZE) -> Tuple[str, str]:
        """Calcula de forma eficiente los hashes MD5 y SHA-256 leyendo el archivo en chunks."""
        md5_hasher = hashlib.md5()
        sha256_hasher = hashlib.sha256()

        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_hasher.update(chunk)
                sha256_hasher.update(chunk)

        return md5_hasher.hexdigest(), sha256_hasher.hexdigest()

    @classmethod
    def scan_directory(cls, directory_path: Optional[Path] = None) -> DuplicateScanReport:
        """Escanea un directorio en busca de archivos duplicados usando optimización multi-etapa."""
        target_dir = Path(directory_path) if directory_path else ATTACHMENTS_DIR
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)

        # Etapa 1: Agrupar por tamaño de archivo (pre-filtrado sin I/O pesado de disco)
        size_map: Dict[int, List[Path]] = {}
        total_scanned = 0

        for root, _, files in os.walk(target_dir):
            for file_name in files:
                full_path = Path(root) / file_name
                try:
                    file_size = full_path.stat().st_size
                    # Ignorar archivos vacíos (0 bytes) del cálculo de duplicados
                    if file_size > 0:
                        size_map.setdefault(file_size, []).append(full_path)
                        total_scanned += 1
                except (OSError, PermissionError):
                    continue

        # Etapa 2: Solo calcular hashes para archivos que comparten el mismo tamaño
        hash_groups: Dict[str, List[FileHashInfo]] = {}
        for size, path_list in size_map.items():
            if len(path_list) > 1:
                # Posibles duplicados, calcular hashes
                for file_path in path_list:
                    try:
                        md5_val, sha256_val = cls.calculate_hashes(file_path)
                        info = FileHashInfo(
                            file_path=str(file_path),
                            file_name=file_path.name,
                            size_bytes=size,
                            md5=md5_val,
                            sha256=sha256_val
                        )
                        hash_groups.setdefault(sha256_val, []).append(info)
                    except (OSError, PermissionError):
                        continue

        # Etapa 3: Identificar grupos de duplicados reales
        duplicate_groups: List[DuplicateGroup] = []
        total_wasted = 0
        unique_count = total_scanned

        for sha256_key, items in hash_groups.items():
            if len(items) > 1:
                # El primero se conserva como original (canónico)
                canonical = items[0].file_path
                duplicates = [item.file_path for item in items[1:]]
                wasted = items[0].size_bytes * len(duplicates)
                total_wasted += wasted
                unique_count -= len(duplicates)

                duplicate_groups.append(DuplicateGroup(
                    sha256=sha256_key,
                    size_bytes=items[0].size_bytes,
                    canonical_file=canonical,
                    duplicate_files=duplicates,
                    wasted_bytes=wasted
                ))

        wasted_mb = round(total_wasted / (1024 * 1024), 2)
        now_str = datetime.now().isoformat()

        report = DuplicateScanReport(
            timestamp=now_str,
            target_directory=str(target_dir),
            total_files_scanned=total_scanned,
            unique_files_count=unique_count,
            duplicate_groups_count=len(duplicate_groups),
            total_wasted_bytes=total_wasted,
            total_wasted_mb=wasted_mb,
            groups=duplicate_groups
        )

        # Guardar reporte en archivo JSON (Files)
        report_filename = f"duplicates_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = REPORTS_DIR / report_filename
        with open(report_path, "w", encoding="utf-8") as rf:
            json.dump(asdict(report), rf, indent=2, ensure_ascii=False)

        return report

    @classmethod
    def clean_duplicates(cls, backup_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Mueve de forma segura los archivos duplicados a una carpeta de reciclaje/backup."""
        report = cls.scan_directory()
        if not report.groups:
            return {
                "status": "success",
                "message": "No se encontraron archivos duplicados para limpiar.",
                "files_removed": 0,
                "freed_mb": 0.0
            }

        target_backup = backup_dir if backup_dir else (REPORTS_DIR / "duplicates_backup")
        target_backup.mkdir(parents=True, exist_ok=True)

        files_moved = 0
        bytes_freed = 0

        for group in report.groups:
            for dup_path_str in group.duplicate_files:
                dup_path = Path(dup_path_str)
                if dup_path.exists():
                    dest = target_backup / f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{dup_path.name}"
                    shutil.move(str(dup_path), str(dest))
                    files_moved += 1
                    bytes_freed += group.size_bytes

        return {
            "status": "success",
            "message": f"Limpieza completada: se aislaron {files_moved} archivos duplicados.",
            "files_removed": files_moved,
            "freed_bytes": bytes_freed,
            "freed_mb": round(bytes_freed / (1024 * 1024), 2),
            "backup_folder": str(target_backup)
        }
