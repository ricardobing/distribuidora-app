"""002 seed carriers

Revision ID: 002
Revises: 001
Create Date: 2026-02-28 00:01:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (nombre_canonico, aliases_json_str, regex_pattern, es_externo, es_pickup, prioridad_regex)
CARRIERS = [
    ("RETIRO EN GALPON",
     '["retiro galpon","retira","retira en galpon","busca","viene a buscar","pickup"]',
     r"(?i)(retir[ao]\s+(en\s+)?gal[oó]?n|retira\s+en\s+dep[oó]sito|pasa\s+a\s+(buscar|retirar))",
     False, True, 10),
    ("ANDREANI", '["andreani","andreanni","andreani"]',
     r"(?i)andreani", True, False, 20),
    ("OCA", '["oca","o.c.a."]',
     r"(?i)\boca\b", True, False, 20),
    ("CORREO ARGENTINO", '["correo","correo argentino","correo arg"]',
     r"(?i)(correo\s+argentino|^correo$)", True, False, 20),
    ("VIA CARGO", '["via cargo","viacargo","via_cargo"]',
     r"(?i)via\s*cargo", True, False, 20),
    ("URBANO", '["urbano","urbano express","urbano exp"]',
     r"(?i)urbano(\s+express)?", True, False, 20),
    ("LAAR", '["laar","laarcourier"]',
     r"(?i)\blaar\b", True, False, 20),
    ("TUPUY", '["tupuy","tu puy"]',
     r"(?i)tupuy", True, False, 20),
    ("SERVIENTREGA", '["servientrega","servi entrega"]',
     r"(?i)servientrega", True, False, 20),
    ("MOOVA", '["moova","muuva"]',
     r"(?i)moova", True, False, 20),
    ("RAPPI", '["rappi","rapi"]',
     r"(?i)rappi", True, False, 20),
    ("PEDIDOS YA", '["pedidos ya","pedidosya","pya"]',
     r"(?i)pedidos\s*ya", True, False, 20),
    ("MERCADO ENVIOS",
     '["mercado envios","mercadoenvios","ml envios","meli envios"]',
     r"(?i)mercado\s+env[i]os", True, False, 20),
    ("ENVIO PROPIO",
     '["envio propio","propio","reparto propio","repartidor propio"]',
     r"(?i)(envio\s+propio|reparto\s+propio|repartidor\s+propio)", False, False, 30),
    ("DESCONOCIDO", '[]', None, True, False, 99),
]


def upgrade() -> None:
    # Use raw SQL with explicit CAST to avoid type mismatch with JSONB
    for nombre, aliases, regex, es_externo, es_pickup, prioridad in CARRIERS:
        op.execute(sa.text(
            "INSERT INTO carriers "
            "(nombre_canonico, aliases, regex_pattern, es_externo, es_pickup, activo, prioridad_regex) "
            "VALUES (:nombre, CAST(:aliases AS jsonb), :regex, :es_externo, :es_pickup, TRUE, :prioridad) "
            "ON CONFLICT (nombre_canonico) DO NOTHING"
        ).bindparams(
            nombre=nombre,
            aliases=aliases,
            regex=regex,
            es_externo=es_externo,
            es_pickup=es_pickup,
            prioridad=prioridad,
        ))


def downgrade() -> None:
    op.execute("DELETE FROM carriers")
