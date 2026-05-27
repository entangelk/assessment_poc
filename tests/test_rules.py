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
from assessment_harness.rules import (
    run_rule_l1,
    run_rule_l5,
    run_rule_l6,
    run_rule_one,
    run_rule_zero,
    severity_counts,
)


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
    spec_text: str = (
        "Implement refund handling for cancelled orders.\n"
        "Provide an audit log for every refund decision.\n"
        "third line.\n"
    ),
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
# snapshot text grounding (Defect 1)
# ---------------------------------------------------------------------------


def test_spec_text_not_in_snapshot_is_caught() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    spec = _baseline_spec()
    spec["spec_items"][0]["text"] = "FABRICATED requirement that is not in source."
    diagnostics = run_rule_zero(spec, _baseline_rubric(), _baseline_traces(), snapshot)
    assert "spec_text_not_in_snapshot_span" in _codes(diagnostics)


def test_spec_text_matching_snapshot_is_not_flagged() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    diagnostics = run_rule_zero(
        _baseline_spec(), _baseline_rubric(), _baseline_traces(), snapshot
    )
    assert "spec_text_not_in_snapshot_span" not in _codes(diagnostics)


def test_spec_quote_not_in_snapshot_is_caught() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    spec = _baseline_spec()
    spec["spec_items"][0]["source_ref"]["quote"] = "FABRICATED quote not in span."
    diagnostics = run_rule_zero(spec, _baseline_rubric(), _baseline_traces(), snapshot)
    assert "spec_quote_not_in_snapshot_span" in _codes(diagnostics)


def test_spec_quote_in_snapshot_is_not_flagged() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    spec = _baseline_spec()
    spec["spec_items"][0]["source_ref"]["quote"] = "refund handling for cancelled"
    diagnostics = run_rule_zero(spec, _baseline_rubric(), _baseline_traces(), snapshot)
    assert "spec_quote_not_in_snapshot_span" not in _codes(diagnostics)


def test_evidence_quote_not_in_snapshot_span_is_caught() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    traces = _baseline_traces()
    quote = traces["trace_links"][0]["evidence_quotes"][0]
    quote["source_ref"] = {
        "document_id": "DOC_SPEC",
        "start_line": 1,
        "end_line": 1,
    }
    quote["quote"] = "FABRICATED text not in line 1."
    # Switch mode so the substring-vs-spec-text rule does not also fire.
    quote["verification_mode"] = "ai_judgement"
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, snapshot)
    assert "evidence_quote_not_in_snapshot_span" in _codes(diagnostics)


def test_evidence_quote_in_snapshot_span_is_not_flagged() -> None:
    snapshot = _make_snapshot()
    _attach_exists(snapshot, exists=True)
    traces = _baseline_traces()
    traces["trace_links"][0]["evidence_quotes"][0]["source_ref"] = {
        "document_id": "DOC_SPEC",
        "start_line": 1,
        "end_line": 1,
    }
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, snapshot)
    assert "evidence_quote_not_in_snapshot_span" not in _codes(diagnostics)


# ---------------------------------------------------------------------------
# evidence completeness for N:M trace links (Defect 2)
# ---------------------------------------------------------------------------


def test_evidence_quote_missing_for_spec_id_is_caught() -> None:
    traces = _baseline_traces()
    # N:M link: spec_ids has S1 and S2, evidence only covers S1.
    traces["trace_links"][0]["spec_ids"] = ["S1", "S2"]
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, None)
    matching = [d for d in diagnostics if d.code == "evidence_quote_missing_for_spec_id"]
    assert matching, "expected at least one missing-evidence diagnostic"
    assert any(d.location.get("spec_id") == "S2" for d in matching)


def test_complete_evidence_coverage_is_not_flagged() -> None:
    diagnostics = run_rule_zero(
        _baseline_spec(), _baseline_rubric(), _baseline_traces(), None
    )
    assert "evidence_quote_missing_for_spec_id" not in _codes(diagnostics)


