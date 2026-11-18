"""Módulo PII: detecção heurística e redação sem persistir o conteúdo bruto."""
import re

PATTERNS = {
    "cpf": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "saude": re.compile(r"(?i)\b(?:CID(?:-?10)?\s*[:=]\s*[A-Z]\d{2}(?:\.\d{1,2})?|(?:diagn[oó]stico|condi[cç][aã]o\s+de\s+sa[uú]de|exame\s+m[eé]dico)\s*[:=]\s*[^;\n]{3,80})"),
    "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "telefone": re.compile(r"(?<!\d)(?:\+55\s?)?\(?\d{2}\)?\s?9?\d{4}[\s\-]?\d{4}(?!\d)"),
    "senha": re.compile(r"(?i)\b(?:senha|password|token|api[_\-]?key)\s*[:=]\s*\S+"),
}

REMEDIATION = {
    "saude": "Dados de saúde são sensíveis: limite a finalidade, restrinja acesso e não exponha informações clínicas em logs.",
    "cpf": "Evite transmitir ou registrar CPFs; aplique mascaramento e retenção mínima.",
    "email": "Não registre e-mails completos em logs públicos; substitua por pseudônimo.",
    "telefone": "Oculte telefones em logs e painéis; restrinja acesso aos registros.",
    "senha": "Nunca registre credenciais ou tokens. Remova-os antes de qualquer log ou envio externo.",
}

def classify(text: str) -> dict:
    kinds = [name for name, regex in PATTERNS.items() if regex.search(text)]
    redacted = text
    for name, regex in PATTERNS.items():
        redacted = regex.sub(f"[{name.upper()}_REDACTED]", redacted)
    return {"pii_types": kinds, "redacted": redacted[:180]}
