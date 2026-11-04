from fastapi import Depends
from app.core.uow import UnitOfWork
from app.core.database import SessionFactory
from .service import PostService

def get_uow() -> UnitOfWork:
    return UnitOfWork(session_factory=SessionFactory)

def get_post_service(uow: UnitOfWork = Depends(get_uow)) -> PostService:
    return PostService(uow)