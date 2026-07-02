"""
AEGIS-OS Database Layer — SQLAlchemy ORM models.
All investigation entities persisted in PostgreSQL.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    from sqlalchemy import (
        String, Text, Float, Boolean, Integer, DateTime, JSON,
        ForeignKey, Enum as SAEnum, Index
    )
    from sqlalchemy.dialects.postgresql import UUID, ARRAY
    from sqlalchemy.orm import Mapped, mapped_column, relationship
    from sqlalchemy.sql import func

    from database.postgres import Base

    _SQLALCHEMY_AVAILABLE = True
except ModuleNotFoundError:
    import logging
    logging.getLogger("aegis.models").warning("SQLAlchemy/asyncpg not installed — ORM models disabled.")
    _SQLALCHEMY_AVAILABLE = False
    # Create stub Base so the file can still be imported
    class Base:
        pass

if _SQLALCHEMY_AVAILABLE:
    pass  # All model classes below are defined at module level



def new_uuid() -> str:
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    lead_investigator = "lead_investigator"
    investigator = "investigator"
    viewer = "viewer"

class PodStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    archived = "archived"
    closed = "closed"

class EvidenceType(str, enum.Enum):
    autopsy_report = "autopsy_report"
    witness_statement = "witness_statement"
    image = "image"
    crime_scene_photo = "crime_scene_photo"
    gps_log = "gps_log"
    call_detail_record = "call_detail_record"
    cctv_video = "cctv_video"
    phone_metadata = "phone_metadata"
    medical_report = "medical_report"
    pdf = "pdf"
    json_data = "json_data"
    csv_data = "csv_data"
    video = "video"
    other = "other"

class PersonRole(str, enum.Enum):
    victim = "victim"
    suspect = "suspect"
    witness = "witness"
    investigator = "investigator"
    unknown = "unknown"

class WorkflowStep(str, enum.Enum):
    pod_created = "pod_created"
    evidence_uploaded = "evidence_uploaded"
    intake_running = "intake_running"
    intake_complete = "intake_complete"
    autopsy_analysis = "autopsy_analysis"
    digital_correlation = "digital_correlation"
    graph_update = "graph_update"
    timeline_build = "timeline_build"
    risk_assessment = "risk_assessment"
    hypothesis_gen = "hypothesis_gen"
    investigator_review = "investigator_review"
    report_generation = "report_generation"
    case_closed = "case_closed"

class ReportType(str, enum.Enum):
    executive = "executive"
    investigator = "investigator"
    court = "court"
    evidence_index = "evidence_index"

class AgentJobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ─── Users ────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    badge_number: Mapped[Optional[str]] = mapped_column(String(50))
    department: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.investigator)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime)

    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")


# ─── Investigation Pods ───────────────────────────────────────────────────────
class Pod(Base):
    __tablename__ = "pods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pod_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g. CASE-2026-001
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[PodStatus] = mapped_column(SAEnum(PodStatus), default=PodStatus.active)
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low|medium|high|critical
    district: Mapped[Optional[str]] = mapped_column(String(255))
    fir_number: Mapped[Optional[str]] = mapped_column(String(100))
    assigned_investigators: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    evidence: Mapped[List["Evidence"]] = relationship(back_populates="pod", cascade="all, delete-orphan")
    persons: Mapped[List["Person"]] = relationship(back_populates="pod", cascade="all, delete-orphan")
    timeline_events: Mapped[List["TimelineEvent"]] = relationship(back_populates="pod", cascade="all, delete-orphan")
    hypotheses: Mapped[List["Hypothesis"]] = relationship(back_populates="pod", cascade="all, delete-orphan")
    risk_scores: Mapped[List["RiskScore"]] = relationship(back_populates="pod", cascade="all, delete-orphan")
    reports: Mapped[List["Report"]] = relationship(back_populates="pod", cascade="all, delete-orphan")
    workflow_state: Mapped[Optional["WorkflowState"]] = relationship(back_populates="pod", uselist=False)
    agent_jobs: Mapped[List["AgentJob"]] = relationship(back_populates="pod")


# ─── Evidence ─────────────────────────────────────────────────────────────────
class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pod_id: Mapped[str] = mapped_column(String(36), ForeignKey("pods.id"), nullable=False, index=True)
    evidence_number: Mapped[str] = mapped_column(String(50))  # EV-001, EV-002, etc.
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_type: Mapped[EvidenceType] = mapped_column(SAEnum(EvidenceType), default=EvidenceType.other)
    file_path: Mapped[Optional[str]] = mapped_column(Text)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA-256
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)  # OCR output
    structured_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Entity extraction
    ai_classification: Mapped[Optional[str]] = mapped_column(String(100))
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    chain_of_custody: Mapped[Optional[List[Dict]]] = mapped_column(JSON, default=list)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(36))
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pod: Mapped["Pod"] = relationship(back_populates="evidence")

    __table_args__ = (Index("ix_evidence_pod_type", "pod_id", "evidence_type"),)


# ─── Persons ──────────────────────────────────────────────────────────────────
class Person(Base):
    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pod_id: Mapped[str] = mapped_column(String(36), ForeignKey("pods.id"), nullable=False, index=True)
    person_code: Mapped[Optional[str]] = mapped_column(String(50))  # V-001 (victim), S-001 (suspect)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[PersonRole] = mapped_column(SAEnum(PersonRole), default=PersonRole.unknown)
    age: Mapped[Optional[int]] = mapped_column(Integer)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    contact_number: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(Text)
    occupation: Mapped[Optional[str]] = mapped_column(String(255))
    known_associations: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    linked_evidence_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    risk_level: Mapped[str] = mapped_column(String(20), default="unknown")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pod: Mapped["Pod"] = relationship(back_populates="persons")


# ─── Timeline Events ──────────────────────────────────────────────────────────
class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pod_id: Mapped[str] = mapped_column(String(36), ForeignKey("pods.id"), nullable=False, index=True)
    event_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    event_type: Mapped[str] = mapped_column(String(100))  # gps | cdr | cctv | witness | autopsy | financial
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    location_name: Mapped[Optional[str]] = mapped_column(String(255))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    source_evidence_id: Mapped[Optional[str]] = mapped_column(String(36))
    persons_involved: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    is_conflicting: Mapped[bool] = mapped_column(Boolean, default=False)
    conflict_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pod: Mapped["Pod"] = relationship(back_populates="timeline_events")


# ─── Hypotheses ───────────────────────────────────────────────────────────────
class Hypothesis(Base):
    __tablename__ = "hypotheses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pod_id: Mapped[str] = mapped_column(String(36), ForeignKey("pods.id"), nullable=False, index=True)
    hypothesis_number: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    supporting_evidence_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    contradicting_evidence_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    additional_evidence_needed: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    generated_by: Mapped[str] = mapped_column(String(100), default="hypothesis_agent")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    pod: Mapped["Pod"] = relationship(back_populates="hypotheses")


# ─── Risk Scores ──────────────────────────────────────────────────────────────
class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pod_id: Mapped[str] = mapped_column(String(36), ForeignKey("pods.id"), nullable=False, index=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    urgency_level: Mapped[str] = mapped_column(String(20))  # low|medium|high|critical
    factors: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    anomalies: Mapped[Optional[List[Dict]]] = mapped_column(JSON, default=list)
    inconsistencies: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    recommendations: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    calculated_by: Mapped[str] = mapped_column(String(100), default="risk_assessment_agent")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pod: Mapped["Pod"] = relationship(back_populates="risk_scores")


# ─── Reports ──────────────────────────────────────────────────────────────────
class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pod_id: Mapped[str] = mapped_column(String(36), ForeignKey("pods.id"), nullable=False, index=True)
    report_type: Mapped[ReportType] = mapped_column(SAEnum(ReportType))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_markdown: Mapped[Optional[str]] = mapped_column(Text)
    content_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft|pending_approval|approved|finalized
    approved_by: Mapped[Optional[str]] = mapped_column(String(36))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    generated_by: Mapped[str] = mapped_column(String(100), default="report_agent")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    pod: Mapped["Pod"] = relationship(back_populates="reports")


# ─── Workflow States ──────────────────────────────────────────────────────────
class WorkflowState(Base):
    __tablename__ = "workflow_states"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pod_id: Mapped[str] = mapped_column(String(36), ForeignKey("pods.id"), unique=True, nullable=False)
    current_step: Mapped[WorkflowStep] = mapped_column(SAEnum(WorkflowStep), default=WorkflowStep.pod_created)
    step_history: Mapped[Optional[List[Dict]]] = mapped_column(JSON, default=list)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    pause_reason: Mapped[Optional[str]] = mapped_column(String(500))
    approved_by: Mapped[Optional[str]] = mapped_column(String(36))
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    pod: Mapped["Pod"] = relationship(back_populates="workflow_state")


# ─── Agent Jobs ───────────────────────────────────────────────────────────────
class AgentJob(Base):
    __tablename__ = "agent_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pod_id: Mapped[str] = mapped_column(String(36), ForeignKey("pods.id"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[AgentJobStatus] = mapped_column(SAEnum(AgentJobStatus), default=AgentJobStatus.pending)
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    tool_calls: Mapped[Optional[List[Dict]]] = mapped_column(JSON, default=list)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    pod: Mapped["Pod"] = relationship(back_populates="agent_jobs")


# ─── Audit Logs ───────────────────────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # CREATE|READ|UPDATE|DELETE|INVOKE
    resource_type: Mapped[str] = mapped_column(String(100))  # pod|evidence|agent|report|workflow
    resource_id: Mapped[Optional[str]] = mapped_column(String(36))
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")

    __table_args__ = (Index("ix_audit_timestamp_user", "timestamp", "user_id"),)
