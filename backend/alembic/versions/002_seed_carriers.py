"""002 seed carriers

Revision ID: 002
Revises: 001
Create Date: 2025-01-01 00:01:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CARRIERS = [
    # (nombre_canonico, aliases_json, regex_pattern, es_externo, es_pickup, prioridad_regex)
    ("RETIRO EN GALPON", '["retiro galpon","retira","retira en galpon","busca","viene a buscar","pickup"]', r"(?i)(retir[ao]|busca|viene\s+a\s+buscar|pickup|lo\s+retira|lo\s+busca)", False, True, 10),
    ("ANDREANI", '["andreani","andreanni","andreaní"]', r"(?i)andreani", True, False, 20),
    ("OCA", '["oca","o\.c\.a\."]', r"(?i)\boca\b", True, False, 20),
    ("CORREO ARGENTINO", '["correo","correo argentino","correo arg"]', r"(?i)(correo\s+argentino|^correo$)", True, False, 20),
    ("VIA CARGO", '["via cargo","viacargo","via_cargo"]', r"(?i)via\s*cargo", True, False, 20),
    ("URBANO", '["urbano","urbano express","urbano exp"]', r"(?i)urbano(\s+express)?", True, False, 20),
    ("LAAR", '["laar","laarcourier"]', r"(?i)\blaar\b", True, False, 20),
    ("TUPUY", '["tupuy","tu puy"]', r"(?i)tupuy", True, False, 20),
    ("SERVIENTREGA", '["servientrega","servi entrega"]', r"(?i)servientrega", True, False, 20),
    ("MOOVA", '["moova","muuva"]', r"(?i)moova", True, False, 20),
    ("RAPPI", '["rappi","rapi"]', r"(?i)rappi", True, False, 20),
    ("PEDIDOS YA", '["pedidos ya","pedidosya","pya"]', r"(?i)pedidos\s*ya", True, False, 20),
    ("MERCADO ENVIOS", '["mercado envios","mercadoenvios","ml envios","meli envios"]', r"(?i)mercado\s+env[íi]os", True, False, 20),
    ("ENVIO PROPIO", '["envio propio","propio","reparto propio","repartidor propio"]', r"(?i)(envio\s+propio|reparto\s+propio|repartidor\s+propio)", False, False, 30),
    ("DESCONOCIDO", '[]', None, True, False, 99),
]


def upgrade() -> None:
    carriers_table = sa.table(
        "carriers",
        sa.column("nombre_canonico", sa.String),
        sa.column("aliases", sa.Text),
        sa.column("regex_pattern", sa.Text),
        sa.column("es_externo", sa.Boolean),
        sa.column("es_pickup", sa.Boolean),
        sa.column("prioridad_regex", sa.Integer),
    )
    op.bulk_insert(
        carriers_table,
        [
            {
                "nombre_canonico": nombre,
                "aliases": aliases,
                "regex_pattern": regex,
                "es_externo": es_externo,
                "es_pickup": es_pickup,
                "prioridad_regex": prioridad,
            }
            for nombre, aliases, regex, es_externo, es_pickup, prioridad in CARRIERS
        ]
    )


def downgrade() -> None:
    op.execute("DELETE FROM carriers")
