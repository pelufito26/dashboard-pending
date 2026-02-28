# Sistema de Filtros y Accionables - Documentación

## 📋 Descripción General

Sistema completo para analizar órdenes pendientes y generar accionables automáticos basados en múltiples criterios logísticos.

---

## 🎯 Filtros Implementados

### ⚠️ **CONDICIÓN GLOBAL**
**Todos los filtros se aplican SOLO si `Logistics Milestone` es:**
- `'1.1 - First Mile: Seller'`
- `'1.2 - Already with seller_delivered_at'`

---

### **FILTRO 1: Owner 2P: no tiene compra**
**Condiciones:**
- `order_type`: 1P / 2P / 1P_DIRECT
- `fue_comprada`: NO TIENE COMPRA

**Accionable:** `"Owner 2P: no tiene compra"`

---

### **FILTRO 2: PENDING BOT**
**Condiciones:**
- `order_type`: 1P / 2P / 1P_DIRECT
- `fue_comprada`: TIENE COMPRA
- `eta_amazon_delivery_date`: Vacío
- `Scraped Eta Amazon`: Vacío

**Accionable:** `"PENDING BOT"`

---

### **FILTRO 3: Análisis de eta_amazon_delivery_date** ⭐ (PRIORIDAD)
**Condiciones:**
- `eta_amazon_delivery_date` tiene valor

**Lógica de evaluación:**
| Diferencia días | Accionable |
|-----------------|------------|
| > 0 | `Entrega fecha futura` |
| 0 o -1 | `En tiempo ocasa procese` |
| -2 a -4 | `Discrepancia de entrega, plazo BOT recompre` |
| < -4 | `Recomprar 2P` |

---

### **FILTRO 4: Análisis de Scraped Eta Amazon**
**Condiciones:**
- `eta_amazon_delivery_date`: Vacío (solo se aplica si el filtro 3 no aplica)
- `Scraped Eta Amazon`: Tiene valor

**Lógica:** Misma evaluación que FILTRO 3

**Casos especiales:**
- `"Information not found"` → `PENDING BOT`
- `"Order cancelled"` / `"Approval needed"` → `Recomprar 2P`

---

### **FILTRO 5: Reasignar sent MELI**
**Condiciones:**
- `order_type`: 3P
- `Order Status + Aux (fso)`: sent -
- `last status - status_aux 17track`: InfoReceived - InfoReceived
- `Merchant Name`: MercadoLibre / MeLiUS_Standard / MeLiUS_Fashion / MercadoLibreUY
- `Days since sent_date` > 2

**Accionable:** `"Reasignar sent MELI"`

---

### **FILTRO 6: Cancelar - order was not received by deposit**
**Condiciones:**
- `order_type`: 3P
- `Order Status + Aux (fso)`: sent -
- `last status - status_aux 17track` es uno de:
  - `Exception - Exception_Returned`
  - `Exception - Exception_Returning`
  - `Exception - Exception_Other`
  - `Exception - Exception_Cancel`

**Accionable:** `"Cancelar - order was not received by deposit"`

---

### **FILTRO 7: Entrega fecha futura (por 17track)**
**Condiciones:**
- `order_type`: 3P
- `Order Status + Aux (fso)`: sent -
- `last status - status_aux 17track` es uno de:
  - `OutForDelivery - OutForDelivery_Other`
  - `InTransit - InTransit_Other`
  - `InTransit - InTransit_PickedUp`
  - `Exception - Exception_Delayed`

**Accionable:** `"Entrega fecha futura"`

---

### **FILTRO 8: Seller a tiempo de enviar (US)**
**Condiciones:**
- `Order Status + Aux (fso)`: in_process -
- `order_type`: 3P
- `Days since in process date` **< 6**
- `Seller Country Iso`: US

**Accionable:** `"Seller a tiempo de enviar"`

---

### **FILTRO 9: Seller a tiempo de enviar (CN)**
**Condiciones:**
- `Order Status + Aux (fso)`: in_process -
- `order_type`: 3P
- `Days since in process date` **< 4**
- `Seller Country Iso`: CN

**Accionable:** `"Seller a tiempo de enviar"`

---

### **FILTRO 10: Orden en condiciones para reasignar (US)**
**Condiciones:**
- `Order Status + Aux (fso)`: in_process -
- `order_type`: 3P
- `Days since in process date` **> 5**
- `Seller Country Iso`: US

**Accionable:** `"Orden en condiciones para reasignar"`

---

### **FILTRO 11: Orden en condiciones para reasignar (CN)**
**Condiciones:**
- `Order Status + Aux (fso)`: in_process -
- `order_type`: 3P
- `Days since in process date` **>= 4**
- `Seller Country Iso`: CN

