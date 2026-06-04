"""Unit tests for `models.py` loader edge cases.

The other test modules exercise loaders indirectly via the CLI. This module
covers paths that are easy to miss there: missing files, malformed YAML,
schema violations, sha256 mismatch, relative-path resolution, and span bounds.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from assessment_harness.models import (
    Document,
    HarnessInputError,
    SourceSnapshot,
    load_policy,
    load_source_snapshot,
    load_validated,
    read_yaml,
)
from assessment_harness.schemas import SCHEMA_FILES, validate


def test_read_yaml_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(HarnessInputError) as exc_info:
        read_yaml(tmp_path / "does_not_exist.yaml")
    assert "file not found" in str(exc_info.value)


def test_read_yaml_invalid_yaml_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("this: is: not: valid", encoding="utf-8")
    with pytest.raises(HarnessInputError) as exc_info:
        read_yaml(path)
    assert "invalid YAML" in str(exc_info.value)


def test_load_validated_schema_violation_raises(tmp_path: Path) -> None:
    path = tmp_path / "spec.yaml"
    # `spec_items` entries require id/text/requirement_level/source_ref.
    path.write_text(
        yaml.safe_dump({"spec_items": [{"id": "S1"}]}),
        encoding="utf-8",
    )
    with pytest.raises(HarnessInputError) as exc_info:
        load_validated(path, "spec_items")
    assert exc_info.value.errors, "expected populated error list"


def test_load_validated_top_level_must_be_mapping(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(HarnessInputError) as exc_info:
        load_validated(path, "spec_items")
    assert "top-level value must be a mapping" in str(exc_info.value)


def test_phase_two_contract_schemas_are_registered_and_validate_plan_examples() -> None:
    candidates = {
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
                        "quote": "Implement refund handling for cancelled orders.",
                    },
                },
                "agent_runner": "claude_agent_sdk",
                "agent_run_id": "run_2026_05_25_a1b2",
                "source_excerpt": "Implement refund handling for cancelled orders.",
                "confidence": 0.82,
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
                "agent_runner": "claude_agent_sdk",
                "agent_run_id": "run_2026_05_25_a1b2",
                "integrity_status": "pending_check",
            }
        ],
        "trace_link_candidates": [
            {
                "candidate_id": "TC1",
                "proposed_item": {
                    "rubric_id": "R1",
                    "spec_ids": ["S1"],
                    "rationale": "R1 evaluates the documented refund requirement.",
                    "evidence_quotes": [
                        {
                            "spec_id": "S1",
                            "quote": "Implement refund handling for cancelled orders.",
                            "verification_mode": "token_sequence",
                            "source_ref": {
                                "document_id": "DOC_SPEC",
                                "start_line": 42,
                                "end_line": 42,
                            },
                        }
                    ],
                    "semantic_status": "pending_verification",
                },
                "agent_runner": "claude_agent_sdk",
                "agent_run_id": "run_2026_05_25_a1b2",
                "integrity_status": "pending_check",
            }
        ],
    }
    id_map = {
        "id_map": [
            {
                "canonical_id": "S1",
                "entity_type": "spec_item",
                "run_refs": [
                    {"run_id": "run_a1b2", "local_id": "S4"},
                    {"run_id": "run_c3d4", "local_id": "S1"},
                ],
            }
        ]
    }
    semantic_verifications = {
        "semantic_verifications": [
            {
                "trace_link_id": "T1",
                "status_proposal": "agent_supported",
                "rationale": (
                    "Rubric criterion is explicitly disclosed by the referenced "
                    "requirement."
                ),
                "source_refs": [
                    {"document_id": "DOC_SPEC", "start_line": 42, "end_line": 42},
                    {"document_id": "DOC_RUBRIC", "start_line": 18, "end_line": 22},
                ],
                "support": {
                    "total_valid_runs": 3,
                    "found_in_runs": ["verify_a1b2", "verify_c3d4"],
                },
                "variants": [],
            }
        ]
    }
    materialization_summary = {
        "review_id": "review_1",
        "trace_link_decision_count": 1,
        "review_queue_decision_count": 1,
        "unsupported_decision_count": 0,
        "output_paths": {
            "spec_items_path": "reviewed/spec_items.yaml",
            "rubric_items_path": "reviewed/rubric_items.yaml",
            "trace_links_path": "reviewed/trace_links.yaml",
            "review_queue_path": "reviewed/review_queue.json",
            "materialization_summary_path": (
                "reviewed/materialization_summary.json"
            ),
        },
        "source_paths": {
            "final_review_path": "review/final_review.yaml",
            "compacted_dir": "compacted",
            "review_queue_path": "compacted/review_queue.json",
        },
    }

    assert "candidates" in SCHEMA_FILES
    assert "compacting" in SCHEMA_FILES
    assert "id_map" in SCHEMA_FILES
    assert "semantic_verifications" in SCHEMA_FILES
    assert "materialization_summary" in SCHEMA_FILES
    assert validate("candidates", candidates) == []
    assert validate("id_map", id_map) == []
    assert validate("semantic_verifications", semantic_verifications) == []
    assert validate("materialization_summary", materialization_summary) == []
    materialization_summary_without_source_paths = dict(materialization_summary)
    del materialization_summary_without_source_paths["source_paths"]
    assert validate(
        "materialization_summary", materialization_summary_without_source_paths
    ) == []


def test_phase_two_contract_schemas_reject_untraceable_entries() -> None:
    candidate_errors = validate(
        "candidates",
        {
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
                    "agent_runner": "claude_agent_sdk",
                    "integrity_status": "validated",
                }
            ],
            "rubric_item_candidates": [],
            "trace_link_candidates": [],
        },
    )
    id_map_errors = validate(
        "id_map",
        {
            "id_map": [
                {
                    "canonical_id": "S1",
                    "entity_type": "spec_item",
                    "run_refs": [],
                }
            ]
        },
    )
    semantic_errors = validate(
        "semantic_verifications",
        {
            "semantic_verifications": [
                {
                    "trace_link_id": "T1",
                    "status_proposal": "human_accepted",
                    "rationale": "invalid final status as verifier proposal",
                    "source_refs": [],
                    "support": {"total_valid_runs": 1, "found_in_runs": ["verify_1"]},
                    "variants": [],
                }
            ]
        },
    )

    assert any("agent_run_id" in error for error in candidate_errors)
    assert id_map_errors
    assert semantic_errors


@pytest.mark.parametrize(
    ("candidate_kind", "proposed_item", "expected_error"),
    [
        (
            "spec_item_candidates",
            {
                "text": "Implement refund handling for cancelled orders.",
                "requirement_level": "must",
                "source_ref": {
                    "document_id": "DOC_SPEC",
                    "start_line": 42,
                    "end_line": 42,
                },
            },
            "'id' is a required property",
        ),
        (
            "spec_item_candidates",
            {
                "id": "S1",
                "text": "Implement refund handling for cancelled orders.",
                "requirement_level": "mandatory",
                "source_ref": {
                    "document_id": "DOC_SPEC",
                    "start_line": 42,
                    "end_line": 42,
                },
            },
            "'mandatory' is not one of",
        ),
        (
            "spec_item_candidates",
            "garbage",
            "is not of type 'object'",
        ),
        (
            "rubric_item_candidates",
            {
                "id": "R1",
                "evaluation_role": "scored",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 18,
                    "end_line": 22,
                },
            },
            "'title' is a required property",
        ),
        (
            "trace_link_candidates",
            {
                "rubric_id": "R1",
                "spec_ids": ["S1"],
                "evidence_quotes": [
                    {
                        "spec_id": "S1",
                        "quote": "Implement refund handling for cancelled orders.",
                        "verification_mode": "exact",
                    }
                ],
            },
            "'exact' is not one of",
        ),
        (
            "spec_item_candidates",
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
            },
            "'text' is a required property",
        ),
    ],
)
def test_candidates_schema_rejects_invalid_proposed_item_shape(
    candidate_kind: str,
    proposed_item: object,
    expected_error: str,
) -> None:
    candidates = {
        "spec_item_candidates": [],
        "rubric_item_candidates": [],
        "trace_link_candidates": [],
    }
    candidates[candidate_kind].append(
        {
            "candidate_id": "C1",
            "proposed_item": proposed_item,
            "agent_runner": "claude_agent_sdk",
            "agent_run_id": "run_2026_05_25_a1b2",
            "integrity_status": "pending_check",
        }
    )

    errors = validate("candidates", candidates)

    assert any(expected_error in error for error in errors)


def test_candidates_schema_rejects_invalid_integrity_status() -> None:
    errors = validate(
        "candidates",
        {
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
                    "agent_runner": "claude_agent_sdk",
                    "agent_run_id": "run_2026_05_25_a1b2",
                    "integrity_status": "accepted",
                }
            ],
            "rubric_item_candidates": [],
            "trace_link_candidates": [],
        },
    )

    assert errors


def test_candidates_schema_accepts_source_grounding_mismatch_status() -> None:
    errors = validate(
        "candidates",
        {
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
                    "agent_runner": "claude_agent_sdk",
                    "agent_run_id": "run_2026_05_25_a1b2",
                    "integrity_status": "source_grounding_mismatch",
                }
            ],
            "rubric_item_candidates": [],
            "trace_link_candidates": [],
        },
    )

    assert errors == []


def test_load_source_snapshot_computes_sha256(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.md"
    rubric_path = tmp_path / "rubric.md"
    spec_path.write_text("hello spec\n", encoding="utf-8")
    rubric_path.write_text("hello rubric\n", encoding="utf-8")

    manifest = {
        "project_id": "p",
        "assessment_version": "v1",
        "documents": [
            {
                "document_id": "DOC_SPEC",
                "role": "candidate_spec",
                "path": "spec.md",
                "sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
            },
            {
                "document_id": "DOC_RUBRIC",
                "role": "evaluator_rubric",
                "path": "rubric.md",
                "sha256": hashlib.sha256(rubric_path.read_bytes()).hexdigest(),
            },
        ],
    }
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    snapshot = load_source_snapshot(manifest_path)
    assert snapshot.project_id == "p"
    assert set(snapshot.documents) == {"DOC_SPEC", "DOC_RUBRIC"}
    spec_doc = snapshot.get("DOC_SPEC")
    assert spec_doc is not None
    assert spec_doc.hash_matches is True
    assert spec_doc.lines == ["hello spec"]
    assert spec_doc.path.resolve() == spec_path.resolve()


def test_load_source_snapshot_detects_hash_mismatch(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.md"
    spec_path.write_text("content A\n", encoding="utf-8")
    manifest = {
        "project_id": "p",
        "assessment_version": "v1",
        "documents": [
            {
                "document_id": "DOC_SPEC",
                "role": "candidate_spec",
                "path": "spec.md",
                "sha256": "0" * 64,  # intentionally wrong
            }
        ],
    }
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    snapshot = load_source_snapshot(manifest_path)
    doc = snapshot.get("DOC_SPEC")
    assert doc is not None
    assert doc.hash_matches is False
    assert doc.expected_sha256 == "0" * 64
    assert doc.actual_sha256 == hashlib.sha256(b"content A\n").hexdigest()


def test_load_source_snapshot_resolves_relative_path(tmp_path: Path) -> None:
    nested = tmp_path / "source"
    nested.mkdir()
    spec_path = nested / "spec.md"
    spec_path.write_text("body\n", encoding="utf-8")

    manifest = {
        "project_id": "p",
        "assessment_version": "v1",
        "documents": [
            {
                "document_id": "DOC_SPEC",
                "role": "candidate_spec",
                "path": "source/spec.md",
                "sha256": hashlib.sha256(b"body\n").hexdigest(),
            }
        ],
    }
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    snapshot = load_source_snapshot(manifest_path)
    assert snapshot.get("DOC_SPEC").path.resolve() == spec_path.resolve()


def test_load_policy_none_returns_empty_dict() -> None:
    assert load_policy(None) == {}


def test_document_has_span_bounds() -> None:
    doc = Document(
        document_id="d",
        role="candidate_spec",
        path=Path("/tmp/x"),
        expected_sha256="0" * 64,
        actual_sha256="0" * 64,
        lines=["a", "b", "c"],
    )
    assert doc.has_span(1, 1) is True
    assert doc.has_span(1, 3) is True
    assert doc.has_span(3, 3) is True
    # under-strict guard: invalid spans must be rejected
    assert doc.has_span(0, 1) is False
    assert doc.has_span(1, 4) is False
    assert doc.has_span(2, 1) is False


def test_document_span_text_returns_joined_lines() -> None:
    doc = Document(
        document_id="d",
        role="candidate_spec",
        path=Path("/tmp/x"),
        expected_sha256="0" * 64,
        actual_sha256="0" * 64,
        lines=["alpha", "beta", "gamma"],
    )
    assert doc.span_text(1, 1) == "alpha"
    assert doc.span_text(1, 3) == "alpha\nbeta\ngamma"
    assert doc.span_text(2, 3) == "beta\ngamma"


def test_document_span_text_out_of_range_raises() -> None:
    doc = Document(
        document_id="d",
        role="candidate_spec",
        path=Path("/tmp/x"),
        expected_sha256="0" * 64,
        actual_sha256="0" * 64,
        lines=["only"],
    )
    with pytest.raises(IndexError):
        doc.span_text(1, 5)


def test_source_snapshot_get_returns_none_for_unknown() -> None:
    snapshot = SourceSnapshot(project_id="p", assessment_version="v1", documents={})
    assert snapshot.get("DOC_MISSING") is None
