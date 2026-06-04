"""Read-only rubric tools for framework-neutral agent runners."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from assessment_harness.models import HarnessInputError, load_validated


def list_rubric_items(rubric_items_path: Path) -> list[dict[str, Any]]:
    """Return compact rubric item summaries from a validated rubric artifact."""
    rubric_doc = load_validated(rubric_items_path, "rubric_items")
    items: list[dict[str, Any]] = []
    for item in rubric_doc.get("rubric_items", []):
        summary = {
            "id": item["id"],
            "title": item["title"],
            "evaluation_role": item["evaluation_role"],
            "source_ref": copy.deepcopy(item["source_ref"]),
        }
        if "weight" in item:
            summary["weight"] = item["weight"]
        items.append(summary)
    return items


def get_rubric_item(rubric_items_path: Path, rubric_id: str) -> dict[str, Any]:
    """Return one full rubric item by ID from a validated rubric artifact."""
    rubric_doc = load_validated(rubric_items_path, "rubric_items")
    matches = [
        item for item in rubric_doc.get("rubric_items", []) if item.get("id") == rubric_id
    ]
    if not matches:
        raise HarnessInputError(f"rubric item not found: {rubric_id}")
    if len(matches) > 1:
        raise HarnessInputError(f"rubric item id is ambiguous: {rubric_id}")
    return copy.deepcopy(matches[0])
