"""001 initial schema — source of truth

Revision ID: 001
Revises:
Create Date: 2026-02-28 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology")

    # ── usuarios ──────────────────────────────────────────────────────────
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nombre", sa.String(200)),
        sa.Column("rol", sa.String(50), nullable=False, server_default="operador"),
        sa.Column("activo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── carriers ──────────────────────────────────────────────────────────
    op.create_table(
        "carriers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("nombre_canonico", sa.String(200), nullable=False, unique=True),
        sa.Column("aliases", postgresql.JSONB, server_default="[]"),
        sa.Column("regex_pattern", sa.Text),
        sa.Column("es_externo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("es_pickup", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("activo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("prioridad_regex", sa.Integer, nullable=False, server_default="50"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── remitos ───────────────────────────────────────────────────────────
    op.create_table(
        "remitos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("numero", sa.String(100), nullable=False, unique=True),
        sa.Column("cliente", sa.String(500)),
        sa.Column("direccion_raw", sa.Text),
        sa.Column("direccion_normalizada", sa.Text),
        sa.Column("localidad", sa.String(200)),
        sa.Column("observaciones", sa.Text),
        sa.Column("lat", sa.Float),
        sa.Column("lng", sa.Float),
        sa.Column("geocode_provider", sa.String(50)),
        sa.Column("geocode_score", sa.Float),
        sa.Column("geocode_formatted", sa.Text),
        sa.Column("estado_clasificacion", sa.String(50), nullable=False, server_default="pendiente"),
        sa.Column("estado_lifecycle", sa.String(50), nullable=False, server_default="ingresado"),
        sa.Column("motivo_clasificacion", sa.Text),
        sa.Column("carrier_id", sa.Integer, sa.ForeignKey("carriers.id", ondelete="SET NULL")),
        sa.Column("ventana_raw", sa.Text),
        sa.Column("ventana_tipo", sa.String(50)),
        sa.Column("ventana_desde_min", sa.Integer),
        sa.Column("ventana_hasta_min", sa.Integer),
        sa.Column("llamar_antes", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("es_urgente", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("es_prioridad", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("pipeline_error", sa.Text),
        sa.Column("source", sa.String(100), server_default="manual"),
        sa.Column("fecha_ingreso", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("fecha_armado", sa.DateTime(timezone=True)),
        sa.Column("fecha_entregado", sa.DateTime(timezone=True)),
        sa.Column("fecha_historico", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_remitos_numero", "remitos", ["numero"])
    op.create_index("ix_remitos_estado_clasificacion", "remitos", ["estado_clasificacion"])
    op.create_index("ix_remitos_estado_lifecycle", "remitos", ["estado_lifecycle"])
    op.execute(
        "CREATE INDEX ix_remitos_lat_lng ON remitos (lat, lng) "
        "WHERE lat IS NOT NULL AND lng IS NOT NULL"
    )

    # ── pedidos_listos ────────────────────────────────────────────────────
    op.create_table(
        "pedidos_listos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("numero_remito", sa.String(100), nullable=False, unique=True),
        sa.Column("raw_data", postgresql.JSONB, server_default="{}"),
        sa.Column("linked_remito_id", sa.Integer, sa.ForeignKey("remitos.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── rutas ─────────────────────────────────────────────────────────────
    op.create_table(
        "rutas",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("fecha", sa.Date, nullable=False),
        sa.Column("estado", sa.String(50), nullable=False, server_default="generando"),
        sa.Column("total_paradas", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_excluidos", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duracion_estimada_min", sa.Integer),
        sa.Column("distancia_total_km", sa.Float),
        sa.Column("gmaps_links", postgresql.JSONB, server_default="[]"),
        sa.Column("ruta_geom", postgresql.JSONB),
        sa.Column("config_snapshot", postgresql.JSONB, server_default="{}"),
        sa.Column("api_cost_estimate", sa.Float, server_default="0"),
        sa.Column("billing_detail", postgresql.JSONB),
        sa.Column("deposito_lat", sa.Float),
        sa.Column("deposito_lng", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_rutas_fecha", "rutas", ["fecha"])

    # ── ruta_paradas ──────────────────────────────────────────────────────
    op.create_table(
        "ruta_paradas",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ruta_id", sa.Integer, sa.ForeignKey("rutas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("remito_id", sa.Integer, sa.ForeignKey("remitos.id", ondelete="SET NULL")),
        sa.Column("remito_numero", sa.String(100)),
        sa.Column("orden", sa.Integer, nullable=False),
        sa.Column("lat_snapshot", sa.Float),
        sa.Column("lng_snapshot", sa.Float),
        sa.Column("cliente_snapshot", sa.String(500)),
        sa.Column("direccion_snapshot", sa.Text),
        sa.Column("observaciones_snapshot", sa.Text),
        sa.Column("minutos_desde_anterior", sa.Float),
        sa.Column("tiempo_espera_min", sa.Float, server_default="10"),
        sa.Column("minutos_acumulados", sa.Float),
        sa.Column("distancia_desde_anterior_km", sa.Float),
        sa.Column("es_urgente", sa.Boolean, server_default="false"),
        sa.Column("es_prioridad", sa.Boolean, server_default="false"),
        sa.Column("ventana_tipo", sa.String(50)),
        sa.Column("estado", sa.String(50), server_default="pendiente"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_ruta_paradas_ruta_id", "ruta_paradas", ["ruta_id"])

    # ── ruta_excluidos ────────────────────────────────────────────────────
    op.create_table(
        "ruta_excluidos",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ruta_id", sa.Integer, sa.ForeignKey("rutas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("remito_id", sa.Integer, sa.ForeignKey("remitos.id", ondelete="SET NULL")),
        sa.Column("remito_numero", sa.String(100)),
        sa.Column("cliente_snapshot", sa.String(500)),
        sa.Column("direccion_snapshot", sa.Text),
        sa.Column("motivo", sa.String(200), nullable=False),
        sa.Column("distancia_km", sa.Float),
        sa.Column("observaciones_snapshot", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_ruta_excluidos_ruta_id", "ruta_excluidos", ["ruta_id"])

    # ── geo_cache ─────────────────────────────────────────────────────────
    op.create_table(
        "geo_cache",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("key_normalizada", sa.String(512), nullable=False, unique=True),
        sa.Column("query_original", sa.Text, nullable=False),
        sa.Column("lat", sa.Float, nullable=False),
        sa.Column("lng", sa.Float, nullable=False),
        sa.Column("formatted_address", sa.Text),
        sa.Column("has_street_number", sa.Boolean, server_default="false"),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("score", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_geo_cache_key", "geo_cache", ["key_normalizada"])

    # ── distance_matrix_cache ─────────────────────────────────────────────
    op.create_table(
        "distance_matrix_cache",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("origin_lat", sa.Float, nullable=False),
        sa.Column("origin_lng", sa.Float, nullable=False),
        sa.Column("dest_lat", sa.Float, nullable=False),
        sa.Column("dest_lng", sa.Float, nullable=False),
        sa.Column("duration_sec", sa.Float, nullable=False),
        sa.Column("distance_m", sa.Float),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── historico_entregados ──────────────────────────────────────────────
    op.create_table(
        "historico_entregados",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("remito_id", sa.Integer, sa.ForeignKey("remitos.id", ondelete="SET NULL")),
        sa.Column("numero", sa.String(100), nullable=False),
        sa.Column("cliente", sa.String(500)),
        sa.Column("direccion_snapshot", sa.Text),
        sa.Column("localidad", sa.String(200)),
        sa.Column("observaciones", sa.Text),
        sa.Column("lat", sa.Float),
        sa.Column("lng", sa.Float),
        sa.Column("carrier_nombre", sa.String(200)),
        sa.Column("es_urgente", sa.Boolean, server_default="false"),
        sa.Column("es_prioridad", sa.Boolean, server_default="false"),
        sa.Column("obs_entrega", sa.Text),
        sa.Column("estado_al_archivar", sa.String(50)),
        sa.Column("fecha_ingreso", sa.DateTime(timezone=True)),
        sa.Column("fecha_armado", sa.DateTime(timezone=True)),
        sa.Column("fecha_entregado", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_archivado", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("mes_cierre", sa.String(7), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_historico_mes_cierre", "historico_entregados", ["mes_cierre"])
    op.create_index("ix_historico_numero", "historico_entregados", ["numero"])

    # ── audit_log ─────────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
        sa.Column("accion", sa.String(100), nullable=False),
        sa.Column("entidad", sa.String(100)),
        sa.Column("entidad_id", sa.Integer),
        sa.Column("detalle", postgresql.JSONB, server_default="{}"),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── billing_traces ────────────────────────────────────────────────────
    op.create_table(
        "billing_traces",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(100)),
        sa.Column("stage", sa.String(100)),
        sa.Column("service", sa.String(100), nullable=False),
        sa.Column("sku", sa.String(100)),
        sa.Column("units", sa.Integer, server_default="1"),
        sa.Column("estimated_cost", sa.Float, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── config_ruta ───────────────────────────────────────────────────────
    op.create_table(
        "config_ruta",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False, server_default="str"),
        sa.Column("descripcion", sa.Text),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("config_ruta")
    op.drop_table("billing_traces")
    op.drop_table("audit_log")
    op.drop_table("historico_entregados")
    op.drop_table("distance_matrix_cache")
    op.drop_table("geo_cache")
    op.drop_table("ruta_excluidos")
    op.drop_table("ruta_paradas")
    op.drop_table("rutas")
    op.drop_table("pedidos_listos")
    op.drop_table("remitos")
    op.drop_table("carriers")
    op.drop_table("usuarios")
