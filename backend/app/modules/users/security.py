from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt

from app.core.config import settings


class UserSecurity:
    @staticmethod
    def hash_password(password: str) -> str:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("A senha deve possuir no máximo 72 caracteres.")
        return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            password_bytes = plain_password.encode("utf-8")
            if len(password_bytes) > 72:
                return False
            return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
        except (ValueError, TypeError, AttributeError):
            return False

    @staticmethod
    def create_access_token(user_id: UUID) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "user_id": str(user_id),
            "iat": datetime.now(timezone.utc),
            "exp": expires_at,
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
