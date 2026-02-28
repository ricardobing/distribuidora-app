from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"MolyMarket API v{settings.APP_VERSION} iniciando...")
    # Startup: verificar conexión DB
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("Conexión a base de datos OK")
    except Exception as e:
        logger.error(f"Error de conexión a DB: {e}")
        raise
    yield
    # Shutdown
    await engine.dispose()
    logger.info("MolyMarket API shutdown completo")


app = FastAPI(
    title="MolyMarket API",
    version=settings.APP_VERSION,
    description="Sistema de distribución de alimentos — Mendoza, Argentina",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.router import api_router  # noqa: E402
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
