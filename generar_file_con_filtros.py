"""
Genera un Excel con todos los filtros (1-11) aplicados.
Así podés abrirlo y ver qué órdenes quedan sin comentario (Accionables vacío).
"""
import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard'))
import pandas as pd
from accionables_logic import process_excel

_script_dir = os.path.dirname(os.path.abspath(__file__))
_candidatos = [
    f for f in os.listdir(_script_dir)
    if f.startswith("Order Detail - Pending Orders First Mile_ In Process POV") and f.endswith(".xlsx")
]
if not _candidatos:
    _candidatos = [f for f in os.listdir(_script_dir) if f.endswith(".xlsx")]
if not _candidatos:
    print("No hay ningún .xlsx en la carpeta del proyecto.")
    sys.exit(1)
_candidatos.sort(key=lambda f: os.path.getmtime(os.path.join(_script_dir, f)), reverse=True)
file_path = os.path.join(_script_dir, _candidatos[0])
_match = re.search(r"\((\d+)\)\.xlsx$", _candidatos[0])
_num = _match.group(1) if _match else "out"
output_name = f"Order_Detail_con_Accionables_({_num}).xlsx"
output_path = os.path.join(_script_dir, output_name)

print(f"Entrada:  {_candidatos[0]}")
print(f"Salida:   {output_name}\n")

df = pd.read_excel(file_path)
df_result, stats = process_excel(df)

# Columna auxiliar para filtrar rápido "sin comentario"
df_result["Sin comentario"] = (df_result["Accionables"].astype(str).str.strip() == "").map({True: "Sí", False: "No"})

df_result.to_excel(output_path, index=False)
print("Archivo generado:", output_path)

# Resumen: órdenes sin comentario
sin_comentario = (df_result["Accionables"].astype(str).str.strip() == "")
n_sin = sin_comentario.sum()
n_con = len(df_result) - n_sin
print(f"\n--- Resumen ---")
print(f"Total órdenes:        {len(df_result)}")
print(f"Con accionable:       {n_con}")
print(f"Sin comentario:       {n_sin}")

if n_sin > 0:
    df_sin = df_result[sin_comentario]
    print(f"\n--- Órdenes SIN comentario (por tipo/estado) ---")
    if "order_type" in df_sin.columns and "Order Status + Aux (fso)" in df_sin.columns:
        cross = pd.crosstab(df_sin["order_type"], df_sin["Order Status + Aux (fso)"])
        print(cross.to_string())
    if "Logistics Milestone" in df_sin.columns:
        print("\nPor Logistics Milestone:")
        print(df_sin["Logistics Milestone"].value_counts().head(10).to_string())
print("\nListo. Abrí el Excel y filtrá por columna 'Sin comentario' = Sí para ver las que no tienen accionable.")
