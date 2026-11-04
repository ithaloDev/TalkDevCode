from app.modules.users.router import user_router
from app.modules.posts.router import post_router
from app.modules.comments.router import comment_router

__all__ = [
    "user_router",
    "post_router",
    "comment_router"
]
