from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


database_url = make_url(settings.SQLALCHEMY_DATABASE_URL)
connect_args = {}

if database_url.drivername in {"postgres", "postgresql"}:
    database_url = database_url.set(drivername="postgresql+asyncpg")
    query = dict(database_url.query)
    sslmode = query.pop("sslmode", None)

    if sslmode == "require":
        connect_args["ssl"] = "require"
    elif sslmode not in (None, "disable"):
        raise ValueError(
            "SSL mode não suportado na URL do PostgreSQL. "
            "Use sslmode=require para conexões Supabase."
        )

    # O pooler em modo transaction (porta 6543) não mantém prepared statements.
    if database_url.port == 6543:
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
