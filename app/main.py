from fastapi import FastAPI, Depends, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.database import SessionLocal, engine, Base
from app.excel_utils import generar_excel
from typing import Optional
from datetime import datetime
import glob
import re
import os
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi import Depends
from . import crud, database
from datetime import datetime
from collections import OrderedDict

templates = Jinja2Templates(directory="app/templates")

# Crear las tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tramitador de Productos Defectuosos")

# Servir archivos estáticos (imágenes de tramitaciones)
app.mount("/archivos_generados", StaticFiles(directory="archivos_generados"), name="archivos_generados")

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Ruta principal (opcional: puedes dejarla para test)
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Mostrar el formulario para crear una nueva tramitación
@app.get("/nueva-tramitacion")
def mostrar_formulario(request: Request):
    return templates.TemplateResponse("nueva_tramitacion.html", {"request": request})

@app.post("/nueva-tramitacion")
def crear_tramitacion(
    request: Request,
    num_albaran: list[str] = Form(...),
    num_tramitacion: list[str] = Form(...),
    fecha: list[str] = Form(...),
    modelo: list[str] = Form(...),
    sn_imei: list[str] = Form(...),
    descripcion_averia: list[str] = Form(...),
    caja: list[str] = Form(...),
    cargador: list[str] = Form(...),
    otros: list[str] = Form(...),
    parte: list[str] = Form(...),
    de_tienda: list[str] = Form(...),
    codigo_interno: list[str] = Form(...),
    db: Session = Depends(get_db)
):
    tramitacion = models.Tramitacion()  # Sin proveedor
    db.add(tramitacion)
    db.flush()

    from datetime import datetime
    for i in range(len(num_albaran)):
        # Limpiar posibles espacios y recortar la fecha a 10 caracteres (YYYY-MM-DD)
        fecha_str = fecha[i].strip()[:10]
        try:
            fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except Exception:
            fecha_dt = datetime.now().date()
        producto = models.Producto(
            num_albaran=num_albaran[i],
            num_tramitacion=num_tramitacion[i],
            fecha=fecha_dt,
            modelo=modelo[i],
            sn_imei=sn_imei[i],
            descripcion_averia=descripcion_averia[i],
            caja=caja[i],
            cargador=cargador[i],
            otros=otros[i],
            parte=parte[i],
            de_tienda=de_tienda[i],
            codigo_interno=codigo_interno[i],
            tramitacion_id=tramitacion.id
        )
        db.add(producto)

    db.commit()
    db.refresh(tramitacion)
    ruta_excel = generar_excel(tramitacion)
    return RedirectResponse(url=f"/tramitacion/{tramitacion.id}", status_code=303)

# Página de detalles de una tramitación
@app.get("/tramitacion/{tramitacion_id}")
def detalle_tramitacion(tramitacion_id: int, request: Request, db: Session = Depends(get_db)):
    tramitacion = db.query(models.Tramitacion).filter(models.Tramitacion.id == tramitacion_id).first()
    if not tramitacion:
        return templates.TemplateResponse("error.html", {"request": request, "mensaje": "Tramitación no encontrada"}, status_code=404)
    # Buscar imágenes en la carpeta correspondiente
    imagenes_encontradas = []
    if tramitacion.productos and tramitacion.productos[0].num_tramitacion:
        carpeta = tramitacion.productos[0].num_tramitacion.replace('/', '_')
        ruta_carpeta = os.path.join("archivos_generados", carpeta)
        if os.path.isdir(ruta_carpeta):
            for ext in ['jpg','jpeg','png','gif','bmp','JPG','JPEG','PNG','GIF','BMP']:
                imagenes_encontradas.extend([
                    f"/archivos_generados/{carpeta}/" + f for f in os.listdir(ruta_carpeta) if f.lower().endswith('.' + ext)
                ])
    return templates.TemplateResponse(
        "detalle_tramitacion.html",
        {"request": request, "tramitacion": tramitacion, "imagenes_encontradas": imagenes_encontradas}
    )

# Consultar tramitaciones (opcional: filtrar por proveedor, fechas)
@app.get("/tramitaciones")
def listar_tramitaciones(request: Request, desde: Optional[str] = None, hasta: Optional[str] = None, db: Session = Depends(get_db)):
    from datetime import datetime
    desde_dt = datetime.strptime(desde, "%Y-%m-%d").date() if desde else None
    hasta_dt = datetime.strptime(hasta, "%Y-%m-%d").date() if hasta else None
    tramitaciones = crud.obtener_tramitaciones(db, desde=desde_dt, hasta=hasta_dt)
    return templates.TemplateResponse("tramitaciones.html", {"request": request, "tramitaciones": tramitaciones})

@app.get("/api/siguiente-num-tramitacion")
def siguiente_num_tramitacion(db: Session = Depends(get_db)):
    ultimo = db.query(models.Producto).order_by(models.Producto.id.desc()).first()
    if ultimo is not None and getattr(ultimo, "num_tramitacion", None):
        try:
            # Extraer la parte numérica antes de la barra
            num, anio = ultimo.num_tramitacion.split("/")
            siguiente = f"{int(num)+1}/{anio}"
        except Exception:
            siguiente = "1/2025"
    else:
        siguiente = "1/2025"
    return JSONResponse(content={"siguiente": siguiente})

