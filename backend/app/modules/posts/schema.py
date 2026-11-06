from datetime import datetime
from uuid import UUID

from app.core.datetime_utils import utc_isoformat

from fastapi import Query

from pydantic import BaseModel, ConfigDict, StringConstraints, field_serializer, model_validator
from typing import Annotated, Optional


Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]
Content = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100000)]

class PaginationParams(BaseModel):
    limit: int = Query(default=20, ge=1, le=100)
    offset: int = Query(default=0, ge=0)
    search: Optional[str] = Query(default="", min_length=1, max_length=200)

class PostCreateSchema(BaseModel):
    title: Title
    content: Content


class PostUpdateSchema(BaseModel):
    title: Optional[Title] = None
    content: Optional[Content] = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if self.title is None and self.content is None:
            raise ValueError("Informe ao menos o título ou o conteúdo para atualizar.")
        return self


class PostAuthorSchema(BaseModel):
    id: UUID
    username: str

    model_config = ConfigDict(from_attributes=True)


class PostResponseSchema(BaseModel):
    id: UUID
    title: str
    content: str
    author_id: UUID
    author: PostAuthorSchema
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        return utc_isoformat(value)
    
class PostActivityResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    
    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime) -> str:
        return utc_isoformat(value)

    model_config = ConfigDict(from_attributes=True)
