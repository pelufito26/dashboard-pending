# Subir a GitHub y desplegar en Vercel

## Parte 1: Subir el proyecto a GitHub

Abrí una terminal en la carpeta del proyecto (o en Cursor: Terminal → New Terminal) y ejecutá estos comandos **uno por uno**.

### 1. Inicializar Git (si todavía no es un repositorio)

```bash
cd "c:\Users\user\Desktop\Materiales\Report-Pending"
git init
```

### 2. Agregar todos los archivos

```bash
git add .
```

### 3. Primer commit

```bash
git commit -m "Dashboard accionables con filtros - listo para Vercel"
```

### 4. Crear el repo en GitHub y conectar

- En GitHub.com: **New repository** (o el botón **+** → New repository).
- Nombre sugerido: `report-pending` o `dashboard-accionables`.
- **No** marques "Add a README" si ya tenés código local.
- Creá el repo (sin .gitignore ni README si ya los tenés en el proyecto).

### 5. Conectar tu carpeta local con GitHub y subir

En la terminal (reemplazá `TU_USUARIO` y `NOMBRE_REPO` por tu usuario de GitHub y el nombre del repo):

```bash
git remote add origin https://github.com/TU_USUARIO/NOMBRE_REPO.git
git branch -M main
git push -u origin main
```

Si GitHub te pide usuario y contraseña: usá tu **usuario** y un **Personal Access Token** (no la contraseña de la cuenta). Para crear un token: GitHub → Settings → Developer settings → Personal access tokens.

---

## Parte 2: Desplegar en Vercel

1. Entrá a [vercel.com](https://vercel.com) e iniciá sesión (con GitHub si querés).
2. **Add New** → **Project**.
3. **Import** el repositorio que acabás de subir (elegí `report-pending` o el nombre que hayas usado).
4. **Importante:** en *Root Directory* hacé clic en **Edit** y poné: `dashboard`.
5. Dejá **Build Command** y **Output Directory** como vienen (Vercel los toma de `dashboard/vercel.json`).
6. Clic en **Deploy**.

Cuando termine, vas a tener una URL como `https://tu-proyecto.vercel.app`. La API quedará en `https://tu-proyecto.vercel.app/api/process`.

---

## Resumen de comandos (copiar y pegar)

```bash
cd "c:\Users\user\Desktop\Materiales\Report-Pending"
git init
git add .
git commit -m "Dashboard accionables con filtros - listo para Vercel"
git remote add origin https://github.com/TU_USUARIO/NOMBRE_REPO.git
git branch -M main
git push -u origin main
```

No olvides reemplazar `TU_USUARIO` y `NOMBRE_REPO` antes de ejecutar `git remote add origin` y `git push`.
