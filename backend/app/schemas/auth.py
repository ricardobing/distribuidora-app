from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    email: str
    rol: str


class UserCreate(BaseModel):
    email: str
    password: str
    nombre: Optional[str] = None
    rol: str = "operador"


class UserResponse(BaseModel):
    id: int
    email: str
    nombre: Optional[str] = None
    rol: str
    activo: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None
