
from fastapi import APIRouter

from app.modules import (
    user_router,
    post_router,
    comment_router,
)


api_router = APIRouter()

api_router.include_router(user_router, prefix="/v1", tags=["Users"])

api_router.include_router(post_router, prefix="/v1", tags=["Posts"])

api_router.include_router(comment_router, prefix="/v1", tags=["Comments"])
