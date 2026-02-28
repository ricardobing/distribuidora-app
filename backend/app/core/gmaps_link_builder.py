"""
Builds Google Maps route links respecting the 10-waypoint limit.

Google Maps URL format:
https://www.google.com/maps/dir/?api=1&origin=LAT,LNG&destination=LAT,LNG&waypoints=LAT,LNG|LAT,LNG|...
"""
from typing import Optional
import urllib.parse


def build_gmaps_links(
    stops: list[dict],  # [{"lat": float, "lng": float, "label": str}, ...]
    depot_lat: float,
    depot_lng: float,
    max_waypoints: int = 10,
) -> list[str]:
    """
    Fragmenta la lista de paradas en links de Google Maps con max_waypoints waypoints.
    El depósito actúa como origin del primer tramo y destino del último.
    """
    if not stops:
        return []

    links = []
    # Fragmentar en grupos de max_waypoints+1 puntos (origin+N waypoints+destination)
    # Cada fragmento: origin=prev_last, waypoints=stops[i:i+max_waypoints-1], destination=stops[i+max_waypoints-1]
    all_points = stops[:]
    chunk_size = max_waypoints  # N waypoints por tramo

    i = 0
    while i < len(all_points):
        chunk = all_points[i : i + chunk_size]
        if i == 0:
            origin = f"{depot_lat},{depot_lng}"
        else:
            prev = all_points[i - 1]
            origin = f"{prev['lat']},{prev['lng']}"

        if i + chunk_size >= len(all_points):
            # Último tramo — destino = depósito
            destination = f"{depot_lat},{depot_lng}"
        else:
            last = chunk[-1]
            destination = f"{last['lat']},{last['lng']}"
            chunk = chunk[:-1]  # El último del chunk pasa a ser destination

        waypoints = "|".join(f"{p['lat']},{p['lng']}" for p in chunk[:-1] if chunk) if len(chunk) > 1 else ""
        # Simplificado: origin → waypoints → destination
        waypoints_all = "|".join(f"{p['lat']},{p['lng']}" for p in chunk)

        params: dict[str, str] = {
            "api": "1",
            "origin": origin,
            "destination": destination,
        }
        if waypoints_all:
            params["waypoints"] = waypoints_all

        url = "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(params)
        links.append(url)
        i += chunk_size

    return links
