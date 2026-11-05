import asyncio
from uuid import UUID
from typing import Sequence
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.core.uow import UnitOfWork
from app.modules.users.roles import UserRole
from app.modules.comments.repository import CommentRepository
from app.modules.comments.schema import CommentActivityResponse
from app.modules.posts.repository import PostRepository
from app.modules.posts.schema import PostActivityResponse
from app.modules.users.model import User
from .repository import UserRepository
from .security import UserSecurity
from .schema import UserActivityMeta, UserActivityResponse, UserCreateRequest, UserLoginRequest, UserResponse, TokenResponse

class UserService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def register_new_user(self, data: UserCreateRequest) -> UserResponse:
        async with self.uow:
            repo = self.uow.get_repository(UserRepository)
            
            password_hash = await asyncio.to_thread(UserSecurity.hash_password, data.password)

            try:
                user = await repo.create(
                    username=data.username,
                    email=data.email,
                    password_hash=password_hash,
                )
                await self.uow.commit()
            except IntegrityError:
                await self.uow.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username ou e-mail já cadastrado no sistema.",
                ) from None

            await self.uow.refresh(user)
            return UserResponse.model_validate(user)

    async def authenticate_user(self, data: UserLoginRequest) -> TokenResponse:
        async with self.uow:
            repo = self.uow.get_repository(UserRepository)
            user = await repo.get_by_username(data.username)
            
            if not user or not await asyncio.to_thread(UserSecurity.verify_password, data.password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Username ou senha inválidos",
                )
            
            token = UserSecurity.create_access_token(user.id)
            
            return TokenResponse(access_token=token)

    async def get_all_users(self) -> Sequence[UserResponse]:
        async with self.uow:
            repo = self.uow.get_repository(UserRepository)
            users = await repo.get_all()
            
            return [UserResponse.model_validate(user) for user in users]

    async def get_user_by_id(self, user_id: UUID) -> UserResponse:
        async with self.uow:
            repo = self.uow.get_repository(UserRepository)
            user = await repo.get_by_id(user_id)
            
            if not user:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
            return UserResponse.model_validate(user)
        
    async def get_my_activity(self, current_user: User) -> UserActivityResponse:
        async with self.uow:
            comment_repo = self.uow.get_repository(CommentRepository)
            post_repo = self.uow.get_repository(PostRepository)

            comments = await comment_repo.get_all_by_user_id(current_user.id)
            posts = await post_repo.get_all_by_author_id(current_user.id)

            return UserActivityResponse(
                user=UserActivityMeta.model_validate(current_user),
                posts=[PostActivityResponse.model_validate(post) for post in posts],
                comments=[
                    CommentActivityResponse(
                        id=comment.id,
                        content=comment.content,
                        post_id=comment.post_id,
                        post_title=comment.post.title,
                        created_at=comment.created_at,
                        parent_username=comment.parent_author.username if comment.parent_author else None
                    )
                    for comment in comments
                ]
            )
        
    async def delete_user(self, target_user_id: UUID) -> None:
        async with self.uow:
            repo = self.uow.get_repository(UserRepository)

            user = await repo.get_by_id(target_user_id)

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado."
                )
                
            if user.role == UserRole.ADMIN:
                admin_count = await repo.count_by_role(UserRole.ADMIN)

                if admin_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Não é possível excluir o último administrador."
                    )

            await repo.delete(user)
            await self.uow.commit()
    
    
    # ------------ Funções de admin ------------
    
    async def update_user_role(self, target_user_id: UUID, new_role: UserRole, admin_id: UUID) -> UserResponse:
        async with self.uow:
            repo = self.uow.get_repository(UserRepository)
            
            admin = await repo.get_by_id(admin_id)

            # Impedir que outros como usuário e membros do staff mude o papel
            if admin is None or admin.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Somente administradores podem executar esta operação.",
                )
            
            # Impedir que o proprio admin altera o seu papel de admin
            if target_user_id == admin_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você não pode alterar o próprio papel.",
                )

            target_user = await repo.get_by_id(target_user_id)

            if target_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado.",
                )

            # Não permite que removar o último administrador.
            if target_user.role == UserRole.ADMIN and new_role != UserRole.ADMIN:
                admin_count = await repo.count_by_role(UserRole.ADMIN)

                if admin_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Não é possível remover o último administrador.",
                    )

            target_user.role = new_role

            await self.uow.commit()
            await self.uow.refresh(target_user)

            return UserResponse.model_validate(target_user)


    async def delete_user_by_staff(self, target_user_id: UUID, admin_id: UUID) -> None:
        async with self.uow:
            repo = self.uow.get_repository(UserRepository)
            
            admin = await repo.get_by_id(admin_id)

            # Valida se quem está executando a operação é administrador.
            if admin is None or admin.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Somente administradores podem executar esta operação."
                )

            if target_user_id == admin_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Não pode excluir a própria conta admin."
                )

            user = await repo.get_by_id(target_user_id)

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado."
                )

            if user.role == UserRole.ADMIN:
                admin_count = await repo.count_by_role(UserRole.ADMIN)

                if admin_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Não é possível excluir o último administrador."
                    )

            await repo.delete(user)
            await self.uow.commit()