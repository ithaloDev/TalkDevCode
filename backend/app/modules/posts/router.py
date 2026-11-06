from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.modules.users.deps import get_current_user, require_staff
from app.modules.users.model import User
from .deps import get_post_service
from .schema import PostCreateSchema, PostResponseSchema, PostUpdateSchema, PaginationParams
from .service import PostService


post_router = APIRouter(prefix="/posts", tags=["Posts"])


@post_router.get("/", response_model=Sequence[PostResponseSchema])
async def list_posts(
    params: PaginationParams = Depends(),
    service: PostService = Depends(get_post_service)
):
    return await service.list_posts(limit=params.limit, offset=params.offset, search=params.search)


@post_router.get("/{post_id}", response_model=PostResponseSchema)
async def get_post(post_id: UUID, service: PostService = Depends(get_post_service)):
    return await service.get_post(post_id)


@post_router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponseSchema)
async def create_post(
    data: PostCreateSchema,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    post = await service.create_post(data.title, data.content, current_user.id)
    return post


@post_router.put("/{post_id}", response_model=PostResponseSchema)
async def update_post(
    post_id: UUID,
    data: PostUpdateSchema,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    post = await service.update_post(post_id, data.title, data.content, current_user.id)
    return post


@post_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PostService = Depends(get_post_service),
):
    await service.delete_post(post_id=post_id, user_id=current_user.id)


@post_router.delete("/{post_id}/staff", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post_by_staff(
    post_id: UUID,
    current_user: User = Depends(require_staff),
    service: PostService = Depends(get_post_service),
):
    await service.delete_post_by_staff(target_post_id=post_id, user_role=current_user.role)
