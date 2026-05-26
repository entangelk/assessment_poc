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


def test_clean_assignment_yields_pre_review_unconfirmed_trace_coverage(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Slice 2 contract: `clean_assignment` keeps its pre-review state
    (every trace_link is `pending_verification`), so the canonical "clean"
    Phase 0 baseline is `status=provisional_findings`, exit `0`,
    `blocking_count=0`, and one `unconfirmed_trace_coverage` (medium /
    provisional) finding per scored rubric (R1 + R2). Rule 0 diagnostics
    must stay empty. Per HANDOFF Active Decisions: PoC's automation flow
    cannot synthesize `human_accepted` on its own, so this medium baseline
    *is* the canonical post-Rule-0 state.
    """
    code, findings, diagnostics = _run_check(
        fixture_dir / "clean_assignment", tmp_path, use_manifest=True
    )
    capsys.readouterr()
    assert code == 0, f"diagnostics: {diagnostics}"
    assert findings["status"] == "provisional_findings"
    assert findings["blocking_count"] == 0
    assert diagnostics["summary"]["high"] == 0
    assert diagnostics["diagnostics"] == []

    unconfirmed = [
        f for f in findings["findings"] if f["type"] == "unconfirmed_trace_coverage"
    ]
    rubric_ids = sorted(f["rubric_id"] for f in unconfirmed)
    assert rubric_ids == ["R1", "R2"], (
        "clean_assignment has two scored rubrics (R1 and R2) traced with "
        "pending_verification, both must surface medium findings."
    )
    for f in unconfirmed:
        assert f["severity"] == "medium"
        assert f["decision_status"] == "provisional"

    # Over-strict: no possible_orphan or bonus findings should surface here.
    other_types = {f["type"] for f in findings["findings"]} - {"unconfirmed_trace_coverage"}
    assert other_types == set(), f"unexpected finding types: {other_types}"


def test_orphan_scored_rubric_fixture_emits_possible_orphan(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Under-strict guard: the orphan_scored_rubric fixture must yield
    BOTH Rule 1 branches:

    - R2 (scored, untraced) → `possible_orphan_scored_rubric_item` (high)
    - R1 (scored, traced with pending_verification) →
      `unconfirmed_trace_coverage` (medium)

    `status=provisional_findings`, exit code 0, blocking_count 0. Rule 0
    diagnostics stay clean because the fixture is grounded (Slice 1.5).
    """
    code, findings, diagnostics = _run_check(
        fixture_dir / "orphan_scored_rubric", tmp_path, use_manifest=True
    )
    capsys.readouterr()
    assert code == 0, f"diagnostics: {diagnostics}, findings: {findings}"
    assert findings["status"] == "provisional_findings"
    assert findings["blocking_count"] == 0
    assert diagnostics["summary"]["high"] == 0

    orphan = [
        f
        for f in findings["findings"]
        if f["type"] == "possible_orphan_scored_rubric_item"
    ]
    assert len(orphan) == 1
    assert orphan[0]["rubric_id"] == "R2"
    assert orphan[0]["severity"] == "high"
    assert orphan[0]["decision_status"] == "provisional"

    unconfirmed = [
        f
        for f in findings["findings"]
        if f["type"] == "unconfirmed_trace_coverage"
    ]
    assert len(unconfirmed) == 1
    assert unconfirmed[0]["rubric_id"] == "R1"
    assert unconfirmed[0]["severity"] == "medium"
    assert unconfirmed[0]["decision_status"] == "provisional"


def test_reference_integrity_fixture_blocks_with_exit_two(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, findings, diagnostics = _run_check(
        fixture_dir / "reference_integrity", tmp_path, use_manifest=True
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
