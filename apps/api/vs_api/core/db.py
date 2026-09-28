"""Database engines: async (API) and sync (worker, Alembic, `Session.run_sync` helpers)."""
from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import get_settings


@lru_cache(maxsize=1)
def async_engine():
    return create_async_engine(get_settings().database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)


@lru_cache(maxsize=1)
def async_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(async_engine(), expire_on_commit=False)


@lru_cache(maxsize=1)
def sync_engine(url: str | None = None):
    return create_engine(url or get_settings().database_url_sync, pool_pre_ping=True)


def sync_session_factory(url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(sync_engine(url), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory()() as session:
        yield session
