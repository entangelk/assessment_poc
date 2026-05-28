"""JSON Schema discovery and validation helpers.

Schemas live in the repo's top-level ``schemas/`` directory by default. The
directory can be overridden with the ``ASSESSMENT_HARNESS_SCHEMA_DIR``
environment variable so the Docker image and editable installs both work.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


SCHEMA_FILES: dict[str, str] = {
    "source_manifest": "source_manifest.schema.json",
    "spec_items": "spec_items.schema.json",
    "rubric_items": "rubric_items.schema.json",
    "trace_links": "trace_links.schema.json",
    "policy": "policy.schema.json",
    "findings": "findings.schema.json",
    "integrity_diagnostics": "integrity_diagnostics.schema.json",
    "cli_output": "cli_output.schema.json",
    "review_queue": "review_queue.schema.json",
    "final_review": "final_review.schema.json",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def schema_dir() -> Path:
    env = os.environ.get("ASSESSMENT_HARNESS_SCHEMA_DIR")
    if env:
        return Path(env)
    return _repo_root() / "schemas"


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict[str, Any]:
    if name not in SCHEMA_FILES:
        raise KeyError(f"unknown schema: {name}")
    path = schema_dir() / SCHEMA_FILES[name]
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validator_for(name: str) -> Draft202012Validator:
    return Draft202012Validator(load_schema(name))


def validate(name: str, instance: Any) -> list[str]:
    """Return human-readable error messages; empty list if valid."""
    errors = sorted(validator_for(name).iter_errors(instance), key=lambda e: e.path)
    return [_format_error(err) for err in errors]


def _format_error(error: Any) -> str:
    path = "/".join(str(p) for p in error.absolute_path) or "<root>"
    return f"{path}: {error.message}"
