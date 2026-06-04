"""Contract tests for framework-neutral read-only agent tools."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from assessment_harness.models import HarnessInputError
from assessment_harness.tools import (
    get_rubric_item,
    list_rubric_items,
    list_sections,
    read_spec_section,
)


def test_list_sections_returns_markdown_heading_spans(fixture_dir: Path) -> None:
    sections = list_sections(fixture_dir / "clean_assignment/source/spec.md")

    assert sections == [
        {
            "title": "Refund Service Spec",
            "level": 1,
            "start_line": 1,
            "content_start_line": 3,
            "end_line": 14,
        },
        {
            "title": "Requirements",
            "level": 2,
            "start_line": 3,
            "content_start_line": 5,
            "end_line": 6,
        },
        {
            "title": "Optional features",
            "level": 2,
            "start_line": 8,
            "content_start_line": 10,
            "end_line": 10,
        },
        {
            "title": "Notes",
            "level": 2,
            "start_line": 12,
            "content_start_line": 14,
            "end_line": 14,
        },
    ]


def test_read_spec_section_returns_case_insensitive_exact_section(
    fixture_dir: Path,
) -> None:
    section = read_spec_section(
        fixture_dir / "clean_assignment/source/spec.md", "requirements"
    )

    assert section["title"] == "Requirements"
    assert section["start_line"] == 3
    assert section["end_line"] == 6
    assert "Implement refund handling" in section["text"]
    assert "Idempotent retries" in section["text"]
    assert "Optional features" not in section["text"]


def test_read_spec_section_rejects_missing_or_ambiguous_section(
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "spec.md"
    spec_path.write_text(
        "# Spec\n\n## Requirements\nOne.\n\n## Requirements\nTwo.\n",
        encoding="utf-8",
    )

    with pytest.raises(HarnessInputError, match="ambiguous"):
        read_spec_section(spec_path, "Requirements")
    with pytest.raises(HarnessInputError, match="not found"):
        read_spec_section(spec_path, "Scoring")


def test_read_spec_section_returns_non_inverted_span_for_empty_section(
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "spec.md"
    spec_path.write_text("# Spec\n\n## Empty\n\n## Next\nText.\n", encoding="utf-8")

    section = read_spec_section(spec_path, "Empty")

    assert section["content_start_line"] == section["end_line"]
    assert section["text"] == ""


def test_read_spec_section_empty_section_does_not_include_adjacent_heading(
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "spec.md"
    spec_path.write_text("# Spec\n\n## Overview\n## Details\nText.\n", encoding="utf-8")

    section = read_spec_section(spec_path, "Overview")

    assert section["text"] == ""
    assert "## Details" not in section["text"]
    assert section["content_start_line"] == section["end_line"] == 3
    assert section["end_line"] < 4


def test_list_rubric_items_returns_validated_summaries(fixture_dir: Path) -> None:
    items = list_rubric_items(fixture_dir / "clean_assignment/rubric_items.yaml")

    assert [item["id"] for item in items] == ["R1", "R2", "R3", "R4"]
    assert items[0] == {
        "id": "R1",
        "title": "Refund handling",
        "evaluation_role": "scored",
        "weight": 10,
        "source_ref": {"document_id": "DOC_RUBRIC", "start_line": 3, "end_line": 4},
    }
    assert "weight" not in items[3]


def test_get_rubric_item_returns_full_validated_item(fixture_dir: Path) -> None:
    item = get_rubric_item(fixture_dir / "clean_assignment/rubric_items.yaml", "R3")

    assert item["id"] == "R3"
    assert item["evaluation_role"] == "bonus"
    assert item["description"] == (
        "Bonus credit for audit log entries on every refund decision."
    )
    assert item["evidence_required"] == ["code"]


def test_rubric_tools_return_deep_copies(fixture_dir: Path) -> None:
    rubric_path = fixture_dir / "clean_assignment/rubric_items.yaml"

    summaries = list_rubric_items(rubric_path)
    summaries[0]["source_ref"]["start_line"] = 999
    full_item = get_rubric_item(rubric_path, "R3")
    full_item["evidence_required"].append("mutation")

    assert list_rubric_items(rubric_path)[0]["source_ref"]["start_line"] == 3
    assert get_rubric_item(rubric_path, "R3")["evidence_required"] == ["code"]


def test_get_rubric_item_rejects_missing_item(fixture_dir: Path) -> None:
    with pytest.raises(HarnessInputError, match="not found"):
        get_rubric_item(fixture_dir / "clean_assignment/rubric_items.yaml", "R404")


def test_get_rubric_item_rejects_ambiguous_id(
    fixture_dir: Path, tmp_path: Path
) -> None:
    source_doc = yaml.safe_load(
        (fixture_dir / "clean_assignment/rubric_items.yaml").read_text(
            encoding="utf-8"
        )
    )
    source_doc["rubric_items"].append(dict(source_doc["rubric_items"][0]))
    duplicate_path = tmp_path / "duplicate_rubric_items.yaml"
    duplicate_path.write_text(yaml.safe_dump(source_doc), encoding="utf-8")

    with pytest.raises(HarnessInputError, match="ambiguous"):
        get_rubric_item(duplicate_path, "R1")
