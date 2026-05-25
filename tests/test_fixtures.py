"""End-to-end fixture regressions.

These tests exercise the file-on-disk path: parse YAML, validate schemas,
ground source_ref with the snapshot manifest, run Rule 0, and emit the
findings/diagnostics JSON contract. They are deliberately fast (file I/O only)
so the regression catches drift between schema, loader, rule engine, and CLI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from assessment_harness.cli import main


def _run_check(
    fixture_subdir: Path,
    tmp_path: Path,
    *,
    use_manifest: bool,
) -> tuple[int, dict, dict]:
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    argv = [
        "--output",
        "json",
        "check",
        "--spec-items",
        str(fixture_subdir / "spec_items.yaml"),
        "--rubric-items",
        str(fixture_subdir / "rubric_items.yaml"),
        "--trace-links",
        str(fixture_subdir / "trace_links.yaml"),
        "--policy",
        str(fixture_subdir / "policy.yaml"),
        "--out",
        str(out),
        "--diagnostics-out",
        str(diag),
    ]
    if use_manifest:
        argv += ["--source-manifest", str(fixture_subdir / "source_manifest.yaml")]
    code = main(argv)
    findings_doc = json.loads(out.read_text(encoding="utf-8"))
    diag_doc = json.loads(diag.read_text(encoding="utf-8"))
    return code, findings_doc, diag_doc


def test_clean_assignment_passes_check_with_manifest(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, findings, diagnostics = _run_check(
        fixture_dir / "clean_assignment", tmp_path, use_manifest=True
    )
    capsys.readouterr()
    assert code == 0, f"diagnostics: {diagnostics}"
    assert findings["status"] == "success"
    assert findings["findings"] == []
    assert diagnostics["summary"]["high"] == 0
    assert diagnostics["diagnostics"] == []


def test_clean_assignment_passes_check_without_manifest(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, findings, diagnostics = _run_check(
        fixture_dir / "clean_assignment", tmp_path, use_manifest=False
    )
    capsys.readouterr()
    assert code == 0, f"diagnostics: {diagnostics}"
    assert findings["status"] == "success"
    assert diagnostics["summary"]["high"] == 0


def test_reference_integrity_fixture_blocks_with_exit_two(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, findings, diagnostics = _run_check(
        fixture_dir / "reference_integrity", tmp_path, use_manifest=False
    )
    capsys.readouterr()
    assert code == 2
    assert findings["status"] == "invalid_input"
    assert findings["findings"] == []
    codes = {d["code"] for d in diagnostics["diagnostics"]}
    expected = {
        "duplicate_spec_id",
        "duplicate_rubric_id",
        "dangling_rubric_reference",
        "dangling_spec_reference",
        "evidence_quote_spec_id_mismatch",
        "evidence_quote_empty",
        "evidence_quote_token_sequence_mismatch",
        "evidence_quote_missing_for_spec_id",
    }
    missing = expected - codes
    assert not missing, f"missing diagnostic codes: {missing}"
    assert diagnostics["summary"]["high"] >= len(expected)
