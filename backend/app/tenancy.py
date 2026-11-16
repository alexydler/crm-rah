"""Autorización por organización: membresía activa verificada en BD en CADA request.

El ``organizacion_id`` de la URL solo identifica qué organización se pide; la prueba de acceso
es la fila de ``membresias`` del ``sub`` del token verificado. Se ignoran cabeceras como
``X-Organization-ID`` y cualquier ``organizacion_id`` del cuerpo.
"""
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import Usuario, get_current_user
from .db import bind_tenant, get_db
from .models import Membresia, Organizacion, Usuario as UsuarioDB

# Permisos por acción (primera iteración, ver docs/ARQUITECTURA_MULTIAGENCIA.md).
# `asesor` aún no puede editar/subir fotos: falta `asignado_membresia_id` para limitarlo a su
# cartera; se bloquea en vez de conceder acceso amplio.
LEER = frozenset({'propietario', 'gerente', 'asesor', 'marketing', 'consulta'})
CREAR_INMUEBLE = frozenset({'propietario', 'gerente', 'asesor'})
EDITAR_INMUEBLE = frozenset({'propietario', 'gerente'})
SUBIR_MEDIA = frozenset({'propietario', 'gerente'})
GESTIONAR_MIEMBROS = frozenset({'propietario'})


@dataclass(frozen=True)
class Contexto:
    usuario: Usuario
    organizacion_id: UUID
    membresia_id: UUID
    rol: str


def membresias_activas(db: Session, sub: str) -> list[tuple[Membresia, Organizacion]]:
    stmt = (
        select(Membresia, Organizacion)
        .join(Organizacion, Organizacion.id == Membresia.organizacion_id)
        .join(UsuarioDB, UsuarioDB.id == Membresia.usuario_id)
        .where(UsuarioDB.subject == sub, UsuarioDB.estado == 'activo',
               Membresia.estatus == 'activa', Organizacion.estatus == 'activa')
        .order_by(Organizacion.nombre_comercial.asc())
    )
    return [(m, o) for m, o in db.execute(stmt).all()]


def get_contexto(
    org_id: UUID,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Contexto:
    # Solo el sub verificado (sin org) por si la BD aplica RLS a `membresias` por usuario.
    bind_tenant(db, None, usuario.sub)
    membresia = db.scalar(
        select(Membresia)
        .join(Organizacion, Organizacion.id == Membresia.organizacion_id)
        .join(UsuarioDB, UsuarioDB.id == Membresia.usuario_id)
        .where(
            Membresia.organizacion_id == org_id,
            UsuarioDB.subject == usuario.sub,
            UsuarioDB.estado == 'activo',
            Membresia.estatus == 'activa',
            Organizacion.estatus == 'activa',
        )
    )
    if membresia is None:
        # Misma respuesta exista o no la organización: no revela qué UUIDs existen.
        raise HTTPException(status.HTTP_403_FORBIDDEN, 'Sin membresía activa en esta organización')
    # Solo ahora, con la membresía verificada, se fija el contexto RLS de la transacción.
    bind_tenant(db, membresia.organizacion_id, usuario.sub)
    return Contexto(usuario=usuario, organizacion_id=membresia.organizacion_id,
                    membresia_id=membresia.id, rol=membresia.rol)


def requiere(roles: frozenset[str]) -> Callable[..., Contexto]:
    def _dep(ctx: Contexto = Depends(get_contexto)) -> Contexto:
        if ctx.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, 'Rol sin permiso para esta acción')
        return ctx

    return _dep
