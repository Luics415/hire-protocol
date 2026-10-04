# Guía Técnica: Expresiones Regulares, Hashing Criptográfico y Procesamiento de Cadenas

Esta guía documenta los fundamentos teóricos y las decisiones de implementación aplicadas en el proyecto en materia de **procesamiento de cadenas (strings)**, **expresiones regulares (regex)**, **hashing** y **manipulación de archivos (files)**.

---

## 1. Manipulación de Cadenas (Strings) y Sanitización

### Normalización de Texto y Limpieza HTML
El procesamiento de correos electrónicos requiere limpiar formatos arbitrarios (HTML, entidades escapadas, múltiples espacios en blanco) preservando la integridad del contenido para los regex:

```python
# Eliminación de bloques scripts y estilos sin ejecutar código
cleaned = re.sub(r"<(script|style).*?>.*?</\1>", " ", html_content, flags=re.DOTALL | re.IGNORECASE)

# Conversión de etiquetas de bloque en saltos de línea legibles
cleaned = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", cleaned, flags=re.IGNORECASE)

# Decodificación de entidades HTML (&nbsp;, &aacute;, &lt;, etc.)
cleaned = html.unescape(cleaned)
```

### Detección de Discrepancia en Hipervínculos (Spoofing)
Uno de los vectores de phishing más comunes es mostrar un texto ancla legítimo (ej. `paypal.com`) mientras el atributo `href` conduce a un servidor malicioso:

$$\text{Texto Visible} \neq \text{Dominio de Destino}$$

Se implementa mediante una comparación de dominio normalizado:
```python
pattern = re.compile(r'<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
# Comprobación de que visible_domain == target_domain
```

---

## 2. Expresiones Regulares (Regex) Avanzadas

### A. Intimidación y Urgencia Psicológica
Detecta ingeniería social basada en la provocación de pánico y decisiones apresuradas:
```regex
(?i)\b(urgente|inmediatamente|cuenta suspendida|bloqueo de cuenta|acceso no autorizado|verifique su identidad|24 horas|alerta crítica|immediate action|verify your identity)\b
```
* **`(?i)`**: Ignora mayúsculas y minúsculas (*case-insensitive*).
* **`\b`**: Límite de palabra (*word boundary*), asegurando que no haya falsos positivos con palabras compuestas.

### B. Detección de Estafas de Falso Empleo (Telegram / Cripto / Pagos Previos)
```regex
(?i)\b(gana (?:\$\s*\d+|\d+\s*d[oó]lares) al d[ií]a|trabajo f[aá]cil desde casa|sin experiencia|da likes a videos|deposito de garant[ií]a|contactar por telegram|wa\.me/)\b
```
* **`(?: ... )`**: Grupos no-capturadores (*non-capturing groups*) que permiten la agrupación lógica de opciones sin alterar los resultados de `re.finditer()`.

### C. Extracción de Salario y Rangos Monetarios
Extrae montos en USD, MXN, EUR, tanto individuales como rangos:
```regex
(?i)(?:salario|sueldo|compensaci[oó]n|salary)?\s*:?\s*(?:(?:usd|\$|€|mxn)\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d+)?)\s*(?:-|a|to)\s*(?:usd|\$|€|mxn)?\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d+)?)|(?:usd|\$|€|mxn)\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d+)?))
```

---

## 3. Hashing Criptográfico y Deduplicación

### Estrategia de Lectura por Bloques (Chunked Streaming)
Calcular el hash de archivos pesados (CVs en PDF, videos o respaldos) cargando todo el contenido en memoria RAM provoca desbordamientos y caídas de servicio. Por ello, la lectura se realiza en buffers constantes:

$$\text{Buffer Size} = 65,536 \text{ bytes (64 KB)}$$

```python
md5_hasher = hashlib.md5()
sha256_hasher = hashlib.sha256()

with open(file_path, "rb") as f:
    while chunk := f.read(65536):
        md5_hasher.update(chunk)
        sha256_hasher.update(chunk)
```

### Algoritmo de Detección de Duplicados en 3 Fases
1. **Filtro Rápido por Tamaño (`stat.st_size`)**:
   - Dos archivos con tamaños en bytes distintos nunca pueden ser idénticos.
   - Complejidad: $\mathcal{O}(N)$ lecturas de metadata de directorio sin I/O en bloques de disco.
2. **Hash MD5 Preliminar**:
   - Se procesa rápidamente solo para los subconjuntos de archivos con tamaños coincidentes.
3. **Validación Criptográfica SHA-256**:
   - Confirmación final con nula probabilidad de colisión matemática.

---

## 4. Gestión de Archivos y Cuarentena (Files)

Cuando un correo supera el umbral crítico de amenaza ($\text{Score} \ge 7.0$), se extrae y neutraliza en disco:
* **Ruta de Cuarentena**: `data/quarantine/threat_<timestamp>_<sha256[:10]>.json`
* **Contenido**:
  - Metadatos completos del remitente.
  - Indicadores forenses y pesos individuales.
  - Huella criptográfica SHA-256 del cuerpo.
  - Texto sanitizado para análisis seguro.
