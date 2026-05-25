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
