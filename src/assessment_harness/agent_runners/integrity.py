"""Structural run-level classification for normalized candidate artifacts."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from assessment_harness.agent_runners.validation import validate_candidate_audit_trace


_CANDIDATE_SECTIONS = (
    "spec_item_candidates",
    "rubric_item_candidates",
    "trace_link_candidates",
)


@dataclass(frozen=True)
class CandidateRunIntegrityResult:
    """Result of structural candidate artifact classification."""

    integrity_status: str
    candidates: dict[str, list[dict[str, Any]]]
    errors: tuple[str, ...]


def classify_candidate_run_integrity(
    candidates: Mapping[str, Any],
    audit_trace: Sequence[Mapping[str, Any]],
) -> CandidateRunIntegrityResult:
    """Classify one normalized candidate run before deep Rule 0 validation."""
    errors = tuple(validate_candidate_audit_trace(candidates, audit_trace))
    if not errors:
        return CandidateRunIntegrityResult(
            integrity_status="structurally_validated",
            candidates=_with_integrity_status(candidates, "structurally_validated"),
            errors=(),
        )

    integrity_status = (
        "schema_violation"
        if any(_is_schema_error(error) for error in errors)
        else "trace_attribution_error"
    )
    return CandidateRunIntegrityResult(
        integrity_status=integrity_status,
        candidates=_with_integrity_status(candidates, integrity_status),
        errors=errors,
    )


def _is_schema_error(error: str) -> bool:
    return error.startswith("candidates:") or error.startswith("audit_trace/")


def _with_integrity_status(
    candidates: Mapping[str, Any],
    integrity_status: str,
) -> dict[str, list[dict[str, Any]]]:
    updated: dict[str, list[dict[str, Any]]] = {}
    for section in _CANDIDATE_SECTIONS:
        entries = candidates.get(section, [])
        updated_entries: list[dict[str, Any]] = []
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, Mapping):
                    updated_entry = copy.deepcopy(dict(entry))
                    updated_entry["integrity_status"] = integrity_status
                    updated_entries.append(updated_entry)
        updated[section] = updated_entries
    return updated
