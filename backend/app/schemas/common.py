from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    pages: int
    size: int


class ErrorResponse(BaseModel):
    detail: str


class OkResponse(BaseModel):
    ok: bool = True
    message: Optional[str] = None
