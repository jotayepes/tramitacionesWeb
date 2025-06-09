from datetime import date
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
#from datetime import datetime
from app.database import Base


class Tramitacion(Base):
    __tablename__ = "tramitaciones"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, default=date.today)

    productos = relationship("Producto", back_populates="tramitacion")


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    tramitacion_id = Column(Integer, ForeignKey("tramitaciones.id"))
    num_albaran = Column(String, nullable=False)
    num_tramitacion = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)
    modelo = Column(String, nullable=False)
    sn_imei = Column(String, nullable=False)
    descripcion_averia = Column(String, nullable=False)
    caja = Column(String, nullable=False)
    cargador = Column(String, nullable=False)
    otros = Column(String, nullable=False)
    parte = Column(String, nullable=False)
    de_tienda = Column(String, nullable=False)
    codigo_interno = Column(String, nullable=False)

    tramitacion = relationship("Tramitacion", back_populates="productos")
