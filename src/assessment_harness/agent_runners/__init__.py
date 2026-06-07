"""Agent runner protocol implementations.

Only the framework-neutral protocol and deterministic mock runner live here
for now. Real SDK integrations are later Phase 2 work.
"""

from assessment_harness.agent_runners.base import AgentRunResult, AgentRunner
from assessment_harness.agent_runners.deterministic import (
    DeterministicExtractionRunner,
)
from assessment_harness.agent_runners.integrity import (
    CandidateRunIntegrityResult,
    classify_candidate_run_integrity,
    classify_deep_candidate_run_integrity,
)
from assessment_harness.agent_runners.mock import MockFixtureRunner
from assessment_harness.agent_runners.normalization import normalize_result_candidates
from assessment_harness.agent_runners.validation import validate_candidate_audit_trace

__all__ = [
    "AgentRunResult",
    "AgentRunner",
    "CandidateRunIntegrityResult",
    "DeterministicExtractionRunner",
    "MockFixtureRunner",
    "classify_candidate_run_integrity",
    "classify_deep_candidate_run_integrity",
    "normalize_result_candidates",
    "validate_candidate_audit_trace",
]
