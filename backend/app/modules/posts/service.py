from app.core.uow import UnitOfWork
from app.modules.users.roles import UserRole
from .repository import PostRepository
from uuid import UUID
from typing import Sequence, Optional
from .model import Post
from fastapi import HTTPException, status

class PostService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def list_posts(self, limit: int = 10, offset: int = 0, search: str | None = None) -> Sequence[Post]: 
        async with self.uow: 
            repo = self.uow.get_repository(PostRepository) 
            return await repo.get_all(limit=limit, offset=offset, search=search)

    async def get_post(self, post_id: UUID) -> Post:
        async with self.uow:
            repo = self.uow.get_repository(PostRepository)
            post = await repo.get_by_id(post_id)
            if not post:
                raise HTTPException(status_code=404, detail="Post não encontrado")
            return post

    async def create_post(self, title: str, content: str, author_id: UUID) -> Post:
        async with self.uow:
            repo = self.uow.get_repository(PostRepository)
            post = await repo.create(title=title, content=content, author_id=author_id)

            await self.uow.commit()
            persisted_post = await repo.get_by_id(post.id)
            return persisted_post

    async def update_post(self, post_id: UUID, title: Optional[str], content: Optional[str], user_id: UUID) -> Post:
        async with self.uow:
            repo = self.uow.get_repository(PostRepository)
            
            post = await repo.get_by_id(post_id)
            
            if not post:
                raise HTTPException(status_code=404, detail="Post não encontrado")
            
            # Valida se o usuário logado é o autor do post
            if post.author_id != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para editar este post")
            
            post_updated = await repo.update(post, title, content)

            await self.uow.commit()
            return post

    
    async def delete_post(self, post_id: UUID, user_id: UUID) -> None:
        async with self.uow:
            repo = self.uow.get_repository(PostRepository)

            post = await repo.get_by_id(post_id)

            if post is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post não encontrado.",
                )

            is_author = post.author_id == user_id

            if not is_author:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você não tem permissão para excluir este post.",
                )

            await repo.delete(post)
            await self.uow.commit()
            
    async def delete_post_by_staff(self, target_post_id: UUID, user_role: UserRole) -> None:
        async with self.uow:
            repo = self.uow.get_repository(PostRepository)

            target_post = await repo.get_by_id(target_post_id)

            if target_post is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post não encontrado.",
                )
                
            is_staff = user_role in {
                UserRole.MODERATOR,
                UserRole.ADMIN
            }

            if not is_staff:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você não tem permissão para excluir este post.",
                )

            await repo.delete(target_post)
            await self.uow.commit()
