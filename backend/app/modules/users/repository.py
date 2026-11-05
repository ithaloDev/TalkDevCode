from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.modules.users.roles import UserRole
from .model import User
from typing import Optional, Sequence
from uuid import UUID

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def add(self,instance: User):
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def create(self, username: str, email: str, password_hash: str) -> User:
        new_user = User(username=username, email=email, password_hash=password_hash)
        return await self.add(new_user)
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.session.execute(
            select(User).filter_by(id=user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).filter_by(email=email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).filter_by(username=username)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[User]:
        result = await self.session.execute(select(User))
        return result.scalars().all()

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()
    
    # Isso e para evitar que o último administrado seja deletado
    async def count_by_role(self, role: UserRole) -> int:
        query = select(func.count(User.id)).where(User.role == role)
        result = await self.session.execute(query)

        return result.scalar_one()
