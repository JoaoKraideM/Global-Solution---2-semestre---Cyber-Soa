"""Inicialização automática: Alembic -> administrador -> demos opt-in -> verificação do esquema."""
from pathlib import Path
from sqlalchemy import inspect
from alembic import command
from alembic.config import Config

from app import config
from app.database import engine
from app.seed import main as seed_main

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_TABLES = {"alembic_version", "users", "stations", "readings", "security_events",
                   "audit_findings", "security_triage_actions", "iot_devices"}


def bootstrap():
    config.require_secrets()
    alembic_cfg = Config(str(ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(ROOT / "alembic"))
    print("[BOOT] Aplicando migrações Alembic...")
    command.upgrade(alembic_cfg, "head")
    seed_main()
    with engine.connect() as connection:
        missing = REQUIRED_TABLES - set(inspect(connection).get_table_names())
        if missing:
            raise RuntimeError("Tabelas ausentes após migrações: " + ", ".join(sorted(missing)))
    print("[BOOT] Esquema verificado. Iniciando aplicação.")


if __name__ == "__main__":
    bootstrap()
