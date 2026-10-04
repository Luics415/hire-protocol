"""
Pruebas Unitarias del Buscador de Archivos Duplicados mediante Hashing Criptográfico.
"""

import pytest
from pathlib import Path
from src.duplicate_finder import DuplicateFinder


def test_duplicate_file_detection_and_cleaning(tmp_path: Path):
    # Crear archivos de prueba en un directorio temporal
    test_dir = tmp_path / "files_test"
    test_dir.mkdir()

    content_a = b"Contenido identico del Curriculum Vitae de prueba version 2026."
    content_b = b"Otro archivo diferente con datos tecnicos de postulacion."

    # Archivo original A
    file1 = test_dir / "CV_Senior_Backend.pdf"
    file1.write_bytes(content_a)

    # Copia exacta de A con otro nombre
    file2 = test_dir / "CV_Senior_Backend_copia.pdf"
    file2.write_bytes(content_a)

    # Tercera copia de A
    file3 = test_dir / "CV_Senior_Backend_final_v2.pdf"
    file3.write_bytes(content_a)

    # Archivo diferente B
    file4 = test_dir / "Carta_Recomendacion.pdf"
    file4.write_bytes(content_b)

    # 1. Escanear directorio
    report = DuplicateFinder.scan_directory(test_dir)
    assert report.total_files_scanned == 4
    assert report.duplicate_groups_count == 1
    assert report.unique_files_count == 2  # A y B
    assert len(report.groups[0].duplicate_files) == 2  # 2 copias redundantes de A

    # 2. Verificar hashes
    md5_1, sha256_1 = DuplicateFinder.calculate_hashes(file1)
    md5_2, sha256_2 = DuplicateFinder.calculate_hashes(file2)
    assert md5_1 == md5_2
    assert sha256_1 == sha256_2

    # 3. Limpiar duplicados enviándolos a carpeta de backup
    backup_dir = tmp_path / "backup"
    clean_res = DuplicateFinder.clean_duplicates(backup_dir=backup_dir)

    assert clean_res["status"] == "success"
    # El archivo canónico debe permanecer
    assert file1.exists() or Path(report.groups[0].canonical_file).exists()
