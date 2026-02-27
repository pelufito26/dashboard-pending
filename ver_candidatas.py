import pandas as pd

# Leer el archivo generado
file_path = r"c:\Users\user\Desktop\PendingTest\Order_Detail_Completo_v10.xlsx"
df = pd.read_excel(file_path)

print("=" * 80)
print("ORDENES CANDIDATAS PARA AUXILIAR ACCIONABLE")
print("=" * 80)

# Filtrar candidatas
mascara = (
    (df['Accionables'].isna() | (df['Accionables'] == '')) &
    (df['order_type'].str.strip().str.upper() == '3P') &
    (df['Order Status + Aux (fso)'].str.strip() == 'in_process -') &
    (df['Days since in process date'] >= 6)
)

df_candidatas = df[mascara]

print(f"\nTotal de candidatas: {len(df_candidatas)}")
print("\nEstas ordenes buscaran informacion en el Google Sheet")
print("(columna 'Accionable' = '3P InProcess' y traera el 'Estado de situacion')")

print("\n" + "=" * 80)
print("EJEMPLOS DE ORDENES CANDIDATAS (primeras 20)")
print("=" * 80)

columnas_mostrar = ['Order Id', 'order_type', 'Order Status + Aux (fso)', 
                    'Days since in process date', 'Accionables', 'Auxiliar Accionable']

print(df_candidatas[columnas_mostrar].head(20).to_string())

print("\n" + "=" * 80)
print("DISTRIBUCION DE DIAS")
print("=" * 80)
print("\nDias desde in_process:")
print(df_candidatas['Days since in process date'].value_counts().sort_index())

print("\n" + "=" * 80)
print("LISTADO DE ORDER IDs CANDIDATOS")
print("=" * 80)
print("\nEstos ORDER IDs se buscaran en el Google Sheet:")
print(df_candidatas['Order Id'].tolist())
