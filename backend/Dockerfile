FROM python:3.12-slim

# Evitar escritura de .pyc y habilitar logs inmediatos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente y directorios necesarios
COPY run_service.py test_lab.py pytest.ini .env.example ./
COPY src/ ./src/
COPY data/ ./data/
COPY tests/ ./tests/

EXPOSE 8000

# Punto de entrada
CMD ["python", "run_service.py", "--serve", "--host", "0.0.0.0", "--port", "8000"]
