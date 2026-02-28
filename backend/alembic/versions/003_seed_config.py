"""003 seed config and admin user

Revision ID: 003
Revises: 002
Create Date: 2026-02-28 00:02:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import bcrypt

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONFIG_DEFAULTS = [
    ("tiempo_espera_min",   "10",       "int",   "Minutos de espera por parada"),
    ("deposito_lat",        "-32.91973","float", "Latitud del depósito (Guaymallén)"),
    ("deposito_lng",        "-68.81829","float", "Longitud del depósito (Guaymallén)"),
    ("deposito_direccion",  "Elpidio González 2753, Guaymallén, Mendoza", "str", "Dirección del depósito"),
    ("hora_desde",          "09:00",    "str",   "Hora inicio de entregas"),
    ("hora_hasta",          "14:00",    "str",   "Hora fin de entregas"),
    ("evitar_saltos_min",   "25",       "int",   "Umbral en minutos para detectar saltos anómalos"),
    ("vuelta_galpon_min",   "25",       "int",   "Tiempo mínimo para regresar al galpón (filtro)"),
    ("proveedor_matrix",    "ors",      "str",   "Proveedor distance matrix: ors|google|mapbox"),
    ("utilizar_ventana",    "true",     "bool",  "Filtrar remitos por ventana horaria"),
    ("distancia_max_km",    "45.0",     "float", "Radio máximo de entrega en km"),
    ("velocidad_urbana_kmh","40",       "float", "Velocidad promedio urbana km/h (Haversine fallback)"),
    ("dm_block_size",       "10",       "int",   "Tamaño de bloque NxN para distance matrix"),
    ("geocode_cache_days",  "30",       "int",   "Días de validez del caché de geocodificación"),
    ("max_remitos_ruta",    "40",       "int",   "Máximo de remitos por ruta"),
]


def upgrade() -> None:
    config_table = sa.table(
        "config_ruta",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
        sa.column("tipo", sa.String),
        sa.column("descripcion", sa.Text),
    )
    op.bulk_insert(
        config_table,
        [{"key": k, "value": v, "tipo": t, "descripcion": d}
         for k, v, t, d in CONFIG_DEFAULTS]
    )

    # Admin user — password: admin1234
    pw_bytes = bcrypt.hashpw(b"admin1234", bcrypt.gensalt()).decode("utf-8")
    users_table = sa.table(
        "usuarios",
        sa.column("email", sa.String),
        sa.column("password_hash", sa.String),
        sa.column("nombre", sa.String),
        sa.column("rol", sa.String),
        sa.column("activo", sa.Boolean),
    )
    op.bulk_insert(users_table, [{
        "email": "admin@molymarket.com",
        "password_hash": pw_bytes,
        "nombre": "Administrador",
        "rol": "admin",
        "activo": True,
    }])


def downgrade() -> None:
    op.execute("DELETE FROM config_ruta")
    op.execute("DELETE FROM usuarios WHERE email = 'admin@molymarket.com'")
