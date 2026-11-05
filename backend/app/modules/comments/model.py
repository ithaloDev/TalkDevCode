from typing import TYPE_CHECKING
import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Text, UUID, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.users.model import User
    from app.modules.posts.model import Post

class Comment(Base):
    __tablename__ = "comments"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("posts.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    
    post: Mapped["Post"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")
    parent: Mapped["Comment | None"] = relationship(remote_side="Comment.id", back_populates="replies", foreign_keys=[parent_id])
    replies: Mapped[list["Comment"]] = relationship(back_populates="parent", cascade="all, delete-orphan", passive_deletes=True)

    @property
    def parent_author(self):
        return self.parent.author if self.parent is not None else None