@app.get("/api/ultimo-num-albaran")
def ultimo_num_albaran():
    carpeta = "archivos_generados"
    patron = os.path.join(carpeta, "albaran_*.pdf")
    archivos = glob.glob(patron)
    if archivos:
        # Ordenar por fecha de modificación descendente
        archivos.sort(key=os.path.getmtime, reverse=True)
        for archivo in archivos:
            nombre = os.path.basename(archivo)
            m = re.match(r"albaran_(\d+)\.pdf", nombre)
            if m:
                return JSONResponse(content={"ultimo": m.group(1)})
    return JSONResponse(content={"ultimo": ""})

@app.post("/tramitacion/{tramitacion_id}/imagenes")
def cargar_imagenes(tramitacion_id: int, imagenes: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    tramitacion = db.query(models.Tramitacion).filter(models.Tramitacion.id == tramitacion_id).first()
    if not tramitacion or not tramitacion.productos:
        return RedirectResponse(url=f"/tramitacion/{tramitacion_id}", status_code=303)
    num_tramitacion = tramitacion.productos[0].num_tramitacion.replace('/', '_')
    carpeta = os.path.join("archivos_generados", num_tramitacion)
    os.makedirs(carpeta, exist_ok=True)
    for imagen in imagenes:
        nombre = imagen.filename
        if not nombre:
            continue
        ruta_destino = os.path.join(carpeta, nombre)
        with open(ruta_destino, "wb") as f:
            f.write(imagen.file.read())
    return RedirectResponse(url=f"/tramitacion/{tramitacion_id}", status_code=303)

@app.get("/buscar-tramitacion")
def buscar_tramitacion(request: Request, fecha: Optional[str] = None, num_albaran: Optional[str] = None, num_tramitacion: Optional[str] = None, codigo_interno: Optional[str] = None, parte: Optional[str] = None, sn_imei: Optional[str] = None, db: Session = Depends(get_db)):
    resultados = None
    if any([fecha, num_albaran, num_tramitacion, codigo_interno, parte, sn_imei]):
        query = db.query(models.Tramitacion).join(models.Producto)
        if fecha:
            query = query.filter(models.Producto.fecha == fecha)
        if num_albaran:
            query = query.filter(models.Producto.num_albaran == num_albaran)
        if num_tramitacion:
            query = query.filter(models.Producto.num_tramitacion == num_tramitacion)
        if codigo_interno:
            query = query.filter(models.Producto.codigo_interno == codigo_interno)
        if parte:
            query = query.filter(models.Producto.parte == parte)
        if sn_imei:
            query = query.filter(models.Producto.sn_imei == sn_imei)
        resultados = query.distinct().all()
    return templates.TemplateResponse("buscar_tramitacion.html", {"request": request, "resultados": resultados})

@app.get("/estadisticas", response_class=HTMLResponse)
def estadisticas(request: Request, db: Session = Depends(get_db)):
    # Total tramitaciones
    total_tramitaciones = db.query(models.Tramitacion).count()
    # Total productos
    total_productos = db.query(models.Producto).count()
    # Tramitaciones por mes (último año)
    hoy = datetime.now()
    meses = [(hoy.year if hoy.month - i > 0 else hoy.year - 1, (hoy.month - i - 1) % 12 + 1) for i in range(11, -1, -1)]
    from collections import OrderedDict
    tramitaciones_por_mes = OrderedDict()
    for y, m in meses:
        count = db.query(models.Tramitacion).filter(models.Tramitacion.fecha.like(f"{y}-{m:02d}-%")).count()
        tramitaciones_por_mes[f"{y}-{m:02d}"] = count
    # Tramitaciones totales por año
    tramitaciones_por_ano = db.query(
        models.Tramitacion.fecha,
    ).all()
    conteo_tramitaciones_ano = {}
    for t in tramitaciones_por_ano:
        anio = t[0].year
        conteo_tramitaciones_ano[anio] = conteo_tramitaciones_ano.get(anio, 0) + 1
    conteo_tramitaciones_ano = dict(sorted(conteo_tramitaciones_ano.items()))
    # Productos tramitados por año
    productos_por_ano = db.query(models.Producto.fecha).all()
    conteo_productos_ano = {}
    for p in productos_por_ano:
        anio = p[0].year
        conteo_productos_ano[anio] = conteo_productos_ano.get(anio, 0) + 1
    conteo_productos_ano = dict(sorted(conteo_productos_ano.items()))
    # Número de productos tramitados por código interno
    from sqlalchemy import func
    productos_por_codigo = db.query(models.Producto.codigo_interno, func.count(models.Producto.id)).group_by(models.Producto.codigo_interno).order_by(func.count(models.Producto.id).desc()).all()
    return templates.TemplateResponse("estadisticas.html", {
        "request": request,
        "total_tramitaciones": total_tramitaciones,
        "total_productos": total_productos,
        "tramitaciones_por_mes": tramitaciones_por_mes.items(),
        "tramitaciones_por_ano": conteo_tramitaciones_ano.items(),
        "productos_por_ano": conteo_productos_ano.items(),
        "productos_por_codigo": productos_por_codigo
    })
