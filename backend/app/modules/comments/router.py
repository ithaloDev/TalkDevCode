from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.users.deps import get_current_user, require_staff
from app.modules.users.schema import UserResponse
from .deps import get_comment_service
from .schema import CommentCreate, CommentResponse, CommentUpdate
from .service import CommentService


comment_router = APIRouter(prefix="/comments", tags=["Comments"])


@comment_router.get("/", response_model=Sequence[CommentResponse])
async def list_comments(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    service: CommentService = Depends(get_comment_service),
):
    return await service.list_comments(limit=limit, offset=offset)


@comment_router.get("/post/{post_id}", response_model=Sequence[CommentResponse])
async def list_comments_by_post(
    post_id: UUID,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    service: CommentService = Depends(get_comment_service),
):
    return await service.list_comments_by_post(post_id, limit=limit, offset=offset)


@comment_router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(comment_id: UUID, service: CommentService = Depends(get_comment_service)):
    return await service.get_comment(comment_id)


@comment_router.post("/", status_code=status.HTTP_201_CREATED, response_model=CommentResponse)
async def create_comment(
    data: CommentCreate,
    current_user: UserResponse = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    return await service.create_comment(data=data, user_id=current_user.id)


@comment_router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    content: CommentUpdate,
    current_user: UserResponse = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    return await service.update_comment(comment_id=comment_id, content=content, user_id=current_user.id)


@comment_router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    await service.delete_comment(comment_id=comment_id, user_id=current_user.id)


@comment_router.delete("/{comment_id}/staff", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_by_staff(
    comment_id: UUID,
    current_user: UserResponse = Depends(require_staff),
    service: CommentService = Depends(get_comment_service),
):
    await service.delete_comment_by_staff(comment_id=comment_id, user_role=current_user.role)
