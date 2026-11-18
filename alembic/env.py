from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.config import DATABASE_URL
from app.base import Base
from app import models  # noqa: F401 - registrar todas as tabelas

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic precisa da URL completa (inclusive senha) e usa %% para escapar percentuais no INI.
connection_url = DATABASE_URL.render_as_string(hide_password=False)
config.set_main_option("sqlalchemy.url", connection_url.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=connection_url, target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
