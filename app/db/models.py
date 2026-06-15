from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="representative", nullable=False)  # admin, manager, representative
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="discovered", nullable=False)  # discovered, researched, qualified, disqualified
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    # Relationships
    reports: Mapped[List["ResearchReport"]] = relationship("ResearchReport", back_populates="lead", cascade="all, delete-orphan")
    outreach_messages: Mapped[List["OutreachMessage"]] = relationship("OutreachMessage", back_populates="lead", cascade="all, delete-orphan")

class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    profile: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    growth_signals: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    hiring_signals: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    tech_adoption: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    risks: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    raw_report: Mapped[str] = mapped_column(String(10000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="reports")

class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    email_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    email_body: Mapped[str] = mapped_column(String(5000), nullable=False)
    linkedin_message: Mapped[str] = mapped_column(String(2000), nullable=False)
    sales_angle: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)  # draft, sent
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="outreach_messages")

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    target_criteria: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    current_step: Mapped[str] = mapped_column(String(50), nullable=False)  # START, discover_companies, research_companies, qualify_companies, generate_outreach, human_review, END
    status: Mapped[str] = mapped_column(String(50), default="RUNNING", nullable=False)  # RUNNING, AWAITING_REVIEW, COMPLETED, FAILED
    variables: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # WorkflowState dict
    errors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_run_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_calls: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    token_usage: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    execution_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    log_message: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
