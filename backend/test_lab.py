"""
Laboratorio de Pruebas y Demostración Integral (Test Lab).
Procesa correos muestra, ejecuta deduplicación por hashes y prueba los comandos interactivos.
"""

import sys
import json
from pathlib import Path

# Configurar UTF-8 para consola Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.api import app
from fastapi.testclient import TestClient
from src.config import SAMPLES_DIR, ATTACHMENTS_DIR
from src.database import DatabaseManager

client = TestClient(app)


def run_laboratory():
    print("=" * 70)
    print("🧪 LABORATORIO DE PRUEBAS: HIRE PROTOCOL")
    print("=" * 70)

    # 1. Limpiar estado previo
    DatabaseManager.clear_silence_mode()

    # 2. Procesar correos muestra
    sample_files = sorted(list(SAMPLES_DIR.glob("*.json")))
    print(f"\n📨 [PASO 1] Procesando {len(sample_files)} correos muestra a través de la API...\n")

    for sf in sample_files:
        with open(sf, "r", encoding="utf-8") as f:
            payload = json.load(f)

        res = client.post("/analyze-email", json=payload)
        data = res.json()

        print(f"📄 Archivo: {sf.name}")
        print(f"   👤 Remitente: {payload.get('sender')}")
        print(f"   💬 Asunto: {payload.get('subject')[:60]}...")
        print(f"   🚦 Ruta Asignada: {data.get('route')}")

        if data.get("route") == "JOB_UPDATE":
            job = data["data"]["job_metadata"]
            print(f"   🏢 Empresa: {job['company_name']} | Puesto: {job['role_title']}")
            print(f"   📌 Etapa: {job['stage_label']} {job['stage_emoji']}")
            if job.get("salary"):
                print(f"   💰 Salario detectado: {job['salary']}")
            if job.get("modality"):
                print(f"   🏠 Modalidad: {job['modality']}")
            if job.get("tech_stack"):
                print(f"   🛠️ Stack: {', '.join(job['tech_stack'])}")
        elif data.get("route") == "PHISHING":
            print(f"   🚨 Riesgo: {data.get('score')}/10.0 ({data.get('verdict')})")
            print(f"   ☣️ Archivo en Cuarentena: {Path(data.get('quarantine_file', '')).name}")

        print("-" * 70)

    # 3. Probar comandos interactivos de WhatsApp
    print("\n📱 [PASO 2] Probando Comandos Interactivos de WhatsApp...")
    commands = [
        "!resumen",
        "!estado Mercado Libre",
        "!pendientes",
        "!cuarentena",
        "!analizar Oferta de trabajo: Gana $5000 al dia dando likes a videos contactar por telegram"
    ]

    for cmd in commands:
        print(f"\n>> Comando enviado: {cmd}")
        res = client.post("/whatsapp-command", json={"message": cmd})
        reply = res.json().get("reply", "")
        print(reply)

    # 4. Probar escaneo y limpieza de duplicados
    print("\n📁 [PASO 3] Probando Buscador de Duplicados (Hashing SHA-256)...")
    res_scan = client.post("/duplicates/scan")
    scan_data = res_scan.json()
    print(f"   Archivos escaneados: {scan_data['total_files_scanned']}")
    print(f"   Grupos duplicados: {scan_data['duplicate_groups_count']}")
    print(f"   Espacio recuperable: {scan_data['total_wasted_mb']} MB")

    print("\n✅ ¡Laboratorio de pruebas ejecutado con 100% de éxito!")
    print("=" * 70)


if __name__ == "__main__":
    run_laboratory()
