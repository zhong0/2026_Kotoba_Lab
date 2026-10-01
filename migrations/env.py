from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import app_config

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)


def _sqlalchemy_url() -> str:
    # app 用 psycopg 直接連線（postgresql://）；SQLAlchemy 需要指明 driver
    url = app_config.DATABASE_URL
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def run_migrations_offline() -> None:
    """產生 SQL 而不連線（alembic upgrade head --sql），可用來檢視將執行的語句。"""
    context.configure(url=_sqlalchemy_url(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_sqlalchemy_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
