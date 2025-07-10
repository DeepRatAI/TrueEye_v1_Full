# Imagen base ligera de Python
FROM python:3.10-slim

# No buffer de salida, no escribir bytecode .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependencias primero (para cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la app y estáticos
COPY . .

# Crear un usuario no-root para seguridad
RUN useradd -m -u 1000 appuser \
 && chown -R appuser:appuser /app
USER appuser

# Railway expone $PORT, mapeamos internamente al 80
EXPOSE 80

# HEALTHCHECK: comprobar /health en localhost:80
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost/health').raise_for_status()"

# Lanzar Uvicorn apuntando a la variable $PORT (o 80 por defecto)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-80} --log-level info --access-log --workers 1"]
