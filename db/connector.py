import contextlib

from sqlalchemy import Engine, NullPool, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession as AsyncSessionType
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session as SessionType
from sqlalchemy.orm import sessionmaker

from common.settings import settings


class DatabaseConnector:
    @staticmethod
    def get_engine() -> Engine:
        return create_engine(
            url=settings.DB_DSN,
            poolclass=NullPool,
        )

    @staticmethod
    async def get_async_engine() -> AsyncEngine:
        url = settings.DB_DSN.replace('sqlite:', 'sqlite+aiosqlite:')
        url = url.replace('postgresql', 'postgresql+asyncpg')
        return create_async_engine(
            url=url,
            poolclass=NullPool,
            echo=True,
        )

    @staticmethod
    def get_session(
        session_engine: Engine | AsyncEngine, is_async: bool = False
    ) -> sessionmaker | async_sessionmaker:

        sessionmaker_func, session_class = (
            (async_sessionmaker, AsyncSessionType) if is_async else (sessionmaker, SessionType)
        )
        session = sessionmaker_func(
            bind=session_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=session_class,
        )
        return session

    @classmethod
    @contextlib.contextmanager
    def get_sync_session(cls) -> SessionType:
        engine = cls.get_engine()
        session = cls.get_session(session_engine=engine)
        with session() as sync_session:
            try:
                yield sync_session
            finally:
                sync_session.close()

    @classmethod
    @contextlib.asynccontextmanager
    async def get_async_session(cls, schema: str | None = None) -> AsyncSessionType:
        """Асинхронный контекстный менеджер подключения к базе данных."""
        database_schema = schema or settings.DATABASE_SCHEMA
        session = cls.get_session(session_engine=await cls.get_async_engine(), is_async=True)
        async with session() as async_session:
            try:
                conn = await async_session.connection()
                await conn.execution_options(schema_translate_map={None: database_schema})
                yield async_session
            finally:
                await async_session.close()


Session = DatabaseConnector.get_sync_session
AsyncSession = DatabaseConnector.get_async_session
