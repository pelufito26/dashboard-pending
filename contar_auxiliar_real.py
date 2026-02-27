import pandas as pd
import numpy as np

# Leer el archivo generado
file_path = r"c:\Users\user\Desktop\PendingTest\Order_Detail_Completo_v10.xlsx"
df = pd.read_excel(file_path)

print("=" * 80)
print("CONTEO REAL DE AUXILIAR ACCIONABLE")
print("=" * 80)

# Contar los que realmente tienen valor (no vacío, no NaN)
con_valor = df['Auxiliar Accionable'].notna() & (df['Auxiliar Accionable'] != '') & (df['Auxiliar Accionable'] != 'nan')
print(f"\nOrdenes con Auxiliar Accionable (valor real): {con_valor.sum()}")

# Filtrar candidatas
mascara_candidatas = (
    (df['Accionables'].isna() | (df['Accionables'] == '')) &
    (df['order_type'].str.strip().str.upper() == '3P') &
    (df['Order Status + Aux (fso)'].str.strip() == 'in_process -') &
    (df['Days since in process date'] >= 6)
)

candidatas = df[mascara_candidatas]
candidatas_con_valor = candidatas[
    candidatas['Auxiliar Accionable'].notna() & 
    (candidatas['Auxiliar Accionable'] != '') & 
    (candidatas['Auxiliar Accionable'] != 'nan')
]

print(f"Ordenes candidatas totales: {len(candidatas)}")
print(f"Ordenes candidatas con Auxiliar (valor real): {len(candidatas_con_valor)}")

print("\n" + "=" * 80)
print("EJEMPLOS DE CANDIDATAS CON VALOR")
print("=" * 80)

columnas = ['Order Id', 'order_type', 'Order Status + Aux (fso)', 
            'Days since in process date', 'Auxiliar Accionable']

print(candidatas_con_valor[columnas].head(15).to_string())

print("\n" + "=" * 80)
print("VALORES UNICOS DE AUXILIAR ACCIONABLE")
print("=" * 80)

df_con_valor = df[con_valor]
print(f"\nTotal de ordenes con Auxiliar: {len(df_con_valor)}")
print("\nValores encontrados:")
print(df_con_valor['Auxiliar Accionable'].value_counts())
