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

    def validate_for_production(self) -> None:
        """Aborta el inicio si la configuracion es insegura en produccion."""
        if self.ENVIRONMENT != "production":
            return

        weak_keys = {
            "changeme-use-a-real-secret-in-production",
            "change-me-in-production-at-least-32-chars",
            "change-me",
            "secret",
            "",
        }
        if any(self.SECRET_KEY.startswith(w) for w in weak_keys) or len(self.SECRET_KEY) < 32:
            raise RuntimeError(
                "SECRET_KEY inseguro en produccion. "
                "Generar con: python -c 'import secrets; print(secrets.token_hex(32))'"
            )

        # Extraer password de DATABASE_URL para validarlo
        from urllib.parse import urlparse
        parsed = urlparse(self.DATABASE_URL.replace("+asyncpg", ""))
        db_password = parsed.password or ""
        if db_password in ("", "molypass", "postgres", "password"):
            raise RuntimeError(
                "La password de PostgreSQL en DATABASE_URL es insegura para produccion. "
                "Usar una password fuerte y unica."
            )


settings = Settings()
