"""Contract tests for framework-neutral agent runners."""

from __future__ import annotations

from pathlib import Path

import copy
from typing import Any

import pytest

from assessment_harness.agent_runners import (
    AgentRunner,
    MockFixtureRunner,
    classify_candidate_run_integrity,
    classify_deep_candidate_run_integrity,
    normalize_result_candidates,
    validate_candidate_audit_trace,
)
from assessment_harness.models import SourceSnapshot, load_source_snapshot
from assessment_harness.schemas import validate


def _candidate_artifacts(run_id: str = "run_1") -> dict[str, Any]:
    return {
        "spec_item_candidates": [
            {
                "candidate_id": "SC1",
                "proposed_item": {
                    "id": "S1",
                    "text": "Implement refund handling for cancelled orders.",
                    "requirement_level": "must",
                    "source_ref": {
                        "document_id": "DOC_SPEC",
                        "start_line": 42,
                        "end_line": 42,
                    },
                },
                "agent_runner": "mock_fixture",
                "agent_run_id": run_id,
                "integrity_status": "pending_check",
            }
        ],
        "rubric_item_candidates": [
            {
                "candidate_id": "RC1",
                "proposed_item": {
                    "id": "R1",
                    "title": "Refund policy handling",
                    "evaluation_role": "scored",
                    "source_ref": {
                        "document_id": "DOC_RUBRIC",
                        "start_line": 18,
                        "end_line": 22,
                    },
                },
                "agent_runner": "mock_fixture",
                "agent_run_id": run_id,
                "integrity_status": "pending_check",
            }
        ],
        "trace_link_candidates": [
            {
                "candidate_id": "TC1",
                "proposed_item": {
                    "rubric_id": "R1",
                    "spec_ids": ["S1"],
                    "evidence_quotes": [
                        {
                            "spec_id": "S1",
                            "quote": "Implement refund handling for cancelled orders.",
                            "verification_mode": "token_sequence",
                        }
                    ],
                },
                "agent_runner": "mock_fixture",
                "agent_run_id": run_id,
                "integrity_status": "pending_check",
            }
        ],
    }


def _audit_trace(run_id: str = "run_1") -> list[dict[str, Any]]:
    return [
        {
            "run_id": run_id,
            "turn": 0,
            "role": "system",
            "content_ref": "mock_fixture_replay",
        },
        {
            "run_id": run_id,
            "finish_reason": "complete",
            "turns": 0,
            "tool_call_count": 0,
        },
    ]


def _normalized_clean_run(
    fixture_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], SourceSnapshot]:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment", run_id="mock_run")
    result = runner.run(
        spec_path=fixture_dir / "clean_assignment" / "source" / "spec.md",
        rubric_path=fixture_dir / "clean_assignment" / "source" / "rubric.md",
        tools=[],
        max_turns=1,
        policy={"rules": {}},
    )
    candidates = normalize_result_candidates(result)
    snapshot = load_source_snapshot(
        fixture_dir / "clean_assignment" / "source_manifest.yaml"
    )
    return candidates, result.audit_trace, snapshot


def test_mock_fixture_runner_satisfies_agent_runner_protocol(
    fixture_dir: Path,
) -> None:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment")

    assert isinstance(runner, AgentRunner)


def test_mock_fixture_runner_replays_fixture_artifacts(fixture_dir: Path) -> None:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment", run_id="mock_run")
    result = runner.run(
        spec_path=fixture_dir / "clean_assignment" / "source" / "spec.md",
        rubric_path=fixture_dir / "clean_assignment" / "source" / "rubric.md",
        tools=[],
        max_turns=1,
        policy={"rules": {}},
    )

    assert result.run_id == "mock_run"
    assert result.runner_name == "mock_fixture"
    assert result.finish_reason == "complete"
    assert validate("spec_items", result.artifacts["spec_items"]) == []
    assert validate("rubric_items", result.artifacts["rubric_items"]) == []
    assert validate("trace_links", result.artifacts["trace_links"]) == []
    assert len(result.audit_trace) > 0
    assert all(validate("agent_trace", event) == [] for event in result.audit_trace)
    assert result.audit_trace[-1]["finish_reason"] == "complete"
    assert result.raw_trace[0]["fixture_dir"].endswith("clean_assignment")


