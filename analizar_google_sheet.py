import pandas as pd
import requests
from io import StringIO

# Configuración Google Sheet
GOOGLE_SHEET_ID = "1DhKbkkUJY2e4m_O5tWdOe0ELrerc7ODoh41ip3BvUjs"
GID = "1672015976"

print("=" * 80)
print("ANALISIS DE VALORES EN GOOGLE SHEET")
print("=" * 80)

url_export = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid={GID}"

try:
    response = requests.get(url_export, timeout=30)
    response.raise_for_status()
    df_sheet = pd.read_csv(StringIO(response.text))
    
    print(f"\n[OK] Registros en Google Sheet: {len(df_sheet)}")
    print(f"\n[OK] Columnas encontradas:")
    for i, col in enumerate(df_sheet.columns, 1):
        print(f"  {i}. '{col}'")
    
    # Buscar columna de Accionable
    columna_accionable = None
    for col in df_sheet.columns:
        if 'accionable' in col.lower() and 'auxiliar' not in col.lower():
            columna_accionable = col
            break
    
    if columna_accionable:
        print(f"\n[OK] Columna de Accionable detectada: '{columna_accionable}'")
        
        print("\n" + "=" * 80)
        print("VALORES UNICOS EN COLUMNA 'Accionable'")
        print("=" * 80)
        
        valores = df_sheet[columna_accionable].value_counts()
        print(f"\nTotal de valores unicos: {len(valores)}")
        print("\nDistribucion de valores:")
        print(valores)
        
        print("\n" + "=" * 80)
        print("BUSQUEDA DE VALORES SIMILARES A '3P InProcess'")
        print("=" * 80)
        
        # Buscar valores que contengan "3P" e "InProcess"
        df_filtrado = df_sheet[
            df_sheet[columna_accionable].str.contains('3P', case=False, na=False) &
            df_sheet[columna_accionable].str.contains('InProcess', case=False, na=False)
        ]
        
        print(f"\nRegistros con '3P' e 'InProcess' en el texto: {len(df_filtrado)}")
        
        if len(df_filtrado) > 0:
            print("\nValores encontrados:")
            print(df_filtrado[columna_accionable].value_counts())
            
            print("\n[NOTA] El valor exacto que debes buscar es uno de los anteriores")
            print("Actualmente buscamos: '3P InProcess'")
        else:
            print("\n[ADVERTENCIA] No se encontraron registros con '3P' e 'InProcess'")
            print("Verifica el contenido del Google Sheet")
        
        # Buscar solo "3P"
        print("\n" + "=" * 80)
        print("REGISTROS QUE CONTIENEN '3P'")
        print("=" * 80)
        
        df_3p = df_sheet[df_sheet[columna_accionable].str.contains('3P', case=False, na=False)]
        print(f"\nTotal: {len(df_3p)}")
        if len(df_3p) > 0:
            print("\nValores:")
            print(df_3p[columna_accionable].value_counts())
    else:
        print("\n[ERROR] No se encontro columna de Accionable")

except Exception as e:
    print(f"\n[ERROR] Al leer Google Sheet: {e}")
