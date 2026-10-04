# 🛡️ Hire Protocol
### *Agente Local Inteligente de Postulaciones Laborales, Detección Forense de Phishing y Deduplicación Criptográfica*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![n8n](https://img.shields.io/badge/n8n-Orchestration-FF6D5A.svg?logo=n8n&logoColor=white)](https://n8n.io)
[![Tests](https://img.shields.io/badge/Tests-22%20Passed%20(100%25)-success.svg)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

<p align="center">
  <img src="docs/images/cover-hire-protocol.jpg" alt="Hire Protocol Cover Banner" width="100%" style="border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.5);" />
</p>

---

## 📌 Descripción General

**Hire Protocol** es un agente técnico autónomo y estrictamente local diseñado para automatizar la monitorización y seguimiento de procesos de selección laboral sin interactuar ni responder automáticamente a los reclutadores, garantizando privacidad y discreción absoluta.

El sistema cuenta con un **Hub interactivo y Buscador de Herramientas desde la terminal**, permitiendo conectar y probar WhatsApp, buzones de correo (IMAP/Gmail), Discord y n8n, asegurando su persistencia en disco (SQLite y `.env`) para que tus conexiones sigan vigentes cada vez que apagues y enciendas tu computadora.

El protocolo combina la orquestación de **n8n** con un núcleo en **Python** especializado en:
1. **Hub y Buscador de Herramientas en Terminal**: Panel interactivo con búsqueda en tiempo real de integraciones y persistencia permanente indestructible.
2. **Detección Heurística de Phishing y Ciberamenazas**: Análisis forense de cabeceras, enlaces con spoofing visual y patrones de intimidación o estafas laborales.
3. **Clasificación Inteligente de Vacantes**: Identificación de bolsas de trabajo (LinkedIn, Indeed, Computrabajo) y ATS corporativos (Workday, Greenhouse, Lever), extrayendo automáticamente **salario**, **modalidad** y **stack tecnológico**.
4. **Buscador Criptográfico de Archivos Duplicados**: Escáner de almacenamiento en bloques de 64 KB con hashing MD5 y SHA-256 para depurar versiones redundantes de CVs y adjuntos de correo.
5. **Interacción Bidireccional en WhatsApp**: Control total del asistente vía comandos interactivos (`!resumen`, `!estado`, `!pendientes`, `!analizar`, `!duplicados`, `!limpiar`, etc.).
6. **Bitácora Técnica en Discord**: Registro en segundo plano con embeds detallados para no saturar tu mensajería personal.

---

## 🏗️ Arquitectura del Sistema

```mermaid
flowchart TD
    A["📨 Servidor de Correo / Webhook"] --> B["⚙️ n8n Workflow Engine"]
    
    subgraph n8n_Core ["Orquestador n8n"]
        B --> C["HTTP Request: POST /analyze-email"]
        C --> D{"Switch Ruteo de Eventos"}
    end

    subgraph Python_Backend ["Motor Python de Seguridad y Clasificación"]
        C --> E["Parser de Correos (Strings & Files)"]
        E --> F["Detector Antiphishing (Regex & Hashes)"]
        E --> G["Clasificador de Vacantes (Regex Salario/Stack)"]
        E --> H["Buscador de Duplicados (SHA-256 Chunks)"]
        
        F --> I["Aislamiento en Cuarentena"]
        G --> J["Persistencia en SQLite"]
    end
    
    D -->|Ruta Phishing| K["🚨 Alerta Crítica WhatsApp"]
    D -->|Ruta Postulación| L["💼 Notificación WhatsApp"]
    D -->|Bitácora Detallada| M["📜 Canal de Discord (Embed)"]
    D -->|Descarte / Lista Negra| N["📁 Archivo Silencioso"]
```

<p align="center">
  <img src="docs/images/hire-protocol-n8n-workflow.jpg" alt="Lienzo de Orquestación Visual n8n" width="100%" style="border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);" />
  <br>
  <em>Lienzo de orquestación visual en n8n: Ingesta de correo, análisis con motor Python y ruteo a WhatsApp/Discord.</em>
</p>

---

## 💻 Pilares Técnicos Implementados

| Pilar | Implementación Concreta en el Código |
| :--- | :--- |
| **n8n** | Workflows exportados en JSON para ingesta de buzón, ruteo por switch y bot interactivo bidireccional. |
| **Python** | Microservicio REST con FastAPI, runners CLI y suite de pruebas unitarias/integración con `pytest`. |
| **Strings** | Normalización Unicode, sanitización de etiquetas HTML, detección de hipervínculos engañosos y tokens de empresa. |
| **Expresiones Regulares (Regex)** | Límites de palabra (`\b`), grupos no-capturadores (`(?:...)`), patrones de intimidación psicológica y extracción de salarios/stack. |
| **Hashing** | Lectura por streaming de buffers constantes (64 KB) con MD5 y SHA-256 para auditoría de archivos y URLs. |
| **Archivos (Files)** | Manejo de estructuras `.eml`, aislamiento seguro en `data/quarantine/`, backup de adjuntos y persistencia SQLite. |

---

## 📱 Comandos Interactivos de WhatsApp

El bot soporta interacción bidireccional completa. Puedes enviarle cualquiera de estos comandos desde tu chat personal:

| Comando | Utilidad | Ejemplo de Salida |
| :--- | :--- | :--- |
| **`!resumen`** | Muestra el estado consolidado de todas tus postulaciones y amenazas bloqueadas. | *Total: 6 \| Entrevistas: 4 \| Pruebas Técnicas: 1 \| Bloqueadas: 5* |
| **`!estado <empresa>`** | Consulta el último movimiento y tareas pendientes con una empresa en específico. | `!estado Mercado Libre` ➔ *Invitación a entrevista técnica ($4,500 USD, Remoto)* |
| **`!pendientes`** | Lista únicamente los procesos donde debes realizar una acción (agendar llamada, entregar código). | *1. Nubank (Prueba Técnica) \| 2. Mercado Libre (Entrevista)* |
| **`!rechazos`** | Muestra los procesos finalizados para no darles seguimiento innecesario. | *Lista de candidaturas cerradas recientemente.* |
| **`!analizar <texto>`** | Escanea al instante cualquier mensaje o enlace sospechoso reenviado al chat. | `!analizar Gana $5000 al día dando likes...` ➔ *Score: 4.5/10 (SOSPECHOSO)* |
| **`!cuarentena`** | Inspecciona los correos fraudulentos que el bot frenó y envió a la bóveda de seguridad. | *Muestra remitentes maliciosos y nivel de riesgo.* |
| **`!duplicados`** | Ejecuta el escáner de hashes SHA-256 y reporta espacio ocupado por CVs y adjuntos repetidos. | *Archivos escaneados: 6 \| Duplicados: 2 \| Espacio: 45 MB* |
| **`!limpiar`** | Traslada automáticamente las copias redundantes a una carpeta de resguardo sin borrar originales. | *Limpieza completada: 3 archivos aislados.* |
| **`!ignorar <email/dominio>`** | Añade un remitente o dominio spammer a tu lista negra personal. | `!ignorar spam-jobs.com` ➔ *Remitente bloqueado.* |
| **`!silencio [horas]`** | Pausa temporalmente las alertas de WhatsApp durante reuniones o entrevistas. | `!silencio 2` ➔ *Modo silencio activo hasta las 19:30.* |
| **`!ayuda`** | Despliega la guía de comandos disponibles con formato amigable. | *Menú interactivo de ayuda.* |

<p align="center">
  <img src="docs/images/hire-protocol-whatsapp-bot.jpg" alt="Bot Bidireccional de WhatsApp & Alerta de Phishing" width="360" style="border-radius: 18px; box-shadow: 0 8px 30px rgba(0,0,0,0.5);" />
  <br>
  <em>Interacción real con el bot de WhatsApp: Consultas de estado y alerta crítica de phishing aislado en cuarentena.</em>
</p>

---

---

## ⚡ Puesta en Marcha Inmediata (1 Clic en Cualquier Computadora)

El proyecto está preparado para funcionar de inmediato sin configuraciones complejas tras clonarlo en cualquier máquina:

### Opción A: Script Automático (Recomendado)

* **En Windows**: Haz doble clic en [`start.bat`](start.bat) o ejecútalo desde tu terminal:
  ```powershell
  .\start.bat
  ```
  *(Crea el entorno virtual `.venv` automáticamente, instala dependencias, inicializa `.env` y despliega el menú de inicio).*

* **En Linux / macOS**: Ejecuta el lanzador universal:
  ```bash
  chmod +x start.sh
  ./start.sh
  ```

### Opción B: Despliegue con Docker Compose

Si cuentas con Docker instalado, puedes levantar tanto el backend Python como n8n con un solo comando:
```bash
docker compose up -d
```
* **n8n UI**: `http://localhost:5678`
* **Python API**: `http://localhost:8000`

---

## 🔍 Hub Interactivo & Buscador de Herramientas desde la Terminal

Al ejecutar [`start.bat`](start.bat), [`start.sh`](start.sh) o `python backend/run_service.py`, Hire Protocol despliega su **Hub & Buscador Interactivo**:

<p align="center">
  <img src="docs/images/hire-protocol-terminal-hub.jpg" alt="Hire Protocol Terminal Hub & Buscador de Herramientas" width="100%" style="border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);" />
  <br>
  <em>Consola interactiva de Hire Protocol: Búsqueda dinámica de herramientas en tiempo real y persistencia local.</em>
</p>

```text
========================================================================
  🛡️  HIRE PROTOCOL - HUB INTERACTIVO & BUSCADOR DE HERRAMIENTAS
========================================================================
ℹ️  Tus herramientas conectadas se guardan de forma permanente en tu máquina.
   Seguirán vinculadas mañana al reiniciar tu computadora (100% Local y Privado).

HERRAMIENTAS INTEGRADAS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 [1] ✅ WhatsApp Bot Gateway             | Mensajería y Alertas | Mock Local Activo
 [2] ⚪ Servicio de Correo (IMAP/Gmail)  | Buzón de Entrada     | Vía n8n (Modo Webhook)
 [3] ✅ Discord Security Logger          | Bitácora Forense     | Webhook Activo
 [4] ✅ Orquestador n8n                  | Automatización       | Vinculado (http://localhost:5678)
 [5] ✅ Motor Antiphishing & Cuarentena  | Seguridad Heurística | Activo (Umbral: 4.0 / 7.0)
 [6] ✅ Deduplicador Criptográfico       | Almacenamiento Local | Activo (Bloques: 64 KB)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACCIONES:
 [S] 🚀 Iniciar Servidor Hire Protocol (FastAPI)
 [B] 🔍 Buscar Herramientas por Nombre o Etiqueta
 [T] 🧪 Ejecutar Suite de Pruebas y Laboratorio Demo
 [0] 🚪 Salir
========================================================================
```

* **Búsqueda en tiempo real**: Escribe términos como `whatsapp`, `correo`, `discord`, `hash` para filtrar herramientas al instante.
* **Persistencia permanente indestructible**: Los tokens y credenciales se guardan automáticamente en tu archivo `.env` y en la base SQLite local (`settings`). Puedes apagar la máquina y mañana tus conexiones seguirán listas sin necesidad de reconfigurar.

---

## 🔐 Gestión de Licencias y Credenciales 100% Locales

> **Privacidad Absoluta**: Toda la herramienta es un **agente estrictamente local**. Tus credenciales de WhatsApp, tokens de Twilio, webhooks de Discord y cuentas de correo **nunca se envían a servidores de terceros ni a la nube**.

El proyecto incluye el asistente interactivo por consola para vincular tus licencias y cuentas sin editar archivos manualmente:

```powershell
# Iniciar el asistente interactivo de credenciales
python backend/run_service.py --configure

# Comprobar el estado de vinculación (con claves enmascaradas)
python backend/run_service.py --credentials
```

Para una guía detallada sobre cómo vincular cuentas de Gmail (OAuth/IMAP), Meta Cloud API y Twilio, consulta [`docs/CREDENTIALS_AND_ACCOUNTS.md`](docs/CREDENTIALS_AND_ACCOUNTS.md).

---

## 🚀 Instalación y Pruebas Manuales (Paso a Paso)

### 1. Configurar Entorno Virtual
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Ejecutar Pruebas y Laboratorio Demo
```powershell
# Ejecutar suite de pruebas unitarias e integración (18 tests)
.\.venv\Scripts\pytest -v

# Ejecutar el laboratorio interactivo end-to-end
.\.venv\Scripts\python test_lab.py
```

### 3. Iniciar Servicios
```powershell
# Terminal 1: Iniciar API Python
.\.venv\Scripts\python run_service.py --serve

# Terminal 2: Iniciar n8n nativamente
npx n8n
```
1. Abre tu navegador en **`http://localhost:5678`**.
2. Dirígete a **Workflows** ➔ **Import from File**.
3. Selecciona `workflows/email_analyzer_workflow.json` y `workflows/whatsapp_bidirectional_bot_workflow.json`.

---

## 📂 Estructura del Repositorio

```text
.
├── backend/
│   ├── src/
│   │   ├── api.py                      # Endpoints FastAPI para n8n (/credentials, /status, etc.)
│   │   ├── command_handler.py          # Lógica de comandos interactivos de WhatsApp
│   │   ├── config.py                   # Configuración y variables de entorno flexibles
│   │   ├── database.py                 # Persistencia SQLite local
│   │   ├── duplicate_finder.py         # Hashing SHA-256/MD5 en bloques para duplicados
│   │   ├── email_parser.py             # Parser de cadenas, archivos .eml y HTML
│   │   ├── job_classifier.py           # Clasificador de vacantes con Regex (salario/stack)
│   │   ├── notifier.py                 # Despachador de WhatsApp (Twilio/Mock) y Discord
│   │   └── phishing_detector.py        # Motor heurístico antiphishing y cuarentena
│   ├── tests/
│   │   ├── test_api_endpoints.py       # Pruebas de integración de la API
│   │   ├── test_command_handler.py     # Pruebas de comandos de WhatsApp
│   │   ├── test_duplicate_finder.py    # Pruebas de deduplicación criptográfica
│   │   ├── test_job_classifier.py      # Pruebas de regex de empleo
│   │   └── test_phishing.py            # Pruebas del motor antiphishing
│   ├── data/
│   │   ├── samples/                    # Muestras reales (.json y .eml)
│   │   ├── attachments/                # Archivos de prueba para escaneo
│   │   └── quarantine/                 # Bóveda de correos maliciosos aislados (.gitkeep)
│   ├── Dockerfile                      # Imagen ligera de contenedor Python
│   ├── test_lab.py                     # Demostración E2E con 1 comando
│   ├── run_service.py                  # CLI runner con asistente --configure
│   └── requirements.txt                # Dependencias fijadas
├── workflows/
│   ├── email_analyzer_workflow.json    # Workflow n8n principal de análisis y ruteo
│   └── whatsapp_bidirectional_bot_workflow.json # Workflow n8n del bot de WhatsApp
├── docs/
│   ├── ARCHITECTURE.md                 # Especificación técnica de arquitectura
│   ├── CREDENTIALS_AND_ACCOUNTS.md     # Guía de licencias, cuentas de correo y privacidad local
│   ├── REGEX_AND_HASHING.md            # Guía detallada de expresiones regulares y hashes
│   └── N8N_SETUP_GUIDE.md              # Manual de configuración local de n8n
├── docker-compose.yml                  # Despliegue de 1 comando (Backend + n8n)
├── start.bat                           # Lanzador interactivo automático para Windows
├── start.sh                            # Lanzador interactivo automático para Linux/macOS
├── .env.example                        # Plantilla de variables de entorno
├── LICENSE                             # Licencia Apache 2.0
└── README.md                           # Documentación principal
```

---

## 📜 Licencia

Distribuido bajo la licencia **Apache 2.0**. Consulta el archivo [`LICENSE`](LICENSE) para más detalles.
