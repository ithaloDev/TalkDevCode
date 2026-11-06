from datetime import datetime
from uuid import UUID

from app.core.datetime_utils import utc_isoformat

from fastapi import Query

from pydantic import BaseModel, ConfigDict, StringConstraints, field_serializer
from typing import Annotated, Optional

CommentContent = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]

class PaginationParams(BaseModel):
    limit: int = Query(default=20, ge=1, le=100)
    offset: int = Query(default=0, ge=0)

class CommentCreate(BaseModel):
    content: CommentContent
    post_id: UUID
    parent_id: Optional[UUID] = None


class CommentUpdate(BaseModel):
    content: CommentContent


class CommentAuthor(BaseModel):
    id: UUID
    username: str

    model_config = ConfigDict(from_attributes=True)


class CommentResponse(BaseModel):
    id: UUID
    content: str
    post_id: UUID
    user_id: UUID
    author: CommentAuthor
    parent_id: Optional[UUID] = None
    parent_author: Optional[CommentAuthor] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        return utc_isoformat(value)


class CommentActivityResponse(BaseModel):
    id: UUID
    content: str
    post_id: UUID
    post_title: str
    created_at: datetime
    parent_username: Optional[str] = None
    
    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> str:
        return utc_isoformat(value)

    model_config = ConfigDict(from_attributes=True)
    
    