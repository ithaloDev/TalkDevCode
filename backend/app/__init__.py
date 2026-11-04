import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.database import engine


logger = logging.getLogger("talkdevcode")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando TalkDevCode API")
    try:
        # O schema é gerenciado exclusivamente pelo Alembic durante o deploy.
        yield
    finally:
        await engine.dispose()
        logger.info("TalkDevCode API encerrada")


def create_app() -> FastAPI:
    if settings.ENVIRONMENT.lower() == "production" and settings.JWT_SECRET_KEY == "CHANGE-ME-IN-ENVIRONMENT":
        raise RuntimeError("Configure JWT_SECRET_KEY antes de iniciar em produção.")

    app = FastAPI(
        title="TalkDevCode API",
        description="API do blog TalkDevCode",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(api_router, prefix="/api")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception):
        logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor."},
        )

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}

    frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app
