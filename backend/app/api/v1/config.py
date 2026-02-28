from fastapi import APIRouter, Depends, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_admin
from app.models.config import ConfigRuta
from app.models.usuario import Usuario
from app.schemas.config import ConfigRutaResponse, ConfigRutaUpdate
from app.schemas.common import OkResponse
from app.core.exceptions import not_found

router = APIRouter(prefix="/config", tags=["config"])

# Default config values
DEFAULT_CONFIG = {
    "tiempo_espera_min": ("10", "int", "Minutos de espera por parada"),
    "deposito_lat": ("-32.91973", "float", "Latitud del depósito"),
    "deposito_lng": ("-68.81829", "float", "Longitud del depósito"),
    "deposito_direccion": ("Elpidio González 2753, Guaymallén, Mendoza", "str", "Dirección del depósito"),
    "hora_desde": ("09:00", "str", "Hora inicio de entregas"),
    "hora_hasta": ("14:00", "str", "Hora fin de entregas"),
    "evitar_saltos_min": ("25", "int", "Umbral en minutos para saltos anómalos"),
    "vuelta_galpon_min": ("25", "int", "Tiempo mínimo para regresar al galpón"),
    "proveedor_matrix": ("ors", "str", "Proveedor de matrix de distancias: ors|google|mapbox"),
    "utilizar_ventana": ("true", "bool", "Filtrar por ventana horaria"),
    "distancia_max_km": ("45.0", "float", "Radio máximo de entrega en km"),
    "velocidad_urbana_kmh": ("40", "float", "Velocidad promedio urbana en km/h"),
    "dm_block_size": ("10", "int", "Tamaño de bloque para matriz de distancias"),
    "geocode_cache_days": ("30", "int", "Días de validez para caché de geocodificación"),
    "max_remitos_ruta": ("40", "int", "Máximo de remitos por ruta"),
}


@router.get("/", response_model=list[ConfigRutaResponse])
async def list_config(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    result = await db.execute(select(ConfigRuta).order_by(ConfigRuta.key))
    return result.scalars().all()


@router.get("/{key}", response_model=ConfigRutaResponse)
async def get_config(
    key: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    result = await db.execute(select(ConfigRuta).where(ConfigRuta.key == key))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise not_found(f"Config '{key}'")
    return cfg


@router.put("/{key}", response_model=ConfigRutaResponse, dependencies=[Depends(require_admin)])
async def update_config(
    key: str = Path(...),
    body: ConfigRutaUpdate = Body(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(ConfigRuta).where(ConfigRuta.key == key))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise not_found(f"Config '{key}'")
    cfg.value = body.value
    await db.commit()
    await db.refresh(cfg)
    return cfg


@router.post("/reset", response_model=OkResponse, dependencies=[Depends(require_admin)])
async def reset_config(db: AsyncSession = Depends(get_db)):
    """Restaura todos los valores de configuración a los defaults."""
    for key, (value, tipo, desc) in DEFAULT_CONFIG.items():
        result = await db.execute(select(ConfigRuta).where(ConfigRuta.key == key))
        cfg = result.scalar_one_or_none()
        if cfg:
            cfg.value = value
        else:
            cfg = ConfigRuta(key=key, value=value, tipo=tipo, descripcion=desc)
            db.add(cfg)
    await db.commit()
    return OkResponse(message="Configuración restaurada a valores default")
