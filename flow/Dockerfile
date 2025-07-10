# Usamos la imagen oficial de Langflow
FROM langflowai/langflow:latest

# Indicar al arranque de Langflow qué bundles cargar
ENV LANGFLOW_BUNDLE_URLS='["https://huggingface.co/spaces/DeepRat/TrueEye_Flow/raw/main/TrueEyeBeta.json"]'

# Railway inyecta el puerto en la variable $PORT
# Exponemos el puerto 80 internamente, y en el CMD mapeamos $PORT → 80
EXPOSE 80

# Healthcheck para asegurarnos de que Langflow responde en /health
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

# Arrancamos Langflow escuchando en 0.0.0.0 y en el puerto que indique $PORT (o 80 por defecto)
CMD ["sh", "-c", "langflow run --host 0.0.0.0 --port ${PORT:-80}"]
