"""
AEGIS-OS Lemma SDK — Investigation Pod
=======================================
The Pod is the fundamental Lemma unit. Every forensic investigation lives
inside its own Pod, with isolated state, files, agents, and workflow.

Architecture:
  Pod
  ├── Metadata (case number, title, status, investigators)
  ├── Files (uploaded evidence files)
  ├── Datastore (structured entities: persons, locations, events, etc.)
  ├── Workflow State (which step the investigation is at)
  └── Agent Memory (what each agent has processed and concluded)
"""
from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger("aegis.lemma.pod")


class PodStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    archived = "archived"
    closed = "closed"


@dataclass
class AgentMemoryEntry:
    """A single record in the agent's memory."""
    agent_name: str
    timestamp: str
    action: str
    summary: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PodAgentMemory:
    """Per-agent memory store within a Pod."""
    entries: List[AgentMemoryEntry] = field(default_factory=list)

    def record(self, agent_name: str, action: str, summary: str, data: Dict = None) -> None:
        self.entries.append(AgentMemoryEntry(
            agent_name=agent_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            summary=summary,
            data=data or {},
        ))

    def get_agent_history(self, agent_name: str) -> List[AgentMemoryEntry]:
        return [e for e in self.entries if e.agent_name == agent_name]

    def to_context_string(self, agent_name: str, last_n: int = 5) -> str:
        """Format recent entries as an LLM-friendly context string."""
        history = self.get_agent_history(agent_name)[-last_n:]
        if not history:
            return "No previous context for this agent."
        lines = []
        for e in history:
            lines.append(f"[{e.timestamp[:19]}] {e.action}: {e.summary}")
        return "\n".join(lines)


@dataclass
class InvestigationPod:
    """
    Lemma Pod — The atomic container for a forensic investigation.

    Every case becomes its own Pod. The Pod owns:
    - Identity (pod_id, pod_key, name)
    - Access control (investigators)
    - Agent memory (what each agent knows)
    - Workflow state tracking
    """
    pod_id: str
    pod_key: str                         # e.g. CASE-2026-001
    name: str
    description: str = ""
    status: PodStatus = PodStatus.active
    severity: str = "medium"             # low | medium | high | critical
    district: Optional[str] = None
    fir_number: Optional[str] = None
    investigators: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_memory: PodAgentMemory = field(default_factory=PodAgentMemory)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    closed_at: Optional[str] = None

    # ─── Lifecycle ──────────────────────────────────────────────────────────
    def suspend(self, reason: str = "") -> None:
        self.status = PodStatus.suspended
        self.metadata["suspend_reason"] = reason
        self._touch()
        logger.info(f"Pod {self.pod_key} suspended: {reason}")

    def resume(self) -> None:
        self.status = PodStatus.active
        self.metadata.pop("suspend_reason", None)
        self._touch()
        logger.info(f"Pod {self.pod_key} resumed.")

    def archive(self) -> None:
        self.status = PodStatus.archived
        self.closed_at = datetime.now(timezone.utc).isoformat()
        self._touch()
        logger.info(f"Pod {self.pod_key} archived.")

    def close(self) -> None:
        self.status = PodStatus.closed
        self.closed_at = datetime.now(timezone.utc).isoformat()
        self._touch()
        logger.info(f"Pod {self.pod_key} closed.")

    # ─── Agent Memory Interface ─────────────────────────────────────────────
    def record_agent_action(self, agent_name: str, action: str, summary: str, data: Dict = None) -> None:
        """Record an agent action into the pod's memory."""
        self.agent_memory.record(agent_name, action, summary, data)
        self._touch()

    def get_agent_context(self, agent_name: str) -> str:
        """Get formatted context for an agent."""
        return self.agent_memory.to_context_string(agent_name)

    # ─── Serialization ──────────────────────────────────────────────────────
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    def to_summary(self) -> Dict[str, Any]:
        """Lightweight summary for API responses."""
        return {
            "pod_id": self.pod_id,
            "pod_key": self.pod_key,
            "name": self.name,
            "status": self.status.value,
            "severity": self.severity,
            "district": self.district,
            "investigators": self.investigators,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    @classmethod
    def create(
        cls,
        name: str,
        pod_key: Optional[str] = None,
        description: str = "",
        severity: str = "medium",
        district: Optional[str] = None,
        fir_number: Optional[str] = None,
        investigators: Optional[List[str]] = None,
        **metadata,
    ) -> "InvestigationPod":
        """Factory method — creates a new Investigation Pod."""
        pod_id = str(uuid.uuid4())
        if not pod_key:
            year = datetime.now().year
            short_id = pod_id[:8].upper()
            pod_key = f"CASE-{year}-{short_id}"

        pod = cls(
            pod_id=pod_id,
            pod_key=pod_key,
            name=name,
            description=description,
            severity=severity,
            district=district,
            fir_number=fir_number,
            investigators=investigators or [],
            metadata=metadata,
        )
        logger.info(f"New Pod created: {pod_key} | {name}")
        return pod


class PodManager:
    """
    In-memory Pod registry with database persistence hook.
    In production, pods are persisted in PostgreSQL.
    """
    _pods: Dict[str, InvestigationPod] = {}

    @classmethod
    def register(cls, pod: InvestigationPod) -> None:
        cls._pods[pod.pod_id] = pod

    @classmethod
    def get(cls, pod_id: str) -> Optional[InvestigationPod]:
        return cls._pods.get(pod_id)

    @classmethod
    def get_by_key(cls, pod_key: str) -> Optional[InvestigationPod]:
        for pod in cls._pods.values():
            if pod.pod_key == pod_key:
                return pod
        return None

    @classmethod
    def list_active(cls) -> List[InvestigationPod]:
        return [p for p in cls._pods.values() if p.status == PodStatus.active]

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> InvestigationPod:
        """Reconstruct a Pod from a database record."""
        return InvestigationPod(
            pod_id=row["id"],
            pod_key=row["pod_key"],
            name=row["name"],
            description=row.get("description", ""),
            status=PodStatus(row.get("status", "active")),
            severity=row.get("severity", "medium"),
            district=row.get("district"),
            fir_number=row.get("fir_number"),
            investigators=row.get("assigned_investigators") or [],
            metadata=row.get("metadata") or {},
        )
