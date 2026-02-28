import math


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calcula la distancia haversine entre dos puntos geográficos.
    Retorna distancia en kilómetros. R = 6371 km.
    """
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def haversine_minutes(
    lat1: float, lng1: float, lat2: float, lng2: float, speed_kmh: float = 40.0
) -> float:
    """Distancia haversine convertida a tiempo estimado en minutos."""
    km = haversine(lat1, lng1, lat2, lng2)
    return (km / speed_kmh) * 60.0
