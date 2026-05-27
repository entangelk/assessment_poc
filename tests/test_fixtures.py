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
from assessment_harness.schemas import validate


def _run_check(
    fixture_subdir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    use_manifest: bool,
) -> tuple[int, dict, dict, dict]:
    """Run `check` end-to-end and return ``(exit_code, envelope, findings_doc,
    diagnostics_doc)``. The CLI envelope is captured from stdout so tests can
    assert on the public agent-consumable contract (informational counts,
    next_actions) — not just on the on-disk findings/diagnostics files.
    """
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
    captured = capsys.readouterr()
    envelope = json.loads(captured.out)
    findings_doc = json.loads(out.read_text(encoding="utf-8"))
    diag_doc = json.loads(diag.read_text(encoding="utf-8"))
    return code, envelope, findings_doc, diag_doc


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
    code, envelope, findings, diagnostics = _run_check(
        fixture_dir / "clean_assignment", tmp_path, capsys, use_manifest=True
    )
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

    # CLI envelope contract: clean_assignment baseline keeps medium count
    # only — protects the public envelope field from silent removal.
    assert envelope["provisional_high_count"] == 0
    assert envelope["provisional_medium_count"] == 2
    assert envelope["provisional_informational_count"] == 0
    assert envelope["review_queue_count"] == 0
    assert Path(envelope["review_queue_path"]).exists()


