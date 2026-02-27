import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import requests
from io import StringIO

"""
=== SCRIPT COMPLETO: GENERAR ACCIONABLES + AUXILIAR ACCIONABLE ===

*** CONDICIÓN GLOBAL PARA TODOS LOS FILTROS ***
Solo se aplican filtros si 'Logistics Milestone' es:
    - '1.1 - First Mile: Seller'
    - '1.2 - Already with seller_delivered_at'

FILTRO 1: Owner 2P: no tiene compra
    - OrderType: 1P/2P/1P_DIRECT
    - fue_comprada: NO TIENE COMPRA

FILTRO 2: PENDING BOT
    - OrderType: 1P/2P/1P_DIRECT
    - fue_comprada: TIENE COMPRA
    - Sin ETAs (eta_amazon_delivery_date y Scraped Eta Amazon vacíos)

FILTRO 3: Análisis de eta_amazon_delivery_date (PRIORIDAD)
    - Evalúa diferencia de días y asigna:
        * Entrega fecha futura (diferencia > 0)
        * En tiempo ocasa procese (diferencia 0 o -1)
        * Discrepancia de entrega, plazo BOT recompre (diferencia -2 a -4)
        * Recomprar 2P (diferencia < -4)

FILTRO 4: Análisis de Scraped Eta Amazon
    - Solo si eta_amazon_delivery_date está vacío
    - Misma lógica que FILTRO 3

FILTRO 5: Reasignar sent MELI
    - order_type: 3P
    - Order Status: sent -
    - 17track: InfoReceived - InfoReceived
    - Merchant: MercadoLibre/MeLiUS_Standard/MeLiUS_Fashion/MercadoLibreUY
    - Diferencia días desde sent_date > 2

FILTRO 6: Cancelar - order was not received by deposit
    - order_type: 3P
    - Order Status: sent -
    - 17track: Exception - Exception_Returned/Returning/Other/Cancel

FILTRO 7: Entrega fecha futura (por 17track)
    - order_type: 3P
    - Order Status: sent -
    - 17track: OutForDelivery - OutForDelivery_Other / InTransit - InTransit_Other/PickedUp / Exception - Exception_Delayed

AUXILIAR ACCIONABLE (desde Google Sheet):
    - Solo para órdenes SIN accionables después de los 7 filtros
    - order_type = '3P'
    - Order Status + Aux (fso) = 'in_process -'
    - Days since in process date >= 6
    - Busca el ORDER ID en el Google Sheet
    - Si encuentra coincidencia, copia el 'Estado de situación'
"""

# CONFIGURACIÓN: usa el archivo "Order Detail - Pending..." en la carpeta del script
# PREFER_FILE_NUM: si está definido (ej. 42), usa ese archivo; si no, el más reciente
PREFER_FILE_NUM = 42
import os
_script_dir = os.path.dirname(os.path.abspath(__file__))
_candidatos = [
    f for f in os.listdir(_script_dir)
    if f.startswith("Order Detail - Pending Orders First Mile_ In Process POV") and f.endswith(".xlsx")
]
if not _candidatos:
    raise FileNotFoundError(
        f'No se encontró archivo "Order Detail - Pending Orders First Mile_ In Process POV (*).xlsx" en {_script_dir}'
    )
# Preferir archivo (N) si existe; si no, el más reciente
_preferidos = [f for f in _candidatos if f"({PREFER_FILE_NUM})" in f] if PREFER_FILE_NUM else []
if _preferidos:
    _candidatos = _preferidos
else:
    _candidatos.sort(key=lambda f: os.path.getmtime(os.path.join(_script_dir, f)), reverse=True)
file_path = os.path.join(_script_dir, _candidatos[0])
# Salida: Order_Detail_Completo_(N).xlsx usando el número del archivo de entrada
_match = re.search(r"\((\d+)\)\.xlsx$", _candidatos[0])
_num = _match.group(1) if _match else "out"
_output_name = f"Order_Detail_Completo_({_num}).xlsx"
output_path = os.path.join(_script_dir, _output_name)

# Google Sheet Config
GOOGLE_SHEET_ID = "1DhKbkkUJY2e4m_O5tWdOe0ELrerc7ODoh41ip3BvUjs"
GID = "1672015976"

print("=" * 80)
print("SCRIPT COMPLETO: GENERAR ACCIONABLES + AUXILIAR ACCIONABLE")
print("=" * 80)

# Leer el archivo Excel de la carpeta
print("\n[PASO 1] Leyendo archivo Excel local...")
print(f"         Archivo: {_candidatos[0]}")
df = pd.read_excel(file_path)
print(f"[OK] Ordenes cargadas: {len(df)}")

