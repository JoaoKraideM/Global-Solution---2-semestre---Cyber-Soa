"""Gera evidências acadêmicas locais, sem senhas, tokens ou registros brutos.

Não envia nada à OpenAI. Para análise real, use o botão no admin com OPENAI_API_KEY.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select, func

from app.database import SessionLocal
from app.models import Station, Reading, SecurityEvent, AuditFinding
from app.security_intelligence import local_report, is_security_signal
from app.taint import audit_flow


def generate():
    with SessionLocal() as db:
        stations = db.scalar(select(func.count()).select_from(Station)) or 0
        readings = db.scalar(select(func.count()).select_from(Reading).where(Reading.is_simulated.is_(True))) or 0
        events = db.scalars(select(SecurityEvent).where(SecurityEvent.is_demo.is_(True)).order_by(SecurityEvent.id)).all()
        findings = db.scalars(select(AuditFinding).where(AuditFinding.is_demo.is_(True)).order_by(AuditFinding.id)).all()
        cases = []
        for e in events:
            if not is_security_signal(e):
                continue
            report = local_report(e)
            cases.append({"event_id": e.id, "scenario": e.summary, "severity": e.severity,
                "is_demo": True, "example_analysis": report})
    flow = audit_flow("CPF: 000.000.000-00; senha: SIMULADA_NUNCA_REAL", "formulario", "log_bruto")
    return {
        "project": "SombraViva — Global Solution FIAP 2026.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "origin": "DEMONSTRACAO_DIDATICA", "actual_openai_call": False,
        "disclaimer": "Nenhum ataque real ocorreu e este relatório não representa saída da OpenAI.",
        "counts": {"stations": stations, "synthetic_readings": readings,
                   "synthetic_security_events": len(events), "synthetic_pii_findings": len(findings)},
        "pii_taint": {"source": flow["source"], "sink": flow["sink"],
                      "pii_types": flow["pii_types"], "blocked": flow["blocked"],
                      "severity": flow["severity"], "redacted_preview": "[AMOSTRA_FICTICIA_REDACTED]"},
        "soc_examples": cases,
        "manual_ai_demo": "Entre em /admin, marque Incluir cenários fictícios e clique Examinar com IA / regras. Com OPENAI_API_KEY válida será feita uma chamada opt-in; sem ela, resposta local identificada como regras."
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", default="evidencias/evidencias_soa_cyber_demo.json")
    args=parser.parse_args()
    path=Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(generate(), ensure_ascii=False, indent=2), encoding="utf-8")
    print("Evidências sintéticas geradas:", path)
    print("Sem envio de payloads à OpenAI e sem segredos do .env.")


if __name__ == "__main__":
    main()