def test_dangling_spec_id_is_not_double_reported_as_missing_evidence() -> None:
    """A spec_id that does not exist in spec_items should surface only as
    `dangling_spec_reference`; the completeness check skips it to avoid
    duplicate noise. (over-strict guard)
    """
    traces = _baseline_traces()
    traces["trace_links"][0]["spec_ids"] = ["S1", "S999"]
    diagnostics = run_rule_zero(_baseline_spec(), _baseline_rubric(), traces, None)
    assert "dangling_spec_reference" in _codes(diagnostics)
    s999_missing = [
        d
        for d in diagnostics
        if d.code == "evidence_quote_missing_for_spec_id"
        and d.location.get("spec_id") == "S999"
    ]
    assert s999_missing == []


# ---------------------------------------------------------------------------
# severity contract — every Rule 0 trigger surfaces as high
# ---------------------------------------------------------------------------


def _trigger(spec, rubric, traces, code: str) -> None:
    """Mutate the baseline so Rule 0 fires the given diagnostic code."""
    if code == "duplicate_spec_id":
        spec["spec_items"].append(copy.deepcopy(spec["spec_items"][0]))
    elif code == "duplicate_rubric_id":
        rubric["rubric_items"].append(copy.deepcopy(rubric["rubric_items"][0]))
    elif code == "dangling_rubric_reference":
        traces["trace_links"][0]["rubric_id"] = "R999"
    elif code == "dangling_spec_reference":
        traces["trace_links"][0]["spec_ids"] = ["S999"]
        traces["trace_links"][0]["evidence_quotes"][0]["spec_id"] = "S999"
    elif code == "evidence_quote_spec_id_mismatch":
        traces["trace_links"][0]["evidence_quotes"][0]["spec_id"] = "S2"
    elif code == "evidence_quote_empty":
        traces["trace_links"][0]["evidence_quotes"][0]["quote"] = "   "
    elif code == "evidence_quote_missing_for_spec_id":
        traces["trace_links"][0]["spec_ids"] = ["S1", "S2"]
    elif code == "evidence_quote_token_sequence_mismatch":
        traces["trace_links"][0]["evidence_quotes"][0]["quote"] = "no match anywhere."
    else:  # pragma: no cover - guard against typo
        raise AssertionError(f"unknown trigger code: {code}")


@pytest.mark.parametrize(
    "code",
    [
        "duplicate_spec_id",
        "duplicate_rubric_id",
        "dangling_rubric_reference",
        "dangling_spec_reference",
        "evidence_quote_spec_id_mismatch",
        "evidence_quote_empty",
        "evidence_quote_missing_for_spec_id",
        "evidence_quote_token_sequence_mismatch",
    ],
)
def test_rule_zero_trigger_is_high_severity(code: str) -> None:
    spec = _baseline_spec()
    rubric = _baseline_rubric()
    traces = _baseline_traces()
    _trigger(spec, rubric, traces, code)
    diagnostics = run_rule_zero(spec, rubric, traces, None)
    matching = [d for d in diagnostics if d.code == code]
    assert matching, f"expected trigger {code!r} to fire"
    assert all(d.severity == "high" for d in matching)


# ---------------------------------------------------------------------------
# Rule 1 — Scored Rubric Coverage, slice 1: no-trace branch
# ---------------------------------------------------------------------------


def _findings_of_type(findings: list[Any], finding_type: str) -> list[Any]:
    return [f for f in findings if f.type == finding_type]


def test_scored_rubric_with_no_trace_link_surfaces_possible_orphan() -> None:
    """Under-strict guard: a scored rubric item without any trace link must
    raise `possible_orphan_scored_rubric_item` (high / provisional). If this
    test stops failing on a regression that drops the no-link branch, the
    rule has gone silent.
    """
    rubric = {
        "rubric_items": [
            {
                "id": "R1",
                "title": "Refund handling",
                "evaluation_role": "scored",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 1,
                    "end_line": 1,
                },
            },
            {
                "id": "R2",
                "title": "Idempotency",
                "evaluation_role": "scored",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 2,
                    "end_line": 2,
                },
            },
        ]
    }
    traces = {
        "trace_links": [
            {
                "rubric_id": "R1",
                "spec_ids": ["S1"],
                "evidence_quotes": [
                    {
                        "spec_id": "S1",
                        "quote": "...",
                        "verification_mode": "ai_judgement",
                    }
                ],
            }
        ]
    }
    findings = run_rule_one(rubric, traces)
    orphans = _findings_of_type(findings, "possible_orphan_scored_rubric_item")
    assert len(orphans) == 1
    assert orphans[0].rubric_id == "R2"
    assert orphans[0].severity == "high"
    assert orphans[0].decision_status == "provisional"


def test_scored_rubric_with_trace_link_is_not_orphan_flagged() -> None:
    """Over-strict guard A: a scored rubric that IS traced (any
    semantic_status) must not be flagged as `possible_orphan_*`. If we
    later mishandle `semantic_status` and over-promote pending coverage
    into orphans, this guard will catch the regression.
    """
    rubric = {
        "rubric_items": [
            {
                "id": "R1",
                "title": "Refund handling",
                "evaluation_role": "scored",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 1,
                    "end_line": 1,
                },
            }
        ]
    }
    traces = {
        "trace_links": [
            {
                "rubric_id": "R1",
                "spec_ids": ["S1"],
                "evidence_quotes": [
                    {
                        "spec_id": "S1",
                        "quote": "...",
                        "verification_mode": "ai_judgement",
                    }
                ],
                "semantic_status": "pending_verification",
            }
        ]
    }
    findings = run_rule_one(rubric, traces)
    assert _findings_of_type(findings, "possible_orphan_scored_rubric_item") == []


def test_bonus_or_qualitative_orphan_is_not_flagged_by_rule_one_slice_one() -> None:
    """Over-strict guard B: only `scored` items are in scope for the
    possible-orphan branch. A `bonus` or `qualitative` item without a
    trace must not be flagged as scored-orphan. (Bonus orphans get an
    informational finding in a later slice; qualitative items are out of
    scope for Rule 1 entirely.)
    """
    rubric = {
        "rubric_items": [
            {
                "id": "RB",
                "title": "Audit log",
                "evaluation_role": "bonus",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 1,
                    "end_line": 1,
                },
            },
            {
                "id": "RQ",
                "title": "Code quality",
                "evaluation_role": "qualitative",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 2,
                    "end_line": 2,
                },
            },
        ]
    }
    traces = {"trace_links": []}
    findings = run_rule_one(rubric, traces)
    assert _findings_of_type(findings, "possible_orphan_scored_rubric_item") == []


def test_rule_one_baseline_emits_unconfirmed_trace_coverage() -> None:
    """The Rule 0 baseline (R1 scored, traced to S1 with no semantic_status)
    must now produce exactly one `unconfirmed_trace_coverage` finding
    (medium / provisional) because the link is not yet human-accepted.
    Documents the pre-review state per plan §6 Rule 1.
    """
    findings = run_rule_one(_baseline_rubric(), _baseline_traces())
    types = [f.type for f in findings]
    assert types == ["unconfirmed_trace_coverage"]
    assert findings[0].severity == "medium"
    assert findings[0].decision_status == "provisional"
    assert findings[0].rubric_id == "R1"


# ---------------------------------------------------------------------------
# Rule 1 — Scored Rubric Coverage, slice 2: unconfirmed_trace_coverage branch
# ---------------------------------------------------------------------------


def _rubric_one_scored() -> dict[str, Any]:
    return {
        "rubric_items": [
            {
                "id": "R1",
                "title": "Refund handling",
                "evaluation_role": "scored",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 1,
                    "end_line": 1,
                },
            }
        ]
    }


def _trace_with_status(status: str | None) -> dict[str, Any]:
    link: dict[str, Any] = {
        "rubric_id": "R1",
        "spec_ids": ["S1"],
        "evidence_quotes": [
            {
                "spec_id": "S1",
                "quote": "...",
                "verification_mode": "ai_judgement",
            }
        ],
    }
    if status is not None:
        link["semantic_status"] = status
    return {"trace_links": [link]}


@pytest.mark.parametrize(
    "status",
    [
        "pending_verification",
        "agent_supported",
        "agent_rejected",
        "agent_uncertain",
        "human_rejected",
        "rerun_requested",
    ],
)
def test_non_human_accepted_status_yields_unconfirmed_trace_coverage(
    status: str,
) -> None:
    """Under-strict guard: every non-final-coverage semantic_status (pre-review
    pending/agent_* plus post-review human_rejected/rerun_requested) must
    surface `unconfirmed_trace_coverage` (medium / provisional).
    """
    findings = run_rule_one(_rubric_one_scored(), _trace_with_status(status))
    matching = [f for f in findings if f.type == "unconfirmed_trace_coverage"]
    assert len(matching) == 1
    assert matching[0].severity == "medium"
    assert matching[0].decision_status == "provisional"
    assert matching[0].rubric_id == "R1"
    assert matching[0].evidence is not None
    assert matching[0].evidence["link_count"] == 1
    assert matching[0].evidence["semantic_statuses"] == [status]


