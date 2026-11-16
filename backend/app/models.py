from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Inmueble(Base):
    __tablename__ = 'inmuebles'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    titulo: Mapped[str] = mapped_column(String(180))
    tipo: Mapped[str] = mapped_column(String(24))
    operacion: Mapped[str] = mapped_column(String(12))
    precio: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    moneda: Mapped[str] = mapped_column(String(3), default='USD')
    direccion: Mapped[str | None] = mapped_column(String(250))
    zona: Mapped[str] = mapped_column(String(120))
    estado_ve: Mapped[str | None] = mapped_column(String(100))
    municipio: Mapped[str | None] = mapped_column(String(100))
    parroquia: Mapped[str | None] = mapped_column(String(100))
    urbanizacion: Mapped[str | None] = mapped_column(String(120))
    codigo_referencia: Mapped[str | None] = mapped_column(String(80), unique=True)
    m2_construidos: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    m2_parcela: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    habitaciones: Mapped[int | None] = mapped_column(SmallInteger)
    banos: Mapped[int | None] = mapped_column(SmallInteger)
    extras: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    descripcion: Mapped[str] = mapped_column(Text, default='')
    estado: Mapped[str] = mapped_column(String(20), default='borrador')
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InmuebleMedia(Base):
    __tablename__ = 'inmueble_media'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    inmueble_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey('inmuebles.id', ondelete='CASCADE'))
    object_key: Mapped[str] = mapped_column(Text, unique=True)
    tipo: Mapped[str] = mapped_column(String(24), default='foto')
    etiqueta_estancia: Mapped[str | None] = mapped_column(String(60))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str] = mapped_column(String(80))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
