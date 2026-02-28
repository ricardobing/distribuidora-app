"""
Route generation service: orquestador completo.
Migra: generarRutaDesdeFraccionados_() del sistema original.
"""
import logging
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.remito import Remito, RemitoEstadoClasificacion, RemitoEstadoLifecycle
from app.models.ruta import Ruta, RutaParada, RutaExcluido, RutaEstado, ParadaEstado
from app.models.config import ConfigRuta
from app.services import distance_matrix_service, route_optimizer, window_service
from app.services.distance_matrix_service import MatrixPoint
from app.services.route_optimizer import RoutePoint
from app.core.haversine import haversine, haversine_minutes
from app.core.constants import (
    DEPOT_LAT, DEPOT_LNG, MAX_DISTANCE_FROM_DEPOT_KM, URBAN_SPEED_KMH,
)
from app.core.gmaps_link_builder import build_gmaps_links

logger = logging.getLogger(__name__)


async def generate_route(
    db: AsyncSession,
    config_override: Optional[dict] = None,
) -> Ruta:
    """Pipeline completo de generación de ruta."""
    # 1. Cargar configuración
    config = await _load_config(db)
    if config_override:
        if hasattr(config_override, "model_dump"):
            config.update({k: v for k, v in config_override.model_dump().items() if v is not None})
        elif isinstance(config_override, dict):
            config.update({k: v for k, v in config_override.items() if v is not None})

    depot_lat = float(config.get("deposito_lat", DEPOT_LAT))
    depot_lng = float(config.get("deposito_lng", DEPOT_LNG))
    hora_desde = config.get("hora_desde", "09:00")
    hora_hasta = config.get("hora_hasta", "14:00")
    evitar_saltos_min = float(config.get("evitar_saltos_min", 25))
    vuelta_galpon_min = float(config.get("vuelta_galpon_min", 25))
    distancia_max_km = float(config.get("distancia_max_km", MAX_DISTANCE_FROM_DEPOT_KM))
    tiempo_espera_min = float(config.get("tiempo_espera_min", 10))
    utilizar_ventana = str(config.get("utilizar_ventana", "true")).lower() in ("true", "1", "yes")
    proveedor_matrix = config.get("proveedor_matrix", "ors")

    # 2. Cargar candidatos (enviar + armado + lat/lng not null)
    result = await db.execute(
        select(Remito).where(
            Remito.estado_clasificacion == RemitoEstadoClasificacion.enviar.value,
            Remito.estado_lifecycle == RemitoEstadoLifecycle.armado.value,
            Remito.lat.isnot(None),
            Remito.lng.isnot(None),
        )
    )
    candidates_raw = result.scalars().all()

    if not candidates_raw:
        ruta = Ruta(
            fecha=date.today(),
            estado=RutaEstado.generada.value,
            config_snapshot=config,
            deposito_lat=depot_lat,
            deposito_lng=depot_lng,
            total_paradas=0,
            total_excluidos=0,
            gmaps_links=[],
        )
        db.add(ruta)
        await db.commit()
        await db.refresh(ruta)
        return ruta

    # Convertir a RoutePoints
    all_points: list[RoutePoint] = []
    for r in candidates_raw:
        if r.lat is None or r.lng is None:
            continue
        all_points.append(RoutePoint(
            idx=len(all_points),
            lat=r.lat,
            lng=r.lng,
            remito_id=r.id,
            numero=r.numero,
            cliente=r.cliente or "",
            direccion=r.direccion_normalizada or r.direccion_raw or "",
            observaciones=r.observaciones or "",
            urgente=r.es_urgente,
            prioridad=r.es_prioridad,
            ventana_tipo=r.ventana_tipo or "SIN_HORARIO",
            ventana_desde_min=r.ventana_desde_min,
            ventana_hasta_min=r.ventana_hasta_min,
            llamar_antes=r.llamar_antes,
        ))

    excluded_idxs: list[int] = []
    exclusion_reasons: dict[int, str] = {}

    # 3. Filtro de distancia máxima
    for i, p in enumerate(all_points):
        dist = haversine(depot_lat, depot_lng, p.lat, p.lng)
        if dist > distancia_max_km and not p.urgente and not p.prioridad:
            excluded_idxs.append(i)
            exclusion_reasons[i] = f"distancia_maxima ({dist:.1f} km > {distancia_max_km} km)"

    # 4. Filtro de ventana horaria
    if utilizar_ventana:
        for i, p in enumerate(all_points):
            if i in excluded_idxs or p.urgente:
                continue
            w = window_service.WindowResult(
                tipo=p.ventana_tipo,
                desde_min=p.ventana_desde_min,
                hasta_min=p.ventana_hasta_min,
                ventana_tipo=p.ventana_tipo,
            )
            if not window_service.is_within_config_window(w, hora_desde, hora_hasta):
                excluded_idxs.append(i)
                exclusion_reasons[i] = "ventana_horaria"

    # 5. Filtro de vuelta al galpón
    for i, p in enumerate(all_points):
        if i in excluded_idxs or p.urgente or p.prioridad:
            continue
        time_vuelta = haversine_minutes(p.lat, p.lng, depot_lat, depot_lng, URBAN_SPEED_KMH)
        if time_vuelta > vuelta_galpon_min:
            excluded_idxs.append(i)
            exclusion_reasons[i] = f"vuelta_galpon ({time_vuelta:.1f} min > {vuelta_galpon_min} min)"

    active_points = [p for i, p in enumerate(all_points) if i not in excluded_idxs]

    if not active_points:
        ruta = Ruta(
            fecha=date.today(),
            estado=RutaEstado.generada.value,
            config_snapshot=config,
            deposito_lat=depot_lat,
            deposito_lng=depot_lng,
            total_paradas=0,
            total_excluidos=len(excluded_idxs),
            gmaps_links=[],
        )
        db.add(ruta)
        await db.flush()
        await _save_excluded(db, ruta.id, all_points, excluded_idxs, exclusion_reasons, candidates_raw)
        await db.commit()
        await db.refresh(ruta)
        return ruta

    # 6. Distance Matrix NxN
    matrix_points = [MatrixPoint(lat=p.lat, lng=p.lng, label=p.numero) for p in active_points]
    try:
        matrix = await distance_matrix_service.get_matrix_nxn(
            db, matrix_points, provider=proveedor_matrix
        )
    except Exception as e:
        logger.warning(f"DM API failed, usando Haversine fallback: {e}")
        n = len(active_points)
        matrix = [[
            haversine_minutes(
                active_points[i].lat, active_points[i].lng,
                active_points[j].lat, active_points[j].lng,
                URBAN_SPEED_KMH
            ) if i != j else 0.0
            for j in range(n)
        ] for i in range(n)]

    # 7. Optimizar ruta
    opt_result = route_optimizer.optimize(
        active_points, matrix, depot_lat, depot_lng, evitar_saltos_min
    )

    for i in opt_result.excluded_idxs:
        orig_idx = active_points[i].idx
        if orig_idx not in excluded_idxs:
            excluded_idxs.append(orig_idx)
        exclusion_reasons[orig_idx] = opt_result.exclusion_reasons.get(i, "salto")

    final_points = opt_result.ordered_points

    # 8. Calcular tiempos acumulados
    minutes_accumulated = 0.0
    total_distance = 0.0
    paradas_data = []

    for i, p in enumerate(final_points):
        p_idx_in_active = next(
            (j for j, ap in enumerate(active_points) if ap.idx == p.idx), 0
        )
        if i == 0:
            dur = haversine_minutes(depot_lat, depot_lng, p.lat, p.lng, URBAN_SPEED_KMH)
            dist = haversine(depot_lat, depot_lng, p.lat, p.lng)
        else:
            prev_p = final_points[i - 1]
            prev_idx_in_active = next(
                (j for j, ap in enumerate(active_points) if ap.idx == prev_p.idx), 0
            )
            try:
                dur = matrix[prev_idx_in_active][p_idx_in_active]
            except IndexError:
                dur = haversine_minutes(prev_p.lat, prev_p.lng, p.lat, p.lng, URBAN_SPEED_KMH)
            dist = haversine(prev_p.lat, prev_p.lng, p.lat, p.lng)

        minutes_accumulated += dur + tiempo_espera_min
        total_distance += dist
        paradas_data.append({
            "point": p,
            "minutos_desde_anterior": dur,
            "tiempo_espera_min": tiempo_espera_min,
            "minutos_acumulados": minutes_accumulated,
            "distancia_km": dist,
        })

    # 9. Google Maps links
    stops_for_gmaps = [{"lat": p.lat, "lng": p.lng, "label": p.numero} for p in final_points]
    gmaps_links = build_gmaps_links(stops_for_gmaps, depot_lat, depot_lng)

    # 10. GeoJSON LineString para la ruta
    coords = [(depot_lng, depot_lat)] + [(p.lng, p.lat) for p in final_points] + [(depot_lng, depot_lat)]
    ruta_geom_json = None
    if len(coords) >= 2:
        ruta_geom_json = {
            "type": "LineString",
            "coordinates": coords
        }

    # 11. Guardar ruta
    ruta = Ruta(
        fecha=date.today(),
        estado=RutaEstado.generada.value,
        config_snapshot=config,
        deposito_lat=depot_lat,
        deposito_lng=depot_lng,
        total_paradas=len(final_points),
        total_excluidos=len(excluded_idxs),
        duracion_estimada_min=int(minutes_accumulated),
        distancia_total_km=round(total_distance, 2),
        gmaps_links=gmaps_links,
        ruta_geom=ruta_geom_json,
    )
    db.add(ruta)
    await db.flush()

    # Guardar paradas
    for orden, pd in enumerate(paradas_data, start=1):
        p = pd["point"]
        remito_obj = next((r for r in candidates_raw if r.id == p.remito_id), None)
        parada = RutaParada(
            ruta_id=ruta.id,
            remito_id=p.remito_id,
            remito_numero=p.numero,
            orden=orden,
            lat_snapshot=p.lat,
            lng_snapshot=p.lng,
            cliente_snapshot=p.cliente,
            direccion_snapshot=p.direccion,
            observaciones_snapshot=p.observaciones,
            minutos_desde_anterior=pd["minutos_desde_anterior"],
            tiempo_espera_min=pd["tiempo_espera_min"],
            minutos_acumulados=pd["minutos_acumulados"],
            distancia_desde_anterior_km=pd["distancia_km"],
            es_urgente=p.urgente,
            es_prioridad=p.prioridad,
            ventana_tipo=p.ventana_tipo,
            estado=ParadaEstado.pendiente.value,
        )
        db.add(parada)

    # Guardar excluidos
    await _save_excluded(db, ruta.id, all_points, excluded_idxs, exclusion_reasons, candidates_raw)

    await db.commit()
    await db.refresh(ruta)
    return ruta