def test_missing_semantic_status_yields_unconfirmed_trace_coverage() -> None:
    """Under-strict guard variant: a trace link with no `semantic_status` at
    all (Phase 0 baseline before semantic verifier runs) is also pre-review,
    so the rule must flag it.
    """
    findings = run_rule_one(_rubric_one_scored(), _trace_with_status(None))
    matching = [f for f in findings if f.type == "unconfirmed_trace_coverage"]
    assert len(matching) == 1


@pytest.mark.parametrize("status", ["human_accepted", "human_overridden"])
def test_human_accepted_status_skips_unconfirmed_trace_coverage(status: str) -> None:
    """Over-strict guard A: `human_accepted` and `human_overridden` are the
    only statuses that count as final coverage per plan §6 Rule 1. They must
    suppress the unconfirmed finding entirely.
    """
    findings = run_rule_one(_rubric_one_scored(), _trace_with_status(status))
    assert _findings_of_type(findings, "unconfirmed_trace_coverage") == []
    assert _findings_of_type(findings, "possible_orphan_scored_rubric_item") == []


def test_any_human_accepted_link_suppresses_unconfirmed_finding() -> None:
    """Over-strict guard B: among multiple links for the same rubric, even
    one `human_accepted` is enough to confirm coverage — the medium finding
    must not fire just because OTHER links remain pending.
    """
    traces = {
        "trace_links": [
            {
                "rubric_id": "R1",
                "spec_ids": ["S1"],
                "evidence_quotes": [
                    {"spec_id": "S1", "quote": "x", "verification_mode": "ai_judgement"}
                ],
                "semantic_status": "pending_verification",
            },
            {
                "rubric_id": "R1",
                "spec_ids": ["S2"],
                "evidence_quotes": [
                    {"spec_id": "S2", "quote": "y", "verification_mode": "ai_judgement"}
                ],
                "semantic_status": "human_accepted",
            },
        ]
    }
    findings = run_rule_one(_rubric_one_scored(), traces)
    assert _findings_of_type(findings, "unconfirmed_trace_coverage") == []


def test_orphan_and_unconfirmed_are_mutually_exclusive() -> None:
    """Over-strict guard C: a scored rubric without any link surfaces only as
    `possible_orphan`. The `unconfirmed_trace_coverage` branch must not also
    fire on the same rubric — that would double-count one orphan.
    """
    rubric = _rubric_one_scored()
    findings = run_rule_one(rubric, {"trace_links": []})
    types = [f.type for f in findings]
    assert types == ["possible_orphan_scored_rubric_item"]


def test_bonus_qualitative_skipped_even_with_pending_links() -> None:
    """Over-strict guard D: `bonus` / `qualitative` rubric items stay out of
    the `unconfirmed_trace_coverage` branch even when they have pending
    links. Bonus orphan handling is slice 3 territory.
    """
    rubric = {
        "rubric_items": [
            {
                "id": "RB",
                "title": "Audit log",
                "evaluation_role": "bonus",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 1,
                    "end_line": 1,
                },
            },
            {
                "id": "RQ",
                "title": "Code quality",
                "evaluation_role": "qualitative",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 2,
                    "end_line": 2,
                },
            },
        ]
    }
    traces = {
        "trace_links": [
            {
                "rubric_id": "RB",
                "spec_ids": ["S1"],
                "evidence_quotes": [
                    {"spec_id": "S1", "quote": "x", "verification_mode": "ai_judgement"}
                ],
                "semantic_status": "pending_verification",
            },
            {
                "rubric_id": "RQ",
                "spec_ids": ["S1"],
                "evidence_quotes": [
                    {"spec_id": "S1", "quote": "y", "verification_mode": "ai_judgement"}
                ],
                "semantic_status": "pending_verification",
            },
        ]
    }
    findings = run_rule_one(rubric, traces)
    assert _findings_of_type(findings, "unconfirmed_trace_coverage") == []


