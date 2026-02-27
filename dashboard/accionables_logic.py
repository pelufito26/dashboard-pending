"""
Lógica de accionables reutilizable: recibe un DataFrame del Excel
y devuelve el mismo con columna 'Accionables' y estadísticas.
Misma lógica que generar_accionables_completo_v8.py (filtros 1-7, sin Google Sheet).
"""
import pandas as pd
from datetime import datetime, timedelta
import re


def parsear_scraped_eta(texto, fecha_referencia):
    if pd.isna(texto):
        return None
    texto = str(texto).strip()
    if texto in ['Information not found']:
        return 'PENDING_BOT_SPECIAL'
    if 'Order cancelled' in texto or 'Approval needed' in texto:
        return 'RECOMPRAR_2P_SPECIAL'
    if texto in ['*', '']:
        return None
    año_actual = fecha_referencia.year
    mes_actual = fecha_referencia.month
    try:
        if 'tomorrow' in texto.lower():
            return fecha_referencia + timedelta(days=1)
        dias_semana = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        for dia_nombre, dia_num in dias_semana.items():
            if dia_nombre in texto.lower():
                dias_hasta = (dia_num - fecha_referencia.weekday()) % 7
                if dias_hasta == 0:
                    dias_hasta = 7
                return fecha_referencia + timedelta(days=dias_hasta)
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
            año = año_actual + 1 if mes < mes_actual else año_actual
            return datetime(año, mes, dia)
        return None
    except Exception:
        return None


def evaluar_fecha_eta(fecha_eta, fecha_referencia):
    if fecha_eta is None:
        return None
    if fecha_eta == 'PENDING_BOT_SPECIAL':
        return 'PENDING BOT'
    if fecha_eta == 'RECOMPRAR_2P_SPECIAL':
        return 'Recomprar 2P'
    diferencia_dias = (fecha_eta - fecha_referencia).days
    if diferencia_dias > 0:
        return 'Entrega fecha futura'
    if diferencia_dias in (0, -1):
        return 'En tiempo ocasa procese'
    if -4 <= diferencia_dias <= -2:
        return 'Discrepancia de entrega, plazo BOT recompre'
    if diferencia_dias < -4:
        return 'Recomprar 2P'
    return None


