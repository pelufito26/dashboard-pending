# Dashboard Accionables

Dashboard para subir el archivo Excel **"Order Detail - Pending Orders First Mile_ In Process POV (*).xlsx"** y ver estadísticas y distribución de accionables (misma lógica que `generar_accionables_completo_v8.py`, filtros 1-7, sin Google Sheet).

---

## Deploy en Vercel (recomendado)

Para dejarlo publicado y no tener que correr nada en local:

1. **Subí el proyecto a GitHub** (solo la carpeta `dashboard` o el repo que contenga `dashboard` como raíz del deploy).

2. En [vercel.com](https://vercel.com): **Add New Project** → Importá el repo.

3. **Configuración del proyecto:**
   - **Root Directory:** `dashboard` (si el repo es Report-Pending y dashboard está adentro, poné `dashboard`).
   - **Build Command** y **Output Directory:** se usan los de `vercel.json` (build del frontend → `frontend/dist`). No hace falta cambiarlos si la raíz del deploy es `dashboard`.

4. **Deploy.** Vercel va a instalar dependencias del frontend, construir la app y desplegar la API en `/api/process`. La URL quedará tipo `https://tu-proyecto.vercel.app`.

### Guardar el último archivo subido (opcional)

Para que quien entre a la web vea el último Excel procesado y pueda reemplazarlo subiendo uno nuevo:

1. En [Vercel Marketplace](https://vercel.com/marketplace) agregá **Upstash Redis** (o Redis) a tu proyecto.
2. La integración inyecta las variables de entorno. El backend usa `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN` (o `KV_REST_API_URL` / `KV_REST_API_TOKEN`).
3. Redeploy. Al subir un Excel se guarda el resultado; al entrar a la web se carga ese resultado y cualquiera puede subir otro archivo para reemplazarlo.

Si no configurás Redis, el dashboard sigue funcionando: solo no se persiste el último archivo entre visitas.

**Límite importante:** En Vercel el body de las serverless tiene un **límite de 4,5 MB**. Si el Excel es más pesado, puede fallar la subida. Para archivos muy grandes, seguí usando el script en local.

---

## Cómo correrlo en local

### 1. Backend (Python)

**Opción A – Windows (recomendado):** ejecutá el script desde la carpeta del backend:

```bat
cd dashboard\backend
run.bat
```

(O doble clic en `dashboard\backend\run.bat`.)

**Opción B – Si tenés `pip` y `uvicorn` en el PATH:**

```bash
cd dashboard/backend
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Opción C – Si solo tenés Python instalado (Windows):**

```powershell
cd dashboard\backend
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

(Si `py` no funciona, probá con `python` en lugar de `py`.)

### 2. Frontend (Node)

```bash
cd dashboard/frontend
npm install
npm run dev
```

Abrí **http://localhost:5173**. El front hace proxy de `/api` al backend en el puerto 8000.

### 3. Uso

- En la página, elegí o arrastrá el archivo Excel.
- El backend procesa el archivo con la misma lógica de accionables y devuelve estadísticas y tabla.
- El dashboard muestra: total de órdenes, órdenes con milestone válido, órdenes con accionables, gráfico de distribución y tabla filtrable.

## Estructura

- `api/process.py`: función serverless de Vercel (FastAPI), `POST /api/process` para subir Excel.
- `accionables_logic.py`: lógica de accionables (filtros 1-7), usada por la API.
- `frontend/`: Vite + React, subida de archivo, cards, gráfico (Recharts) y tabla con filtros.
- `backend/`: versión local del API (opcional), para desarrollar con `uvicorn` en tu máquina.

## Nota

El **Auxiliar Accionable** (Google Sheet) no se ejecuta en esta API. Solo se aplican los 7 filtros. Si necesitás esa columna, podés seguir usando el script `generar_accionables_completo_v8.py` y luego subir el Excel ya generado (el backend también puede aceptar un Excel que ya tenga la columna "Accionables"; si existe, la usa y recalcula estadísticas).
