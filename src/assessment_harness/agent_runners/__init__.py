"""Agent runner protocol implementations.

Only the framework-neutral protocol and deterministic mock runner live here
for now. Real SDK integrations are later Phase 2 work.
"""

from assessment_harness.agent_runners.base import AgentRunResult, AgentRunner
from assessment_harness.agent_runners.mock import MockFixtureRunner
from assessment_harness.agent_runners.validation import validate_candidate_audit_trace

__all__ = [
    "AgentRunResult",
    "AgentRunner",
    "MockFixtureRunner",
    "validate_candidate_audit_trace",
]
