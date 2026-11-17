"""API v2 multiorganización. Contrato: docs/CONTRATO_API_V2_PROPUESTO.md.

Capas en cada request bajo /organizaciones/{org_id}:
1. Token OIDC verificado (401).
2. Membresía activa del `sub` en `org_id`, consultada en BD (403) → contexto RLS SET LOCAL.
3. Rol con permiso para la acción (403).
4. Consultas filtradas explícitamente por (organizacion_id, id) además de RLS (404 si es ajeno).
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import Usuario, get_current_user
from .db import bind_tenant, get_db
from .imagenes import leer_imagen_validada
from .models import Inmueble, InmuebleMedia, Membresia, Organizacion
from .schemas import (
    Estado, InmuebleCreateV2, InmuebleOutV2, InmueblePatchV2, MediaOut, MeOut, OrganizacionOut, Tipo,
)
from .storage import Storage, clave_original, get_storage
from .tenancy import (
    CREAR_INMUEBLE, EDITAR_INMUEBLE, GESTIONAR_MIEMBROS, LEER, SUBIR_MEDIA, Contexto, membresias_activas,
    requiere,
)

router = APIRouter(prefix='/api/v2', tags=['v2'])
auditoria = logging.getLogger('rah.auditoria')

ORG = '/organizaciones/{org_id}'


def _audit(ctx: Contexto, accion: str, objetivo: UUID) -> None:
    # Sin tokens, emails ni datos personales: solo identificadores.
    auditoria.info('accion=%s org=%s sub=%s objetivo=%s', accion, ctx.organizacion_id, ctx.usuario.sub, objetivo)


def _organizaciones_de(db: Session, usuario: Usuario) -> list[OrganizacionOut]:
    bind_tenant(db, None, usuario.sub)
    return [OrganizacionOut(id=o.id, slug=o.slug, nombre_comercial=o.nombre_comercial, rol=m.rol)
            for m, o in membresias_activas(db, usuario.sub)]


def _inmueble_de_org(db: Session, ctx: Contexto, inmueble_id: UUID) -> Inmueble:
    inmueble = db.scalar(
        select(Inmueble).where(Inmueble.organizacion_id == ctx.organizacion_id, Inmueble.id == inmueble_id)
    )
    if inmueble is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Inmueble no encontrado')
    return inmueble


def _media_out(ctx: Contexto, media: InmuebleMedia, storage: Storage) -> MediaOut:
    # Defensa en profundidad: la fila debe ser de la org verificada antes de firmar nada.
    if media.organizacion_id != ctx.organizacion_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Medio no encontrado')
    return MediaOut(
        id=media.id, inmueble_id=media.inmueble_id, tipo=media.tipo,
        etiqueta_estancia=media.etiqueta_estancia, orden=media.orden, content_type=media.content_type,
        url_temporal=storage.presign_get(ctx.organizacion_id, media.object_key),
    )


def _es_referencia_duplicada(exc: IntegrityError) -> bool:
    return 'idx_inmuebles_org_codigo_referencia' in str(exc.orig)


# ------------------------------------------------------------------ identidad y organización

@router.get('/me', response_model=MeOut)
def me(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return MeOut(sub=usuario.sub, email=usuario.email, nombre=usuario.nombre,
                 organizaciones=_organizaciones_de(db, usuario))


@router.get('/me/organizaciones', response_model=list[OrganizacionOut])
def mis_organizaciones(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return _organizaciones_de(db, usuario)


@router.get(ORG, response_model=OrganizacionOut)
def leer_organizacion(ctx: Contexto = Depends(requiere(LEER)), db: Session = Depends(get_db)):
    org = db.get(Organizacion, ctx.organizacion_id)
    return OrganizacionOut(id=org.id, slug=org.slug, nombre_comercial=org.nombre_comercial, rol=ctx.rol)


@router.delete(ORG + '/membresias/{membresia_id}', status_code=204)
def revocar_membresia(
    membresia_id: UUID, ctx: Contexto = Depends(requiere(GESTIONAR_MIEMBROS)), db: Session = Depends(get_db),
):
    """Aprobado por el integrador (2026-11-17) para la matriz de aceptación; solo propietario.
    No borra la fila: la marca `inactiva` (valor del CHECK de la migración 0001)."""
    membresia = db.scalar(
        select(Membresia).where(Membresia.organizacion_id == ctx.organizacion_id, Membresia.id == membresia_id)
    )
    if membresia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Membresía no encontrada')
    if membresia.id == ctx.membresia_id:
        raise HTTPException(status.HTTP_409_CONFLICT, 'No puedes revocar tu propia membresía')
    membresia.estatus = 'inactiva'
    db.commit()
    _audit(ctx, 'membresia.revocar', membresia_id)


# ------------------------------------------------------------------ inmuebles

@router.get(ORG + '/inmuebles', response_model=list[InmuebleOutV2])
def listar_inmuebles(
    tipo: Tipo | None = None, estado: Estado | None = None,
    ctx: Contexto = Depends(requiere(LEER)), db: Session = Depends(get_db),
):
    stmt = select(Inmueble).where(Inmueble.organizacion_id == ctx.organizacion_id)
    if tipo:
        stmt = stmt.where(Inmueble.tipo == tipo)
    if estado:
        stmt = stmt.where(Inmueble.estado == estado)
    return db.scalars(stmt.order_by(Inmueble.creado_en.desc(), Inmueble.titulo.asc()).limit(100)).all()


@router.post(ORG + '/inmuebles', response_model=InmuebleOutV2, status_code=201)
def crear_inmueble(
    payload: InmuebleCreateV2, ctx: Contexto = Depends(requiere(CREAR_INMUEBLE)), db: Session = Depends(get_db),
):
    inmueble = Inmueble(**payload.model_dump(), organizacion_id=ctx.organizacion_id)
    db.add(inmueble)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if _es_referencia_duplicada(exc):
            raise HTTPException(status.HTTP_409_CONFLICT, 'Referencia duplicada en esta organización') from None
        raise
    db.refresh(inmueble)
    _audit(ctx, 'inmueble.crear', inmueble.id)
    return inmueble


@router.get(ORG + '/inmuebles/{inmueble_id}', response_model=InmuebleOutV2)
def leer_inmueble(inmueble_id: UUID, ctx: Contexto = Depends(requiere(LEER)), db: Session = Depends(get_db)):
    return _inmueble_de_org(db, ctx, inmueble_id)


@router.patch(ORG + '/inmuebles/{inmueble_id}', response_model=InmuebleOutV2)
def editar_inmueble(
    inmueble_id: UUID, payload: InmueblePatchV2,
    ctx: Contexto = Depends(requiere(EDITAR_INMUEBLE)), db: Session = Depends(get_db),
):
    inmueble = _inmueble_de_org(db, ctx, inmueble_id)
    try:
        cambios = payload.cambios()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    for campo, valor in cambios.items():
        setattr(inmueble, campo, valor)
    inmueble.actualizado_en = func.now()
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if _es_referencia_duplicada(exc):
            raise HTTPException(status.HTTP_409_CONFLICT, 'Referencia duplicada en esta organización') from None
        raise
    db.refresh(inmueble)
    _audit(ctx, 'inmueble.editar', inmueble.id)
    return inmueble


# ------------------------------------------------------------------ medios

@router.get(ORG + '/inmuebles/{inmueble_id}/media', response_model=list[MediaOut])
def listar_media(
    inmueble_id: UUID, ctx: Contexto = Depends(requiere(LEER)),
    db: Session = Depends(get_db), storage: Storage = Depends(get_storage),
):
    _inmueble_de_org(db, ctx, inmueble_id)
    items = db.scalars(
        select(InmuebleMedia)
        .where(InmuebleMedia.organizacion_id == ctx.organizacion_id, InmuebleMedia.inmueble_id == inmueble_id)
        .order_by(InmuebleMedia.orden.asc(), InmuebleMedia.creado_en.asc())
    ).all()
    salida = [_media_out(ctx, m, storage) for m in items]
    if salida:
        _audit(ctx, 'media.emitir_urls', inmueble_id)
    return salida


@router.post(ORG + '/inmuebles/{inmueble_id}/media', response_model=MediaOut, status_code=201)
async def subir_media(
    inmueble_id: UUID,
    archivo: UploadFile = File(...),
    etiqueta_estancia: str | None = Form(default=None, max_length=60),
    ctx: Contexto = Depends(requiere(SUBIR_MEDIA)),
    db: Session = Depends(get_db),
    storage: Storage = Depends(get_storage),
):
    _inmueble_de_org(db, ctx, inmueble_id)  # antes de leer/guardar nada
    contenido, content_type, extension = await leer_imagen_validada(archivo)
    key = clave_original(ctx.organizacion_id, inmueble_id, extension)
    storage.put(key, contenido, content_type)
    media = InmuebleMedia(
        organizacion_id=ctx.organizacion_id, inmueble_id=inmueble_id, object_key=key, tipo='foto',
        etiqueta_estancia=etiqueta_estancia, content_type=content_type, orden=0,
    )
    db.add(media)
    try:
        db.commit()
    except Exception:
        db.rollback()
        storage.delete(key)  # no dejar objetos huérfanos sin fila
        raise
    db.refresh(media)
    _audit(ctx, 'media.subir', media.id)
    return _media_out(ctx, media, storage)
