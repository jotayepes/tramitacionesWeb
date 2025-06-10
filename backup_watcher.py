import time
import shutil
import os
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Rutas
ORIGEN_DIR = "archivos_generados"
DB_PATH = "tramita.db"
DESTINO_BASE = r""
DIAS_RETENCION = 30  # Días antes de eliminar backups antiguos

def hacer_copia():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(DESTINO_BASE, f"backup_{timestamp}")
    os.makedirs(destino, exist_ok=True)

    try:
        shutil.copy(DB_PATH, os.path.join(destino, os.path.basename(DB_PATH)))
        shutil.copytree(ORIGEN_DIR, os.path.join(destino, ORIGEN_DIR))
        print(f"[{timestamp}] Copia realizada en: {destino}")
    except Exception as e:
        print(f"[{timestamp}] Error al realizar la copia: {e}")

    eliminar_antiguos()

def eliminar_antiguos():
    ahora = datetime.now()
    for nombre in os.listdir(DESTINO_BASE):
        ruta = os.path.join(DESTINO_BASE, nombre)
        if os.path.isdir(ruta) and nombre.startswith("backup_"):
            try:
                fecha_str = nombre.split("_")[1]
                fecha_backup = datetime.strptime(fecha_str, "%Y%m%d")
                if ahora - fecha_backup > timedelta(days=DIAS_RETENCION):
                    shutil.rmtree(ruta)
                    print(f"[{datetime.now()}] Backup eliminado por antigüedad: {ruta}")
            except Exception as e:
                print(f"Error procesando {ruta}: {e}")

class CambiosDetectados(FileSystemEventHandler):
    def __init__(self):
        self.ultimo_evento = 0
        self.debounce_segundos = 30  # Solo permite una copia cada 30 segundos

    def on_modified(self, event):
        # Solo reaccionar a cambios en archivos, no directorios
        if event.is_directory:
            return
        ahora = time.time()
        if ahora - self.ultimo_evento > self.debounce_segundos:
            self.ultimo_evento = ahora
            hacer_copia()

if __name__ == "__main__":
    event_handler = CambiosDetectados()
    observer = Observer()
    observer.schedule(event_handler, path=ORIGEN_DIR, recursive=True)
    observer.start()
    print("Observando cambios en:", ORIGEN_DIR)

    try:
        while True:
            time.sleep(3)  # Menos ciclos por segundo, menos CPU
    except KeyboardInterrupt:
        observer.stop()
    observer.join()