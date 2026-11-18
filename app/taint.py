"""Rastreamento explícito: entrada não confiável -> sanitização -> destino.
Demonstração de taint analysis para requisitos acadêmicos (não é SAST completo).
"""
from dataclasses import dataclass
from app.pii import classify, REMEDIATION

UNSAFE_SINKS = {"log_bruto", "resposta_publica", "servico_externo"}

@dataclass(frozen=True)
class TaintedValue:
    value: str
    origin: str
    sanitized: bool = False


def redact(value: TaintedValue) -> TaintedValue:
    return TaintedValue(classify(value.value)["redacted"], value.origin, sanitized=True)


def audit_flow(text: str, source: str, sink: str) -> dict:
    incoming = TaintedValue(value=text, origin=source)
    pii = classify(incoming.value)
    unsafe = sink in UNSAFE_SINKS
    sanitized = redact(incoming)
    # Uma saída pública ou log bruto com entrada contaminada é bloqueada.
    blocked = unsafe and bool(pii["pii_types"]) and not incoming.sanitized
    if blocked:
        severity = "high" if any(t in pii["pii_types"] for t in ("senha", "saude")) else "medium"
    else:
        severity = "info"
    fix = " ".join(REMEDIATION[t] for t in pii["pii_types"]) or "Valide entrada, utilize queries parametrizadas e evite logs de payloads brutos."
    return {
        "source": source,
        "sink": sink,
        "tainted": True,
        "pii_types": pii["pii_types"],
        "blocked": blocked,
        "action": "bloqueado" if blocked else "permitido",
        "severity": severity,
        "redacted_preview": sanitized.value,
        "sanitization_applied": True,
        "remediation": fix,
        "explanation": "Conteúdo não confiável não alcançou o destino sem sanitização." if blocked else "Fluxo demonstrativo permitido; a entrada original permanece não confiável.",
    }
