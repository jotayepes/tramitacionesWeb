@echo off
echo Activando entorno virtual...
call env\Scripts\activate

echo Iniciando servidor FastAPI en segundo plano...
start /min cmd /k "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --http h11"

timeout /t 2 > nul