def test_mock_fixture_runner_output_normalizes_to_candidate_artifacts(
    fixture_dir: Path,
) -> None:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment", run_id="mock_run")
    result = runner.run(
        spec_path=fixture_dir / "clean_assignment" / "source" / "spec.md",
        rubric_path=fixture_dir / "clean_assignment" / "source" / "rubric.md",
        tools=[],
        max_turns=1,
        policy={"rules": {}},
    )

    candidates = normalize_result_candidates(result)

    assert validate("candidates", candidates) == []
    assert validate_candidate_audit_trace(candidates, result.audit_trace) == []
    assert candidates["spec_item_candidates"][0]["candidate_id"] == "SC1"
    assert candidates["spec_item_candidates"][0]["agent_runner"] == "mock_fixture"
    assert candidates["spec_item_candidates"][0]["agent_run_id"] == "mock_run"
    assert candidates["spec_item_candidates"][0]["integrity_status"] == "pending_check"


@pytest.mark.parametrize(
    ("candidate_section", "stripped_fields"),
    [
        (
            "spec_item_candidates",
            ["support", "identity_basis", "variants"],
        ),
        (
            "rubric_item_candidates",
            ["support", "identity_basis", "variants"],
        ),
        (
            "trace_link_candidates",
            [
                "support",
                "identity_basis",
                "variants",
                "sources",
                "reviewed_by",
                "reviewed_at",
            ],
        ),
    ],
)
def test_candidate_normalization_strips_compacting_only_fields(
    fixture_dir: Path,
    candidate_section: str,
    stripped_fields: list[str],
) -> None:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment", run_id="mock_run")
    result = runner.run(
        spec_path=fixture_dir / "clean_assignment" / "source" / "spec.md",
        rubric_path=fixture_dir / "clean_assignment" / "source" / "rubric.md",
        tools=[],
        max_turns=1,
        policy={"rules": {}},
    )

    candidates = normalize_result_candidates(result)
    proposed_item = candidates[candidate_section][0]["proposed_item"]

    for field in stripped_fields:
        assert field not in proposed_item


def test_candidate_run_integrity_marks_clean_structural_run_candidates_structural(
    fixture_dir: Path,
) -> None:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment", run_id="mock_run")
    result = runner.run(
        spec_path=fixture_dir / "clean_assignment" / "source" / "spec.md",
        rubric_path=fixture_dir / "clean_assignment" / "source" / "rubric.md",
        tools=[],
        max_turns=1,
        policy={"rules": {}},
    )
    candidates = normalize_result_candidates(result)

    integrity = classify_candidate_run_integrity(candidates, result.audit_trace)

    assert integrity.integrity_status == "structurally_validated"
    assert integrity.errors == ()
    assert validate("candidates", integrity.candidates) == []
    assert {
        candidate["integrity_status"]
        for section in integrity.candidates.values()
        for candidate in section
    } == {"structurally_validated"}
    assert candidates["spec_item_candidates"][0]["integrity_status"] == "pending_check"


def test_candidate_run_integrity_does_not_claim_deep_rule_zero_validation() -> None:
    candidates = _candidate_artifacts(run_id="run_1")
    candidates["rubric_item_candidates"] = []
    candidates["trace_link_candidates"][0]["proposed_item"] = {
        "rubric_id": "R_DOES_NOT_EXIST",
        "spec_ids": ["S_DOES_NOT_EXIST"],
        "evidence_quotes": [
            {
                "spec_id": "S_MISMATCH",
                "quote": "totally unrelated quote",
                "verification_mode": "token_sequence",
            }
        ],
    }

    integrity = classify_candidate_run_integrity(candidates, _audit_trace("run_1"))

    assert integrity.integrity_status == "structurally_validated"
    assert integrity.errors == ()
    assert {
        candidate["integrity_status"]
        for section in integrity.candidates.values()
        for candidate in section
    } == {"structurally_validated"}


def test_deep_candidate_run_integrity_promotes_clean_run_to_validated(
    fixture_dir: Path,
) -> None:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment", run_id="mock_run")
    result = runner.run(
        spec_path=fixture_dir / "clean_assignment" / "source" / "spec.md",
        rubric_path=fixture_dir / "clean_assignment" / "source" / "rubric.md",
        tools=[],
        max_turns=1,
        policy={"rules": {}},
    )
    candidates = normalize_result_candidates(result)
    snapshot = load_source_snapshot(
        fixture_dir / "clean_assignment" / "source_manifest.yaml"
    )

    integrity = classify_deep_candidate_run_integrity(
        candidates,
        result.audit_trace,
        snapshot,
    )

    assert integrity.integrity_status == "validated"
    assert integrity.errors == ()
    assert validate("candidates", integrity.candidates) == []
    assert {
        candidate["integrity_status"]
        for section in integrity.candidates.values()
        for candidate in section
    } == {"validated"}
    assert candidates["spec_item_candidates"][0]["integrity_status"] == "pending_check"


