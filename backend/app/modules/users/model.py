import uuid
from sqlalchemy import String, UUID, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from .roles import UserRole
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.posts.model import Post
    from app.modules.comments.model import Comment

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False, length=80), default=UserRole.USER, server_default=UserRole.USER, nullable=False)

    posts: Mapped[List["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship(back_populates="author", cascade="all, delete-orphan")