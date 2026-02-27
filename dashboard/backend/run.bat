@echo off
cd /d "%~dp0"
echo Instalando dependencias...
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo Probando con 'python' en lugar de 'py'...
    python -m pip install -r requirements.txt
)
echo.
echo Iniciando servidor en http://127.0.0.1:8000
py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
if errorlevel 1 (
    python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
)
pause
