from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Float, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.base import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="admin")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Station(Base):
    __tablename__ = "stations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    setting: Mapped[str] = mapped_column(String(120))
    simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    api_key_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    readings: Mapped[list["Reading"]] = relationship(back_populates="station")

class Reading(Base):
    __tablename__ = "readings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"), index=True)
    temperature_c: Mapped[float] = mapped_column(Float)
    humidity_pct: Mapped[float] = mapped_column(Float)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    station: Mapped[Station] = relationship(back_populates="readings")

class SecurityEvent(Base):
    __tablename__ = "security_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20))
    outcome: Mapped[str] = mapped_column(String(30))
    summary: Mapped[str] = mapped_column(String(300))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    triage_status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)
    triage_note: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    triaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AuditFinding(Base):
    __tablename__ = "audit_findings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(60))
    sink: Mapped[str] = mapped_column(String(60))
    field: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(30))
    evidence_redacted: Mapped[str] = mapped_column(String(200), default="")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remediation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class SecurityTriageAction(Base):
    """Trilha de decisões administrativas, sem PII, credenciais ou payload bruto."""
    __tablename__ = "security_triage_actions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("security_events.id"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    previous_status: Mapped[str] = mapped_column(String(20))
    next_status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
