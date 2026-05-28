"""Agent runner protocol implementations.

Only the framework-neutral protocol and deterministic mock runner live here
for now. Real SDK integrations are later Phase 2 work.
"""

from assessment_harness.agent_runners.base import AgentRunResult, AgentRunner
from assessment_harness.agent_runners.mock import MockFixtureRunner

__all__ = ["AgentRunResult", "AgentRunner", "MockFixtureRunner"]
