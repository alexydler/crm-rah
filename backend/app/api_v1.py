"""API v1 del prototipo (SIN autenticación). Solo DEMO local.

Deshabilitada por defecto (ENABLE_V1_DEMO=false): el router no se monta y sus rutas dan 404.
Si se habilita, exige V1_DEMO_ORGANIZACION_ID y todas las consultas quedan acotadas a esa
organización DEMO (filtro explícito + contexto RLS), nunca a datos de agencias.
"""
from collections.abc import Generator
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import bind_tenant, get_db
from .imagenes import leer_imagen_validada
from .models import Inmueble, InmuebleMedia
from .schemas import Estado, InmuebleCreate, InmuebleOut, MediaOut, Tipo
from .storage import Storage, clave_original, get_storage, prefijo_organizacion

router = APIRouter(prefix='/api/v1', tags=['v1-demo'])


def _demo_org() -> UUID:
    if settings.v1_demo_organizacion_id is None:
        raise RuntimeError('ENABLE_V1_DEMO=true requiere V1_DEMO_ORGANIZACION_ID')
    return settings.v1_demo_organizacion_id


def demo_db(db: Session = Depends(get_db)) -> Generator[Session, None, None]:
    bind_tenant(db, _demo_org(), None)
    yield db


def media_response(media: InmuebleMedia, storage: Storage) -> MediaOut:
    if media.object_key.startswith(prefijo_organizacion(media.organizacion_id)):
        url = storage.presign_get(media.organizacion_id, media.object_key)
    else:
        url = storage.presign_get_legacy(media.object_key)
    return MediaOut(
        id=media.id, inmueble_id=media.inmueble_id, tipo=media.tipo,
        etiqueta_estancia=media.etiqueta_estancia, orden=media.orden,
        content_type=media.content_type, url_temporal=url,
    )


def get_inmueble_or_404(inmueble_id: UUID, db: Session) -> Inmueble:
    inmueble = db.scalar(
        select(Inmueble).where(Inmueble.id == inmueble_id, Inmueble.organizacion_id == _demo_org())
    )
    if inmueble is None:
        raise HTTPException(status_code=404, detail='Inmueble no encontrado')
    return inmueble


@router.get('/inmuebles', response_model=list[InmuebleOut])
def listar_inmuebles(tipo: Tipo | None = None, estado: Estado | None = None, db: Session = Depends(demo_db)):
    stmt = select(Inmueble).where(Inmueble.organizacion_id == _demo_org())
    if tipo:
        stmt = stmt.where(Inmueble.tipo == tipo)
    if estado:
        stmt = stmt.where(Inmueble.estado == estado)
    return db.scalars(stmt.order_by(Inmueble.creado_en.desc(), Inmueble.titulo.asc()).limit(100)).all()


@router.post('/inmuebles', response_model=InmuebleOut, status_code=201)
def crear_inmueble(payload: InmuebleCreate, db: Session = Depends(demo_db)):
    inmueble = Inmueble(**payload.model_dump(), organizacion_id=_demo_org())
    db.add(inmueble)
    db.commit()
    db.refresh(inmueble)
    return inmueble


@router.get('/inmuebles/{inmueble_id}', response_model=InmuebleOut)
def leer_inmueble(inmueble_id: UUID, db: Session = Depends(demo_db)):
    return get_inmueble_or_404(inmueble_id, db)


@router.get('/inmuebles/{inmueble_id}/media', response_model=list[MediaOut])
def listar_media(inmueble_id: UUID, db: Session = Depends(demo_db), storage: Storage = Depends(get_storage)):
    get_inmueble_or_404(inmueble_id, db)
    media_items = db.scalars(
        select(InmuebleMedia)
        .where(InmuebleMedia.inmueble_id == inmueble_id, InmuebleMedia.organizacion_id == _demo_org())
        .order_by(InmuebleMedia.orden.asc(), InmuebleMedia.creado_en.asc())
    ).all()
    return [media_response(media, storage) for media in media_items]


@router.post('/inmuebles/{inmueble_id}/media', response_model=MediaOut, status_code=201)
async def subir_foto(
    inmueble_id: UUID,
    archivo: UploadFile = File(...),
    etiqueta_estancia: str | None = Form(default=None, max_length=60),
    db: Session = Depends(demo_db),
    storage: Storage = Depends(get_storage),
):
    get_inmueble_or_404(inmueble_id, db)
    contenido, content_type, extension = await leer_imagen_validada(archivo)
    org = _demo_org()
    key = clave_original(org, inmueble_id, extension)
    storage.put(key, contenido, content_type)
    media = InmuebleMedia(
        organizacion_id=org, inmueble_id=inmueble_id, object_key=key, tipo='foto',
        etiqueta_estancia=etiqueta_estancia, content_type=content_type, orden=0,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media_response(media, storage)