**Accionable:** `"Orden en condiciones para reasignar"`

---

## 🔍 Auxiliar Accionable (Google Sheet)

### **¿Cuándo se aplica?**
Solo para órdenes que cumplen **TODAS** estas condiciones:

1. **NO tienen accionables** (después de aplicar filtros 1-7)
2. `order_type` = '3P'
3. `Order Status + Aux (fso)` = 'in_process - '
4. `Days since in process date` >= 6 días

### **Proceso:**
1. Busca el `ORDER ID` en el Google Sheet
2. Filtra registros donde `Accionable = "3P InProcess"`
3. Si encuentra coincidencia, copia el comentario de la columna L (`Estado de situación`)
4. Lo agrega en la nueva columna `Auxiliar Accionable`

### **Google Sheet URL:**
```
https://docs.google.com/spreadsheets/d/1DhKbkkUJY2e4m_O5tWdOe0ELrerc7ODoh41ip3BvUjs/edit?gid=1672015976
```

---

## 🚀 Scripts Disponibles

### **1. generar_accionables_v7.py**
- Solo genera accionables (filtros 1-7)
- No incluye Auxiliar Accionable

### **2. agregar_auxiliar_accionable.py**
- Solo agrega columna "Auxiliar Accionable"
- Requiere archivo con accionables ya generados

### **3. generar_accionables_completo_v8.py** ⭐ **RECOMENDADO**
- Proceso completo en un solo script:
  - Genera accionables (filtros 1-7)
  - Agrega Auxiliar Accionable desde Google Sheet
  - Muestra estadísticas completas

---

## 📊 Uso del Script Completo

### **Requisitos:**
```bash
pip install pandas openpyxl requests
```

### **Configuración:**
Edita las rutas en el script:
```python
file_path = r"c:\Users\user\Desktop\PendingTest\Order Detail - Pending Orders First Mile_ In Process POV  (34).xlsx"
output_path = r"c:\Users\user\Desktop\PendingTest\Order_Detail_Completo_v10.xlsx"
```

### **Ejecutar:**
```bash
python generar_accionables_completo_v8.py
```

### **Output:**
Archivo Excel con dos nuevas columnas:
- **`Accionables`**: Resultados de filtros 1-7
- **`Auxiliar Accionable`**: Comentarios del Google Sheet

---

## 📈 Estadísticas que genera

```
✓ Órdenes totales procesadas
✓ Órdenes con Logistics Milestone válido
✓ Órdenes con accionables (filtros 1-7)
✓ Órdenes candidatas para auxiliar
✓ Coincidencias encontradas en Google Sheet
✓ Distribución de accionables por tipo
```

---

## 🔒 Permisos del Google Sheet

**Importante:** El Google Sheet debe tener permisos de lectura:
- **Opción 1:** Público (cualquiera con el enlace)
- **Opción 2:** Compartido con tu cuenta

Si es privado, considera usar el navegador automatizado (MCP Browser).

---

## ⚙️ Estructura de columnas esperadas

### **Archivo Local (Excel):**
- Order Id
- order_type
- fue_comprada
- eta_amazon_delivery_date
- Scraped Eta Amazon
- Order Status + Aux (fso)
- last status - status_aux 17track
- Merchant Name
- Day of sent_date
- Days since in process date
- Logistics Milestone

### **Google Sheet:**
- **Columna A:** ORDER ID
- **Columna con "Accionable":** Debe contener "3P InProcess"
- **Columna L:** Estado de situación

---

## 📝 Notas Importantes

1. **Prioridad de ETAs:** El script prioriza `eta_amazon_delivery_date` sobre `Scraped Eta Amazon`
2. **Accionables múltiples:** Una orden puede tener varios accionables separados por ` | `
3. **Fecha dinámica:** El script usa la fecha actual del sistema para cálculos
4. **Logistics Milestone:** Es una condición bloqueante para todos los filtros

---

## 🐛 Troubleshooting

### **Error al leer Google Sheet:**
- Verifica permisos del archivo
- Verifica que la URL y GID sean correctos
- Chequea conexión a internet

### **No encuentra columnas:**
- Verifica nombres de columnas en el Google Sheet
- El script busca por palabras clave (order, id, accionable, estado)

### **Sin coincidencias en Auxiliar Accionable:**
- Verifica que existan órdenes candidatas
- Verifica que el Google Sheet tenga registros con "3P InProcess"
- Verifica que los ORDER IDs coincidan exactamente

---

## 📧 Contacto

Para dudas o mejoras, contacta al equipo de desarrollo.

**Última actualización:** Febrero 2026
