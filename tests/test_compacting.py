"""Contract tests for Phase 2 union compacting."""

from __future__ import annotations

from typing import Any

import pytest

from assessment_harness.compacting import (
    CompactingInputError,
    compact_validated_candidates,
)
from assessment_harness.schemas import validate


def _candidate_run(
    *,
    run_id: str,
    spec_id: str,
    rubric_id: str,
    text: str = "Implement refund handling for cancelled orders.",
    title: str = "Refund policy handling",
    integrity_status: str = "validated",
) -> dict[str, list[dict[str, Any]]]:
    return {
        "spec_item_candidates": [
            {
                "candidate_id": "SC1",
                "proposed_item": {
                    "id": spec_id,
                    "text": text,
                    "requirement_level": "must",
                    "source_ref": {
                        "document_id": "DOC_SPEC",
                        "start_line": 42,
                        "end_line": 42,
                    },
                },
                "agent_runner": "mock_fixture",
                "agent_run_id": run_id,
                "integrity_status": integrity_status,
            }
        ],
        "rubric_item_candidates": [
            {
                "candidate_id": "RC1",
                "proposed_item": {
                    "id": rubric_id,
                    "title": title,
                    "description": "Checks the refund requirement.",
                    "evaluation_role": "scored",
                    "source_ref": {
                        "document_id": "DOC_RUBRIC",
                        "start_line": 18,
                        "end_line": 22,
                    },
                },
                "agent_runner": "mock_fixture",
                "agent_run_id": run_id,
                "integrity_status": integrity_status,
            }
        ],
        "trace_link_candidates": [
            {
                "candidate_id": "TC1",
                "proposed_item": {
                    "rubric_id": rubric_id,
                    "spec_ids": [spec_id],
                    "rationale": "The rubric evaluates the refund requirement.",
                    "evidence_quotes": [
                        {
                            "spec_id": spec_id,
                            "quote": "Implement refund handling for cancelled orders.",
                            "verification_mode": "token_sequence",
                        }
                    ],
                    "semantic_status": "pending_verification",
                },
                "agent_runner": "mock_fixture",
                "agent_run_id": run_id,
                "integrity_status": integrity_status,
            }
        ],
    }


def _policy() -> dict[str, Any]:
    return {
        "compacting": {
            "identity_basis": {
                "spec_item": "source+section+normalized_text",
                "rubric_item": "title+normalized_description",
                "trace_link": "rubric_id+sorted(spec_ids)",
            }
        }
    }


def test_compacting_preserves_single_run_candidates_without_auto_exclusion() -> None:
    compacted = compact_validated_candidates(
        [_candidate_run(run_id="run_1", spec_id="S_LOCAL", rubric_id="R_LOCAL")],
        _policy(),
    )

    assert validate("compacting", compacted) == []
    assert compacted["spec_items"][0]["id"] == "S1"
    assert compacted["rubric_items"][0]["id"] == "R1"
    assert compacted["trace_links"][0]["rubric_id"] == "R1"
    assert compacted["trace_links"][0]["spec_ids"] == ["S1"]
    assert compacted["trace_links"][0]["evidence_quotes"][0]["spec_id"] == "S1"
    assert compacted["trace_links"][0]["reviewed_by"] is None
    assert compacted["trace_links"][0]["reviewed_at"] is None
    assert compacted["spec_items"][0]["support"] == {
        "total_valid_runs": 1,
        "found_in_runs": ["run_1"],
    }
    assert compacted["spec_items"][0]["variants"][0]["proposed_item"]["id"] == (
        "S_LOCAL"
    )


