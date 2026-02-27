import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

# Leer el archivo Excel (21)
file_path = r"c:\Users\user\Desktop\PendingTest\Order Detail - Pending Orders First Mile_ In Process POV  (21).xlsx"

print("Leyendo archivo Excel (21)...")
df = pd.read_excel(file_path)

# Fecha de hoy (dinámica)
fecha_hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
print(f"\nFecha de analisis (hoy): {fecha_hoy.strftime('%d/%m/%Y')}")

# Función para parsear texto de Scraped Eta Amazon
def parsear_scraped_eta(texto, fecha_referencia):
    """
    Parsea el texto de Scraped Eta Amazon y retorna una fecha datetime.
    Retorna None si no puede parsear o si es un texto inválido.
    """
    if pd.isna(texto):
        return None
    
    texto = str(texto).strip()
    
    # Casos especiales que se manejan fuera (retornar strings especiales)
    if texto in ['Information not found']:
        return 'PENDING_BOT_SPECIAL'
    
    if 'Order cancelled' in texto or 'Approval needed' in texto:
        return 'RECOMPRAR_2P_SPECIAL'
    
    # Ignorar otros casos especiales
    if texto in ['*', '']:
        return None
    
    # Extraer el año de referencia
    año_actual = fecha_referencia.year
    mes_actual = fecha_referencia.month
    
    try:
        # Casos: "Arriving tomorrow" o "Arriving by tomorrow"
        if 'tomorrow' in texto.lower():
            return fecha_referencia + timedelta(days=1)
        
        # Casos: "Arriving Saturday", "Now arriving Monday", etc.
        dias_semana = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for dia_nombre, dia_num in dias_semana.items():
            if dia_nombre in texto.lower():
                # Calcular el próximo día de la semana
                dias_hasta = (dia_num - fecha_referencia.weekday()) % 7
                if dias_hasta == 0:  # Si es el mismo día, tomar la próxima semana
                    dias_hasta = 7
                return fecha_referencia + timedelta(days=dias_hasta)
        
        # Casos: "Arriving by December 19", "Now arriving January 2"
        # Extraer mes y día usando regex
        patron_fecha = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})'
        match = re.search(patron_fecha, texto)
        
        if match:
            mes_nombre = match.group(1)
            dia = int(match.group(2))
            
            meses = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                'September': 9, 'October': 10, 'November': 11, 'December': 12
            }
            
            mes = meses[mes_nombre]
            
            # Determinar el año correcto
            # Si el mes es menor que el mes actual, probablemente es año siguiente
            if mes < mes_actual:
                año = año_actual + 1
            else:
                año = año_actual
            
            return datetime(año, mes, dia)
        
        # Si no se pudo parsear, retornar None
        return None
        
    except Exception as e:
        return None

# Función para evaluar diferencia de días y asignar accionable
def evaluar_fecha_eta(fecha_eta, fecha_referencia):
    """
    Evalúa la diferencia entre la fecha ETA y la fecha de referencia,
    y retorna el accionable correspondiente.
    """
    if fecha_eta is None:
        return None
    
    # Manejar casos especiales
    if fecha_eta == 'PENDING_BOT_SPECIAL':
        return 'PENDING BOT'
    
    if fecha_eta == 'RECOMPRAR_2P_SPECIAL':
        return 'Recomprar 2P'
    
    diferencia_dias = (fecha_eta - fecha_referencia).days
    
    if diferencia_dias > 0:
        return 'Entrega fecha futura'
    elif diferencia_dias == 0 or diferencia_dias == -1:
        return 'En tiempo ocasa procese'
    elif diferencia_dias >= -4 and diferencia_dias <= -2:
        return 'Discrepancia de entrega, plazo BOT recompre'
    elif diferencia_dias < -4:
        return 'Recomprar 2P'
    
    return None

