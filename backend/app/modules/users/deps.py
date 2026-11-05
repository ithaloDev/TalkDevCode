from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.database import SessionFactory
from app.core.uow import UnitOfWork
from .model import User
from .repository import UserRepository
from .roles import UserRole
from .service import UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def get_uow() -> UnitOfWork:
    return UnitOfWork(session_factory=SessionFactory)


def get_user_service(uow: UnitOfWork = Depends(get_uow)) -> UserService:
    return UserService(uow)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    uow: UnitOfWork = Depends(get_uow),
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        raw_user_id = payload.get("user_id")
        user_id = UUID(raw_user_id)
    except (jwt.PyJWTError, ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar as credenciais.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    async with uow:
        repository = uow.get_repository(UserRepository)
        user = await repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado ou inativo.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user


def require_roles(*allowed_roles: UserRole):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não possui permissão para realizar esta operação.",
            )
        return current_user
    return role_checker


require_admin = require_roles(UserRole.ADMIN)
require_staff = require_roles(UserRole.MODERATOR, UserRole.ADMIN)