# ---------------------------------------------------------------------------
# Rule 1 — Scored Rubric Coverage, slice 3: orphan_bonus_rubric_item branch
# ---------------------------------------------------------------------------


def _bonus_rubric(rid: str = "RB") -> dict[str, Any]:
    return {
        "rubric_items": [
            {
                "id": rid,
                "title": "Audit log",
                "evaluation_role": "bonus",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 1,
                    "end_line": 1,
                },
            }
        ]
    }


def test_bonus_rubric_without_link_yields_orphan_bonus_finding() -> None:
    """Under-strict guard: a bonus rubric item with no trace link must
    surface `orphan_bonus_rubric_item` (informational / provisional). Per
    plan v1.10 §6 Rule 1, bonus orphans do not block gating; the severity
    must stay `informational`.
    """
    findings = run_rule_one(_bonus_rubric(), {"trace_links": []})
    matching = _findings_of_type(findings, "orphan_bonus_rubric_item")
    assert len(matching) == 1
    assert matching[0].rubric_id == "RB"
    assert matching[0].severity == "informational"
    assert matching[0].decision_status == "provisional"


@pytest.mark.parametrize(
    "status",
    [
        "pending_verification",
        "agent_supported",
        "agent_rejected",
        "agent_uncertain",
        "human_accepted",
        "human_overridden",
        "human_rejected",
        "rerun_requested",
    ],
)
def test_bonus_rubric_with_any_link_is_not_orphan_bonus(status: str) -> None:
    """Over-strict guard A: a bonus rubric WITH any trace link (regardless
    of semantic_status) must not be flagged. Per plan v1.10 §6 Rule 1,
    semantic_status is not consulted for bonus items — having a link is
    enough to suppress the informational finding.
    """
    traces = {
        "trace_links": [
            {
                "rubric_id": "RB",
                "spec_ids": ["S1"],
                "evidence_quotes": [
                    {"spec_id": "S1", "quote": "x", "verification_mode": "ai_judgement"}
                ],
                "semantic_status": status,
            }
        ]
    }
    findings = run_rule_one(_bonus_rubric(), traces)
    assert _findings_of_type(findings, "orphan_bonus_rubric_item") == []


def test_scored_orphan_is_not_also_flagged_as_bonus_orphan() -> None:
    """Over-strict guard B: an `evaluation_role == scored` rubric with no
    link must only emit `possible_orphan_scored_rubric_item`, NOT also
    `orphan_bonus_rubric_item`. The two branches are mutually exclusive on
    `evaluation_role`.
    """
    findings = run_rule_one(_rubric_one_scored(), {"trace_links": []})
    types = sorted({f.type for f in findings})
    assert types == ["possible_orphan_scored_rubric_item"]


def test_qualitative_rubric_without_link_is_not_flagged() -> None:
    """Over-strict guard C: a qualitative rubric without a link stays
    out of Rule 1 entirely — neither scored-orphan nor bonus-orphan
    branches apply. (Qualitative items are out of Rule 1's scope per
    plan §6.)
    """
    rubric = {
        "rubric_items": [
            {
                "id": "RQ",
                "title": "Code quality",
                "evaluation_role": "qualitative",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 1,
                    "end_line": 1,
                },
            }
        ]
    }
    findings = run_rule_one(rubric, {"trace_links": []})
    assert findings == []


