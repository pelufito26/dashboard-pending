"""
Exporta un Excel con los mismos filtros que usa el dashboard:
- Lee el archivo Order Detail (47), aplica process_excel (accionables) y filtro por milestone.
- Guarda un Excel con las columnas que usa el tablero para que puedas validar
  qué se está presentando y por qué algunas órdenes no tienen comentario/accionable.
"""
import os
import sys

import pandas as pd

# Asegurar imports desde la carpeta dashboard
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from accionables_logic import process_excel

# Archivo de entrada (47) - mismo nombre que pediste
INPUT_NAME = "Order Detail - Pending Orders First Mile_ In Process POV  (47).xlsx"
OUTPUT_NAME = "Order_Detail_con_Accionables_filtros_dashboard_(47)_validar.xlsx"

# Columnas que expone el dashboard (mismo orden que en process.py)
COLUMNAS_EXPORT = [
    "Order Id",
    "order_type",
    "Order Status + Aux (fso)",
    "Logistics Milestone",
    "Accionables",
    "eta_amazon_delivery_date",
    "Scraped Eta Amazon",
    "Merchant Name",
    "last status - status_aux 17track",
    "Days since in process date",
    "Seller Country Iso",
    "Ageing Buckets (in_process_date)",
    "SLA per mile",
]

MILESTONES_PERMITIDOS = ["1.1 - First Mile: Seller", "1.2 - Already with seller_delivered_at"]


def main():
    # Buscar el (47) en el repo: mismo directorio que este script, o subir un nivel
    base = os.path.dirname(_script_dir)  # repo root
    input_path = os.path.join(base, INPUT_NAME)
    if not os.path.isfile(input_path):
        input_path = os.path.join(_script_dir, INPUT_NAME)
    if not os.path.isfile(input_path):
        print(f"No se encontró el archivo: {INPUT_NAME}")
        print(f"Buscado en: {base} y en {_script_dir}")
        sys.exit(1)

    print(f"Leyendo: {input_path}")
    df = pd.read_excel(input_path)

    print("Aplicando process_excel (misma lógica que el dashboard)...")
    df_result, stats = process_excel(df)

    print("Aplicando filtro por milestone (1.1 / 1.2)...")
    col_lm = "Logistics Milestone"
    if col_lm in df_result.columns:
        df_result = df_result[
            df_result[col_lm].astype(str).str.strip().isin(MILESTONES_PERMITIDOS)
        ].copy()

    existentes = [c for c in COLUMNAS_EXPORT if c in df_result.columns]
    out_df = df_result[existentes].copy()

    output_path = os.path.join(base, OUTPUT_NAME)
    out_df.to_excel(output_path, index=False)
    print(f"Guardado: {output_path}")
    print(f"Filas: {len(out_df)}")
    sin_comentario = (out_df["Accionables"].astype(str).str.strip() == "").sum()
    print(f"Órdenes sin comentario (Accionables vacío): {sin_comentario}")
    print(
        "Las órdenes sin comentario son las que no entran en ninguno de los filtros/reglas de accionables (fue_comprada, eta, scraped, 3P sent, días in_process, etc.)."
    )


if __name__ == "__main__":
    main()
