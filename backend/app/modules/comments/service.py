from typing import Optional, Sequence
from uuid import UUID
from fastapi import HTTPException, status

from app.core.uow import UnitOfWork
from app.modules.comments.model import Comment
from app.modules.comments.repository import CommentRepository
from app.modules.posts.repository import PostRepository
from app.modules.users.roles import UserRole
from app.modules.comments.schema import CommentCreate, CommentResponse, CommentUpdate, PaginationParams


class CommentService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def list_comments(self, limit: int = 20, offset: int = 0) -> Sequence[CommentResponse]:
        async with self.uow:
            repo = self.uow.get_repository(CommentRepository)
            comments = await repo.get_all(limit=limit, offset=offset)
            
            return [CommentResponse.model_validate(comment) for comment in comments]

    async def list_comments_by_post(self, post_id: UUID, limit: int = PaginationParams.limit, offset: int = PaginationParams.offset) -> Sequence[CommentResponse]:
        async with self.uow:
            comment_repo = self.uow.get_repository(CommentRepository)
            post_repo = self.uow.get_repository(PostRepository)

            post = await post_repo.get_by_id(post_id)

            if post is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post não encontrado"
                )
                
            comments = await comment_repo.get_all_comments_by_post(post_id, limit=limit, offset=offset)

            return [CommentResponse.model_validate(comment) for comment in comments]

    async def get_comment(self, comment_id: UUID) -> Optional[CommentResponse]:
        async with self.uow:
            repo = self.uow.get_repository(CommentRepository)
            comment = await repo.get_by_id(comment_id)

            if comment is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comentário não encontrado"
                )

            return CommentResponse.model_validate(comment)

    async def create_comment(self, data: CommentCreate, user_id: UUID) -> CommentResponse:
        async with self.uow:
            comment_repo = self.uow.get_repository(CommentRepository)
            post_repo = self.uow.get_repository(PostRepository)

            post = await post_repo.get_by_id(data.post_id)

            if post is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post não encontrado"
                )

            if data.parent_id is not None:
                parent = await comment_repo.get_by_id(data.parent_id)
                
                if parent is None or parent.post_id != data.post_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentário original não encontrado neste artigo")
                
            comment = await comment_repo.create(content=data.content, post_id=data.post_id, user_id=user_id, parent_id=data.parent_id)

            await self.uow.commit()
            persisted_comment = await comment_repo.get_by_id(comment.id)
            return CommentResponse.model_validate(persisted_comment)

    async def update_comment(self, comment_id: UUID, content: CommentUpdate, user_id: UUID) -> Optional[CommentResponse]:
        async with self.uow:
            repo = self.uow.get_repository(CommentRepository)
            comment = await repo.get_by_id(comment_id)

            if comment is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comentário não encontrado"
                )
                
            is_author = comment.user_id == user_id

            if not is_author:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você não tem permissão para editar este comentário"
                )

            comment = await repo.update(comment, content.content)

            await self.uow.commit()
            return CommentResponse.model_validate(comment)

    
    async def delete_comment(self, comment_id: UUID, user_id: UUID) -> None:
        async with self.uow:
            repo = self.uow.get_repository(CommentRepository)
            comment = await repo.get_by_id(comment_id)

            if comment is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comentário não encontrado.",
                )

            is_author = comment.user_id == user_id

            if not is_author:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você não tem permissão para excluir este comentário.",
                )

            await repo.delete(comment)
            await self.uow.commit()
            
            
    async def delete_comment_by_staff(self, comment_id: UUID, user_role: UserRole) -> None:
        async with self.uow:
            repo = self.uow.get_repository(CommentRepository)
            comment = await repo.get_by_id(comment_id)

            if comment is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Comentário não encontrado.",
                )

            is_staff = user_role in {
                UserRole.ADMIN,
                UserRole.MODERATOR
            }

            if not is_staff:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você não tem permissão para excluir este comentário.",
                )

            await repo.delete(comment)
            await self.uow.commit()