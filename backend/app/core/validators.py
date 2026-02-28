from app.core.constants import (
    MENDOZA_LAT_MIN, MENDOZA_LAT_MAX, MENDOZA_LNG_MIN, MENDOZA_LNG_MAX,
    KNOWN_CITY_CENTERS, CITY_CENTER_TOLERANCE_DEG,
)


def is_in_mendoza(lat: float, lng: float, strict: bool = False) -> bool:
    """Verifica si un punto está dentro del bounding box de Mendoza."""
    if strict:
        # Bbox más ajustado
        return (
            -33.5 <= lat <= -32.0
            and -69.5 <= lng <= -68.0
        )
    # Bbox ampliado (incluye zonas periféricas)
    return (
        MENDOZA_LAT_MIN <= lat <= MENDOZA_LAT_MAX
        and MENDOZA_LNG_MIN <= lng <= MENDOZA_LNG_MAX
    )


def is_known_city_center(lat: float, lng: float) -> bool:
    """True si las coordenadas corresponden al centro exacto de una localidad conocida."""
    for clat, clng in KNOWN_CITY_CENTERS:
        if (
            abs(lat - clat) < CITY_CENTER_TOLERANCE_DEG
            and abs(lng - clng) < CITY_CENTER_TOLERANCE_DEG
        ):
            return True
    return False


def validate_coordinates(lat: float, lng: float) -> dict:
    """Valida un par de coordenadas y retorna un dict con issues."""
    issues = []
    if lat == 0 and lng == 0:
        issues.append("Coordenadas (0, 0) — probablemente nulas")
    if not is_in_mendoza(lat, lng):
        issues.append(f"Coordenadas fuera del bounding box de Mendoza ({lat}, {lng})")
    if is_known_city_center(lat, lng):
        issues.append("Coordenadas corresponden al centro de una localidad (geocodificación genérica)")
    return {
        "valid": len(issues) == 0,
        "in_mendoza": is_in_mendoza(lat, lng),
        "issues": issues,
    }
