from fastapi import Depends

from app.core.database import SessionFactory
from app.core.uow import UnitOfWork

from .service import CommentService

def get_uow() -> UnitOfWork:
    return UnitOfWork(session_factory=SessionFactory)

def get_comment_service(uow: UnitOfWork = Depends(get_uow)) -> CommentService:
    return CommentService(uow)