# Fecha de hoy (dinámica)
fecha_hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
print(f"[OK] Fecha de analisis (hoy): {fecha_hoy.strftime('%d/%m/%Y')}")

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

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
            if mes < mes_actual:
                año = año_actual + 1
            else:
                año = año_actual
            
            return datetime(año, mes, dia)
        
        return None
        
    except Exception as e:
        return None

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

def generar_accionable(row):
    accionables = []
    
    # VALIDACIÓN PREVIA: Solo aplicar filtros si Logistics Milestone cumple condiciones
    if pd.notna(row['Logistics Milestone']):
        logistics_milestone = str(row['Logistics Milestone']).strip()
        milestones_permitidos = ['1.1 - First Mile: Seller', '1.2 - Already with seller_delivered_at']
        
        if logistics_milestone not in milestones_permitidos:
            return ''  # No aplicar ningún filtro si no cumple la condición
    else:
        return ''  # Si el campo está vacío, no aplicar filtros
    
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
    else:
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
        
        if order_type == '3P' and order_status == 'sent -':
            track_17 = str(row['last status - status_aux 17track']).strip() if pd.notna(row['last status - status_aux 17track']) else ''
            merchant = str(row['Merchant Name']).strip() if pd.notna(row['Merchant Name']) else ''
            
            if track_17 == 'InfoReceived - InfoReceived' and merchant in ['MercadoLibre', 'MeLiUS_Standard', 'MeLiUS_Fashion', 'MercadoLibreUY']:
                if pd.notna(row['Day of sent_date']):
                    try:
                        sent_date = pd.to_datetime(row['Day of sent_date'])
                        sent_date = sent_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        diferencia_dias = (fecha_hoy - sent_date).days
                        
                        if diferencia_dias > 2:
                            accionables.append('Reasignar sent MELI')
                    except Exception as e:
                        pass
    
    # FILTRO 6: Excepciones en 17track (order_type 3P con status sent)
    if pd.notna(row['order_type']) and pd.notna(row['Order Status + Aux (fso)']) and pd.notna(row['last status - status_aux 17track']):
        order_type = str(row['order_type']).strip().upper()
        order_status = str(row['Order Status + Aux (fso)']).strip()
        track_17 = str(row['last status - status_aux 17track']).strip()
        
        if order_type == '3P' and order_status == 'sent -':
            excepciones_cancelar = [
                'Exception - Exception_Returned',
                'Exception - Exception_Returning',
                'Exception - Exception_Other',
                'Exception - Exception_Cancel'
            ]
            
            if track_17 in excepciones_cancelar:
                accionables.append('Cancelar - order was not received by deposit')
    
    # FILTRO 7: Estados de entrega/tránsito en 17track (order_type 3P con status sent)
    if pd.notna(row['order_type']) and pd.notna(row['Order Status + Aux (fso)']) and pd.notna(row['last status - status_aux 17track']):
        order_type = str(row['order_type']).strip().upper()
        order_status = str(row['Order Status + Aux (fso)']).strip()
        track_17 = str(row['last status - status_aux 17track']).strip()
        
        if order_type == '3P' and order_status == 'sent -':
            estados_entrega_futura = [
                'OutForDelivery - OutForDelivery_Other',
                'InTransit - InTransit_Other',
                'InTransit - InTransit_PickedUp',
                'Exception - Exception_Delayed'
            ]
            
            if track_17 in estados_entrega_futura:
                accionables.append('Entrega fecha futura')
    
    return ' | '.join(accionables) if accionables else ''

# ============================================================================
# GENERAR ACCIONABLES (FILTROS 1-7)
# ============================================================================

print("\n[PASO 2] Validando Logistics Milestone...")
milestones_validos = df['Logistics Milestone'].isin(['1.1 - First Mile: Seller', '1.2 - Already with seller_delivered_at'])
ordenes_validas = milestones_validos.sum()
print(f"[OK] Ordenes con Logistics Milestone valido: {ordenes_validas}/{len(df)} ({(ordenes_validas/len(df)*100):.2f}%)")

print("\n[PASO 3] Generando columna 'Accionables' (aplicando 7 filtros)...")
df['Accionables'] = df.apply(generar_accionable, axis=1)

accionables_count = (df['Accionables'] != '').sum()
print(f"[OK] Ordenes con accionables: {accionables_count} ({(accionables_count/len(df)*100):.2f}%)")

# ============================================================================
# AGREGAR AUXILIAR ACCIONABLE (DESDE GOOGLE SHEET)
# ============================================================================

