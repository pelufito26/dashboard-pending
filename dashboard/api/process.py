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
# Upstash free tier: max request 10MB. Limitar filas para no superar.
MAX_TABLA_ROWS_STORED = 1500


def _get_redis():
    try:
        from upstash_redis.asyncio import Redis
        # Primero from_env (Vercel + Upstash suelen inyectar UPSTASH_REDIS_REST_URL / TOKEN)
        try:
            return Redis.from_env()
        except Exception:
            pass
        # Vercel + Upstash suelen inyectar KV_REST_API_* o KV_URL; REST API debe ser https://
        url = (
            os.environ.get("UPSTASH_REDIS_REST_URL")
            or os.environ.get("KV_REST_API_URL")
            or os.environ.get("KV_URL")
            or os.environ.get("KVREST_API_URL")
        )
        token = (
            os.environ.get("UPSTASH_REDIS_REST_TOKEN")
            or os.environ.get("KV_REST_API_TOKEN")
            or os.environ.get("KVREST_API_TOKEN")
        )
        if not url or not url.startswith("http"):
            url = None
            token = None
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
        "Merchant Name", "last status - status_aux 17track", "Days since in process date",
        "Seller Country Iso", "Ageing Buckets (in_process_date)"
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
    """Devuelve el último resultado guardado. Incluye redis_ok para diagnóstico."""
    redis = _get_redis()
    if not redis:
        return {"stats": None, "tabla": [], "redis_ok": False}
    try:
        raw = await redis.get(LAST_KEY)
    except Exception:
        return {"stats": None, "tabla": [], "redis_ok": True}
    if raw is None:
        return {"stats": None, "tabla": [], "redis_ok": True}
    try:
        out = json.loads(raw)
        out["redis_ok"] = True
        return out
    except json.JSONDecodeError:
        return {"stats": None, "tabla": [], "redis_ok": True}


@app.post("/")
@app.post("/api/process")
async def process_file(file: UploadFile = File(...)):
    result = await _process_file_impl(file)
    redis = _get_redis()
    if redis:
        # Guardar con tabla limitada para no superar 10MB (límite Upstash free)
        to_store = {
            "stats": result["stats"],
            "tabla": result["tabla"][:MAX_TABLA_ROWS_STORED],
            "total_filas": result["total_filas"],
        }
        payload = json.dumps(to_store, ensure_ascii=False)
        try:
            await redis.set(LAST_KEY, payload)
        except Exception:
            # Si falla por tamaño, intentar solo stats + 500 filas
            try:
                to_store["tabla"] = result["tabla"][:500]
                await redis.set(LAST_KEY, json.dumps(to_store, ensure_ascii=False))
            except Exception:
                pass
    return result
