from pydantic import BaseModel
from typing import Optional


class ConfigRutaResponse(BaseModel):
    key: str
    value: str
    tipo: str
    descripcion: Optional[str] = None

    model_config = {"from_attributes": True}


class ConfigRutaUpdate(BaseModel):
    value: str


class ConfigRutaBulkUpdate(BaseModel):
    items: list[dict]
