"""Modelos SQLAlchemy.

Los modelos multiorganización siguen ``db/design/ESQUEMA_OBJETIVO.md``. La migración real
(Alembic, RLS, roles) la entrega el DBA en ``db/``; estos modelos NO crean tablas en runtime.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, SmallInteger, String, Text,
    UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Valores propuestos; confirmar con el integrador antes de fijarlos como contrato.
ROLES = ('propietario', 'gerente', 'asesor', 'marketing', 'consulta')
ESTATUS_ORGANIZACION = ('activa', 'suspendida')
ESTATUS_MEMBRESIA = ('activa', 'revocada')


class Base(DeclarativeBase):
    pass


class Organizacion(Base):
    __tablename__ = 'organizaciones'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    nombre: Mapped[str] = mapped_column(String(180))
    estatus: Mapped[str] = mapped_column(String(20), default='activa')
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Membresia(Base):
    """Un usuario global (``sub`` OIDC) puede tener varias membresías, una por organización."""

    __tablename__ = 'membresias'
    __table_args__ = (UniqueConstraint('organizacion_id', 'usuario_sub', name='uq_membresias_org_sub'),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organizacion_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('organizaciones.id', ondelete='CASCADE'), index=True
    )
    usuario_sub: Mapped[str] = mapped_column(String(255), index=True)
    rol: Mapped[str] = mapped_column(String(24))
    estatus: Mapped[str] = mapped_column(String(20), default='activa')
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Inmueble(Base):
    __tablename__ = 'inmuebles'
    __table_args__ = (
        # Destino de las FK compuestas (organizacion_id, inmueble_id).
        UniqueConstraint('organizacion_id', 'id', name='uq_inmuebles_org_id'),
        # Referencia única POR organización, no global.
        Index(
            'uq_inmuebles_org_referencia', 'organizacion_id', 'codigo_referencia', unique=True,
            postgresql_where=text('codigo_referencia IS NOT NULL'),
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organizacion_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('organizaciones.id', ondelete='RESTRICT'), index=True
    )
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
    codigo_referencia: Mapped[str | None] = mapped_column(String(80))
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
    __table_args__ = (
        # Impide enlazar una foto a un inmueble de otra organización.
        ForeignKeyConstraint(
            ['organizacion_id', 'inmueble_id'], ['inmuebles.organizacion_id', 'inmuebles.id'],
            ondelete='CASCADE', name='fk_media_inmueble_org',
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organizacion_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey('organizaciones.id', ondelete='RESTRICT'), index=True
    )
    inmueble_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    object_key: Mapped[str] = mapped_column(Text, unique=True)
    tipo: Mapped[str] = mapped_column(String(24), default='foto')
    etiqueta_estancia: Mapped[str | None] = mapped_column(String(60))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str] = mapped_column(String(80))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
