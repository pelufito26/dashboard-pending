import pandas as pd

# Leer el archivo generado
file_path = r"c:\Users\user\Desktop\PendingTest\Order_Detail_Completo_v10.xlsx"
df = pd.read_excel(file_path)

print("=" * 80)
print("ANALISIS DE CANDIDATOS PARA AUXILIAR ACCIONABLE")
print("=" * 80)

# Total de órdenes
print(f"\nTotal de ordenes: {len(df)}")

# CONDICION 1: Sin accionables
sin_accionables = df['Accionables'].isna() | (df['Accionables'] == '')
print(f"\n[CONDICION 1] Ordenes SIN accionables: {sin_accionables.sum()}")

# CONDICION 2: order_type = '3P'
ordenes_3p = df['order_type'].str.strip().str.upper() == '3P'
print(f"[CONDICION 2] Ordenes con order_type = '3P': {ordenes_3p.sum()}")

# CONDICION 3: Order Status + Aux (fso) = 'in_process - '
print(f"\n[CONDICION 3] Analizando 'Order Status + Aux (fso)'...")
print("\nValores unicos encontrados (primeros 20):")
valores_status = df['Order Status + Aux (fso)'].value_counts().head(20)
print(valores_status)

# Verificar si existe exactamente 'in_process - '
in_process = df['Order Status + Aux (fso)'].str.strip() == 'in_process - '
print(f"\nOrdenes con 'in_process - ': {in_process.sum()}")

# CONDICION 4: Days since in process date >= 6
print(f"\n[CONDICION 4] Analizando 'Days since in process date'...")
print(f"Estadisticas de dias:")
print(df['Days since in process date'].describe())

dias_mayor_6 = df['Days since in process date'] >= 6
print(f"\nOrdenes con Days >= 6: {dias_mayor_6.sum()}")

# COMBINANDO CONDICIONES PASO A PASO
print("\n" + "=" * 80)
print("COMBINANDO CONDICIONES")
print("=" * 80)

# Sin accionables
filtro1 = sin_accionables
print(f"Paso 1 - Sin accionables: {filtro1.sum()} ordenes")

# + order_type = '3P'
filtro2 = filtro1 & ordenes_3p
print(f"Paso 2 - + order_type='3P': {filtro2.sum()} ordenes")

# + Order Status = 'in_process - '
filtro3 = filtro2 & in_process
print(f"Paso 3 - + Order Status='in_process - ': {filtro3.sum()} ordenes")

# + Days >= 6
filtro4 = filtro3 & dias_mayor_6
print(f"Paso 4 - + Days >= 6: {filtro4.sum()} ordenes (CANDIDATOS)")

# Si hay órdenes en pasos intermedios, mostrar ejemplos
print("\n" + "=" * 80)
print("EJEMPLOS EN CADA PASO")
print("=" * 80)

if filtro1.sum() > 0:
    print(f"\n[Paso 1] Ejemplos de ordenes SIN accionables (primeras 5):")
    df_paso1 = df[filtro1][['Order Id', 'order_type', 'Order Status + Aux (fso)', 
                             'Days since in process date', 'Accionables']].head()
    print(df_paso1)

if filtro2.sum() > 0:
    print(f"\n[Paso 2] Ejemplos con order_type='3P' (primeras 5):")
    df_paso2 = df[filtro2][['Order Id', 'order_type', 'Order Status + Aux (fso)', 
                             'Days since in process date', 'Accionables']].head()
    print(df_paso2)

if filtro3.sum() > 0:
    print(f"\n[Paso 3] Ejemplos con Order Status='in_process - ' (primeras 5):")
    df_paso3 = df[filtro3][['Order Id', 'order_type', 'Order Status + Aux (fso)', 
                             'Days since in process date', 'Accionables']].head()
    print(df_paso3)

# Analizar órdenes 3P sin accionables con otros status
print("\n" + "=" * 80)
print("ORDENES 3P SIN ACCIONABLES - DISTRIBUCION POR STATUS")
print("=" * 80)

df_3p_sin_acc = df[sin_accionables & ordenes_3p]
print(f"\nTotal ordenes 3P sin accionables: {len(df_3p_sin_acc)}")
print("\nDistribucion por 'Order Status + Aux (fso)':")
print(df_3p_sin_acc['Order Status + Aux (fso)'].value_counts().head(10))

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print(f"Candidatos finales: {filtro4.sum()}")
if filtro4.sum() == 0:
    if filtro3.sum() == 0:
        print("\nRAZON: No hay ordenes 3P sin accionables con status 'in_process - '")
        print("Verifica el valor exacto del campo 'Order Status + Aux (fso)'")
    elif filtro4.sum() == 0:
        print("\nRAZON: Hay ordenes que cumplen las 3 primeras condiciones,")
        print("pero ninguna tiene 'Days since in process date' >= 6")