def test_deep_candidate_run_integrity_rejects_dangling_internal_reference(
    fixture_dir: Path,
) -> None:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment", run_id="mock_run")
    result = runner.run(
        spec_path=fixture_dir / "clean_assignment" / "source" / "spec.md",
        rubric_path=fixture_dir / "clean_assignment" / "source" / "rubric.md",
        tools=[],
        max_turns=1,
        policy={"rules": {}},
    )
    candidates = normalize_result_candidates(result)
    candidates["trace_link_candidates"][0]["proposed_item"]["rubric_id"] = "R_MISSING"
    snapshot = load_source_snapshot(
        fixture_dir / "clean_assignment" / "source_manifest.yaml"
    )

    integrity = classify_deep_candidate_run_integrity(
        candidates,
        result.audit_trace,
        snapshot,
    )

    assert integrity.integrity_status == "invalid_reference"
    assert any("dangling_rubric_reference" in error for error in integrity.errors)
    assert {
        candidate["integrity_status"]
        for section in integrity.candidates.values()
        for candidate in section
    } == {"invalid_reference"}


def test_deep_candidate_run_integrity_rejects_token_sequence_quote_mismatch(
    fixture_dir: Path,
) -> None:
    candidates, audit_trace, snapshot = _normalized_clean_run(fixture_dir)
    quote = candidates["trace_link_candidates"][0]["proposed_item"]["evidence_quotes"][0]
    quote["quote"] = "This quote is not in the referenced spec item."
    quote.pop("source_ref")

    integrity = classify_deep_candidate_run_integrity(
        candidates,
        audit_trace,
        snapshot,
    )

    assert integrity.integrity_status == "quote_mismatch"
    assert any(
        "evidence_quote_token_sequence_mismatch" in error
        for error in integrity.errors
    )


def test_deep_candidate_run_integrity_rejects_evidence_spec_id_mismatch(
    fixture_dir: Path,
) -> None:
    candidates, audit_trace, snapshot = _normalized_clean_run(fixture_dir)
    quote = candidates["trace_link_candidates"][0]["proposed_item"]["evidence_quotes"][0]
    quote["spec_id"] = "S2"

    integrity = classify_deep_candidate_run_integrity(
        candidates,
        audit_trace,
        snapshot,
    )

    assert integrity.integrity_status == "invalid_reference"
    assert any(
        "evidence_quote_spec_id_mismatch" in error
        for error in integrity.errors
    )


def test_deep_candidate_run_integrity_rejects_source_grounding_mismatch(
    fixture_dir: Path,
) -> None:
    candidates, audit_trace, snapshot = _normalized_clean_run(fixture_dir)
    candidates["spec_item_candidates"][0]["proposed_item"]["text"] = (
        "This text is not present in the source span."
    )

    integrity = classify_deep_candidate_run_integrity(
        candidates,
        audit_trace,
        snapshot,
    )

    assert integrity.integrity_status == "source_grounding_mismatch"
    assert any("spec_text_not_in_snapshot_span" in error for error in integrity.errors)
    assert validate("candidates", integrity.candidates) == []


def test_deep_candidate_run_integrity_prefers_reference_over_grounding_and_quote(
    fixture_dir: Path,
) -> None:
    candidates, audit_trace, snapshot = _normalized_clean_run(fixture_dir)
    candidates["spec_item_candidates"][0]["proposed_item"]["text"] = (
        "This text is not present in the source span."
    )
    quote = candidates["trace_link_candidates"][0]["proposed_item"]["evidence_quotes"][0]
    quote["spec_id"] = "S2"
    quote["quote"] = "This quote is not in the referenced spec item."
    quote.pop("source_ref")

    integrity = classify_deep_candidate_run_integrity(
        candidates,
        audit_trace,
        snapshot,
    )

    assert integrity.integrity_status == "invalid_reference"
    assert any(
        "evidence_quote_spec_id_mismatch" in error
        for error in integrity.errors
    )
    assert any("spec_text_not_in_snapshot_span" in error for error in integrity.errors)


def test_deep_candidate_run_integrity_does_not_over_reject_ai_judgement_quote(
    fixture_dir: Path,
) -> None:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment", run_id="mock_run")
    result = runner.run(
        spec_path=fixture_dir / "clean_assignment" / "source" / "spec.md",
        rubric_path=fixture_dir / "clean_assignment" / "source" / "rubric.md",
        tools=[],
        max_turns=1,
        policy={"rules": {}},
    )
    candidates = normalize_result_candidates(result)
    quote = candidates["trace_link_candidates"][0]["proposed_item"]["evidence_quotes"][0]
    quote["quote"] = "Semantic paraphrase that still awaits verifier review."
    quote["verification_mode"] = "ai_judgement"
    quote.pop("source_ref")
    snapshot = load_source_snapshot(
        fixture_dir / "clean_assignment" / "source_manifest.yaml"
    )

    integrity = classify_deep_candidate_run_integrity(
        candidates,
        result.audit_trace,
        snapshot,
    )

    assert integrity.integrity_status == "validated"
    assert not any(
        "evidence_quote_token_sequence_mismatch" in error
        for error in integrity.errors
    )


