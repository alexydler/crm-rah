"""Políticas RLS de lectura por usuario en membresias y organizaciones

Revision ID: 0002_rls_usuario_lectura
Revises: 0001_sprint02_multiagencia
Create Date: 2026-11-16 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_rls_usuario_lectura'
down_revision: Union[str, None] = '0001_sprint02_multiagencia'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Políticas PERMISSIVE de lectura por usuario (app.usuario_sub)
    # Permiten verificar membresía antes de fijar app.organizacion_id y listar organizaciones del usuario en /api/v2/me
    op.execute("""
        DROP POLICY IF EXISTS membresias_propias_lectura ON membresias;
        CREATE POLICY membresias_propias_lectura ON membresias
            AS PERMISSIVE FOR SELECT
            TO PUBLIC
            USING (usuario_id IN (
                SELECT u.id FROM usuarios u
                WHERE u.subject = NULLIF(current_setting('app.usuario_sub', true), '')
            ));

        DROP POLICY IF EXISTS organizaciones_propias_lectura ON organizaciones;
        CREATE POLICY organizaciones_propias_lectura ON organizaciones
            AS PERMISSIVE FOR SELECT
            TO PUBLIC
            USING (id IN (
                SELECT m.organizacion_id FROM membresias m JOIN usuarios u ON u.id = m.usuario_id
                WHERE u.subject = NULLIF(current_setting('app.usuario_sub', true), '')
            ));
    """)


def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS membresias_propias_lectura ON membresias;
        DROP POLICY IF EXISTS organizaciones_propias_lectura ON organizaciones;
    """)
