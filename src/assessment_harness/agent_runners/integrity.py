"""Structural run-level classification for normalized candidate artifacts."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from assessment_harness.agent_runners.validation import validate_candidate_audit_trace
from assessment_harness.models import SourceSnapshot
from assessment_harness.rules import run_rule_zero


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


def classify_deep_candidate_run_integrity(
    candidates: Mapping[str, Any],
    audit_trace: Sequence[Mapping[str, Any]],
    snapshot: SourceSnapshot,
) -> CandidateRunIntegrityResult:
    """Classify one normalized candidate run through candidate Rule 0 checks."""
    structural = classify_candidate_run_integrity(candidates, audit_trace)
    if structural.integrity_status != "structurally_validated":
        return structural

    diagnostics = run_rule_zero(
        _candidate_doc(candidates, "spec_item_candidates", "spec_items"),
        _candidate_doc(candidates, "rubric_item_candidates", "rubric_items"),
        _candidate_doc(candidates, "trace_link_candidates", "trace_links"),
        snapshot,
    )
    if not diagnostics:
        return CandidateRunIntegrityResult(
            integrity_status="validated",
            candidates=_with_integrity_status(candidates, "validated"),
            errors=(),
        )

    errors = tuple(
        f"rule_zero/{diagnostic.code}: {diagnostic.message}"
        for diagnostic in diagnostics
    )
    integrity_status = _deep_rule_zero_status(
        tuple(diagnostic.code for diagnostic in diagnostics)
    )
    return CandidateRunIntegrityResult(
        integrity_status=integrity_status,
        candidates=_with_integrity_status(candidates, integrity_status),
        errors=errors,
    )


_INVALID_REFERENCE_CODES = frozenset(
    {
        "dangling_rubric_reference",
        "dangling_spec_reference",
        "duplicate_rubric_id",
        "duplicate_spec_id",
        "evidence_quote_empty",
        "evidence_quote_missing_for_spec_id",
        "evidence_quote_spec_id_mismatch",
    }
)


_SOURCE_GROUNDING_MISMATCH_CODES = frozenset(
    {
        "evidence_quote_not_in_snapshot_span",
        "evidence_source_ref_mismatch_with_spec",
        "evidence_source_ref_unknown_document",
        "rubric_quote_not_in_snapshot_span",
        "rubric_source_ref_span_invalid",
        "rubric_source_ref_unknown_document",
        "source_document_hash_mismatch",
        "source_document_missing",
        "spec_text_not_in_snapshot_span",
        "spec_quote_not_in_snapshot_span",
        "spec_source_ref_span_invalid",
        "spec_source_ref_unknown_document",
    }
)


_QUOTE_MISMATCH_CODES = frozenset({"evidence_quote_token_sequence_mismatch"})


def _deep_rule_zero_status(diagnostic_codes: tuple[str, ...]) -> str:
    if any(
        code in _INVALID_REFERENCE_CODES
        or code not in _SOURCE_GROUNDING_MISMATCH_CODES | _QUOTE_MISMATCH_CODES
        for code in diagnostic_codes
    ):
        return "invalid_reference"
    if any(code in _SOURCE_GROUNDING_MISMATCH_CODES for code in diagnostic_codes):
        return "source_grounding_mismatch"
    return "quote_mismatch"


def _candidate_doc(
    candidates: Mapping[str, Any],
    candidate_section: str,
    item_section: str,
) -> dict[str, list[dict[str, Any]]]:
    return {
        item_section: [
            dict(candidate["proposed_item"])
            for candidate in candidates.get(candidate_section, [])
            if isinstance(candidate, Mapping)
            and isinstance(candidate.get("proposed_item"), Mapping)
        ]
    }


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
