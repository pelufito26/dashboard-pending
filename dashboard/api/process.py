"""
Vercel serverless function: POST /api/process — recibe Excel y devuelve stats + tabla.
"""
import io
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

app = FastAPI(title="Dashboard Accionables")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/")
async def process_file(file: UploadFile = File(...)):
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
