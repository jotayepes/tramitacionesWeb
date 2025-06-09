@echo off
echo Activando entorno virtual...
call env\Scripts\activate

echo Iniciando servidor FastAPI en segundo plano...
start /min cmd /k "uvicorn app.main:app --reload"

timeout /t 2 > nul