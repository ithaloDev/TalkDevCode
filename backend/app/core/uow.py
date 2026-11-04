from types import TracebackType
from typing import Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self.session_factory()
        return self

    def get_repository(self, repo_class):
        if self.session is None:
            raise RuntimeError("UnitOfWork precisa estar ativo antes de obter um repositório.")
        return repo_class(self.session)

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], traceback: Optional[TracebackType]) -> None:
        if self.session is None:
            return
        try:
            if exc_type:
                await self.rollback()
        finally:
            await self.session.close()
            self.session = None

    async def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("Não existe sessão ativa.")
        await self.session.commit()

    async def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("Não existe sessão ativa.")
        await self.session.rollback()

    async def refresh(self, instance) -> None:
        if self.session is None:
            raise RuntimeError("Não existe sessão ativa.")
        await self.session.refresh(instance)
