"""Valida o esquema MySQL sem depender de servidor rodando na suíte unitária."""
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable
from app import config, models
from app.database import Base


def test_mysql_url_escapes_special_characters(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_USER", "sombraviva")
    monkeypatch.setenv("DB_PASSWORD", "@/colon:#?pass")
    monkeypatch.setenv("DB_NAME", "sombraviva")
    url = config.build_database_url()
    assert url.drivername == "mysql+pymysql"
    assert url.password == "@/colon:#?pass"
    assert url.query["charset"] == "utf8mb4"
    assert "%40" in url.render_as_string(hide_password=False)


def test_mysql_schema_can_compile():
    assert set(Base.metadata.tables) == {"users", "stations", "readings", "security_events", "audit_findings", "security_triage_actions", "iot_devices", "app_settings"}
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=mysql.dialect()))
        assert "CREATE TABLE" in ddl
        assert "PRIMARY KEY" in ddl
