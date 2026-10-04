# 🔐 Guía de Credenciales, Licencias y Cuentas Locales

> **Garantía de Privacidad**: Este agente opera **100% de manera local en tu máquina**.  
> Ni tus correos, ni los estados de tus postulaciones, ni tus contraseñas o licencias de API se envían a servidores de terceros o plataformas en la nube. Todas las credenciales permanecen cifradas o aisladas en tu entorno local.

---

## 1. Filosofía de Aislamiento y Seguridad

* **Archivo `.env` protegido**: El archivo de variables y credenciales está estrictamente incluido en `.gitignore` para garantizar que jamás sea publicado accidentalmente al clonar o hacer `git push`.
* **Modo MOCK predeterminado**: Al clonar el proyecto en cualquier computadora, el agente funciona de inmediato en modo simulado local sin exigir suscripciones ni tarjetas de crédito.
* **Diagnóstico seguro**: Los comandos y endpoints de la API enmascaran tus claves (ej. `ACXX...XXXX`) para que puedas auditar el estado sin exponer secretos.

---

## 2. Vinculación de Mensajería (WhatsApp)

### Opción A: Modo MOCK (Pruebas Locales Inmediatas)
No requiere cuentas externas. Cada notificación o alerta se imprime en la consola del servidor y se devuelve a n8n.
```env
WHATSAPP_PROVIDER=mock
```

### Opción B: Licencia / Cuenta Twilio WhatsApp
1. Crea una cuenta en [Twilio](https://www.twilio.com/) y accede a la sección **WhatsApp Sandbox**.
2. Copia tu **Account SID** y tu **Auth Token**.
3. Configúralos ejecutando el asistente interactivo:
   ```powershell
   python backend/run_service.py --configure
   ```
   o directamente en tu archivo `backend/.env`:
   ```env
   WHATSAPP_PROVIDER=twilio
   TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   TWILIO_AUTH_TOKEN=tu_auth_token_de_twilio
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   USER_WHATSAPP_NUMBER=+5215500000000
   ```

---

## 3. Vinculación de Cuentas de Correo (n8n Local)

Las cuentas de correo electrónico **no se configuran en el código de Python**, sino dentro del orquestador local de **n8n**, garantizando que tus tokens OAuth o contraseñas permanezcan dentro de la base de datos segura de tu n8n personal (`~/.n8n/`):

### Para Gmail:
1. Abre n8n en tu navegador (`http://localhost:5678`).
2. Ve a **Credentials** ➔ **New Credential** ➔ **Gmail OAuth2 API** o **IMAP**.
3. Para IMAP con Gmail:
   - Servidor: `imap.gmail.com`
   - Puerto: `993` (SSL/TLS activado)
   - Usuario: tu dirección de correo
   - Contraseña: una **Contraseña de Aplicación** generada desde tu cuenta de Google (*Seguridad ➔ Verificación en dos pasos ➔ Contraseñas de aplicaciones*).
4. En el workflow `Analizador Inteligente de Correos`, reemplaza el nodo `Webhook Entrada Correo` por el nodo **Email Trigger (IMAP)** o **Gmail Trigger** usando tu credencial guardada.

---

## 4. Bitácora Técnica de Discord (Opcional)

Si deseas recibir un registro técnico detallado de cada correo analizado (con encabezados, score heurístico y hashes) sin saturar tu WhatsApp personal:

1. En tu servidor de Discord, crea un canal privado (ej. `#auditoria-empleos`).
2. Ve a **Ajustes del Canal** ➔ **Integraciones** ➔ **Webhooks** ➔ **Nuevo Webhook**.
3. Copia la URL del webhook y agrégala a tu `backend/.env`:
   ```env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/tu_id/tu_token
   ```

---

## 5. Verificación de Estado

Para verificar en cualquier momento que tus credenciales locales están correctamente cargadas y enlazadas, ejecuta:

```powershell
# Por consola
python backend/run_service.py --credentials

# O desde tu navegador
http://127.0.0.1:8000/credentials
```
