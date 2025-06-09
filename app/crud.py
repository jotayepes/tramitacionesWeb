from sqlalchemy.orm import Session
from app import models, schemas
from typing import List, Optional
from datetime import date


def crear_tramitacion(db: Session, productos: List[schemas.ProductoCreate]):
    # Crear nueva tramitación
    nueva = models.Tramitacion()
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    # Añadir productos asociados
    for p in productos:
        producto = models.Producto(
            num_albaran=p.num_albaran,
            num_tramitacion=p.num_tramitacion,
            fecha=p.fecha,  # Se debe convertir a date si es string
            modelo=p.modelo,
            sn_imei=p.sn_imei,
            descripcion_averia=p.descripcion_averia,
            caja=p.caja,
            cargador=p.cargador,
            otros=p.otros,
            parte=p.parte,
            de_tienda=p.de_tienda,
            codigo_interno=p.codigo_interno,
            tramitacion_id=nueva.id
        )
        db.add(producto)

    db.commit()
    db.refresh(nueva)
    return nueva


def obtener_tramitaciones(
    db: Session,
    desde: Optional[date] = None,
    hasta: Optional[date] = None
):
    query = db.query(models.Tramitacion)
    if desde:
        query = query.filter(models.Tramitacion.fecha >= desde)
    if hasta:
        query = query.filter(models.Tramitacion.fecha <= hasta)
    return query.all()
