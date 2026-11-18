"""Teste de migração real (opt-in): exige TEST_MYSQL_URL com banco *_test existente."""
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


@pytest.mark.mysql_integration
def test_mysql_migrations_and_connectivity():
    test_url = os.getenv("TEST_MYSQL_URL", "").strip()
    if not test_url:
        pytest.skip("Defina TEST_MYSQL_URL para executar a integração em servidor MySQL real")
    parsed = make_url(test_url)
    assert parsed.drivername == "mysql+pymysql", "TEST_MYSQL_URL deve usar mysql+pymysql"
    assert parsed.database and parsed.database.endswith("_test"), (
        "Banco de integração deve ter nome terminado em _test, nunca use a base de produção"
    )
    root = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["DATABASE_URL"] = test_url
    env["APP_ENV"] = "test"
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=root, env=env, check=True)
    engine = create_engine(parsed, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            assert conn.execute(text("SELECT 1")).scalar_one() == 1
            names = set(inspect(conn).get_table_names())
            assert {"users", "stations", "readings", "security_events", "audit_findings", "security_triage_actions", "alembic_version"} <= names
            assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "003"
    finally:
        engine.dispose()
