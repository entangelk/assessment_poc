"""Framework-neutral agent runner protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


@dataclass(frozen=True)
class AgentRunResult:
    """Result returned by an agent runner.

    Candidate-generation runners and verifier runners will eventually return
    richer artifacts. The shared boundary starts with run identity,
    finish reason, and append-only trace data so orchestration can stay
    framework-neutral.
    """

    run_id: str
    runner_name: str
    finish_reason: str
    artifacts: Mapping[str, Any] = field(default_factory=dict)
    audit_trace: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    raw_trace: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    error_message: str | None = None


@runtime_checkable
class AgentRunner(Protocol):
    """Protocol every concrete agent runner must satisfy."""

    name: str

    def run(
        self,
        spec_path: Path,
        rubric_path: Path,
        tools: Sequence[Any],
        max_turns: int,
        policy: Mapping[str, Any],
    ) -> AgentRunResult:
        """Run one extraction/verifier pass and return isolated artifacts."""
