from fastapi import APIRouter

from app.api.v1 import (
    auth, remitos, carriers, rutas, qr,
    entregados, historico, config, geocode,
    pedidos_listos, dashboard, billing
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(remitos.router)
api_router.include_router(carriers.router)
api_router.include_router(rutas.router)
api_router.include_router(qr.router)
api_router.include_router(entregados.router)
api_router.include_router(historico.router)
api_router.include_router(config.router)
api_router.include_router(geocode.router)
api_router.include_router(pedidos_listos.router)
api_router.include_router(dashboard.router)
api_router.include_router(billing.router)