def test_orphan_scored_rubric_fixture_emits_all_three_rule_one_branches(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Under-strict guard: the orphan_scored_rubric fixture must yield ALL
    THREE Rule 1 branches (slices 1+2+3):

    - R2 (scored, untraced) → `possible_orphan_scored_rubric_item` (high)
    - R1 (scored, traced with pending_verification) →
      `unconfirmed_trace_coverage` (medium)
    - R3 (bonus, untraced) → `orphan_bonus_rubric_item` (informational)

    `status=provisional_findings`, exit code 0, blocking_count 0. Rule 0
    diagnostics stay clean because the fixture is grounded (Slice 1.5).
    """
    code, envelope, findings, diagnostics = _run_check(
        fixture_dir / "orphan_scored_rubric", tmp_path, capsys, use_manifest=True
    )
    assert code == 0, f"diagnostics: {diagnostics}, findings: {findings}"
    assert findings["status"] == "provisional_findings"
    assert findings["blocking_count"] == 0
    assert diagnostics["summary"]["high"] == 0

    by_rubric = {
        f["rubric_id"]: (f["type"], f["severity"], f["decision_status"])
        for f in findings["findings"]
    }
    assert by_rubric == {
        "R1": ("unconfirmed_trace_coverage", "medium", "provisional"),
        "R2": ("possible_orphan_scored_rubric_item", "high", "provisional"),
        "R3": ("orphan_bonus_rubric_item", "informational", "provisional"),
    }

    # CLI envelope contract for the all-three-branches case: the public
    # informational fields and the per-branch next_actions are part of the
    # slice 3 contract. Lock them so a future change cannot quietly remove
    # `provisional_informational_count` or the `review_orphan_bonus_rubric`
    # action while finding emission still succeeds.
    assert envelope["status"] == "provisional_findings"
    assert envelope["provisional_high_count"] == 1
    assert envelope["provisional_medium_count"] == 1
    assert envelope["provisional_informational_count"] == 1
    actions_by_rubric = {
        (a["type"], a["rubric_id"]) for a in envelope["next_actions"]
    }
    assert actions_by_rubric == {
        ("review_unconfirmed_trace_coverage", "R1"),
        ("review_orphan_rubric", "R2"),
        ("review_orphan_bonus_rubric", "R3"),
    }


def test_reference_integrity_fixture_blocks_with_exit_two(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, envelope, findings, diagnostics = _run_check(
        fixture_dir / "reference_integrity", tmp_path, capsys, use_manifest=True
    )
    assert code == 2
    assert envelope["status"] == "invalid_input"
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


def test_bonus_misuse_fixture_emits_l1_l5_l6_rule_two_and_orphan_boundaries(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Lint boundary guard: RB1 traces must S1 and co-fires L1 plus L5;
    RB2 traces optional S2 and fires neither; RB3 remains a Rule 1 orphan;
    RB4 traces must S3 without scored coverage and co-fires Rule 2, L5, and L6.
    """
    root = fixture_dir / "bonus_misuse"
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    queue_path = tmp_path / "review_queue.json"
    code = main(
        [
            "--output",
            "json",
            "check",
            "--spec-items",
            str(root / "spec_items.yaml"),
            "--rubric-items",
            str(root / "rubric_items.yaml"),
            "--trace-links",
            str(root / "trace_links.yaml"),
            "--source-manifest",
            str(root / "source_manifest.yaml"),
            "--policy",
            str(root / "policy.yaml"),
            "--out",
            str(out),
            "--diagnostics-out",
            str(diag),
        ]
    )
    envelope = json.loads(capsys.readouterr().out)
    findings = json.loads(out.read_text(encoding="utf-8"))
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    assert code == 0
    assert envelope["review_queue_path"] == str(queue_path)
    assert envelope["review_queue_count"] == 2
    assert envelope["provisional_high_count"] == 1
    assert envelope["provisional_medium_count"] == 5
    assert envelope["provisional_informational_count"] == 1
    assert {
        (a["type"], a.get("spec_id"), a.get("rubric_id"))
        for a in envelope["next_actions"]
    } >= {
        ("review_double_scoring", "S1", None),
        ("review_bonus_mandatory_only", None, "RB1"),
        ("review_orphan_bonus_rubric", None, "RB3"),
        ("review_mandatory_spec_bonus_only", "S3", None),
        ("review_uncovered_must_spec", "S3", None),
    }
    assert validate("review_queue", queue) == []
    assert validate("findings", findings) == []

    l1 = [f for f in findings["findings"] if f["type"] == "double_scored_spec"]
    assert len(l1) == 1
    assert l1[0]["spec_id"] == "S1"
    assert l1[0]["scored_rubric_id"] == "R1"
    assert l1[0]["bonus_rubric_id"] == "RB1"
    l5 = [f for f in findings["findings"] if f["type"] == "bonus_grades_mandatory_only"]
    assert [(f["rubric_id"], f["severity"]) for f in l5] == [
        ("RB1", "medium"),
        ("RB4", "medium"),
    ]
    l6 = [f for f in findings["findings"] if f["type"] == "mandatory_spec_bonus_only_traced"]
    assert [(f["spec_id"], f["bonus_rubric_ids"], f["severity"]) for f in l6] == [
        ("S3", ["RB4"], "high")
    ]
    rule_two = [f for f in findings["findings"] if f["type"] == "uncovered_must_spec_item"]
    assert [(f["spec_id"], f["severity"]) for f in rule_two] == [("S3", "medium")]
    orphan_bonus = [f for f in findings["findings"] if f["type"] == "orphan_bonus_rubric_item"]
    assert [(f["rubric_id"], f["severity"]) for f in orphan_bonus] == [
        ("RB3", "informational")
    ]
    assert queue["review_queue"][0]["type"] == "double_scoring_review"
    assert queue["review_queue"][0]["target"] == {
        "spec_id": "S1",
        "scored_rubric_id": "R1",
        "bonus_rubric_id": "RB1",
    }
    assert queue["review_queue"][1]["type"] == "mandatory_spec_bonus_review"
    assert queue["review_queue"][1]["target"] == {
        "spec_id": "S3",
        "bonus_rubric_ids": ["RB4"],
    }


def test_uncovered_must_spec_fixture_locks_rule_two_structural_boundary(
    fixture_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Rule 2 fixture: an untraced must, a bonus-only must, and a
    qualitative-only must are uncovered, while pending scored coverage and
    non-mandatory specs are not. Bonus-only coverage also preserves L5/L6.
    """
    code, envelope, findings, diagnostics = _run_check(
        fixture_dir / "uncovered_must_spec", tmp_path, capsys, use_manifest=True
    )
    assert code == 0, f"diagnostics: {diagnostics}, findings: {findings}"
    assert diagnostics["diagnostics"] == []
    rule_two = [
        f for f in findings["findings"] if f["type"] == "uncovered_must_spec_item"
    ]
    assert [(f["spec_id"], f["severity"]) for f in rule_two] == [
        ("S_UNTRACED", "medium"),
        ("S_BONUS_ONLY", "medium"),
        ("S_QUAL_ONLY", "medium"),
    ]
    assert "S_COVERED" not in {f["spec_id"] for f in rule_two}
    assert "S_OPTIONAL" not in {f["spec_id"] for f in rule_two}
    assert "S_INFO" not in {f["spec_id"] for f in rule_two}

    assert envelope["provisional_high_count"] == 1
    assert envelope["provisional_medium_count"] == 5
    assert envelope["provisional_informational_count"] == 0
    assert {
        (action["type"], action.get("spec_id"))
        for action in envelope["next_actions"]
    } >= {
        ("review_uncovered_must_spec", "S_UNTRACED"),
        ("review_uncovered_must_spec", "S_BONUS_ONLY"),
        ("review_uncovered_must_spec", "S_QUAL_ONLY"),
        ("review_mandatory_spec_bonus_only", "S_BONUS_ONLY"),
    }
