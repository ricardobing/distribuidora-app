from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_admin
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse, PasswordChange, UserUpdate
from app.core.security import verify_password, create_access_token, hash_password
from app.core.exceptions import not_found, bad_request
from app.models.usuario import Usuario, UserRol
from app.config import settings
from sqlalchemy import select, update as sql_update
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    if not user.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario desactivado")
    token = create_access_token(
        data={"sub": str(user.id), "rol": user.rol},
        expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user_id=user.id,
        email=user.email,
        rol=user.rol
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Usuario = Depends(get_current_user)):
    return current_user


@router.put("/me/password")
async def change_password(
    body: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not verify_password(body.old_password, current_user.password_hash):
        raise bad_request("Contraseña actual incorrecta")
    await db.execute(
        sql_update(Usuario)
        .where(Usuario.id == current_user.id)
        .values(password_hash=hash_password(body.new_password))
    )
    await db.commit()
    return {"ok": True}


@router.post("/register", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Usuario).where(Usuario.email == body.email))
    if existing.scalar_one_or_none():
        raise bad_request("Email ya registrado")
    user = Usuario(
        email=body.email,
        password_hash=hash_password(body.password),
        nombre=body.nombre,
        rol=body.rol,
        activo=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_admin)])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).order_by(Usuario.id))
    return result.scalars().all()


@router.put("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user(user_id: int, body: UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise not_found("Usuario")
    if body.nombre is not None:
        user.nombre = body.nombre
    if body.rol is not None:
        user.rol = body.rol
    if body.activo is not None:
        user.activo = body.activo
    await db.commit()
    await db.refresh(user)
    return user
