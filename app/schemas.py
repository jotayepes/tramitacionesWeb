from pydantic import BaseModel, field_serializer
from typing import List
from datetime import date


# ----- PRODUCTO -----

class ProductoBase(BaseModel):
    num_albaran: str
    num_tramitacion: str
    fecha: date  # Ahora es date, no str
    modelo: str
    sn_imei: str
    descripcion_averia: str
    caja: str
    cargador: str
    otros: str
    parte: str
    de_tienda: str
    codigo_interno: str

    @field_serializer('fecha')
    def serialize_fecha(self, value: date):
        return value.strftime('%Y-%m-%d')

class ProductoCreate(ProductoBase):
    pass

class Producto(ProductoBase):
    id: int
    tramitacion_id: int

    class Config:
        from_attributes = True


# ----- TRAMITACION -----

class TramitacionBase(BaseModel):
    pass

class TramitacionCreate(TramitacionBase):
    productos: List[ProductoCreate]

class Tramitacion(TramitacionBase):
    id: int
    fecha: date
    productos: List[Producto] = []

    class Config:
        from_attributes = True
