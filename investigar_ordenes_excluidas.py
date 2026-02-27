import pandas as pd

# Leer el archivo generado
file_path = r"c:\Users\user\Desktop\Materiales\Report_Analisis_Pending\Order_Detail_Completo_v13.xlsx"
df = pd.read_excel(file_path)

# Órdenes que el usuario menciona que deberían estar
ordenes_cuestion = [
    2877342, 2891009, 2891059, 2892295, 2892545, 2892638, 2893788, 2894146,
    2896311, 2897608, 2899001, 2899177, 2899319, 2899528, 2899591, 2899829,
    2899833, 2899946, 2900058, 2901968, 2904872, 2905576, 2905898, 2907664,
    2907712
]

print("=" * 80)
print("INVESTIGACION DE ORDENES EXCLUIDAS")
print("=" * 80)

# Filtrar estas órdenes
df_investigar = df[df['Order Id'].isin(ordenes_cuestion)]

print(f"\nÓrdenes encontradas en el archivo: {len(df_investigar)}/{len(ordenes_cuestion)}")

if len(df_investigar) == 0:
    print("\n[ERROR] No se encontraron estas órdenes en el archivo")
else:
    print("\n" + "=" * 80)
    print("DETALLES DE CADA ORDEN")
    print("=" * 80)
    
    columnas = ['Order Id', 'order_type', 'Order Status + Aux (fso)', 
                'Days since in process date', 'Accionables', 'Auxiliar Accionable',
                'Logistics Milestone']
    
    for idx, row in df_investigar.iterrows():
        print(f"\n--- ORDER ID: {row['Order Id']} ---")
        print(f"order_type: '{row['order_type']}'")
        print(f"Order Status + Aux (fso): '{row['Order Status + Aux (fso)']}' (strip: '{str(row['Order Status + Aux (fso)']).strip()}')")
        print(f"Days since in process date: {row['Days since in process date']}")
        print(f"Logistics Milestone: '{row['Logistics Milestone']}'")
        print(f"Accionables: '{row['Accionables']}'")
        print(f"Auxiliar Accionable: '{row['Auxiliar Accionable']}'")
        
        # Evaluar condiciones
        print("\nEvaluación de condiciones:")
        
        # Condición 1: Sin accionables
        sin_accionables = pd.isna(row['Accionables']) or row['Accionables'] == ''
        print(f"  1. Sin accionables: {sin_accionables}")
        
        # Condición 2: order_type = '3P'
        es_3p = str(row['order_type']).strip().upper() == '3P'
        print(f"  2. order_type = '3P': {es_3p}")
        
        # Condición 3: Order Status = 'in_process -'
        status_correcto = str(row['Order Status + Aux (fso)']).strip() == 'in_process -'
        print(f"  3. Order Status = 'in_process -': {status_correcto}")
        
        # Condición 4: Days >= 6
        dias_suficientes = row['Days since in process date'] >= 6
        print(f"  4. Days >= 6: {dias_suficientes}")
        
        # Condición 5: Logistics Milestone válido
        milestone_valido = row['Logistics Milestone'] in ['1.1 - First Mile: Seller', '1.2 - Already with seller_delivered_at']
        print(f"  5. Logistics Milestone válido: {milestone_valido}")
        
        # Resultado
        cumple_todas = sin_accionables and es_3p and status_correcto and dias_suficientes and milestone_valido
        print(f"\n  CUMPLE TODAS LAS CONDICIONES: {cumple_todas}")
        
        if not cumple_todas:
            print("  RAZÓN DE EXCLUSIÓN:")
            if not sin_accionables:
                print(f"    - YA TIENE ACCIONABLE: '{row['Accionables']}'")
            if not es_3p:
                print(f"    - NO ES 3P: '{row['order_type']}'")
            if not status_correcto:
                print(f"    - STATUS INCORRECTO: '{str(row['Order Status + Aux (fso)']).strip()}'")
            if not dias_suficientes:
                print(f"    - DÍAS INSUFICIENTES: {row['Days since in process date']} < 6")
            if not milestone_valido:
                print(f"    - MILESTONE INVÁLIDO: '{row['Logistics Milestone']}'")

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE EXCLUSIONES")
    print("=" * 80)
    
    # Contar razones
    sin_accionables_count = 0
    con_accionables_count = 0
    no_3p_count = 0
    status_incorrecto_count = 0
    dias_insuficientes_count = 0
    milestone_invalido_count = 0
    
    for idx, row in df_investigar.iterrows():
        sin_accionables = pd.isna(row['Accionables']) or row['Accionables'] == ''
        es_3p = str(row['order_type']).strip().upper() == '3P'
        status_correcto = str(row['Order Status + Aux (fso)']).strip() == 'in_process -'
        dias_suficientes = row['Days since in process date'] >= 6
        milestone_valido = row['Logistics Milestone'] in ['1.1 - First Mile: Seller', '1.2 - Already with seller_delivered_at']
        
        if sin_accionables:
            sin_accionables_count += 1
        else:
            con_accionables_count += 1
            
        if not es_3p:
            no_3p_count += 1
        if not status_correcto:
            status_incorrecto_count += 1
        if not dias_suficientes:
            dias_insuficientes_count += 1
        if not milestone_valido:
            milestone_invalido_count += 1
    
    print(f"\nÓrdenes con accionables (ya tienen): {con_accionables_count}")
    print(f"Órdenes sin accionables: {sin_accionables_count}")
    print(f"Órdenes que NO son 3P: {no_3p_count}")
    print(f"Órdenes con status incorrecto: {status_incorrecto_count}")
    print(f"Órdenes con días < 6: {dias_insuficientes_count}")
    print(f"Órdenes con milestone inválido: {milestone_invalido_count}")

# Verificar si alguna no está en el archivo
ordenes_no_encontradas = [o for o in ordenes_cuestion if o not in df['Order Id'].values]
if ordenes_no_encontradas:
    print("\n" + "=" * 80)
    print("ÓRDENES NO ENCONTRADAS EN EL ARCHIVO")
    print("=" * 80)
    print(ordenes_no_encontradas)