def test_three_rubrics_three_branches_coexist() -> None:
    """Integration-style guard: a single rubric_items document mixing
    scored/no-trace + scored/pending + bonus/no-trace + qualitative must
    produce exactly three findings (one per Rule 1 branch) with the right
    rubric_ids. Locks slice 1 + slice 2 + slice 3 against each other.
    """
    rubric = {
        "rubric_items": [
            {
                "id": "R_SCORED_NO_LINK",
                "title": "scored no-trace",
                "evaluation_role": "scored",
                "source_ref": {"document_id": "DOC_RUBRIC", "start_line": 1, "end_line": 1},
            },
            {
                "id": "R_SCORED_PENDING",
                "title": "scored pending",
                "evaluation_role": "scored",
                "source_ref": {"document_id": "DOC_RUBRIC", "start_line": 2, "end_line": 2},
            },
            {
                "id": "R_BONUS_NO_LINK",
                "title": "bonus no-trace",
                "evaluation_role": "bonus",
                "source_ref": {"document_id": "DOC_RUBRIC", "start_line": 3, "end_line": 3},
            },
            {
                "id": "R_QUAL",
                "title": "qualitative",
                "evaluation_role": "qualitative",
                "source_ref": {"document_id": "DOC_RUBRIC", "start_line": 4, "end_line": 4},
            },
        ]
    }
    traces = {
        "trace_links": [
            {
                "rubric_id": "R_SCORED_PENDING",
                "spec_ids": ["S1"],
                "evidence_quotes": [
                    {"spec_id": "S1", "quote": "x", "verification_mode": "ai_judgement"}
                ],
                "semantic_status": "pending_verification",
            }
        ]
    }
    findings = run_rule_one(rubric, traces)
    by_rubric = {(f.rubric_id, f.type, f.severity) for f in findings}
    assert by_rubric == {
        ("R_SCORED_NO_LINK", "possible_orphan_scored_rubric_item", "high"),
        ("R_SCORED_PENDING", "unconfirmed_trace_coverage", "medium"),
        ("R_BONUS_NO_LINK", "orphan_bonus_rubric_item", "informational"),
    }


# ---------------------------------------------------------------------------
# Rule L1 — Cross-role Double Scoring
# ---------------------------------------------------------------------------


def _l1_rubrics() -> dict[str, Any]:
    return {
        "rubric_items": [
            {
                "id": "RS",
                "title": "Required behavior",
                "description": "Scores the required behavior.",
                "evaluation_role": "scored",
                "source_ref": {"document_id": "DOC_RUBRIC", "start_line": 1, "end_line": 1},
            },
            {
                "id": "RB",
                "title": "Bonus repeat",
                "description": "Awards bonus for the same behavior.",
                "evaluation_role": "bonus",
                "source_ref": {"document_id": "DOC_RUBRIC", "start_line": 2, "end_line": 2},
            },
        ]
    }


def test_l1_same_spec_traced_by_scored_and_bonus_emits_review_pair() -> None:
    """Under-strict guard: one spec traced by both roles must emit the L1
    finding with paired rubric context and a `double_scoring_review` entry.
    """
    traces = {
        "trace_links": [
            {"rubric_id": "RS", "spec_ids": ["S1"], "evidence_quotes": [], "semantic_status": "human_accepted"},
            {"rubric_id": "RB", "spec_ids": ["S1"], "evidence_quotes": [], "semantic_status": "human_overridden"},
        ]
    }
    findings, queue = run_rule_l1(_l1_rubrics(), traces)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.type == "double_scored_spec"
    assert finding.severity == "medium"
    assert finding.decision_status == "provisional"
    assert finding.spec_id == "S1"
    assert finding.scored_rubric_id == "RS"
    assert finding.bonus_rubric_id == "RB"
    assert finding.evidence["scored_rubric"]["semantic_statuses"] == ["human_accepted"]
    assert finding.evidence["bonus_rubric"]["semantic_statuses"] == ["human_overridden"]
    assert queue == [
        {
            "entry_id": "rq_double_scoring_S1_RS_RB",
            "type": "double_scoring_review",
            "target": {
                "spec_id": "S1",
                "scored_rubric_id": "RS",
                "bonus_rubric_id": "RB",
            },
            "reason": "Spec item 'S1' is traced by both scored rubric 'RS' and bonus rubric 'RB'.",
            "related_runs": [],
            "status": "open",
        }
    ]


def test_l1_scored_only_trace_does_not_emit() -> None:
    """Over-strict guard A: scored-only coverage is not cross-role scoring."""
    traces = {
        "trace_links": [
            {"rubric_id": "RS", "spec_ids": ["S1"], "evidence_quotes": []},
        ]
    }
    assert run_rule_l1(_l1_rubrics(), traces) == ([], [])


def test_l1_different_specs_between_roles_do_not_emit() -> None:
    """Over-strict guard B: role overlap requires the same spec_id."""
    traces = {
        "trace_links": [
            {"rubric_id": "RS", "spec_ids": ["S1"], "evidence_quotes": []},
            {"rubric_id": "RB", "spec_ids": ["S2"], "evidence_quotes": []},
        ]
    }
    assert run_rule_l1(_l1_rubrics(), traces) == ([], [])


