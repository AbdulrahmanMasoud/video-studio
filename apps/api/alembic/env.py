"""Alembic environment: uses DATABASE_URL_SYNC (or ALEMBIC_URL) and the SQLAlchemy models for autogenerate."""
from __future__ import annotations

import os

from sqlalchemy import engine_from_config, pool

from alembic import context
from vs_api.core.models import Base

config = context.config
url = os.environ.get("ALEMBIC_URL") or os.environ.get("DATABASE_URL_SYNC")
if url:
    config.set_main_option("sqlalchemy.url", url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