print("\n[PASO 4] Identificando ordenes para busqueda en Google Sheet...")
print("  Condiciones: Sin accionables + 3P + in_process - + Days >= 6")

mascara = (
    (df['Accionables'].isna() | (df['Accionables'] == '')) &
    (df['order_type'].str.strip().str.upper() == '3P') &
    (df['Order Status + Aux (fso)'].str.strip() == 'in_process -') &
    (df['Days since in process date'] >= 6)
)

df_candidatas = df[mascara]
print(f"[OK] Ordenes candidatas: {len(df_candidatas)}")

print("\n[PASO 5] Leyendo Google Sheet...")
url_export = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid={GID}"

try:
    response = requests.get(url_export, timeout=30)
    response.raise_for_status()
    df_sheet = pd.read_csv(StringIO(response.text))
    print(f"[OK] Registros en Google Sheet: {len(df_sheet)}")
    
    # Detectar columnas
    columna_order_id = None
    columna_estado = None
    
    for col in df_sheet.columns:
        col_lower = col.lower().strip()
        if 'order' in col_lower and 'id' in col_lower:
            columna_order_id = col
        elif 'estado' in col_lower and 'situacion' in col_lower:
            columna_estado = col
    
    print(f"   Columnas detectadas:")
    print(f"   - ORDER ID: {columna_order_id}")
    print(f"   - Estado de situacion: {columna_estado}")
    
    if not all([columna_order_id, columna_estado]):
        print("[ERROR] No se encontraron las columnas ORDER ID y/o Estado de situacion en Google Sheet")
        df['Auxiliar Accionable'] = ''
    else:
        print(f"[OK] Columnas detectadas: ORDER ID={columna_order_id}, Estado={columna_estado}")
        
        # Crear mapeo ORDER ID -> Estado de situacion (TODOS los registros del sheet)
        print(f"[OK] Creando mapeo de {len(df_sheet)} registros del Google Sheet...")
        
        mapeo = {}
        for _, row in df_sheet.iterrows():
            order_id = str(row[columna_order_id]).strip()
            estado = str(row[columna_estado]).strip() if pd.notna(row[columna_estado]) else ''
            if order_id and estado and order_id != 'nan':
                mapeo[order_id] = estado
        
        print(f"[OK] Mapeo creado: {len(mapeo)} ORDER IDs con Estado de situacion")
        
        # Crear columna vacia inicialmente
        df['Auxiliar Accionable'] = ''
        
        # SOLO agregar Auxiliar Accionable a las ordenes candidatas
        # Buscar ORDER IDs de candidatas en el mapeo del Google Sheet
        for idx in df_candidatas.index:
            order_id = str(df.at[idx, 'Order Id']).strip()
            if order_id in mapeo:
                df.at[idx, 'Auxiliar Accionable'] = mapeo[order_id]
                # Agregar '3P inProcess' en la columna Accionables para estas ordenes
                df.at[idx, 'Accionables'] = '3P inProcess'
        
        coincidencias = (df['Auxiliar Accionable'] != '').sum()
        print(f"[OK] Coincidencias encontradas: {coincidencias} (solo en ordenes candidatas)")
        print(f"[OK] Se agrego '3P inProcess' en columna Accionables para identificarlas")

except Exception as e:
    print(f"[ERROR] Al leer Google Sheet: {e}")
    print("  Se creará la columna 'Auxiliar Accionable' vacía")
    df['Auxiliar Accionable'] = ''
    coincidencias = 0

# ============================================================================
# GUARDAR ARCHIVO Y MOSTRAR ESTADÍSTICAS
# ============================================================================

print(f"\n[PASO 6] Guardando archivo completo...")
df.to_excel(output_path, index=False)
print(f"[OK] Archivo guardado: {output_path}")

# Estadísticas finales
print("\n" + "=" * 80)
print("ESTADISTICAS FINALES")
print("=" * 80)
print(f"Ordenes totales: {len(df)}")
print(f"Ordenes con Logistics Milestone valido: {ordenes_validas}")
print(f"Ordenes con accionables (filtros 1-7): {accionables_count}")
print(f"Ordenes candidatas para auxiliar: {len(df_candidatas)}")
print(f"Ordenes con Auxiliar Accionable: {coincidencias}")
print("\nDistribucion de accionables:")
if accionables_count > 0:
    all_accionables = []
    for acc in df[df['Accionables'] != '']['Accionables']:
        all_accionables.extend(acc.split(' | '))
    print(pd.Series(all_accionables).value_counts())
print("=" * 80)
