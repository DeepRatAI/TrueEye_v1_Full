# main.py
import os
import uuid
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
from typing import Optional, Any

# -------------------------------
# CONFIGURACIÓN DE LOGGING
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# -------------------------------
# CARGA DE SECRETS
# -------------------------------
FLOW_API_URL = os.getenv("FLOW_API_URL")
API_KEY       = os.getenv("LANGFLOW_API_KEY")
if not FLOW_API_URL:
    raise RuntimeError("❌ FLOW_API_URL no está definido. Agrégalo en los Secrets de Railway.")
if not API_KEY:
    raise RuntimeError("❌ LANGFLOW_API_KEY no está definido. Agrégalo en los Secrets de Railway.")

logger.info(f"✅ FLOW_API_URL configurado: {FLOW_API_URL[:40]}…")
logger.info(f"✅ LANGFLOW_API_KEY cargada (longitud {len(API_KEY)})")

# -------------------------------
# INICIALIZACIÓN DE LA APP
# -------------------------------
app = FastAPI(title="TrueEye Reports")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", summary="Sirve la interfaz estática")
async def serve_index():
    return FileResponse("static/index.html")

@app.get("/static/te.png", summary="Logo fallback")
async def serve_logo():
    logo_path = "static/te.png"
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    # SVG completo de fallback
    svg_content = """<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
  <circle cx="20" cy="20" r="18" fill="#f6ae2d"/>
  <g transform="translate(20,20)">
    <path d="M -12 0 Q -6 -6 0 -6 Q 6 -6 12 0 Q 6 6 0 6 Q -6 6 -12 0" fill="#420909"/>
    <circle cx="0" cy="0" r="5" fill="#f6ae2d"/>
    <circle cx="0" cy="0" r="3" fill="#420909"/>
    <circle cx="-1" cy="-1" r="1" fill="white" opacity="0.8"/>
  </g>
  <text x="20" y="35" font-family="Arial, sans-serif" font-size="8" font-weight="bold" text-anchor="middle" fill="#420909">TE</text>
</svg>"""
    return Response(svg_content, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})

# -------------------------------
# MODELOS
# -------------------------------
class AnalyzeRequest(BaseModel):
    url: str

class AnalyzeResponse(BaseModel):
    result: str
    success: bool = True
    error: Optional[str] = None

# -------------------------------
# HELPER PARA EXTRAER TEXTO
# -------------------------------
def _extract_text_from_response(data: Any) -> Optional[str]:
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ("outputs", "result", "message", "text", "content"):
            val = data.get(key)
            if isinstance(val, str):
                return val
            elif val is not None:
                nested = _extract_text_from_response(val)
                if nested:
                    return nested
        for val in data.values():
            nested = _extract_text_from_response(val)
            if nested:
                return nested
    if isinstance(data, list):
        for item in data:
            nested = _extract_text_from_response(item)
            if nested:
                return nested
    return None

# -------------------------------
# ENDPOINT /analyze
# -------------------------------
@app.post("/analyze", response_model=AnalyzeResponse, summary="Envía URL al Flow")
async def analyze(request: AnalyzeRequest):
    logger.info(f"📥 Recibida solicitud de análisis para URL: {request.url}")
    session_id = str(uuid.uuid4())
    payload = {
        "input_value":      request.url,
        "input_type":       "chat",
        "output_type":      "chat",
        "session_id":       session_id,
        "output_component": "",
        "tweaks":           None,
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent":    "TrueEye-Railway/1.0",
        "x-api-key":     API_KEY,
    }

    try:
        logger.info("📤 Enviando petición a Langflow...")
        resp = requests.post(FLOW_API_URL, json=payload, headers=headers, timeout=300)
        logger.info(f"📨 Respuesta recibida. Status: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        logger.debug(f"Respuesta JSON completa: {data!r}")

        result_text = _extract_text_from_response(data) or "⚠️ No se pudo extraer un texto claro de la respuesta."
        logger.info("✅ Análisis completado exitosamente")
        return AnalyzeResponse(result=result_text)

    except requests.exceptions.Timeout:
        logger.error("⏱️ Timeout en la petición a Langflow")
        return JSONResponse(
            {"result": "❌ Error: Timeout (el análisis tardó demasiado)", "success": False, "error": "timeout"},
            status_code=504
        )

    except requests.exceptions.HTTPError as e:
        body = e.response.text if e.response is not None else "<no body>"
        status = e.response.status_code if e.response is not None else 502
        logger.error(f"🚫 Error HTTP {status}: {body}")
        return JSONResponse(
            {"result": f"❌ Error HTTP al llamar al Flow: {body}", "success": False, "error": f"http_{status}"},
            status_code=502
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"🔌 Error de conexión o de requests: {e}")
        return JSONResponse(
            {"result": "❌ Error de conexión con el Flow", "success": False, "error": "connection"},
            status_code=502
        )

    except Exception as e:
        logger.exception("💥 Error inesperado en /analyze")
        return JSONResponse(
            {"result": f"❌ Error inesperado: {e}", "success": False, "error": "unknown"},
            status_code=500
        )

# -------------------------------
# HEALTHCHECK
# -------------------------------
@app.get("/health", summary="Estado de salud")
async def health_check():
    return {
        "status":     "healthy",
        "flow_url":   bool(FLOW_API_URL),
        "service":    "TrueEye Reports"
    }
