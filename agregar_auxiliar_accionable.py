import pandas as pd
import requests
from io import StringIO

"""
Script para agregar la columna 'Auxiliar Accionable' desde Google Sheet

CONDICIONES PARA BUSCAR EN GOOGLE SHEET:
- Órdenes SIN accionables (después de aplicar los 7 filtros)
- order_type = '3P'
- Order Status + Aux (fso) = 'in_process -'
- Days since in process date >= 6

PROCESO:
1. Leer archivo local con accionables ya generados
2. Identificar órdenes que cumplen condiciones
3. Leer Google Sheet
4. Crear mapeo ORDER ID → Estado de situacion
5. Buscar coincidencias de ORDER IDs candidatos en el Google Sheet
6. Agregar columna "Auxiliar Accionable" al archivo local
"""

# Configuración
ARCHIVO_LOCAL = r"c:\Users\user\Desktop\PendingTest\Order_Detail_con_Accionables_v9.xlsx"
GOOGLE_SHEET_ID = "1DhKbkkUJY2e4m_O5tWdOe0ELrerc7ODoh41ip3BvUjs"
GID = "1672015976"  # ID de la pestaña específica
OUTPUT_FILE = r"c:\Users\user\Desktop\PendingTest\Order_Detail_con_Auxiliar_v10.xlsx"

print("=" * 70)
print("SCRIPT: Agregar Auxiliar Accionable desde Google Sheet")
print("=" * 70)

# PASO 1: Leer archivo local
print("\n[1/6] Leyendo archivo local con accionables...")
df_local = pd.read_excel(ARCHIVO_LOCAL)
print(f"   ✓ Órdenes totales: {len(df_local)}")

# PASO 2: Identificar órdenes candidatas
print("\n[2/6] Identificando órdenes candidatas para búsqueda en Google Sheet...")
print("   Condiciones:")
print("   - Sin accionables (columna 'Accionables' vacía)")
print("   - order_type = '3P'")
print("   - Order Status + Aux (fso) = 'in_process - '")
print("   - Days since in process date >= 6")

# Filtrar órdenes candidatas
mascara = (
    (df_local['Accionables'].isna() | (df_local['Accionables'] == '')) &
    (df_local['order_type'].str.strip().str.upper() == '3P') &
    (df_local['Order Status + Aux (fso)'].str.strip() == 'in_process -') &
    (df_local['Days since in process date'] >= 6)
)

df_candidatas = df_local[mascara]
print(f"   ✓ Órdenes candidatas encontradas: {len(df_candidatas)}")

if len(df_candidatas) > 0:
    print(f"\n   Ejemplos de órdenes candidatas (primeras 5):")
    print(df_candidatas[['Order Id', 'order_type', 'Order Status + Aux (fso)', 
                         'Days since in process date', 'Accionables']].head())

# PASO 3: Leer Google Sheet
print("\n[3/6] Leyendo Google Sheet...")
url_export = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid={GID}"

try:
    response = requests.get(url_export, timeout=30)
    response.raise_for_status()
    
    # Leer CSV desde el contenido
    df_sheet = pd.read_csv(StringIO(response.text))
    print(f"   ✓ Registros en Google Sheet: {len(df_sheet)}")
    print(f"   ✓ Columnas encontradas: {list(df_sheet.columns)}")
    
except Exception as e:
    print(f"   ✗ Error al leer Google Sheet: {e}")
    print("\n   NOTA: El archivo debe tener permisos de lectura pública o 'cualquiera con el enlace'")
    print("   Si el archivo es privado, considera usar la opción de navegador automatizado.")
    exit(1)

# PASO 4: Crear mapeo de TODOS los registros del Google Sheet
print("\n[4/6] Procesando registros del Google Sheet...")

# Verificar que existan las columnas necesarias
columna_order_id = None
columna_estado = None

# Buscar columnas (pueden tener nombres ligeramente diferentes)
for col in df_sheet.columns:
    col_lower = col.lower().strip()
    if 'order' in col_lower and 'id' in col_lower:
        columna_order_id = col
    elif 'estado' in col_lower and 'situacion' in col_lower:
        columna_estado = col

print(f"   Columnas detectadas:")
print(f"   - ORDER ID: {columna_order_id}")
print(f"   - Estado de situación: {columna_estado}")

if not all([columna_order_id, columna_estado]):
    print("\n   ✗ Error: No se encontraron las columnas ORDER ID y/o Estado de situacion")
    print("   Por favor verifica los nombres de las columnas en el Google Sheet")
    exit(1)

# PASO 5: Crear mapeo ORDER ID → Estado de situación
print("\n[5/6] Creando mapeo ORDER ID → Estado de situación...")
mapeo = {}

for _, row in df_sheet.iterrows():
    order_id = str(row[columna_order_id]).strip()
    estado = str(row[columna_estado]).strip() if pd.notna(row[columna_estado]) else ''
    
    if order_id and estado and order_id != 'nan':
        mapeo[order_id] = estado

print(f"   ✓ Mapeo creado: {len(mapeo)} registros")

if len(mapeo) > 0:
    print(f"\n   Ejemplos del mapeo (primeros 5):")
    for i, (order_id, estado) in enumerate(list(mapeo.items())[:5]):
        print(f"   {i+1}. {order_id} → {estado[:50]}...")

# PASO 6: Agregar columna "Auxiliar Accionable" al DataFrame local
print("\n[6/6] Agregando columna 'Auxiliar Accionable'...")

# Crear columna vacia inicialmente
df_local['Auxiliar Accionable'] = ''

# SOLO agregar Auxiliar Accionable a las ordenes candidatas
for idx in df_candidatas.index:
    order_id = str(df_local.at[idx, 'Order Id']).strip()
    if order_id in mapeo:
        df_local.at[idx, 'Auxiliar Accionable'] = mapeo[order_id]
        # Agregar '3P inProcess' en la columna Accionables para estas ordenes
        df_local.at[idx, 'Accionables'] = '3P inProcess'

# Contar coincidencias
coincidencias = (df_local['Auxiliar Accionable'] != '').sum()
print(f"   ✓ Coincidencias encontradas: {coincidencias} (solo en ordenes candidatas)")
print(f"   ✓ Se agrego '3P inProcess' en columna Accionables para identificarlas")

# Mostrar ejemplos
if coincidencias > 0:
    print(f"\n   Ejemplos de órdenes con Auxiliar Accionable (primeras 5):")
    df_con_auxiliar = df_local[df_local['Auxiliar Accionable'] != '']
    print(df_con_auxiliar[['Order Id', 'order_type', 'Order Status + Aux (fso)', 
                           'Days since in process date', 'Accionables', 
                           'Auxiliar Accionable']].head())

# PASO 7: Guardar archivo
print(f"\n[7/7] Guardando archivo con columna 'Auxiliar Accionable'...")
print(f"   Ruta: {OUTPUT_FILE}")
df_local.to_excel(OUTPUT_FILE, index=False)
print("   ✓ Archivo guardado exitosamente!")

# RESUMEN FINAL
print("\n" + "=" * 70)
print("RESUMEN FINAL")
print("=" * 70)
print(f"Órdenes totales procesadas: {len(df_local)}")
print(f"Órdenes candidatas (sin accionables + condiciones): {len(df_candidatas)}")
print(f"Registros en Google Sheet con '3P InProcess': {len(df_sheet_filtered)}")
print(f"Coincidencias encontradas: {coincidencias}")
print(f"Porcentaje de candidatas con auxiliar: {(coincidencias/len(df_candidatas)*100):.2f}%" if len(df_candidatas) > 0 else "N/A")
print("=" * 70)
