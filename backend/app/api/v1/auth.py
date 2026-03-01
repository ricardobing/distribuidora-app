"""
Router de autenticación y gestión de usuarios.
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_admin
from app.models.usuario import Usuario
from app.schemas.auth import (
    LoginRequest, TokenResponse, UserCreate, UserResponse,
    PasswordChange, UserUpdate,
)
from app.schemas.common import OkResponse
from app.core.security import (
    hash_password, verify_password, create_access_token,
)
from app.config import settings
from app.main import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Autentica usuario y devuelve JWT. Limite: 10 intentos por minuto por IP."""
    result = await db.execute(
        select(Usuario).where(Usuario.email == body.email.lower().strip())
    )
    user = result.scalar_one_or_none()

    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.id, expires_delta=expires)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        email=user.email,
        rol=user.rol,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: Usuario = Depends(get_current_user)):
    """Retorna el usuario autenticado."""
    return current_user


@router.put("/me/password", response_model=OkResponse)
async def change_password(
    body: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Cambia contraseña del usuario autenticado."""
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta",
        )
    current_user.password_hash = hash_password(body.new_password)
    await db.commit()
    return OkResponse(message="Contraseña actualizada correctamente")


# ---------------------------------------------------------------------------
# Gestión de usuarios (solo admin)
# ---------------------------------------------------------------------------

@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_admin)])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).order_by(Usuario.id))
    return result.scalars().all()


@router.post("/users", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Usuario).where(Usuario.email == body.email.lower().strip())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{body.email}' ya registrado",
        )
    user = Usuario(
        email=body.email.lower().strip(),
        nombre=body.nombre or body.email.split("@")[0],
        password_hash=hash_password(body.password),
        rol=body.rol,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user(
    user_id: int = Path(...),
    body: UserUpdate = ...,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if body.nombre is not None:
        user.nombre = body.nombre
    if body.rol is not None:
        user.rol = body.rol
    if body.activo is not None:
        user.activo = body.activo
    await db.commit()
    await db.refresh(user)
    return user
