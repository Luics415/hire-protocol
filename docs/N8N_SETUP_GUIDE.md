# Hire Protocol: Guía de Orquestación con n8n

Esta guía explica cómo ejecutar n8n en tu entorno local e importar los flujos automatizados de Hire Protocol para análisis de correos y bot de WhatsApp.

---

## 1. Requisitos Previos

* **Node.js**: v18.0 o superior (verificado con `node -v`)
* **Python**: 3.10 o superior (verificado con `python --version`)
* **Puerto 5678**: Puerto por defecto de n8n
* **Puerto 8000**: Puerto del microservicio Python

---

## 2. Iniciar el Microservicio de Seguridad en Python

Antes de lanzar los flujos en n8n, el motor de seguridad en Python debe estar escuchando peticiones:

```powershell
cd backend
.\.venv\Scripts\python run_service.py --serve
```

* El servidor arrancará en `http://127.0.0.1:8000`.
* Puedes verificar el estado en cualquier navegador visitando `http://127.0.0.1:8000/status`.

---

## 3. Iniciar n8n Localmente

Puedes iniciar n8n de forma nativa e inmediata utilizando `npx` sin necesidad de contenedores Docker:

```powershell
npx n8n
```

* Al iniciar por primera vez, n8n abrirá la interfaz gráfica en tu navegador:  
  👉 **`http://localhost:5678`**

---

## 4. Importar los Flujos de Trabajo (Workflows)

El proyecto incluye dos flujos listos para importar con un clic:

### A. Flujo 1: Analizador de Correos y Postulaciones
1. En n8n, dirígete al menú lateral izquierdo y haz clic en **Workflows**.
2. Haz clic en el botón superior derecho **Add workflow** (o los 3 puntos `...`).
3. Selecciona **Import from File**.
4. Selecciona el archivo:  
   `workflows/email_analyzer_workflow.json`
5. Activa el workflow haciendo clic en el switch superior **Active**.

### B. Flujo 2: Bot Bidireccional de WhatsApp
1. Haz clic en **Add workflow** ➔ **Import from File**.
2. Selecciona el archivo:  
   `workflows/whatsapp_bidirectional_bot_workflow.json`
3. Activa el workflow.

---

## 5. Probar la Integración

### Prueba de Ingesta de Correo (Simulación de Webhook)
Puedes enviar un correo de prueba directamente al webhook de n8n mediante PowerShell o cURL:

```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook/email-inbox" -Method Post -ContentType "application/json" -Body (@{
    sender = "talent-acquisition@mercadolibre.com"
    subject = "Invitación a entrevista técnica - Backend Engineer"
    text = "Hola, queremos agendar una entrevista técnica. Salario: $4,500 USD. Modalidad: Remoto. Stack: Python, AWS."
} | ConvertTo-Json)
```

### Prueba de Comando de WhatsApp
```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook/whatsapp-command" -Method Post -ContentType "application/json" -Body (@{
    message = "!resumen"
} | ConvertTo-Json)
```

---

## 6. Conexión a Servicios Reales (Producción Opcional)

* **Gmail / IMAP**:
  - En el workflow de n8n, puedes sustituir el nodo `Webhook Entrada Correo` por el nodo oficial **Gmail Trigger** o **Email Trigger (IMAP)** configurando tus credenciales de aplicación.
* **Twilio WhatsApp**:
  - Para recibir mensajes reales en tu teléfono, configura tus credenciales `Account SID` y `Auth Token` en el archivo `.env` o en el nodo de Twilio/WhatsApp de n8n.
* **Discord Webhook**:
  - Pega la URL del webhook de tu canal de Discord en `.env` bajo `DISCORD_WEBHOOK_URL` para recibir la bitácora técnica automática.
