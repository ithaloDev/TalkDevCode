from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .model import Post


class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, instance: Post) -> Post:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_all(self, limit: int = 10, offset: int = 0, search: Optional[str] = None) -> Sequence[Post]:
        query = (
            select(Post)
            .options(selectinload(Post.author))
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        if search:
            query = query.where(Post.title.ilike(f"%{search}%"))
            
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, post_id: UUID) -> Optional[Post]:
        result = await self.session.execute(
            select(Post).options(selectinload(Post.author)).where(Post.id == post_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_by_author_id(self, author_id: UUID) -> Sequence[Post]:
        query = (
            select(Post)
            .where(Post.author_id == author_id)
            .order_by(Post.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, title: str, content: str, author_id: UUID) -> Post:
        post = Post(title=title, content=content, author_id=author_id)
        return await self.add(post)

    async def update(self, post: Post, title: Optional[str], content: Optional[str]) -> Post:
        if title:
            post.title = title
        if content:
            post.content = content
            
        await self.session.flush()
        return post

    async def delete(self, post: Post) -> None:
        await self.session.delete(post)
        await self.session.flush()
