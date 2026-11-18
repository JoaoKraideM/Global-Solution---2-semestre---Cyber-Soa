"""Diagnóstico MySQL e contagem de registros. Não imprime credenciais."""
from sqlalchemy import inspect, select, func, text
from app.config import DATABASE_URL
from app.database import engine, SessionLocal
from app.models import User, Station, Reading, SecurityEvent, AuditFinding, SecurityTriageAction

REQUIRED = {"users", "stations", "readings", "security_events", "audit_findings",
            "security_triage_actions", "alembic_version"}


def main():
    if DATABASE_URL.get_backend_name() != "mysql":
        raise SystemExit("Este diagnóstico exige MySQL. Para testes rápidos use pytest.")
    with engine.connect() as connection:
        name, version = connection.execute(text("SELECT DATABASE(), VERSION() ")).one()
        found = set(inspect(connection).get_table_names())
        missing = REQUIRED - found
        print("Conexão MySQL: OK | Banco:", name, "| Servidor:", version)
        print("Tabelas:", ", ".join(sorted(found)))
        if missing:
            raise SystemExit("Faltam tabelas: " + ", ".join(sorted(missing)) + " — confira o log do bootstrap")
    with SessionLocal() as session:
        for label, model in (("usuários", User), ("estações", Station), ("leituras", Reading),
                             ("eventos", SecurityEvent), ("achados", AuditFinding),
                             ("decisões de triagem", SecurityTriageAction)):
            print(f"{label:20}:", session.scalar(select(func.count()).select_from(model)) or 0)
        n = session.scalar(select(func.count()).select_from(SecurityEvent).where(SecurityEvent.is_demo.is_(True))) or 0
        print("Eventos fictícios (marcados is_demo=1):", n)
    print("Banco validado. O fato de existir um evento não comprova invasão.")


if __name__ == "__main__":
    main()
