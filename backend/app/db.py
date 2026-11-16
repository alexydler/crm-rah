"""Sesiones de base de datos con contexto de tenant por transacción.

El contexto RLS se fija con ``set_config(..., is_local => true)``, equivalente a ``SET LOCAL``:
vive solo dentro de la transacción en curso y PostgreSQL lo descarta en COMMIT/ROLLBACK, por lo
que una conexión devuelta al pool nunca arrastra el tenant del request anterior.

Como una sesión SQLAlchemy puede abrir varias transacciones (p. ej. ``commit()`` y luego
``refresh()``), el valor verificado se guarda en ``session.info`` y se reaplica en cada
``after_begin``. Solo código de servidor escribe ``session.info``; nunca datos del cliente.
"""
from collections.abc import Generator
from uuid import UUID

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

ORG_GUC = 'app.organizacion_id'
SUB_GUC = 'app.usuario_sub'
_INFO_ORG = 'tenant_organizacion_id'
_INFO_SUB = 'tenant_usuario_sub'

_SET_CONTEXT = text(
    f"SELECT set_config('{ORG_GUC}', :org, true), set_config('{SUB_GUC}', :sub, true)"
)


class TenantSession(Session):
    """Sesión que reaplica el contexto verificado al comenzar cada transacción."""


@event.listens_for(TenantSession, 'after_begin')
def _apply_tenant_context(session: Session, transaction, connection) -> None:
    org = session.info.get(_INFO_ORG)
    sub = session.info.get(_INFO_SUB)
    if org is None and sub is None:
        return
    connection.execute(_SET_CONTEXT, {'org': str(org) if org else '', 'sub': sub or ''})


def bind_tenant(session: Session, organizacion_id: UUID | None, usuario_sub: str | None) -> None:
    """Fija el contexto verificado en la transacción actual y en las siguientes de la sesión.

    Llamar SOLO después de comprobar en servidor la membresía (o la org DEMO de v1).
    """
    session.info[_INFO_ORG] = organizacion_id
    session.info[_INFO_SUB] = usuario_sub
    # Si la transacción ya empezó (p. ej. por la consulta de membresía), after_begin ya se
    # ejecutó sin org: la fijamos aquí. Si no, esta sentencia abre la transacción y el
    # listener la fija; repetir set_config es idempotente.
    session.execute(_SET_CONTEXT, {'org': str(organizacion_id) if organizacion_id else '',
                                   'sub': usuario_sub or ''})


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, class_=TenantSession, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
