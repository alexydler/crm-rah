from decimal import Decimal
from typing import Any, ClassVar, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


Tipo = Literal['apartamento', 'casa', 'quinta', 'townhouse', 'local', 'oficina', 'galpon', 'terreno']
Operacion = Literal['venta', 'alquiler']
Estado = Literal['borrador', 'disponible', 'reservado', 'cerrado']


class InmuebleCreate(BaseModel):
    titulo: str = Field(min_length=3, max_length=180)
    tipo: Tipo
    operacion: Operacion
    precio: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    moneda: str = Field(default='USD', min_length=3, max_length=3)
    direccion: str | None = Field(default=None, max_length=250)
    zona: str = Field(min_length=2, max_length=120)
    estado_ve: str | None = Field(default=None, max_length=100)
    municipio: str | None = Field(default=None, max_length=100)
    parroquia: str | None = Field(default=None, max_length=100)
    urbanizacion: str | None = Field(default=None, max_length=120)
    codigo_referencia: str | None = Field(default=None, max_length=80)
    m2_construidos: Decimal | None = Field(default=None, ge=0)
    m2_parcela: Decimal | None = Field(default=None, ge=0)
    habitaciones: int | None = Field(default=None, ge=0, le=100)
    banos: int | None = Field(default=None, ge=0, le=100)
    extras: dict[str, Any] = Field(default_factory=dict)
    descripcion: str = Field(default='', max_length=10000)
    estado: Estado = 'borrador'

    @field_validator('moneda')
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        if not value.isalpha():
            raise ValueError('La moneda debe tener tres letras ISO 4217')
        value = value.upper()
        if value not in ('USD', 'VES'):
            raise ValueError('Solo USD o VES en la primera versión para Venezuela')
        return value


class InmuebleOut(InmuebleCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class MediaOut(BaseModel):
    id: UUID
    inmueble_id: UUID
    tipo: str
    etiqueta_estancia: str | None
    orden: int
    content_type: str
    url_temporal: str


# ---------------------------------------------------------------------------------------------
# API v2 (multiorganización). Ver docs/CONTRATO_API_V2_PROPUESTO.md.
# `id`, `organizacion_id` y `creado_por` los asigna el servidor: el cliente no puede enviarlos
# (extra='forbid' → 422) para que un intento de fijar la organización sea visible y no se ignore.
# ---------------------------------------------------------------------------------------------

Rol = Literal['propietario', 'gerente', 'asesor', 'marketing', 'consulta']


class InmuebleCreateV2(InmuebleCreate):
    model_config = ConfigDict(extra='forbid')


class InmueblePatchV2(BaseModel):
    """Campos editables; todos opcionales. Los campos requeridos en creación no aceptan null."""

    model_config = ConfigDict(extra='forbid')

    titulo: str | None = Field(default=None, min_length=3, max_length=180)
    tipo: Tipo | None = None
    operacion: Operacion | None = None
    precio: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    moneda: str | None = Field(default=None, min_length=3, max_length=3)
    direccion: str | None = Field(default=None, max_length=250)
    zona: str | None = Field(default=None, min_length=2, max_length=120)
    estado_ve: str | None = Field(default=None, max_length=100)
    municipio: str | None = Field(default=None, max_length=100)
    parroquia: str | None = Field(default=None, max_length=100)
    urbanizacion: str | None = Field(default=None, max_length=120)
    codigo_referencia: str | None = Field(default=None, max_length=80)
    m2_construidos: Decimal | None = Field(default=None, ge=0)
    m2_parcela: Decimal | None = Field(default=None, ge=0)
    habitaciones: int | None = Field(default=None, ge=0, le=100)
    banos: int | None = Field(default=None, ge=0, le=100)
    extras: dict[str, Any] | None = None
    descripcion: str | None = Field(default=None, max_length=10000)
    estado: Estado | None = None

    NO_NULL: ClassVar[tuple[str, ...]] = ('titulo', 'tipo', 'operacion', 'precio', 'moneda', 'zona', 'extras', 'descripcion', 'estado')

    @field_validator('moneda')
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return None if value is None else InmuebleCreate.normalize_currency(value)

    def cambios(self) -> dict[str, Any]:
        data = self.model_dump(exclude_unset=True)
        nulos = [k for k in self.NO_NULL if k in data and data[k] is None]
        if nulos:
            raise ValueError(f'No se admite null en: {", ".join(nulos)}')
        return data


class InmuebleOutV2(InmuebleOut):
    organizacion_id: UUID


class OrganizacionOut(BaseModel):
    id: UUID
    slug: str
    nombre_comercial: str
    rol: Rol


class MeOut(BaseModel):
    sub: str
    email: str | None = None
    nombre: str | None = None
    organizaciones: list[OrganizacionOut]
