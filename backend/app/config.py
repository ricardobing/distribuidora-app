from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/molymarket"

    # Auth
    SECRET_KEY: str = "changeme-use-a-real-secret-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 horas
    ALGORITHM: str = "HS256"

    # API Keys
    GOOGLE_MAPS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ORS_API_KEY: str = ""
    MAPBOX_TOKEN: str = ""

    # QR Token (para autenticación de escaneo)
    QR_TOKEN: str = "changeme-qr-token"

    # Geocoding
    GEOCODE_PROVIDER_ORDER: List[str] = ["ors", "mapbox", "google"]
    MENDOZA_LAT_MIN: float = -33.5
    MENDOZA_LAT_MAX: float = -32.0
    MENDOZA_LNG_MIN: float = -69.5
    MENDOZA_LNG_MAX: float = -68.0

    # Distance Matrix
    DM_BLOCK_SIZE: int = 10
    DM_CACHE_TTL_SECONDS: int = 21600  # 6h
    DM_MAX_DESTINATIONS: int = 25

    # Route defaults (se pueden overridear por config_ruta en DB)
    DEFAULT_DEPOT_LAT: float = -32.91973
    DEFAULT_DEPOT_LNG: float = -68.81829
    MAX_DISTANCE_KM: float = 45.0
    URBAN_SPEED_KMH: float = 40.0

    # OpenAI
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.0
    AI_CONFIDENCE_THRESHOLD: float = 0.99
    AI_CANON_THRESHOLD: float = 0.92

    # Legacy compat (Google Sheets ID - solo para migración)
    PEDIDOS_LISTOS_SPREADSHEET_ID: str = ""

    # App
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "https://molymarket.vercel.app",
        "http://localhost:3000",
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
