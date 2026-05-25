"""Lightweight loaders and data containers for Phase 0.

Phase 0 keeps the input model thin: validated dicts plus a small
:class:`SourceSnapshot` helper for resolving manifest documents to their on-disk
text. Compacting structures (`support`, `identity_basis`, `variants`) are not
required for `check` and are pass-through. Later phases will introduce richer
dataclasses where the additional structure pays for itself.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .schemas import validate


class HarnessInputError(Exception):
    """Raised when input cannot be parsed or violates a schema."""

    def __init__(self, message: str, *, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors: list[str] = errors or []


def read_yaml(path: Path) -> Any:
    if not path.exists():
        raise HarnessInputError(f"file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        try:
            return yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise HarnessInputError(f"invalid YAML in {path}: {exc}") from exc


def load_validated(path: Path, schema_name: str) -> dict[str, Any]:
    data = read_yaml(path)
    if not isinstance(data, dict):
        raise HarnessInputError(
            f"{path}: top-level value must be a mapping (got {type(data).__name__})"
        )
    errors = validate(schema_name, data)
    if errors:
        raise HarnessInputError(
            f"{path}: schema validation failed ({schema_name})",
            errors=errors,
        )
    return data


@dataclass
class Document:
    document_id: str
    role: str
    path: Path
    expected_sha256: str
    actual_sha256: str
    lines: list[str] = field(default_factory=list)

    @property
    def hash_matches(self) -> bool:
        return self.expected_sha256.lower() == self.actual_sha256.lower()

    def has_span(self, start_line: int, end_line: int) -> bool:
        return 1 <= start_line <= end_line <= len(self.lines)

    def span_text(self, start_line: int, end_line: int) -> str:
        if not self.has_span(start_line, end_line):
            raise IndexError(
                f"span {start_line}-{end_line} out of range for {self.document_id} (1..{len(self.lines)})"
            )
        return "\n".join(self.lines[start_line - 1 : end_line])


@dataclass
class SourceSnapshot:
    project_id: str
    assessment_version: str
    documents: dict[str, Document]

    def get(self, document_id: str) -> Document | None:
        return self.documents.get(document_id)


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_source_snapshot(manifest_path: Path) -> SourceSnapshot:
    data = load_validated(manifest_path, "source_manifest")
    manifest_dir = manifest_path.parent

    documents: dict[str, Document] = {}
    for entry in data["documents"]:
        doc_path = Path(entry["path"])
        if not doc_path.is_absolute():
            doc_path = (manifest_dir / doc_path).resolve()
        actual_hash = ""
        lines: list[str] = []
        if doc_path.exists():
            actual_hash = _sha256_file(doc_path)
            text = doc_path.read_text(encoding="utf-8")
            lines = text.splitlines()
        documents[entry["document_id"]] = Document(
            document_id=entry["document_id"],
            role=entry["role"],
            path=doc_path,
            expected_sha256=entry["sha256"],
            actual_sha256=actual_hash,
            lines=lines,
        )

    return SourceSnapshot(
        project_id=data["project_id"],
        assessment_version=data["assessment_version"],
        documents=documents,
    )


def load_policy(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return load_validated(path, "policy")
