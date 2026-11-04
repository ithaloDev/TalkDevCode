from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.modules.users.model import User
from app.modules.users.schema import (
    TokenResponse,
    UserCreateRequest,
    UserLoginRequest,
    UserResponse,
    UserRoleUpdate,
)
from app.modules.users.service import UserService

from app.modules.users.deps import get_current_user, get_user_service, require_admin

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(data: UserCreateRequest, service: UserService = Depends(get_user_service)):
    return await service.register_new_user(data)


@user_router.post("/login", response_model=TokenResponse)
async def login(data: UserLoginRequest, service: UserService = Depends(get_user_service)):
    return await service.authenticate_user(data)


@user_router.get("/", response_model=Sequence[UserResponse])
async def list_users(current_user: User = Depends(require_admin), service: UserService = Depends(get_user_service)):
    return await service.get_all_users()


@user_router.get("/me", response_model=UserResponse)
async def get_logged_user(current_user: User = Depends(get_current_user)):
    return current_user


@user_router.get("/me/activity")
async def get_my_activity(
    current_user: User = Depends(get_current_user), 
    service: UserService = Depends(get_user_service)
):
    return await service.get_my_activity(current_user)


@user_router.delete("/me")
async def delete_account(current_user: User = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    await service.delete_user(current_user.id)
    return "Usuário deletado com sucesso"


@user_router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role_by_admin(
    user_id: UUID,
    data: UserRoleUpdate,
    current_user: User = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    return await service.update_user_role(target_user_id=user_id, new_role=data.role, admin_id=current_user.id)


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_staff(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    await service.delete_user_by_staff(target_user_id=user_id, admin_id=current_user.id)
    return "Usuário deletado com sucesso"
