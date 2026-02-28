"""
Prueba interna: verifica que los filtros 8-11 generen bien
'Seller a tiempo de enviar' y 'Orden en condiciones para reasignar'.
Ejecutar desde la raíz del proyecto (Report-Pending).
"""
import os
import sys
import re

# Usar la lógica del dashboard (filtros 1-11)
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
    print("Copiá aquí un 'Order Detail - Pending Orders First Mile_ In Process POV (*).xlsx' y volvé a ejecutar.")
    sys.exit(1)
_candidatos.sort(key=lambda f: os.path.getmtime(os.path.join(_script_dir, f)), reverse=True)
file_path = os.path.join(_script_dir, _candidatos[0])
print(f"Usando archivo: {_candidatos[0]}\n")

df = pd.read_excel(file_path)
tiene_seller_country = "Seller Country Iso" in df.columns
print(f"Columna 'Seller Country Iso' en el Excel: {'Sí' if tiene_seller_country else 'No'}")

df_result, stats = process_excel(df)
print("\n--- Estadísticas ---")
print(f"Órdenes totales: {stats['ordenes_totales']}")
print(f"Con milestone válido: {stats['ordenes_milestone_valido']}")
print(f"Con accionables: {stats['ordenes_con_accionables']}")
print("\nDistribución de accionables:")
for acc, count in sorted(stats.get("distribucion_accionables", {}).items(), key=lambda x: -x[1]):
    print(f"  {count:5d}  {acc}")

# Filtros 8-11
seller_tiempo = (df_result["Accionables"].astype(str).str.contains("Seller a tiempo de enviar", na=False)).sum()
orden_reasignar = (df_result["Accionables"].astype(str).str.contains("Orden en condiciones para reasignar", na=False)).sum()
print("\n--- Filtros 8-11 (nuevos) ---")
print(f"  'Seller a tiempo de enviar':     {seller_tiempo} órdenes")
print(f"  'Orden en condiciones para reasignar': {orden_reasignar} órdenes")

if tiene_seller_country and (seller_tiempo > 0 or orden_reasignar > 0):
    cols = ["Order Id", "order_type", "Order Status + Aux (fso)", "Days since in process date", "Seller Country Iso", "Accionables"]
    cols = [c for c in cols if c in df_result.columns]
    muestras = df_result[df_result["Accionables"].astype(str).str.contains("Seller a tiempo de enviar|Orden en condiciones para reasignar", na=False, regex=True)]
    print(f"\nMuestra de hasta 10 filas con los nuevos accionables:")
    print(muestras[cols].head(10).to_string(index=False))
elif tiene_seller_country:
    print("\nNo se generaron órdenes con los nuevos accionables. Revisá que haya filas con:")
    print("  Order Status + Aux (fso) = 'in_process -', order_type = 3P, Seller Country Iso = US o CN, y Days since in process date según el filtro.")
else:
    print("\nEl Excel no tiene columna 'Seller Country Iso'; los filtros 8-11 no aplican. Agregala al archivo fuente para probarlos.")