# ---------------------------------------------------------------------------
# Rule L5 — Bonus Traces Only Mandatory
# ---------------------------------------------------------------------------


def _l5_specs() -> dict[str, Any]:
    return {
        "spec_items": [
            {"id": "S_MUST", "text": "required", "requirement_level": "must", "source_ref": {}},
            {
                "id": "S_OPTIONAL",
                "text": "optional",
                "requirement_level": "optional",
                "source_ref": {},
            },
            {
                "id": "S_INFORMATIONAL",
                "text": "informational",
                "requirement_level": "informational",
                "source_ref": {},
            },
        ]
    }


def test_l5_bonus_traced_only_to_must_specs_emits_finding() -> None:
    """Under-strict guard: a bonus rubric whose traced specs are all `must`
    must surface `bonus_grades_mandatory_only`, regardless of link status.
    """
    traces = {
        "trace_links": [
            {
                "rubric_id": "RB",
                "spec_ids": ["S_MUST"],
                "evidence_quotes": [],
                "semantic_status": "human_accepted",
            }
        ]
    }
    findings = run_rule_l5(_l5_specs(), _bonus_rubric(), traces)
    assert len(findings) == 1
    assert findings[0].type == "bonus_grades_mandatory_only"
    assert findings[0].rubric_id == "RB"
    assert findings[0].severity == "medium"
    assert findings[0].decision_status == "provisional"


@pytest.mark.parametrize("non_must_spec_id", ["S_OPTIONAL", "S_INFORMATIONAL"])
def test_l5_bonus_with_non_must_trace_does_not_emit(non_must_spec_id: str) -> None:
    """Over-strict guard A: an optional/informational target preserves bonus semantics."""
    traces = {
        "trace_links": [
            {"rubric_id": "RB", "spec_ids": ["S_MUST", non_must_spec_id], "evidence_quotes": []}
        ]
    }
    assert run_rule_l5(_l5_specs(), _bonus_rubric(), traces) == []


def test_l5_untraced_bonus_is_left_to_rule_one() -> None:
    """Over-strict guard B: an untraced bonus is a Rule 1 orphan, not L5."""
    assert run_rule_l5(_l5_specs(), _bonus_rubric(), {"trace_links": []}) == []


# ---------------------------------------------------------------------------
# Rule L6 — Mandatory Spec Bonus-only Coverage
# ---------------------------------------------------------------------------


def _l6_rubrics() -> dict[str, Any]:
    return {
        "rubric_items": [
            {
                "id": "RS",
                "title": "Required behavior",
                "description": "Scores the required behavior.",
                "evaluation_role": "scored",
                "source_ref": {},
            },
            {
                "id": "RB",
                "title": "Bonus treatment",
                "description": "Awards bonus for mandatory work.",
                "evaluation_role": "bonus",
                "source_ref": {},
            },
            {
                "id": "RB_SECOND",
                "title": "Second bonus treatment",
                "description": "Also awards bonus for mandatory work.",
                "evaluation_role": "bonus",
                "source_ref": {},
            },
            {
                "id": "RQ",
                "title": "Qualitative observation",
                "description": "Records qualitative treatment without awarding bonus.",
                "evaluation_role": "qualitative",
                "source_ref": {},
            },
        ]
    }


def test_l6_must_spec_traced_only_by_bonus_emits_review_queue() -> None:
    """Under-strict guard: traced mandatory work with no scored rubric must
    emit L6 with all bonus rubrics and its paired review queue entry.
    """
    traces = {
        "trace_links": [
            {
                "rubric_id": "RB",
                "spec_ids": ["S_MUST"],
                "evidence_quotes": [],
                "semantic_status": "human_accepted",
                "support": {"found_in_runs": ["run-2"]},
            },
            {
                "rubric_id": "RB_SECOND",
                "spec_ids": ["S_MUST"],
                "evidence_quotes": [],
                "semantic_status": "pending_verification",
                "support": {"found_in_runs": ["run-1"]},
            },
        ]
    }
    findings, queue = run_rule_l6(_l5_specs(), _l6_rubrics(), traces)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.type == "mandatory_spec_bonus_only_traced"
    assert finding.spec_id == "S_MUST"
    assert finding.bonus_rubric_ids == ["RB", "RB_SECOND"]
    assert finding.severity == "high"
    assert finding.decision_status == "provisional"
    assert finding.evidence["bonus_rubrics"][0]["semantic_statuses"] == ["human_accepted"]
    assert finding.evidence["bonus_rubrics"][1]["semantic_statuses"] == [
        "pending_verification"
    ]
    assert queue == [
        {
            "entry_id": "rq_mandatory_spec_bonus_S_MUST",
            "type": "mandatory_spec_bonus_review",
            "target": {"spec_id": "S_MUST", "bonus_rubric_ids": ["RB", "RB_SECOND"]},
            "reason": (
                "Mandatory spec item 'S_MUST' is traced only by bonus rubrics "
                "'RB', 'RB_SECOND'."
            ),
            "related_runs": ["run-1", "run-2"],
            "status": "open",
        }
    ]


