"""Validation helpers for isolated agent-run artifacts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from assessment_harness.schemas import validate


def validate_candidate_audit_trace(
    candidates: Mapping[str, Any],
    audit_trace: Sequence[Mapping[str, Any]],
) -> list[str]:
    """Validate candidate artifacts and their audit-trace run attribution."""
    errors: list[str] = []
    errors.extend(f"candidates: {error}" for error in validate("candidates", candidates))

    trace_run_ids: set[str] = set()
    for index, event in enumerate(audit_trace):
        trace_errors = validate("agent_trace", event)
        errors.extend(f"audit_trace/{index}: {error}" for error in trace_errors)
        run_id = event.get("run_id")
        if isinstance(run_id, str):
            trace_run_ids.add(run_id)

    for section in (
        "spec_item_candidates",
        "rubric_item_candidates",
        "trace_link_candidates",
    ):
        entries = candidates.get(section, [])
        if not isinstance(entries, list):
            continue
        for index, candidate in enumerate(entries):
            if not isinstance(candidate, Mapping):
                continue
            run_id = candidate.get("agent_run_id")
            if isinstance(run_id, str) and run_id not in trace_run_ids:
                errors.append(
                    f"{section}/{index}/agent_run_id: {run_id!r} has no matching "
                    "audit_trace run_id"
                )

    return errors
