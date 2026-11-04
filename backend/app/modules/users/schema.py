from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints
from typing import Annotated, List

from app.modules.users.roles import UserRole
from app.modules.posts.schema import PostActivityResponse
from app.modules.comments.schema import CommentActivityResponse


Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")]
Password = Annotated[str, StringConstraints(min_length=8, max_length=72)]


class UserCreateRequest(BaseModel):
    username: Username
    email: EmailStr
    password: Password


class UserLoginRequest(BaseModel):
    username: Username
    password: Password


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
    
class UserActivityMeta(BaseModel):
    id: UUID
    username: str
    
    model_config = ConfigDict(from_attributes=True)
    
class UserActivityResponse(BaseModel):
    user: UserActivityMeta
    posts: List[PostActivityResponse]
    comments: List[CommentActivityResponse]


class UserRoleUpdate(BaseModel):
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