def _generar_accionable_row(row, fecha_hoy):
    accionables = []
    if pd.notna(row.get('Logistics Milestone')):
        logistics_milestone = str(row['Logistics Milestone']).strip()
        if logistics_milestone not in ['1.1 - First Mile: Seller', '1.2 - Already with seller_delivered_at']:
            return ''
    else:
        return ''

    if pd.notna(row.get('order_type')) and pd.notna(row.get('fue_comprada')):
        order_type = str(row['order_type']).strip().upper()
        fue_comprada = str(row['fue_comprada']).strip().upper()
        if order_type in ['1P', '2P', '1P_DIRECT'] and fue_comprada == 'NO TIENE COMPRA':
            accionables.append('Owner 2P: no tiene compra')

    if pd.notna(row.get('order_type')) and pd.notna(row.get('fue_comprada')):
        order_type = str(row['order_type']).strip().upper()
        fue_comprada = str(row['fue_comprada']).strip().upper()
        if order_type in ['1P', '2P', '1P_DIRECT'] and fue_comprada == 'TIENE COMPRA':
            eta_amazon_vacio = pd.isna(row.get('eta_amazon_delivery_date')) or str(row.get('eta_amazon_delivery_date', '')).strip() == ''
            scraped_vacio = pd.isna(row.get('Scraped Eta Amazon')) or str(row.get('Scraped Eta Amazon', '')).strip() == ''
            if eta_amazon_vacio and scraped_vacio:
                accionables.append('PENDING BOT')

    if pd.notna(row.get('eta_amazon_delivery_date')):
        try:
            eta_date = pd.to_datetime(row['eta_amazon_delivery_date']).replace(hour=0, minute=0, second=0, microsecond=0)
            acc = evaluar_fecha_eta(eta_date, fecha_hoy)
            if acc:
                accionables.append(acc)
        except Exception:
            pass
    else:
        if pd.notna(row.get('Scraped Eta Amazon')):
            fecha_parseada = parsear_scraped_eta(row['Scraped Eta Amazon'], fecha_hoy)
            if fecha_parseada:
                acc = evaluar_fecha_eta(fecha_parseada, fecha_hoy)
                if acc:
                    accionables.append(acc)

    if pd.notna(row.get('order_type')) and pd.notna(row.get('Order Status + Aux (fso)')):
        order_type = str(row['order_type']).strip().upper()
        order_status = str(row['Order Status + Aux (fso)']).strip()
        if order_type == '3P' and order_status == 'sent -':
            track_17 = str(row.get('last status - status_aux 17track', '')).strip()
            merchant = str(row.get('Merchant Name', '')).strip()
            if track_17 == 'InfoReceived - InfoReceived' and merchant in ['MercadoLibre', 'MeLiUS_Standard', 'MeLiUS_Fashion', 'MercadoLibreUY']:
                if pd.notna(row.get('Day of sent_date')):
                    try:
                        sent_date = pd.to_datetime(row['Day of sent_date']).replace(hour=0, minute=0, second=0, microsecond=0)
                        if (fecha_hoy - sent_date).days > 2:
                            accionables.append('Reasignar sent MELI')
                    except Exception:
                        pass

    if pd.notna(row.get('order_type')) and pd.notna(row.get('Order Status + Aux (fso)')) and pd.notna(row.get('last status - status_aux 17track')):
        order_type = str(row['order_type']).strip().upper()
        order_status = str(row['Order Status + Aux (fso)']).strip()
        track_17 = str(row['last status - status_aux 17track']).strip()
        if order_type == '3P' and order_status == 'sent -':
            if track_17 in ['Exception - Exception_Returned', 'Exception - Exception_Returning', 'Exception - Exception_Other', 'Exception - Exception_Cancel']:
                accionables.append('Cancelar - order was not received by deposit')

    if pd.notna(row.get('order_type')) and pd.notna(row.get('Order Status + Aux (fso)')) and pd.notna(row.get('last status - status_aux 17track')):
        order_type = str(row['order_type']).strip().upper()
        order_status = str(row['Order Status + Aux (fso)']).strip()
        track_17 = str(row['last status - status_aux 17track']).strip()
        if order_type == '3P' and order_status == 'sent -':
            if track_17 in ['OutForDelivery - OutForDelivery_Other', 'InTransit - InTransit_Other', 'InTransit - InTransit_PickedUp', 'Exception - Exception_Delayed']:
                accionables.append('Entrega fecha futura')

    return ' | '.join(accionables) if accionables else ''


def process_excel(df, fecha_referencia=None):
    """
    Recibe un DataFrame (del Excel Order Detail - Pending...) y opcionalmente fecha_referencia.
    Devuelve (df_con_accionables, stats_dict).
    """
    if fecha_referencia is None:
        fecha_referencia = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    df = df.copy()
    milestones_permitidos = ['1.1 - First Mile: Seller', '1.2 - Already with seller_delivered_at']
    col_lm = 'Logistics Milestone'
    if col_lm not in df.columns:
        df['Accionables'] = ''
        return df, {
            'ordenes_totales': len(df),
            'ordenes_milestone_valido': 0,
            'ordenes_con_accionables': 0,
            'distribucion_accionables': {},
            'fecha_analisis': fecha_referencia.strftime('%Y-%m-%d'),
        }

    df['Accionables'] = df.apply(lambda row: _generar_accionable_row(row, fecha_referencia), axis=1)
    ordenes_validas = df[col_lm].isin(milestones_permitidos).sum()
    accionables_count = (df['Accionables'] != '').sum()

    all_accionables = []
    for acc in df.loc[df['Accionables'] != '', 'Accionables']:
        all_accionables.extend(str(acc).split(' | '))
    distribucion = pd.Series(all_accionables).value_counts().to_dict() if all_accionables else {}

    stats = {
        'ordenes_totales': len(df),
        'ordenes_milestone_valido': int(ordenes_validas),
        'ordenes_con_accionables': int(accionables_count),
        'distribucion_accionables': distribucion,
        'fecha_analisis': fecha_referencia.strftime('%Y-%m-%d'),
    }
    return df, stats
