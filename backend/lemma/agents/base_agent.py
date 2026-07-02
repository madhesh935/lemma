"""
AEGIS-OS Lemma SDK — Base Agent
================================
All investigation agents inherit from BaseAgent.
Provides: memory access, function calling, LLM integration,
structured output, and audit trail.
"""
from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger("aegis.agent.base")


@dataclass
class AgentResult:
    """Standardized output from any Lemma agent."""
    agent_name: str
    pod_id: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    duration_seconds: float = 0.0
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "pod_id": self.pod_id,
            "success": self.success,
            "output": self.output,
            "reasoning": self.reasoning,
            "tool_calls": self.tool_calls,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class BaseAgent(ABC):
    """
    Abstract base for all AEGIS-OS Lemma agents.

    Each agent:
      - Has a unique name and system prompt
      - Can invoke Lemma Functions
      - Records actions to Pod agent memory
      - Returns a structured AgentResult
    """
    name: str = "base_agent"
    description: str = "Base Lemma Agent"
    version: str = "1.0.0"

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.logger = logging.getLogger(f"aegis.agent.{self.name}")
        self._tool_calls: List[Dict] = []

    @abstractmethod
    async def run(self, pod_id: str, context: Dict[str, Any]) -> AgentResult:
        """Execute the agent's task. Must be overridden by subclasses."""
        ...

    async def invoke(self, pod_id: str, context: Dict[str, Any]) -> AgentResult:
        """Public entry point — wraps run() with timing, memory, and error handling."""
        start = time.time()
        self._tool_calls = []
        self.logger.info(f"Agent [{self.name}] starting on pod {pod_id}")

        try:
            result = await self.run(pod_id, context)
            result.duration_seconds = round(time.time() - start, 2)
            result.tool_calls = self._tool_calls

            # Record to pod agent memory if pod is available
            pod = context.get("pod")
            if pod:
                pod.record_agent_action(
                    agent_name=self.name,
                    action="completed",
                    summary=result.reasoning[:200] if result.reasoning else "Task completed",
                    data={"success": result.success, "duration": result.duration_seconds},
                )
            self.logger.info(f"Agent [{self.name}] completed in {result.duration_seconds}s")
            return result

        except Exception as e:
            self.logger.error(f"Agent [{self.name}] failed: {e}")
            return AgentResult(
                agent_name=self.name,
                pod_id=pod_id,
                success=False,
                error=str(e),
                duration_seconds=round(time.time() - start, 2),
            )

    def _call_function(self, fn_name: str, **kwargs) -> Any:
        """Log a function call for transparency and audit."""
        self._tool_calls.append({
            "function": fn_name,
            "args": {k: str(v)[:100] for k, v in kwargs.items()},
            "called_at": datetime.now(timezone.utc).isoformat(),
        })
        self.logger.debug(f"[{self.name}] calling function: {fn_name}")

    def _llm_generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Call the LLM with fallback to a mock response."""
        if not self.llm:
            return f"[Mock LLM Response for {self.name}]: Analysis complete."
        try:
            return self.llm.generate(prompt, system=system or self._get_system_prompt())
        except Exception as e:
            self.logger.warning(f"LLM call failed: {e}")
            return f"[LLM Error: {e}]"

    def _get_system_prompt(self) -> str:
        return (
            f"You are the {self.description} in the AEGIS-OS forensic intelligence platform. "
            f"You analyze evidence, produce structured outputs, and support investigators. "
            f"Never make definitive guilt declarations. Always cite evidence. Be precise."
        )

    @classmethod
    def info(cls) -> Dict[str, str]:
        return {
            "name": cls.name,
            "description": cls.description,
            "version": cls.version,
        }
