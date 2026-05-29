"""Normalization helpers for runner-produced artifacts."""

from __future__ import annotations

from typing import Any

from assessment_harness.agent_runners.base import AgentRunResult


_COMPACTING_ONLY_FIELDS = {
    "identity_basis",
    "reviewed_at",
    "reviewed_by",
    "sources",
    "support",
    "variants",
}


def normalize_result_candidates(
    result: AgentRunResult,
    integrity_status: str = "pending_check",
) -> dict[str, list[dict[str, Any]]]:
    """Convert runner artifact items into pre-compacting candidate artifacts."""
    return {
        "spec_item_candidates": _normalize_items(
            result=result,
            artifact_key="spec_items",
            item_key="spec_items",
            candidate_prefix="SC",
            integrity_status=integrity_status,
        ),
        "rubric_item_candidates": _normalize_items(
            result=result,
            artifact_key="rubric_items",
            item_key="rubric_items",
            candidate_prefix="RC",
            integrity_status=integrity_status,
        ),
        "trace_link_candidates": _normalize_items(
            result=result,
            artifact_key="trace_links",
            item_key="trace_links",
            candidate_prefix="TC",
            integrity_status=integrity_status,
        ),
    }


def _normalize_items(
    *,
    result: AgentRunResult,
    artifact_key: str,
    item_key: str,
    candidate_prefix: str,
    integrity_status: str,
) -> list[dict[str, Any]]:
    artifact = result.artifacts[artifact_key]
    items = artifact[item_key]

    candidates: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        proposed_item = {
            key: value
            for key, value in dict(item).items()
            if key not in _COMPACTING_ONLY_FIELDS
        }
        candidates.append(
            {
                "candidate_id": f"{candidate_prefix}{index}",
                "proposed_item": proposed_item,
                "agent_runner": result.runner_name,
                "agent_run_id": result.run_id,
                "integrity_status": integrity_status,
            }
        )
    return candidates
