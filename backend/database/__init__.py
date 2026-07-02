"""AEGIS-OS Database package — lazy imports, graceful fallback if DB not installed."""

try:
    from database.postgres import Base, get_db, init_db, engine
    from database.models import (
        User, Pod, Evidence, Person, TimelineEvent,
        Hypothesis, RiskScore, Report, WorkflowState, AgentJob, AuditLog
    )
    __all__ = [
        "Base", "get_db", "init_db", "engine",
        "User", "Pod", "Evidence", "Person", "TimelineEvent",
        "Hypothesis", "RiskScore", "Report", "WorkflowState", "AgentJob", "AuditLog",
    ]
except ModuleNotFoundError as e:
    import logging
    logging.getLogger("aegis.db").warning(f"Database modules unavailable (install asyncpg/sqlalchemy): {e}")
    Base = get_db = init_db = engine = None
    User = Pod = Evidence = Person = TimelineEvent = None
    Hypothesis = RiskScore = Report = WorkflowState = AgentJob = AuditLog = None
    __all__ = []
