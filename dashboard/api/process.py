"""
Vercel serverless function: POST /api/process — recibe Excel y devuelve stats + tabla.
Guarda el último resultado en Redis (Upstash) para que cualquiera pueda verlo al entrar.
"""
import io
import json
import os
import sys

# Asegurar que el root del proyecto esté en el path (Vercel ejecuta desde project root)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from accionables_logic import process_excel

LAST_KEY = "dashboard:last"


def _get_redis():
    try:
        from upstash_redis.asyncio import Redis
        url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
        token = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
        if url and token:
            return Redis(url=url, token=token)
    except Exception:
        pass
    return None

app = FastAPI(title="Dashboard Accionables")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _process_file_impl(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Solo se aceptan archivos Excel (.xlsx o .xls)")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"Error al leer el Excel: {str(e)}")

    try:
        df_result, stats = process_excel(df)
    except Exception as e:
        raise HTTPException(500, f"Error al procesar accionables: {str(e)}")

    columnas_export = [
        "Order Id", "order_type", "Order Status + Aux (fso)", "Logistics Milestone",
        "Accionables", "eta_amazon_delivery_date", "Scraped Eta Amazon",
        "Merchant Name", "last status - status_aux 17track", "Days since in process date"
    ]
    existentes = [c for c in columnas_export if c in df_result.columns]
    tabla = df_result[existentes].fillna("").astype(str).to_dict(orient="records")

    return {
        "stats": stats,
        "tabla": tabla,
        "total_filas": len(df_result),
    }


@app.get("/")
@app.get("/api/process")
async def get_last():
    """Devuelve el último resultado guardado (para que quien entre lo vea). Sin Redis devuelve vacío."""
    redis = _get_redis()
    if not redis:
        return {"stats": None, "tabla": []}
    try:
        raw = await redis.get(LAST_KEY)
    except Exception:
        return {"stats": None, "tabla": []}
    if raw is None:
        return {"stats": None, "tabla": []}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"stats": None, "tabla": []}


@app.post("/")
@app.post("/api/process")
async def process_file(file: UploadFile = File(...)):
    result = await _process_file_impl(file)
    redis = _get_redis()
    if redis:
        try:
            await redis.set(LAST_KEY, json.dumps(result, ensure_ascii=False))
        except Exception:
            pass
    return result