def test_candidate_run_integrity_classifies_candidate_schema_errors() -> None:
    candidates = _candidate_artifacts(run_id="run_1")
    del candidates["spec_item_candidates"][0]["agent_run_id"]

    integrity = classify_candidate_run_integrity(candidates, _audit_trace("run_1"))

    assert integrity.integrity_status == "schema_violation"
    assert any(error.startswith("candidates:") for error in integrity.errors)
    assert integrity.candidates["spec_item_candidates"][0]["integrity_status"] == (
        "schema_violation"
    )


def test_candidate_run_integrity_classifies_audit_trace_schema_errors() -> None:
    candidates = _candidate_artifacts(run_id="run_1")
    audit_trace = copy.deepcopy(_audit_trace(run_id="run_1"))
    del audit_trace[0]["content_ref"]

    integrity = classify_candidate_run_integrity(candidates, audit_trace)

    assert integrity.integrity_status == "schema_violation"
    assert any(error.startswith("audit_trace/0") for error in integrity.errors)
    assert integrity.candidates["trace_link_candidates"][0]["integrity_status"] == (
        "schema_violation"
    )


def test_candidate_run_integrity_classifies_missing_trace_attribution() -> None:
    candidates = _candidate_artifacts(run_id="run_without_trace")

    integrity = classify_candidate_run_integrity(candidates, _audit_trace("run_1"))

    assert integrity.integrity_status == "trace_attribution_error"
    assert any("has no matching audit_trace run_id" in error for error in integrity.errors)
    assert validate("candidates", integrity.candidates) == []
    assert {
        candidate["integrity_status"]
        for section in integrity.candidates.values()
        for candidate in section
    } == {"trace_attribution_error"}


def test_agent_trace_schema_rejects_unattributed_event() -> None:
    assert validate("agent_trace", {"finish_reason": "complete"}) != []


def test_agent_trace_schema_requires_role_payload() -> None:
    bare_role_events = [
        {"run_id": "run_1", "turn": 0, "role": "system"},
        {"run_id": "run_1", "turn": 1, "role": "agent"},
        {"run_id": "run_1", "turn": 1, "role": "tool"},
    ]

    for event in bare_role_events:
        assert validate("agent_trace", event) != []


def test_candidate_audit_trace_validation_accepts_matching_run_ids() -> None:
    candidates = _candidate_artifacts(run_id="run_1")
    audit_trace = _audit_trace(run_id="run_1")

    assert validate_candidate_audit_trace(candidates, audit_trace) == []


def test_candidate_audit_trace_validation_rejects_missing_trace_run_id() -> None:
    candidates = _candidate_artifacts(run_id="run_without_trace")
    audit_trace = _audit_trace(run_id="run_1")

    errors = validate_candidate_audit_trace(candidates, audit_trace)

    assert any("has no matching audit_trace run_id" in error for error in errors)


def test_candidate_audit_trace_validation_keeps_schema_errors_visible() -> None:
    candidates = _candidate_artifacts(run_id="run_1")
    del candidates["spec_item_candidates"][0]["agent_run_id"]
    audit_trace = _audit_trace(run_id="run_1")

    errors = validate_candidate_audit_trace(candidates, audit_trace)

    assert any(
        error.startswith("candidates:")
        and "agent_run_id" in error
        and "is a required property" in error
        for error in errors
    )


@pytest.mark.parametrize(
    "section",
    ["spec_item_candidates", "rubric_item_candidates", "trace_link_candidates"],
)
def test_candidate_audit_trace_validation_checks_each_candidate_section(
    section: str,
) -> None:
    candidates = _candidate_artifacts(run_id="run_1")
    candidates[section][0]["agent_run_id"] = "run_without_trace"
    audit_trace = _audit_trace(run_id="run_1")

    errors = validate_candidate_audit_trace(candidates, audit_trace)

    assert any(f"{section}/0/agent_run_id" in error for error in errors)


def test_candidate_audit_trace_validation_rejects_invalid_trace_event() -> None:
    candidates = _candidate_artifacts(run_id="run_1")
    audit_trace = copy.deepcopy(_audit_trace(run_id="run_1"))
    del audit_trace[0]["content_ref"]

    errors = validate_candidate_audit_trace(candidates, audit_trace)

    assert any("audit_trace/0" in error and "content_ref" in error for error in errors)
