"""Rule 0 reference integrity unit tests.

Each rule has two-directional guards: an under-strict guard (the violation is
caught) and an over-strict guard (a normal case is *not* falsely flagged).
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from assessment_harness.models import Document, SourceSnapshot
from assessment_harness.rules import run_rule_zero, severity_counts


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _baseline_spec() -> dict[str, Any]:
    return {
        "spec_items": [
            {
                "id": "S1",
                "text": "Implement refund handling for cancelled orders.",
                "requirement_level": "must",
                "source_ref": {
                    "document_id": "DOC_SPEC",
                    "start_line": 1,
                    "end_line": 1,
                },
            },
            {
                "id": "S2",
                "text": "Provide an audit log for every refund decision.",
                "requirement_level": "optional",
                "source_ref": {
                    "document_id": "DOC_SPEC",
                    "start_line": 2,
                    "end_line": 2,
                },
            },
        ]
    }


def _baseline_rubric() -> dict[str, Any]:
    return {
        "rubric_items": [
            {
                "id": "R1",
                "title": "Refund handling",
                "evaluation_role": "scored",
                "weight": 10,
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 1,
                    "end_line": 1,
                },
            }
        ]
    }


def _baseline_traces() -> dict[str, Any]:
    return {
        "trace_links": [
            {
                "rubric_id": "R1",
                "spec_ids": ["S1"],
                "evidence_quotes": [
                    {
                        "spec_id": "S1",
                        "quote": "Implement refund handling for cancelled orders.",
                        "verification_mode": "token_sequence",
                    }
                ],
            }
        ]
    }


def _codes(diagnostics: list[Any]) -> list[str]:
    return [d.code for d in diagnostics]


# ---------------------------------------------------------------------------
# over-strict guard: clean input has no diagnostics
# ---------------------------------------------------------------------------


def test_clean_input_produces_no_diagnostics() -> None:
    diagnostics = run_rule_zero(
        _baseline_spec(), _baseline_rubric(), _baseline_traces(), snapshot=None
    )
    assert diagnostics == []


# ---------------------------------------------------------------------------
# duplicate ids
# ---------------------------------------------------------------------------


def test_duplicate_spec_id_is_caught() -> None:
    spec = _baseline_spec()
    spec["spec_items"].append(
        {
            "id": "S1",
            "text": "Duplicate id should fail.",
            "requirement_level": "must",
            "source_ref": {
                "document_id": "DOC_SPEC",
                "start_line": 3,
                "end_line": 3,
            },
        }
    )
    diagnostics = run_rule_zero(spec, _baseline_rubric(), _baseline_traces(), None)
    assert "duplicate_spec_id" in _codes(diagnostics)


def test_unique_spec_ids_are_not_flagged() -> None:
    diagnostics = run_rule_zero(
        _baseline_spec(), _baseline_rubric(), _baseline_traces(), None
    )
    assert "duplicate_spec_id" not in _codes(diagnostics)


def test_duplicate_rubric_id_is_caught() -> None:
    rubric = _baseline_rubric()
    rubric["rubric_items"].append(
        {
            "id": "R1",
            "title": "Dupe",
            "evaluation_role": "scored",
            "weight": 1,
            "source_ref": {
                "document_id": "DOC_RUBRIC",
                "start_line": 2,
                "end_line": 2,
            },
        }
    )
    diagnostics = run_rule_zero(_baseline_spec(), rubric, _baseline_traces(), None)
    assert "duplicate_rubric_id" in _codes(diagnostics)


# ---------------------------------------------------------------------------
# dangling references
# ---------------------------------------------------------------------------


def test_dangling_rubric_reference_is_caught() -> None:
    traces = _baseline_traces()
    traces["trace_links"][0]["rubric_id"] = "R999"
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, None)
    assert "dangling_rubric_reference" in _codes(diagnostics)


def test_dangling_spec_reference_is_caught() -> None:
    traces = _baseline_traces()
    traces["trace_links"][0]["spec_ids"] = ["S999"]
    traces["trace_links"][0]["evidence_quotes"][0]["spec_id"] = "S999"
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, None)
    assert "dangling_spec_reference" in _codes(diagnostics)


def test_real_references_are_not_flagged_as_dangling() -> None:
    diagnostics = run_rule_zero(
        _baseline_spec(), _baseline_rubric(), _baseline_traces(), None
    )
    flagged = _codes(diagnostics)
    assert "dangling_rubric_reference" not in flagged
    assert "dangling_spec_reference" not in flagged


# ---------------------------------------------------------------------------
# evidence quotes
# ---------------------------------------------------------------------------


def test_evidence_quote_spec_id_mismatch_is_caught() -> None:
    traces = _baseline_traces()
    traces["trace_links"][0]["evidence_quotes"][0]["spec_id"] = "S2"
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, None)
    assert "evidence_quote_spec_id_mismatch" in _codes(diagnostics)


def test_evidence_quote_empty_is_caught() -> None:
    traces = _baseline_traces()
    traces["trace_links"][0]["evidence_quotes"][0]["quote"] = "   "
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, None)
    assert "evidence_quote_empty" in _codes(diagnostics)


def test_non_empty_quote_is_not_flagged() -> None:
    diagnostics = run_rule_zero(
        _baseline_spec(), _baseline_rubric(), _baseline_traces(), None
    )
    assert "evidence_quote_empty" not in _codes(diagnostics)


def test_token_sequence_mismatch_is_caught() -> None:
    traces = _baseline_traces()
    traces["trace_links"][0]["evidence_quotes"][0]["quote"] = (
        "A sentence that is not in the spec at all."
    )
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, None)
    assert "evidence_quote_token_sequence_mismatch" in _codes(diagnostics)


def test_token_sequence_match_is_not_flagged() -> None:
    diagnostics = run_rule_zero(
        _baseline_spec(), _baseline_rubric(), _baseline_traces(), None
    )
    assert "evidence_quote_token_sequence_mismatch" not in _codes(diagnostics)


def test_token_sequence_normalizes_whitespace() -> None:
    traces = _baseline_traces()
    # Same words, different inner whitespace -- should still match.
    traces["trace_links"][0]["evidence_quotes"][0]["quote"] = (
        "Implement   refund\thandling  for cancelled orders."
    )
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, None)
    assert "evidence_quote_token_sequence_mismatch" not in _codes(diagnostics)


def test_ai_judgement_mode_skips_substring_check() -> None:
    """`ai_judgement` is the PoC default; substring mismatches must not fail
    Rule 0. (Semantic adequacy is deferred to the verifier-agent stage.)
    """
    traces = _baseline_traces()
    traces["trace_links"][0]["evidence_quotes"][0]["quote"] = (
        "Some commentary that paraphrases the spec without quoting it."
    )
    traces["trace_links"][0]["evidence_quotes"][0]["verification_mode"] = "ai_judgement"
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, None)
    assert "evidence_quote_token_sequence_mismatch" not in _codes(diagnostics)


# ---------------------------------------------------------------------------
# source manifest grounding
# ---------------------------------------------------------------------------


def _make_snapshot(
    spec_text: str = "line one\nline two\nline three\n",
    rubric_text: str = "rline one\nrline two\nrline three\n",
    *,
    tamper_hash: str | None = None,
) -> SourceSnapshot:
    spec_hash = hashlib.sha256(spec_text.encode("utf-8")).hexdigest()
    rubric_hash = hashlib.sha256(rubric_text.encode("utf-8")).hexdigest()

    # Use in-memory Document objects -- no on-disk file needed for these tests.
    spec_doc = Document(
        document_id="DOC_SPEC",
        role="candidate_spec",
        path=Path("/tmp/spec.md"),
        expected_sha256=tamper_hash or spec_hash,
        actual_sha256=spec_hash,
        lines=spec_text.splitlines(),
    )
    rubric_doc = Document(
        document_id="DOC_RUBRIC",
        role="evaluator_rubric",
        path=Path("/tmp/rubric.md"),
        expected_sha256=rubric_hash,
        actual_sha256=rubric_hash,
        lines=rubric_text.splitlines(),
    )
    # We override `path.exists` indirectly by making _check_document_integrity
    # skip when path.exists() is false (here the path doesn't exist). To
    # cleanly test span checks, we patch `Document.path` to a real file in
    # tests that need it; for now we provide an alternative path-less snapshot
    # used by tests that only care about span/hash logic.

    snapshot = SourceSnapshot(
        project_id="t",
        assessment_version="v1",
        documents={"DOC_SPEC": spec_doc, "DOC_RUBRIC": rubric_doc},
    )
    return snapshot


class _StubPath:
    def __init__(self, *, exists: bool = True) -> None:
        self._exists = exists

    def exists(self) -> bool:
        return self._exists

    def __str__(self) -> str:  # pragma: no cover - used in messages only
        return "<stub>"


def _attach_exists(snapshot: SourceSnapshot, exists: bool = True) -> None:
    for doc in snapshot.documents.values():
        doc.path = _StubPath(exists=exists)  # type: ignore[assignment]


def test_source_document_hash_mismatch_is_caught() -> None:
    snapshot = _make_snapshot(tamper_hash="0" * 64)
    _attach_exists(snapshot, exists=True)
    diagnostics = run_rule_zero(
        _baseline_spec(), _baseline_rubric(), _baseline_traces(), snapshot
    )
    assert "source_document_hash_mismatch" in _codes(diagnostics)


def test_matching_hash_is_not_flagged() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    diagnostics = run_rule_zero(
        _baseline_spec(), _baseline_rubric(), _baseline_traces(), snapshot
    )
    assert "source_document_hash_mismatch" not in _codes(diagnostics)


def test_source_ref_span_out_of_range_is_caught() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    spec = _baseline_spec()
    spec["spec_items"][0]["source_ref"]["end_line"] = 99
    diagnostics = run_rule_zero(spec, _baseline_rubric(), _baseline_traces(), snapshot)
    assert "spec_source_ref_span_invalid" in _codes(diagnostics)


def test_valid_span_is_not_flagged() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    diagnostics = run_rule_zero(
        _baseline_spec(), _baseline_rubric(), _baseline_traces(), snapshot
    )
    assert "spec_source_ref_span_invalid" not in _codes(diagnostics)


def test_evidence_source_ref_outside_spec_span_is_caught() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    traces = _baseline_traces()
    traces["trace_links"][0]["evidence_quotes"][0]["source_ref"] = {
        "document_id": "DOC_SPEC",
        "start_line": 3,
        "end_line": 3,
    }
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, snapshot)
    assert "evidence_source_ref_mismatch_with_spec" in _codes(diagnostics)


def test_evidence_source_ref_inside_spec_span_is_not_flagged() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    traces = _baseline_traces()
    traces["trace_links"][0]["evidence_quotes"][0]["source_ref"] = {
        "document_id": "DOC_SPEC",
        "start_line": 1,
        "end_line": 1,
    }
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, snapshot)
    assert "evidence_source_ref_mismatch_with_spec" not in _codes(diagnostics)


# ---------------------------------------------------------------------------
# severity contract
# ---------------------------------------------------------------------------


def test_all_rule_zero_diagnostics_are_high_severity() -> None:
    spec = _baseline_spec()
    spec["spec_items"].append(spec["spec_items"][0])  # duplicate
    diagnostics = run_rule_zero(spec, _baseline_rubric(), _baseline_traces(), None)
    assert diagnostics, "expected at least one diagnostic"
    assert all(d.severity == "high" for d in diagnostics)
    counts = severity_counts(diagnostics)
    assert counts["high"] == counts["total"] > 0
