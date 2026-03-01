"""005 add check constraint on usuarios.rol

Revision ID: 005
Revises: 004
Create Date: 2025-01-01 00:00:00.000000

Agrega un CHECK constraint a la columna 'rol' de la tabla 'usuarios'
para garantizar que solo se inserten valores válidos del enum UserRol,
independientemente de la capa de aplicación.
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None

VALID_ROLES = ("admin", "operador", "chofer", "viewer")


def upgrade() -> None:
    # CHECK constraint en rol
    op.create_check_constraint(
        "ck_usuarios_rol_valid",
        "usuarios",
        sa.text(f"rol IN {VALID_ROLES}"),
    )


def downgrade() -> None:
    op.drop_constraint("ck_usuarios_rol_valid", "usuarios", type_="check")
