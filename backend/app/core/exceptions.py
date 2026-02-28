from fastapi import HTTPException, status


class MolyMarketException(Exception):
    """Base exception del sistema."""
    pass


class RemitoNotFound(MolyMarketException):
    pass


class RemitoAlreadyExists(MolyMarketException):
    pass


class InvalidStateTransition(MolyMarketException):
    """Transición de estado no permitida (ej: ENTREGADO sin ARMADO)."""
    pass


class GeocodeError(MolyMarketException):
    pass


class RouteGenerationError(MolyMarketException):
    pass


class ExternalAPIError(MolyMarketException):
    """Error de una API externa (ORS, Mapbox, Google, OpenAI)."""
    pass


# HTTP exceptions listas para usar en routers
def not_found(entity: str = "Recurso") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entity} no encontrado",
    )


def bad_request(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def conflict(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )
