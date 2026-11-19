"""Cobertura da inicialização real, idempotência e exemplos acadêmicos sanitizados."""
import json
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import Session, sessionmaker

from app import seed
from app.base import Base
from app.models import User, Station, Reading, SecurityEvent, AuditFinding, SecurityTriageAction
from app.security_intelligence import local_report


def _counts(session):
    return {model.__tablename__: session.scalar(select(func.count()).select_from(model))
            for model in (User, Station, Reading, SecurityEvent, AuditFinding, SecurityTriageAction)}


def test_seed_initializes_all_demo_domains_and_is_idempotent(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///' + str(tmp_path/'seed.sqlite'))
    Base.metadata.create_all(engine)
    monkeypatch.setattr(seed, 'SessionLocal', sessionmaker(bind=engine))
    monkeypatch.setenv('APP_ENV', 'development')
    monkeypatch.setenv('SEED_DEMO_DATA', 'true')
    seed.main()
    with Session(engine) as session:
        first = _counts(session)
        assert first == {'users': 1, 'stations': 2, 'readings': 48,
                         'security_events': 6, 'audit_findings': 3, 'security_triage_actions': 0}
        assert all(r.is_simulated for r in session.scalars(select(Reading)).all())
        assert all(e.is_demo for e in session.scalars(select(SecurityEvent)).all())
        assert all(f.is_demo for f in session.scalars(select(AuditFinding)).all())
        from app.seed import SOC_SCENARIOS
        for *_, title in SOC_SCENARIOS:
            event = session.scalar(select(SecurityEvent).where(SecurityEvent.summary == title))
            assert event is not None
            report = local_report(event)
            assert report['ai_used'] is False and report['verdict'] == 'Comprometimento não confirmado'
        first_event = session.scalar(select(SecurityEvent).where(SecurityEvent.summary.like('[DEMO-SOC]%')))
        first_event.triage_status = 'investigating'
        session.commit()
    seed.main()
    with Session(engine) as session:
        assert _counts(session) == first
        changed = session.scalar(select(SecurityEvent).where(SecurityEvent.summary.like('[DEMO-SOC]%')))
        assert changed.triage_status == 'investigating'  # não apaga decisão do operador
    engine.dispose()


def test_bootstrap_does_not_insert_fake_evidence_in_production(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///' + str(tmp_path/'prod.sqlite'))
    Base.metadata.create_all(engine)
    monkeypatch.setattr(seed, 'SessionLocal', sessionmaker(bind=engine))
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('SEED_DEMO_DATA', 'true')  # produção prevalece sobre configuração
    seed.main()
    with Session(engine) as session:
        # Em produção só existem as 2 estações que recebem o ESP32 — sem leituras nem eventos fictícios.
        assert _counts(session) == {'users':1,'stations':2,'readings':0,'security_events':0,
                                    'audit_findings':0,'security_triage_actions':0}
    engine.dispose()


def test_fresh_database_migrations_and_seed_twice(tmp_path):
    root=Path(__file__).parents[1]
    path=tmp_path/'fiap_migrated.sqlite'
    env=os.environ.copy()
    env.update({'APP_ENV':'test', 'SEED_DEMO_DATA':'true',
        'DATABASE_URL': 'sqlite:///' + str(path)})
    for _ in range(2):
        done=subprocess.run([sys.executable,'-m','app.bootstrap'],cwd=root,env=env,
                            text=True,capture_output=True,timeout=55)
        assert done.returncode == 0, done.stderr + done.stdout
        assert 'Esquema verificado' in done.stdout
    with create_engine('sqlite:///' + str(path)).connect() as conn:
        assert conn.execute(text('SELECT version_num FROM alembic_version')).scalar() == '004'
        assert conn.execute(text('SELECT COUNT(*) FROM security_events')).scalar() == 6
        assert conn.execute(text('SELECT COUNT(*) FROM audit_findings')).scalar() == 3
        assert conn.execute(text('SELECT COUNT(*) FROM readings')).scalar() == 48


def test_local_evidence_is_explicitly_non_ai_and_redacted(tmp_path, monkeypatch):
    from scripts import exportar_evidencias
    engine = create_engine('sqlite:///' + str(tmp_path/'evidencias.sqlite'))
    Base.metadata.create_all(engine)
    monkeypatch.setenv('APP_ENV', 'development')
    monkeypatch.setenv('SEED_DEMO_DATA', 'true')
    monkeypatch.setattr(seed, 'SessionLocal', sessionmaker(bind=engine))
    monkeypatch.setattr(exportar_evidencias, 'SessionLocal', sessionmaker(bind=engine))
    seed.main()
    evidence = exportar_evidencias.generate()
    result=json.dumps(evidence,ensure_ascii=False)
    assert evidence['actual_openai_call'] is False
    assert evidence['pii_taint']['blocked'] is True
    assert evidence['counts']['synthetic_security_events'] == 6
    assert all(c['example_analysis']['mode']=='regras_locais' for c in evidence['soc_examples'])
    assert 'SIMULADA_NUNCA_REAL' not in result and '000.000.000-00' not in result
    assert 'Comprometimento não confirmado' in result
    engine.dispose()


def test_demo_tour_is_visible_and_development_only(client, token, monkeypatch):
    from app.main import app
    markup=client.get('/admin').text
    js=Path('static/admin.js').read_text()
    assert 'id="demo-tour"' in markup and "$('demo-tour').addEventListener" in js
    monkeypatch.setenv('APP_ENV','production')
    response=client.post('/api/v1/admin/security/demo-scenario',
        headers={'Authorization': 'Bearer ' + token})
    assert response.status_code == 403
    monkeypatch.setenv('APP_ENV','test')
