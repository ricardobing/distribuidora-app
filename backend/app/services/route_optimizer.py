"""
Algoritmos de optimización de rutas.
Migra: sweepAlgorithm_(), twoOptImprove_(), tspNearestNeighbor_(),
fixpointFilterJumps_() del sistema original.
"""
import math
import logging
from dataclasses import dataclass, field
from typing import Optional

from app.core.haversine import haversine_minutes

logger = logging.getLogger(__name__)


@dataclass
class RoutePoint:
    idx: int              # Índice en la lista original
    lat: float
    lng: float
    remito_id: int
    numero: str
    cliente: str
    direccion: str
    observaciones: str
    urgente: bool
    prioridad: bool
    ventana_tipo: str     # 'AM', 'PM', 'SIN_HORARIO'
    ventana_desde_min: Optional[int] = None
    ventana_hasta_min: Optional[int] = None
    llamar_antes: bool = False


@dataclass
class OptimizedRoute:
    ordered_points: list[RoutePoint]
    excluded_idxs: list[int]
    exclusion_reasons: dict[int, str] = field(default_factory=dict)


def sweep(
    depot_lat: float,
    depot_lng: float,
    points: list[RoutePoint],
) -> list[int]:
    """
    Sweep algorithm: ordena puntos por ángulo polar desde el depósito.
    θ = atan2(lat_i - lat_dep, lng_i - lng_dep)
    Retorna lista de índices ordenados por θ ascendente.
    Equivalente a sweepAlgorithm_() del sistema original.
    """
    def polar_angle(p: RoutePoint) -> float:
        return math.atan2(p.lat - depot_lat, p.lng - depot_lng)

    indexed = [(i, polar_angle(p)) for i, p in enumerate(points)]
    indexed.sort(key=lambda x: x[1])
    return [i for i, _ in indexed]


def two_opt(
    order: list[int],
    matrix: list[list[float]],
) -> list[int]:
    """
    2-opt local search.
    Δ = [d(A,C) + d(B,D)] - [d(A,B) + d(C,D)]
    Si Δ < -1e-6 → invertir segmento [i..k].
    Itera hasta convergencia.
    Equivalente a twoOptImprove_() del sistema original.
    """
    n = len(order)
    if n < 4:
        return order

    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            for k in range(i + 2, n):
                a = order[i]
                b = order[i + 1]
                c = order[k - 1]
                d = order[k % n]
                if i == 0 and k == n - 1:
                    continue
                try:
                    delta = (matrix[a][c] + matrix[b][d]) - (matrix[a][b] + matrix[c][d])
                except IndexError:
                    continue
                if delta < -1e-6:
                    order[i + 1 : k] = reversed(order[i + 1 : k])
                    improved = True
    return order


def nearest_neighbor(
    matrix: list[list[float]],
    start: int = 0,
) -> list[int]:
    """
    TSP nearest neighbor: siempre ir al no visitado más cercano.
    Equivalente a tspNearestNeighbor_() del sistema original.
    """
    n = len(matrix)
    visited = [False] * n
    order = [start]
    visited[start] = True

    for _ in range(n - 1):
        last = order[-1]
        best_dist = float("inf")
        best_next = -1
        for j in range(n):
            if not visited[j] and matrix[last][j] < best_dist:
                best_dist = matrix[last][j]
                best_next = j
        if best_next >= 0:
            order.append(best_next)
            visited[best_next] = True

    return order


def fixpoint_filter_jumps(
    points: list[RoutePoint],
    order: list[int],
    matrix: list[list[float]],
    threshold_min: float,
    max_iterations: int = 10,
) -> tuple[list[int], list[int]]:
    """
    Filtro iterativo de saltos post-optimización.
    Excluye el punto con el mayor salto > threshold en cada iteración.
    Respeta urgentes y prioridad (nunca los excluye).
    Retorna (filtered_order, excluded_idxs).
    Equivalente a fixpointFilterJumps_() del sistema original.
    """
    excluded = []
    current_order = list(order)

    for _ in range(max_iterations):
        max_jump = 0.0
        max_jump_idx = -1

        for pos in range(1, len(current_order)):
            prev_i = current_order[pos - 1]
            curr_i = current_order[pos]
            dur = matrix[prev_i][curr_i] if matrix[prev_i][curr_i] < 9e8 else 0
            if dur > max_jump and dur > threshold_min:
                p = points[curr_i]
                if not p.urgente and not p.prioridad:
                    max_jump = dur
                    max_jump_idx = curr_i

        if max_jump_idx < 0:
            break

        excluded.append(max_jump_idx)
        current_order = [i for i in current_order if i != max_jump_idx]

    return current_order, excluded


