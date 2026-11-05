import ssl
from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

class Base(DeclarativeBase):
    pass


database_url = make_url(settings.SQLALCHEMY_DATABASE_URL)
connect_args = {}

# ==============================================================================
# CONFIGURAÇÃO DOS DRIVERS E PARÂMETROS SQL
# ==============================================================================

# 1. POSTGRESQL
if database_url.drivername in "postgresql":
    database_url = database_url.set(drivername="postgresql+asyncpg")
    query = dict(database_url.query)

    ssl_mode = query.pop("ssl", query.pop("sslmode", None))

    if ssl_mode not in (None, "disable", "require", "verify-ca", "verify-full"):
        raise ValueError(
            "Modo SSL não suportado para PostgreSQL. "
            "Use disable, require, verify-ca ou verify-full."
        )

    if ssl_mode:
        if ssl_mode == "disable":
            connect_args["ssl"] = False
        elif ssl_mode in {"require", "allow", "prefer"}:
            ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ctx
        elif ssl_mode in {"verify-ca", "verify-full"}:
            ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            if ssl_mode == "verify-ca":
                ctx.check_hostname = False
            connect_args["ssl"] = ctx
            
    #Para Supabase (Pooler / Porta de Transações)
    elif (database_url.host or "").endswith(".pooler.supabase.com"):
        connect_args["ssl"] = True

    if database_url.port == 6543:
        # No SupaBase Pooler as conexões sempre ficam trocando
        # Não há como as query grava cache
        query["prepared_statement_cache_size"] = "0"

    database_url = database_url.set(query=query)

_is_sqlite = database_url.drivername.startswith("sqlite")

if _is_sqlite:
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    database_url,
    connect_args=connect_args,
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,
)

SessionFactory = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def configure_sqlite(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()
