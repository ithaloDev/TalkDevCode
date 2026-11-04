from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.comments.model import Comment


class CommentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, content: str, post_id: UUID, user_id: UUID, parent_id: UUID | None = None) -> Comment:
        comment = Comment(content=content, post_id=post_id, user_id=user_id, parent_id=parent_id)
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def get_by_id(self, comment_id: UUID) -> Optional[Comment]:
        result = await self.session.execute(
            select(Comment).options(selectinload(Comment.author), selectinload(Comment.parent).selectinload(Comment.author)).where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 20, offset: int = 0) -> Sequence[Comment]:
        query = (
            select(Comment)
            .options(
                selectinload(Comment.author), 
                selectinload(Comment.parent).selectinload(Comment.author)
            )
            .order_by(Comment.created_at.desc(), Comment.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_all_comments_by_post(
        self, post_id: UUID, limit: int = 20, offset: int = 0
    ) -> Sequence[Comment]:
        query = (
            select(Comment)
            .options(selectinload(Comment.author), selectinload(Comment.parent).selectinload(Comment.author))
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc(), Comment.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_all_by_user_id(self, user_id: UUID) -> Sequence[Comment]:
        query = (
            select(Comment)
            .options(
                selectinload(Comment.post),
                selectinload(Comment.parent).selectinload(Comment.author),
            )
            .where(Comment.user_id == user_id)
            .order_by(Comment.created_at.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, comment: Comment, content: str) -> Comment:
        comment.content = content
        await self.session.flush()
        return comment

    async def delete(self, comment: Comment) -> None:
        await self.session.delete(comment)
        await self.session.flush()
