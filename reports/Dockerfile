FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py static/ ./static/

# Exponer puerto que asignar a Railway
EXPOSE ${PORT}

# Arrancar uvicorn usando $PORT
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
