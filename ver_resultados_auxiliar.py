import pandas as pd

# Leer el archivo generado
file_path = r"c:\Users\user\Desktop\PendingTest\Order_Detail_Completo_v10.xlsx"
df = pd.read_excel(file_path)

print("=" * 80)
print("RESULTADOS DEL AUXILIAR ACCIONABLE")
print("=" * 80)

# Total con Auxiliar Accionable
con_auxiliar = df[df['Auxiliar Accionable'] != '']
print(f"\nTotal ordenes con Auxiliar Accionable: {len(con_auxiliar)}")

# Filtrar candidatas originales
mascara_candidatas = (
    (df['Accionables'].isna() | (df['Accionables'] == '')) &
    (df['order_type'].str.strip().str.upper() == '3P') &
    (df['Order Status + Aux (fso)'].str.strip() == 'in_process -') &
    (df['Days since in process date'] >= 6)
)

candidatas_con_auxiliar = df[mascara_candidatas & (df['Auxiliar Accionable'] != '')]
print(f"Ordenes candidatas con Auxiliar Accionable: {len(candidatas_con_auxiliar)}")

print("\n" + "=" * 80)
print("EJEMPLOS DE CANDIDATAS CON AUXILIAR ACCIONABLE (primeras 10)")
print("=" * 80)

columnas = ['Order Id', 'order_type', 'Order Status + Aux (fso)', 
            'Days since in process date', 'Accionables', 'Auxiliar Accionable']

if len(candidatas_con_auxiliar) > 0:
    print(candidatas_con_auxiliar[columnas].head(10).to_string())
else:
    print("No se encontraron candidatas con Auxiliar Accionable")

print("\n" + "=" * 80)
print("DISTRIBUCION DE AUXILIAR ACCIONABLE")
print("=" * 80)

print("\nPor orden de status:")
print(df[df['Auxiliar Accionable'] != '']['Order Status + Aux (fso)'].value_counts().head(10))

print("\n" + "=" * 80)
print("EJEMPLOS DE OTRAS ORDENES CON AUXILIAR (no candidatas)")
print("=" * 80)

otras = df[(df['Auxiliar Accionable'] != '') & ~mascara_candidatas]
print(f"\nTotal: {len(otras)}")

if len(otras) > 0:
    print("\nPrimeros 5 ejemplos:")
    print(otras[columnas].head().to_string())