async def _save_excluded(
    db: AsyncSession,
    ruta_id: int,
    all_points: list[RoutePoint],
    excluded_idxs: list[int],
    exclusion_reasons: dict[int, str],
    candidates_raw: list[Remito],
) -> None:
    seen = set()
    for idx in excluded_idxs:
        if idx in seen or idx >= len(all_points):
            continue
        seen.add(idx)
        p = all_points[idx]
        remito_obj = next((r for r in candidates_raw if r.id == p.remito_id), None)
        exc = RutaExcluido(
            ruta_id=ruta_id,
            remito_id=p.remito_id,
            remito_numero=p.numero,
            cliente_snapshot=p.cliente,
            direccion_snapshot=p.direccion,
            motivo=exclusion_reasons.get(idx, "desconocido"),
            observaciones_snapshot=p.observaciones,
        )
        db.add(exc)


async def _load_config(db: AsyncSession) -> dict:
    """Carga la configuración de ruta desde DB."""
    result = await db.execute(select(ConfigRuta))
    rows = result.scalars().all()
    config: dict = {}
    for row in rows:
        if row.tipo in ("int", "integer"):
            config[row.key] = int(row.value)
        elif row.tipo == "float":
            config[row.key] = float(row.value)
        elif row.tipo in ("bool", "boolean"):
            config[row.key] = row.value.lower() in ("true", "1", "yes", "si")
        else:
            config[row.key] = row.value
    return config