# Crear la columna de Accionables
def generar_accionable(row):
    accionables = []
    
    # FILTRO 1: OrderType 1P/2P sin compra
    if pd.notna(row['order_type']) and pd.notna(row['fue_comprada']):
        order_type = str(row['order_type']).strip().upper()
        fue_comprada = str(row['fue_comprada']).strip().upper()
        
        if order_type in ['1P', '2P', '1P_DIRECT'] and fue_comprada == 'NO TIENE COMPRA':
            accionables.append('Owner 2P: no tiene compra')
    
    # FILTRO 2: OrderType 1P/2P con compra pero sin ETAs
    if pd.notna(row['order_type']) and pd.notna(row['fue_comprada']):
        order_type = str(row['order_type']).strip().upper()
        fue_comprada = str(row['fue_comprada']).strip().upper()
        
        if order_type in ['1P', '2P', '1P_DIRECT'] and fue_comprada == 'TIENE COMPRA':
            eta_amazon_vacio = pd.isna(row['eta_amazon_delivery_date']) or str(row['eta_amazon_delivery_date']).strip() == ''
            scraped_vacio = pd.isna(row['Scraped Eta Amazon']) or str(row['Scraped Eta Amazon']).strip() == ''
            
            if eta_amazon_vacio and scraped_vacio:
                accionables.append('PENDING BOT')
    
    # FILTRO 3: Análisis de eta_amazon_delivery_date cuando tiene valor (PRIORIDAD)
    if pd.notna(row['eta_amazon_delivery_date']):
        try:
            eta_date = pd.to_datetime(row['eta_amazon_delivery_date'])
            eta_date = eta_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            accionable = evaluar_fecha_eta(eta_date, fecha_hoy)
            if accionable:
                accionables.append(accionable)
        except Exception as e:
            pass
    
    # FILTRO 4: Análisis de Scraped Eta Amazon SOLO si eta_amazon_delivery_date está vacío
    else:  # eta_amazon_delivery_date está vacío
        if pd.notna(row['Scraped Eta Amazon']):
            fecha_parseada = parsear_scraped_eta(row['Scraped Eta Amazon'], fecha_hoy)
            if fecha_parseada:
                accionable = evaluar_fecha_eta(fecha_parseada, fecha_hoy)
                if accionable:
                    accionables.append(accionable)
    
    # FILTRO 5: Reasignar sent MELI
    if pd.notna(row['order_type']) and pd.notna(row['Order Status + Aux (fso)']):
        order_type = str(row['order_type']).strip().upper()
        order_status = str(row['Order Status + Aux (fso)']).strip()
        
        # Verificar condiciones
        if order_type == '3P' and order_status == 'sent -':
            # Verificar 17track
            track_17 = str(row['last status - status_aux 17track']).strip() if pd.notna(row['last status - status_aux 17track']) else ''
            
            # Verificar Merchant
            merchant = str(row['Merchant Name']).strip() if pd.notna(row['Merchant Name']) else ''
            
            if track_17 == 'InfoReceived - InfoReceived' and merchant in ['MercadoLibre', 'MeLiUS_Standard', 'MeLiUS_Fashion', 'MercadoLibreUY']:
                # Verificar fecha de sent_date
                if pd.notna(row['Day of sent_date']):
                    try:
                        sent_date = pd.to_datetime(row['Day of sent_date'])
                        sent_date = sent_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        diferencia_dias = (fecha_hoy - sent_date).days
                        
                        if diferencia_dias > 2:
                            accionables.append('Reasignar sent MELI')
                    except Exception as e:
                        pass
    
    # Si no hay accionables, retornar vacío
    return ' | '.join(accionables) if accionables else ''

# Aplicar la función a cada fila
print("\nGenerando columna de Accionables...")
df['Accionables'] = df.apply(generar_accionable, axis=1)

# Mostrar estadísticas
print("\n=== ESTADISTICAS DE ACCIONABLES ===")
accionables_count = (df['Accionables'] != '').sum()
print(f"Total de ordenes con accionables: {accionables_count}")
print(f"Porcentaje: {(accionables_count/len(df)*100):.2f}%")

print("\n=== DISTRIBUCION DE ACCIONABLES ===")
if accionables_count > 0:
    all_accionables = []
    for acc in df[df['Accionables'] != '']['Accionables']:
        all_accionables.extend(acc.split(' | '))
    
    accionables_series = pd.Series(all_accionables)
    print(accionables_series.value_counts())

# Mostrar ejemplos específicos de Reasignar sent MELI
print("\n=== EJEMPLOS DE 'Reasignar sent MELI' ===")
df_meli = df[df['Accionables'].str.contains('Reasignar sent MELI', na=False)]
print(f"Total: {len(df_meli)}")

if len(df_meli) > 0:
    print("\nEjemplos (primeras 10):")
    print(df_meli[['Order Id', 'order_type', 'Order Status + Aux (fso)', 
                    'last status - status_aux 17track', 'Merchant Name', 
                    'Day of sent_date', 'Accionables']].head(10))

# Guardar el archivo con la nueva columna
output_path = r"c:\Users\user\Desktop\PendingTest\Order_Detail_con_Accionables_v6.xlsx"
print(f"\n\nGuardando archivo con accionables en: {output_path}")
df.to_excel(output_path, index=False)
print("Archivo guardado exitosamente!")

# Resumen detallado
print("\n=== RESUMEN DETALLADO ===")
print(f"Ordenes procesadas: {len(df)}")
print(f"Ordenes con accionables: {accionables_count} ({(accionables_count/len(df)*100):.2f}%)")
print(f"Ordenes 'Reasignar sent MELI': {len(df_meli)}")

