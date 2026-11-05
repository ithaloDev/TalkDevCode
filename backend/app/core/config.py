from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str = "sqlite+aiosqlite:///./database.db"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_SECRET_KEY: str = "SECRET_KEY"
    JWT_ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://127.0.0.1:5500, http://localhost:5500"
    SQL_ECHO: bool = False
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET_KEY deve possuir pelo menos 32 caracteres.")
        return value


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