def optimize(
    points: list[RoutePoint],
    matrix: list[list[float]],
    depot_lat: float,
    depot_lng: float,
    evitar_saltos_min: float = 25.0,
) -> OptimizedRoute:
    """
    Pipeline completo de optimización.
    1. Clasificar: URGENTE / PRI_AM / PRI_PM / NORM_AM / NORM_PM
    2. URGENTES: sweep + 2-opt
    3. PRIORIDAD: sweep only
    4. NORMALES: sweep only
    5. Concat: URG → AM_PRI → AM_NORM → PM_PRI → PM_NORM
    6. fixpoint_filter_jumps post-optimización
    """
    if not points:
        return OptimizedRoute(ordered_points=[], excluded_idxs=[])

    # Clasificar
    urgentes = [p for p in points if p.urgente]
    pri_am = [p for p in points if not p.urgente and p.prioridad and p.ventana_tipo == "AM"]
    pri_pm = [p for p in points if not p.urgente and p.prioridad and p.ventana_tipo == "PM"]
    pri_sin = [p for p in points if not p.urgente and p.prioridad and p.ventana_tipo == "SIN_HORARIO"]
    norm_am = [p for p in points if not p.urgente and not p.prioridad and p.ventana_tipo == "AM"]
    norm_pm = [p for p in points if not p.urgente and not p.prioridad and p.ventana_tipo == "PM"]
    norm_sin = [p for p in points if not p.urgente and not p.prioridad and p.ventana_tipo == "SIN_HORARIO"]

    def sort_group(group: list[RoutePoint]) -> list[RoutePoint]:
        """Sweep por grupo."""
        if not group:
            return []
        idxs = sweep(depot_lat, depot_lng, group)
        return [group[i] for i in idxs]

    # Urgentes: sweep + 2-opt
    urg_sorted = sort_group(urgentes)
    if len(urg_sorted) >= 4:
        local_matrix = _sub_matrix(matrix, [p.idx for p in urg_sorted], points)
        local_order = two_opt(list(range(len(urg_sorted))), local_matrix)
        urg_sorted = [urg_sorted[i] for i in local_order]

    # Resto: sweep only
    ordered = (
        urg_sorted
        + sort_group(pri_am)
        + sort_group(pri_sin)
        + sort_group(norm_am)
        + sort_group(norm_sin)
        + sort_group(pri_pm)
        + sort_group(norm_pm)
    )

    # Fixpoint filter
    order_idxs = [p.idx for p in ordered]
    filtered_idxs, excluded_idxs = fixpoint_filter_jumps(
        points, order_idxs, matrix, evitar_saltos_min
    )

    ordered_points = [points[i] for i in filtered_idxs]
    return OptimizedRoute(
        ordered_points=ordered_points,
        excluded_idxs=excluded_idxs,
        exclusion_reasons={i: "salto" for i in excluded_idxs},
    )


def _sub_matrix(
    full_matrix: list[list[float]],
    global_idxs: list[int],
    points: list[RoutePoint],
) -> list[list[float]]:
    """Extrae sub-matriz para un subconjunto de puntos."""
    n = len(global_idxs)
    sub = [[0.0] * n for _ in range(n)]
    for i, gi in enumerate(global_idxs):
        for j, gj in enumerate(global_idxs):
            if gi < len(full_matrix) and gj < len(full_matrix[gi]):
                sub[i][j] = full_matrix[gi][gj]
    return sub