def test_compacting_unions_matching_candidates_and_records_id_map() -> None:
    compacted = compact_validated_candidates(
        [
            _candidate_run(run_id="run_1", spec_id="S_A", rubric_id="R_A"),
            _candidate_run(run_id="run_2", spec_id="S_B", rubric_id="R_B"),
        ],
        _policy(),
    )

    assert validate("compacting", compacted) == []
    assert validate("id_map", {"id_map": compacted["id_map"]}) == []
    assert len(compacted["spec_items"]) == 1
    assert len(compacted["rubric_items"]) == 1
    assert len(compacted["trace_links"]) == 1
    assert compacted["spec_items"][0]["support"]["found_in_runs"] == [
        "run_1",
        "run_2",
    ]
    assert len(compacted["spec_items"][0]["variants"]) == 2
    assert {
        (entry["entity_type"], entry["canonical_id"])
        for entry in compacted["id_map"]
    } == {
        ("spec_item", "S1"),
        ("rubric_item", "R1"),
        ("trace_link", "T1"),
    }
    spec_map = next(
        entry for entry in compacted["id_map"] if entry["entity_type"] == "spec_item"
    )
    assert spec_map["run_refs"] == [
        {"run_id": "run_1", "local_id": "S_A"},
        {"run_id": "run_2", "local_id": "S_B"},
    ]


def test_compacting_excludes_non_validated_candidates_from_artifacts() -> None:
    compacted = compact_validated_candidates(
        [
            _candidate_run(run_id="run_1", spec_id="S_A", rubric_id="R_A"),
            _candidate_run(
                run_id="run_2",
                spec_id="S_B",
                rubric_id="R_B",
                integrity_status="invalid_reference",
            ),
        ],
        _policy(),
    )

    assert validate("compacting", compacted) == []
    assert compacted["spec_items"][0]["support"] == {
        "total_valid_runs": 1,
        "found_in_runs": ["run_1"],
    }
    assert len(compacted["spec_items"][0]["variants"]) == 1
    assert all(
        run_ref["run_id"] == "run_1"
        for id_map_entry in compacted["id_map"]
        for run_ref in id_map_entry["run_refs"]
    )


def test_compacting_excludes_mixed_status_run_as_one_unit() -> None:
    mixed_run = _candidate_run(run_id="run_1", spec_id="S_A", rubric_id="R_A")
    mixed_run["trace_link_candidates"][0]["integrity_status"] = "invalid_reference"

    compacted = compact_validated_candidates([mixed_run], _policy())

    assert validate("compacting", compacted) == []
    assert compacted == {
        "spec_items": [],
        "rubric_items": [],
        "trace_links": [],
        "id_map": [],
    }


def test_compacting_splits_distinct_identity_candidates() -> None:
    compacted = compact_validated_candidates(
        [
            _candidate_run(run_id="run_1", spec_id="S_A", rubric_id="R_A"),
            _candidate_run(
                run_id="run_2",
                spec_id="S_B",
                rubric_id="R_B",
                text="Explain cancellation handling without mentioning refunds.",
            ),
        ],
        _policy(),
    )

    assert validate("compacting", compacted) == []
    assert [item["id"] for item in compacted["spec_items"]] == ["S1", "S2"]
    assert compacted["spec_items"][0]["support"] == {
        "total_valid_runs": 2,
        "found_in_runs": ["run_1"],
    }
    assert {tuple(link["spec_ids"]) for link in compacted["trace_links"]} == {
        ("S1",),
        ("S2",),
    }


def test_compacting_preserves_raw_variants_after_normalized_identity_match() -> None:
    compacted = compact_validated_candidates(
        [
            _candidate_run(run_id="run_1", spec_id="S_A", rubric_id="R_A"),
            _candidate_run(
                run_id="run_2",
                spec_id="S_B",
                rubric_id="R_B",
                text="  IMPLEMENT   REFUND HANDLING for cancelled orders.  ",
            ),
        ],
        _policy(),
    )

    assert validate("compacting", compacted) == []
    assert len(compacted["spec_items"]) == 1
    assert [
        variant["proposed_item"]["text"]
        for variant in compacted["spec_items"][0]["variants"]
    ] == [
        "Implement refund handling for cancelled orders.",
        "  IMPLEMENT   REFUND HANDLING for cancelled orders.  ",
    ]


def test_compacting_rejects_unmapped_trace_references_without_silent_drop() -> None:
    candidate_run = _candidate_run(run_id="run_1", spec_id="S_A", rubric_id="R_A")
    candidate_run["trace_link_candidates"][0]["proposed_item"]["spec_ids"] = [
        "S_MISSING"
    ]

    with pytest.raises(CompactingInputError, match="unmapped spec_ids"):
        compact_validated_candidates([candidate_run], _policy())