def test_l6_must_spec_with_scored_trace_does_not_emit() -> None:
    """Over-strict guard A: any scored coverage suppresses bonus-only L6."""
    traces = {
        "trace_links": [
            {"rubric_id": "RS", "spec_ids": ["S_MUST"], "evidence_quotes": []},
            {"rubric_id": "RB", "spec_ids": ["S_MUST"], "evidence_quotes": []},
        ]
    }
    assert run_rule_l6(_l5_specs(), _l6_rubrics(), traces) == ([], [])


def test_l6_untraced_must_spec_is_left_to_rule_two() -> None:
    """Over-strict guard B: absent traces are Rule 2 territory, not L6."""
    assert run_rule_l6(_l5_specs(), _l6_rubrics(), {"trace_links": []}) == ([], [])


@pytest.mark.parametrize(
    "trace_links",
    [
        [{"rubric_id": "RQ", "spec_ids": ["S_MUST"], "evidence_quotes": []}],
        [
            {"rubric_id": "RB", "spec_ids": ["S_MUST"], "evidence_quotes": []},
            {"rubric_id": "RQ", "spec_ids": ["S_MUST"], "evidence_quotes": []},
        ],
    ],
)
def test_l6_qualitative_trace_is_left_to_rule_two_family(
    trace_links: list[dict[str, Any]],
) -> None:
    """Over-strict guard C: L6 is bonus-only; qualitative involvement is
    reserved for the separate Rule 2-family policy selected by the owner.
    """
    assert run_rule_l6(_l5_specs(), _l6_rubrics(), {"trace_links": trace_links}) == (
        [],
        [],
    )


@pytest.mark.parametrize(
    "code",
    [
        "spec_text_not_in_snapshot_span",
        "spec_quote_not_in_snapshot_span",
        "evidence_quote_not_in_snapshot_span",
        "source_document_hash_mismatch",
        "spec_source_ref_span_invalid",
    ],
)
def test_snapshot_grounding_trigger_is_high_severity(code: str) -> None:
    snapshot = _make_snapshot(tamper_hash="0" * 64 if code == "source_document_hash_mismatch" else None)
    _attach_exists(snapshot, exists=True)
    spec = _baseline_spec()
    traces = _baseline_traces()
    if code == "spec_text_not_in_snapshot_span":
        spec["spec_items"][0]["text"] = "fabricated nonsense."
    elif code == "spec_quote_not_in_snapshot_span":
        spec["spec_items"][0]["source_ref"]["quote"] = "fabricated nonsense."
    elif code == "evidence_quote_not_in_snapshot_span":
        q = traces["trace_links"][0]["evidence_quotes"][0]
        q["source_ref"] = {"document_id": "DOC_SPEC", "start_line": 1, "end_line": 1}
        q["quote"] = "fabricated nonsense."
        q["verification_mode"] = "ai_judgement"
    elif code == "spec_source_ref_span_invalid":
        spec["spec_items"][0]["source_ref"]["end_line"] = 99
    diagnostics = run_rule_zero(spec, _baseline_rubric(), traces, snapshot)
    matching = [d for d in diagnostics if d.code == code]
    assert matching, f"expected trigger {code!r} to fire"
    assert all(d.severity == "high" for d in matching)
    # And the summary helper must also count it under "high".
    counts = severity_counts(diagnostics)
    assert counts["high"] >= len(matching)
