"""Shared pytest fixtures and path bootstrap.

The project uses an `src/` layout. ``pythonpath = ["src"]`` in pyproject.toml
takes care of the import path, but we also point the schema loader at the
repo's `schemas/` directory in case tests are invoked from anywhere other
than the repo root.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _schema_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASSESSMENT_HARNESS_SCHEMA_DIR", str(REPO_ROOT / "schemas"))
    # Force re-import of cached loader paths.
    from assessment_harness import schemas as _schemas

    _schemas.load_schema.cache_clear()


@pytest.fixture
def fixture_dir() -> Path:
    return REPO_ROOT / "fixtures"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT
