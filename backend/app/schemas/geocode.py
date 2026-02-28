from pydantic import BaseModel
from typing import Optional


class GeocodeRequest(BaseModel):
    address: str
    provider: Optional[str] = None  # "ors" | "mapbox" | "google" | None (cascade)


class GeocodeResponse(BaseModel):
    address_input: str
    lat: float
    lng: float
    display_name: Optional[str] = None
    provider: str
    score: Optional[float] = None
    from_cache: bool = False


class GeocodeValidateRequest(BaseModel):
    lat: float
    lng: float


class GeocodeValidateResponse(BaseModel):
    in_bbox: bool
    is_city_center: bool
    is_valid: bool
    message: Optional[str] = None


class GeocodeStatsResponse(BaseModel):
    total_entries: int
    by_provider: dict[str, int]
    expired: int
    hit_rate: Optional[float] = None


class GeocodeBatchRequest(BaseModel):
    addresses: list[str]
    provider: Optional[str] = None
