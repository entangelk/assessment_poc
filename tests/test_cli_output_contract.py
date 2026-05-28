"""CLI envelope contract regression.

Every command must:
- write the stable-core fields (status, exit_code, command, next_actions)
- validate against ``cli_output.schema.json``
- separate JSON output (stdout) from progress/error text (stderr)
- match the documented exit-code semantics
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from assessment_harness.cli import STABLE_CORE_FIELDS, main
from assessment_harness.schemas import validate


def _run_main(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, dict, str]:
    exit_code = main(argv)
    captured = capsys.readouterr()
    return exit_code, json.loads(captured.out), captured.err


def _assert_envelope(envelope: dict) -> None:
    assert validate("cli_output", envelope) == []
    for field in STABLE_CORE_FIELDS:
        assert field in envelope, f"stable-core field {field!r} missing"
    assert isinstance(envelope["next_actions"], list)


def test_check_clean_fixture_returns_success(
    fixture_dir: Path,
    repo_root: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    argv = [
        "--output",
        "json",
        "check",
        "--spec-items",
        str(fixture_dir / "clean_assignment/spec_items.yaml"),
        "--rubric-items",
        str(fixture_dir / "clean_assignment/rubric_items.yaml"),
        "--trace-links",
        str(fixture_dir / "clean_assignment/trace_links.yaml"),
        "--source-manifest",
        str(fixture_dir / "clean_assignment/source_manifest.yaml"),
        "--policy",
        str(fixture_dir / "clean_assignment/policy.yaml"),
        "--out",
        str(out),
        "--diagnostics-out",
        str(diag),
    ]
    code, envelope, _ = _run_main(argv, capsys)
    _assert_envelope(envelope)
    assert code == 0
    # Slice 2: clean_assignment is pre-review (every link pending_verification),
    # so the canonical baseline now surfaces medium provisional findings.
    assert envelope["status"] == "provisional_findings"
    assert envelope["exit_code"] == 0
    assert envelope["command"] == "check"
    assert envelope["review_queue_count"] == 0
    # next_actions carries one review_unconfirmed_trace_coverage per scored
    # rubric (R1, R2). R3 is bonus, R4 is qualitative, neither in scope yet.
    assert all(
        a["type"] == "review_unconfirmed_trace_coverage" for a in envelope["next_actions"]
    )
    assert len(envelope["next_actions"]) == 2

    findings_doc = json.loads(out.read_text(encoding="utf-8"))
    assert findings_doc["status"] == "provisional_findings"
    assert findings_doc["blocking_count"] == 0
    types = {f["type"] for f in findings_doc["findings"]}
    assert types == {"unconfirmed_trace_coverage"}
    diag_doc = json.loads(diag.read_text(encoding="utf-8"))
    assert diag_doc["summary"]["high"] == 0


def test_check_reference_integrity_returns_invalid_input(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    argv = [
        "--output",
        "json",
        "check",
        "--spec-items",
        str(fixture_dir / "reference_integrity/spec_items.yaml"),
        "--rubric-items",
        str(fixture_dir / "reference_integrity/rubric_items.yaml"),
        "--trace-links",
        str(fixture_dir / "reference_integrity/trace_links.yaml"),
        "--source-manifest",
        str(fixture_dir / "reference_integrity/source_manifest.yaml"),
        "--policy",
        str(fixture_dir / "reference_integrity/policy.yaml"),
        "--out",
        str(out),
        "--diagnostics-out",
        str(diag),
    ]
    code, envelope, _ = _run_main(argv, capsys)
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert envelope["exit_code"] == 2

    findings_doc = json.loads(out.read_text(encoding="utf-8"))
    # Per Rule 0: findings.json is always produced; on invalid input it is empty.
    assert findings_doc["status"] == "invalid_input"
    assert findings_doc["findings"] == []

    diag_doc = json.loads(diag.read_text(encoding="utf-8"))
    codes = {d["code"] for d in diag_doc["diagnostics"]}
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
    assert not missing, f"missing expected diagnostics: {missing}"
    assert diag_doc["summary"]["high"] >= len(expected)


def test_check_missing_input_returns_invalid_input(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    argv = [
        "--output",
        "json",
        "check",
        "--spec-items",
        str(tmp_path / "nope.yaml"),
        "--rubric-items",
        str(tmp_path / "nope.yaml"),
        "--trace-links",
        str(tmp_path / "nope.yaml"),
        # --source-manifest is mandatory; provide a path that exists past the
        # manifest-required check so this test still exercises the YAML
        # not-found path rather than short-circuiting on missing manifest.
        "--source-manifest",
        str(tmp_path / "manifest-also-missing.yaml"),
        "--out",
        str(out),
        "--diagnostics-out",
        str(diag),
    ]
    code, envelope, _ = _run_main(argv, capsys)
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert any(action.get("type") == "fix_input" for action in envelope["next_actions"])


def test_check_without_source_manifest_returns_invalid_input(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Under-strict guard for plan v1.8 §5.0: omitting `--source-manifest`
    must exit `2` with `status=invalid_input`, surface a
    `source_manifest_required` diagnostic, and write a `provide_source_manifest`
    next_action so caller agents can recover automatically.
    """
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    argv = [
        "--output",
        "json",
        "check",
        "--spec-items",
        str(tmp_path / "nope.yaml"),
        "--rubric-items",
        str(tmp_path / "nope.yaml"),
        "--trace-links",
        str(tmp_path / "nope.yaml"),
        "--out",
        str(out),
        "--diagnostics-out",
        str(diag),
    ]
    code, envelope, _ = _run_main(argv, capsys)
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert any(
        action.get("type") == "provide_source_manifest"
        for action in envelope["next_actions"]
    )

    diag_doc = json.loads(diag.read_text(encoding="utf-8"))
    codes = {d["code"] for d in diag_doc["diagnostics"]}
    assert "source_manifest_required" in codes


def test_check_with_source_manifest_does_not_surface_manifest_required(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Over-strict guard for plan v1.8 §5.0: a clean fixture WITH manifest
    must not synthesize the manifest-required diagnostic. If a regression
    started emitting `source_manifest_required` unconditionally, this guard
    catches it.
    """
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    argv = [
        "--output",
        "json",
        "check",
        "--spec-items",
        str(fixture_dir / "clean_assignment/spec_items.yaml"),
        "--rubric-items",
        str(fixture_dir / "clean_assignment/rubric_items.yaml"),
        "--trace-links",
        str(fixture_dir / "clean_assignment/trace_links.yaml"),
        "--source-manifest",
        str(fixture_dir / "clean_assignment/source_manifest.yaml"),
        "--policy",
        str(fixture_dir / "clean_assignment/policy.yaml"),
        "--out",
        str(out),
        "--diagnostics-out",
        str(diag),
    ]
    code, envelope, _ = _run_main(argv, capsys)
    _assert_envelope(envelope)
    assert code == 0
    diag_doc = json.loads(diag.read_text(encoding="utf-8"))
    codes = {d["code"] for d in diag_doc["diagnostics"]}
    assert "source_manifest_required" not in codes
    assert not any(
        action.get("type") == "provide_source_manifest"
        for action in envelope["next_actions"]
    )


def test_schema_command_returns_check_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, envelope, _ = _run_main(
        ["--output", "json", "schema", "--command", "check"], capsys
    )
    _assert_envelope(envelope)
    assert code == 0
    assert envelope["command"] == "schema"
    contract = envelope["contract"]
    assert contract["command"] == "check"
    assert contract["stable_core"] == STABLE_CORE_FIELDS
    assert "0" in contract["exit_codes"]
    assert "2" in contract["exit_codes"]

    # Lock the public next_actions_types surface so removals are caught.
    # Each entry below corresponds to a code path a caller agent depends on:
    #   fix_reference_integrity      -- Rule 0 high-diagnostic recovery
    #   fix_input                    -- generic input load failure
    #   provide_source_manifest      -- slice 1.5 mandatory manifest
    #   review_orphan_rubric         -- slice 1 high possible_orphan
    #   review_unconfirmed_trace_coverage -- slice 2 medium provisional
    #   review_orphan_bonus_rubric   -- slice 3 informational bonus orphan
    expected_actions = {
        "fix_reference_integrity",
        "fix_input",
        "provide_source_manifest",
        "review_orphan_rubric",
        "review_unconfirmed_trace_coverage",
        "review_orphan_bonus_rubric",
        "review_double_scoring",
        "review_bonus_mandatory_only",
        "review_mandatory_spec_bonus_only",
        "review_uncovered_must_spec",
        "review_optionality_mismatch",
    }
    assert set(contract["next_actions_types"]) == expected_actions

    # Lock the public informational fields. Each entry is a documented
    # envelope field a caller agent may consume.
    expected_informational = {
        "findings_path",
        "diagnostics_path",
        "blocking_count",
        "high_integrity_count",
        "provisional_high_count",
        "provisional_medium_count",
        "provisional_informational_count",
        "review_queue_path",
        "review_queue_count",
        "input_error",
    }
    assert set(contract["informational"]) == expected_informational


def test_schema_command_returns_gate_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, envelope, _ = _run_main(
        ["--output", "json", "schema", "--command", "gate"], capsys
    )
    _assert_envelope(envelope)
    assert code == 0
    contract = envelope["contract"]
    assert contract["command"] == "gate"
    assert contract["stable_core"] == STABLE_CORE_FIELDS
    assert contract["exit_codes"]["1"] == (
        "confirmed blocking finding exists after final review."
    )
    assert set(contract["next_actions_types"]) == {
        "complete_final_review",
        "fix_final_review",
        "revise_assessment",
    }
    assert "blocking_findings" in contract["informational"]


def test_schema_command_rejects_unknown_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, envelope, _ = _run_main(
        ["--output", "json", "schema", "--command", "totally-not-a-command"], capsys
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"


def _write_findings(path: Path, findings: list[dict]) -> None:
    path.write_text(
        json.dumps(
            {
                "status": "provisional_findings" if findings else "success",
                "findings": findings,
                "blocking_count": 0,
                "generated_at": "2026-05-28T00:00:00Z",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _finding(
    finding_type: str,
    *,
    severity: str = "medium",
    rubric_id: str | None = None,
    spec_id: str | None = None,
    scored_rubric_id: str | None = None,
    bonus_rubric_id: str | None = None,
) -> dict:
    finding = {
        "type": finding_type,
        "severity": severity,
        "decision_status": "provisional",
        "message": f"test finding {finding_type}",
    }
    if rubric_id is not None:
        finding["rubric_id"] = rubric_id
    if spec_id is not None:
        finding["spec_id"] = spec_id
    if scored_rubric_id is not None:
        finding["scored_rubric_id"] = scored_rubric_id
    if bonus_rubric_id is not None:
        finding["bonus_rubric_id"] = bonus_rubric_id
    return finding


def _write_final_review(
    path: Path, findings_path: Path, decisions: list[dict]
) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "review_id": "review_test",
                "reviewer": "tester",
                "reviewed_at": "2026-05-28T00:00:00Z",
                "inputs": {"findings_path": str(findings_path)},
                "decisions": decisions,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _decision(
    target_key: dict,
    *,
    action: str = "accept",
) -> dict:
    return {
        "target_type": "finding",
        "target_key": target_key,
        "action": action,
    }


def _run_gate_with(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    *,
    findings: list[dict],
    decisions: list[dict],
) -> tuple[int, dict]:
    findings_path = tmp_path / "findings.json"
    review_path = tmp_path / "final_review.yaml"
    _write_findings(findings_path, findings)
    _write_final_review(review_path, findings_path, decisions)
    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    return code, envelope


def test_gate_missing_finding_decision_returns_pending_review(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings_path = tmp_path / "findings.json"
    review_path = tmp_path / "final_review.yaml"
    _write_findings(
        findings_path,
        [
            {
                "type": "optionality_mismatch",
                "severity": "high",
                "decision_status": "provisional",
                "rubric_id": "R_HIGH",
                "message": "review optional-only scoring",
            }
        ],
    )
    _write_final_review(review_path, findings_path, decisions=[])

    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    assert code == 0
    assert envelope["status"] == "pending_review"
    assert envelope["pending_decision_count"] == 1
    assert envelope["blocking_count"] == 0
    assert envelope["next_actions"] == [
        {"type": "complete_final_review", "pending_decision_count": 1}
    ]


def test_gate_accept_promotes_rule_one_to_confirmed_blocking_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Under-strict guard: the final-review key for a finding carries only
    generated identifiers (`type`, `rubric_id`). It must not need message,
    evidence, title, text, or other payload copies to promote Rule 1 to a
    confirmed blocking orphan.
    """
    findings_path = tmp_path / "findings.json"
    review_path = tmp_path / "final_review.yaml"
    _write_findings(
        findings_path,
        [
            {
                "type": "unconfirmed_trace_coverage",
                "severity": "medium",
                "decision_status": "provisional",
                "rubric_id": "R1",
                "message": "coverage not final",
                "evidence": {"semantic_statuses": ["human_rejected"]},
            }
        ],
    )
    _write_final_review(
        review_path,
        findings_path,
        decisions=[
            {
                "target_type": "finding",
                "target_key": {"type": "unconfirmed_trace_coverage", "rubric_id": "R1"},
                "action": "accept",
                "note": "Confirmed no final coverage.",
            }
        ],
    )

    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    assert code == 1
    assert envelope["status"] == "fail"
    assert envelope["blocking_count"] == 1
    assert envelope["blocking_findings"][0]["type"] == "orphan_scored_rubric_item"
    assert envelope["blocking_findings"][0]["severity"] == "high"
    assert envelope["blocking_findings"][0]["decision_status"] == "confirmed"


def test_gate_override_dismisses_blocking_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Over-strict guard: a reviewed override must close the finding without
    producing a blocking verdict.
    """
    findings_path = tmp_path / "findings.json"
    review_path = tmp_path / "final_review.yaml"
    _write_findings(
        findings_path,
        [
            {
                "type": "optionality_mismatch",
                "severity": "high",
                "decision_status": "provisional",
                "rubric_id": "R_HIGH",
                "message": "optional-only scoring",
            }
        ],
    )
    _write_final_review(
        review_path,
        findings_path,
        decisions=[
            {
                "target_type": "finding",
                "target_key": {"type": "optionality_mismatch", "rubric_id": "R_HIGH"},
                "action": "override",
                "note": "Rubric was intentionally optional in this round.",
            }
        ],
    )

    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    assert code == 0
    assert envelope["status"] == "success"
    assert envelope["blocking_count"] == 0
    assert envelope["confirmed_finding_count"] == 0
    assert envelope["dismissed_finding_count"] == 1


def test_gate_accepts_nonblocking_confirmed_finding_without_exit_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings_path = tmp_path / "findings.json"
    review_path = tmp_path / "final_review.yaml"
    _write_findings(
        findings_path,
        [
            {
                "type": "uncovered_must_spec_item",
                "severity": "medium",
                "decision_status": "provisional",
                "spec_id": "S_MISSING",
                "message": "must spec lacks scored coverage",
            }
        ],
    )
    _write_final_review(
        review_path,
        findings_path,
        decisions=[
            {
                "target_type": "finding",
                "target_key": {
                    "type": "uncovered_must_spec_item",
                    "spec_id": "S_MISSING",
                },
                "action": "accept",
            }
        ],
    )

    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    assert code == 0
    assert envelope["status"] == "success"
    assert envelope["confirmed_finding_count"] == 1
    assert envelope["blocking_count"] == 0


@pytest.mark.parametrize(
    ("finding", "target_key"),
    [
        (
            _finding(
                "optionality_mismatch",
                severity="high",
                rubric_id="R_OPTIONAL",
            ),
            {"type": "optionality_mismatch", "rubric_id": "R_OPTIONAL"},
        ),
        (
            _finding(
                "mandatory_spec_bonus_only_traced",
                severity="high",
                spec_id="S_BONUS_ONLY",
            ),
            {
                "type": "mandatory_spec_bonus_only_traced",
                "spec_id": "S_BONUS_ONLY",
            },
        ),
    ],
)
def test_gate_accepts_direct_blocking_findings_with_exit_one(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    finding: dict,
    target_key: dict,
) -> None:
    """Under-strict guard for the direct-confirm blocking set: Rule 3 and
    Rule L6 accepted findings must fail even though no Rule 1 promotion occurs.
    """
    code, envelope = _run_gate_with(
        tmp_path,
        capsys,
        findings=[finding],
        decisions=[_decision(target_key)],
    )
    assert code == 1
    assert envelope["status"] == "fail"
    assert envelope["blocking_count"] == 1
    assert envelope["blocking_findings"][0]["type"] == finding["type"]


@pytest.mark.parametrize(
    ("finding", "target_key"),
    [
        (
            _finding(
                "double_scored_spec",
                spec_id="S1",
                scored_rubric_id="R1",
                bonus_rubric_id="RB1",
            ),
            {
                "type": "double_scored_spec",
                "spec_id": "S1",
                "scored_rubric_id": "R1",
                "bonus_rubric_id": "RB1",
            },
        ),
        (
            _finding("bonus_grades_mandatory_only", rubric_id="RB1"),
            {"type": "bonus_grades_mandatory_only", "rubric_id": "RB1"},
        ),
    ],
)
def test_gate_accepts_l1_l5_as_confirmed_nonblocking_findings(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    finding: dict,
    target_key: dict,
) -> None:
    """Over-strict guard: L1/L5 may be confirmed by review, but v0 gate must
    not treat them as external blocking verdicts.
    """
    code, envelope = _run_gate_with(
        tmp_path,
        capsys,
        findings=[finding],
        decisions=[_decision(target_key)],
    )
    assert code == 0
    assert envelope["status"] == "success"
    assert envelope["confirmed_finding_count"] == 1
    assert envelope["blocking_count"] == 0


@pytest.mark.parametrize("action", ["hold", "rerun_requested"])
def test_gate_hold_and_rerun_requested_keep_pending_review(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], action: str
) -> None:
    code, envelope = _run_gate_with(
        tmp_path,
        capsys,
        findings=[_finding("optionality_mismatch", severity="high", rubric_id="R1")],
        decisions=[
            _decision(
                {"type": "optionality_mismatch", "rubric_id": "R1"},
                action=action,
            )
        ],
    )
    assert code == 0
    assert envelope["status"] == "pending_review"
    assert envelope["pending_decision_count"] == 1
    assert envelope["blocking_count"] == 0


def test_gate_rejects_stale_finding_decision(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings_path = tmp_path / "findings.json"
    review_path = tmp_path / "final_review.yaml"
    _write_findings(findings_path, [])
    _write_final_review(
        review_path,
        findings_path,
        decisions=[
            {
                "target_type": "finding",
                "target_key": {"type": "optionality_mismatch", "rubric_id": "R_OLD"},
                "action": "accept",
            }
        ],
    )

    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert envelope["next_actions"][0]["type"] == "fix_final_review"


def test_gate_rejects_duplicate_finding_decisions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, envelope = _run_gate_with(
        tmp_path,
        capsys,
        findings=[_finding("optionality_mismatch", severity="high", rubric_id="R1")],
        decisions=[
            _decision({"type": "optionality_mismatch", "rubric_id": "R1"}),
            _decision({"type": "optionality_mismatch", "rubric_id": "R1"}),
        ],
    )
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "duplicate decisions" in envelope["input_error"]


def test_gate_rejects_non_minimal_finding_target_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings_path = tmp_path / "findings.json"
    review_path = tmp_path / "final_review.yaml"
    _write_findings(
        findings_path,
        [
            {
                "type": "optionality_mismatch",
                "severity": "high",
                "decision_status": "provisional",
                "rubric_id": "R_HIGH",
                "message": "optional-only scoring",
            }
        ],
    )
    _write_final_review(
        review_path,
        findings_path,
        decisions=[
            {
                "target_type": "finding",
                "target_key": {
                    "type": "optionality_mismatch",
                    "rubric_id": "R_HIGH",
                    "message": "copied payload should not be part of identity",
                },
                "action": "accept",
            }
        ],
    )

    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "not minimal" in envelope["input_error"]


def test_gate_rejects_finding_target_key_missing_required_field(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, envelope = _run_gate_with(
        tmp_path,
        capsys,
        findings=[_finding("optionality_mismatch", severity="high", rubric_id="R1")],
        decisions=[_decision({"type": "optionality_mismatch"})],
    )
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "not minimal" in envelope["input_error"]


def test_gate_rejects_unknown_finding_type_in_target_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, envelope = _run_gate_with(
        tmp_path,
        capsys,
        findings=[_finding("optionality_mismatch", severity="high", rubric_id="R1")],
        decisions=[_decision({"type": "made_up_finding", "rubric_id": "R1"})],
    )
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "not minimal" in envelope["input_error"]


def test_gate_rejects_invalid_final_review_schema(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    review_path = tmp_path / "final_review.yaml"
    review_path.write_text(
        yaml.safe_dump(
            {
                "review_id": "review_test",
                "reviewer": "tester",
                "reviewed_at": "2026-05-28T00:00:00Z",
                "inputs": {},
                "decisions": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"


def test_gate_rejects_missing_referenced_findings_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    review_path = tmp_path / "final_review.yaml"
    _write_final_review(review_path, tmp_path / "missing-findings.json", decisions=[])
    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "cannot read findings" in envelope["input_error"]


def test_gate_rejects_invalid_findings_schema(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings_path = tmp_path / "findings.json"
    review_path = tmp_path / "final_review.yaml"
    findings_path.write_text(
        json.dumps(
            {
                "status": "provisional_findings",
                "findings": [
                    {
                        "type": "optionality_mismatch",
                        "severity": "high",
                        "decision_status": "provisional",
                        "rubric_id": "R1",
                    }
                ],
                "blocking_count": 0,
            }
        ),
        encoding="utf-8",
    )
    _write_final_review(review_path, findings_path, decisions=[])
    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "schema validation failed" in envelope["input_error"]


def test_gate_rejects_duplicate_finding_keys_in_findings_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings_path = tmp_path / "findings.json"
    review_path = tmp_path / "final_review.yaml"
    _write_findings(
        findings_path,
        [
            _finding("optionality_mismatch", severity="high", rubric_id="R1"),
            _finding("optionality_mismatch", severity="high", rubric_id="R1"),
        ],
    )
    _write_final_review(review_path, findings_path, decisions=[])
    code, envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", str(review_path)], capsys
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "duplicate gate target keys" in envelope["input_error"]


def test_report_command_writes_markdown(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # First produce a successful check artifact pair.
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    main(
        [
            "--output",
            "json",
            "check",
            "--spec-items",
            str(fixture_dir / "clean_assignment/spec_items.yaml"),
            "--rubric-items",
            str(fixture_dir / "clean_assignment/rubric_items.yaml"),
            "--trace-links",
            str(fixture_dir / "clean_assignment/trace_links.yaml"),
            "--source-manifest",
            str(fixture_dir / "clean_assignment/source_manifest.yaml"),
            "--policy",
            str(fixture_dir / "clean_assignment/policy.yaml"),
            "--out",
            str(out),
            "--diagnostics-out",
            str(diag),
        ]
    )
    capsys.readouterr()  # drain check output

    report_path = tmp_path / "report.md"
    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "report",
            "--findings",
            str(out),
            "--diagnostics",
            str(diag),
            "--out",
            str(report_path),
        ],
        capsys,
    )
    _assert_envelope(envelope)
    assert code == 0
    assert envelope["command"] == "report"
    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    assert "Assessment Harness Report" in text
    assert "Integrity Diagnostics" in text


def test_schema_documented_form_with_trailing_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The documented invocation form puts ``--output`` after the subcommand
    (`assessment-harness schema --command check --output json`). Regression for
    the HANDOFF-tracked CLI contract drift.
    """
    code, envelope, _ = _run_main(
        ["schema", "--command", "check", "--output", "json"], capsys
    )
    _assert_envelope(envelope)
    assert code == 0
    assert envelope["command"] == "schema"


def _write_minimal_grounded_fixture(
    root: Path,
    *,
    spec_items: list[dict],
    rubric_items: list[dict],
    trace_links: list[dict],
    spec_md_text: str,
    rubric_md_text: str,
) -> dict[str, Path]:
    """Build an in-tmp grounded fixture (source files + sha256 manifest +
    schema-valid YAMLs). Returns paths keyed by argv-style names so the test
    can build the CLI invocation directly. Used by boundary tests that need
    isolated single-purpose inputs.
    """
    source = root / "source"
    source.mkdir()
    spec_md = source / "spec.md"
    rubric_md = source / "rubric.md"
    spec_md.write_text(spec_md_text, encoding="utf-8")
    rubric_md.write_text(rubric_md_text, encoding="utf-8")

    manifest = {
        "project_id": root.name,
        "assessment_version": "v1",
        "documents": [
            {
                "document_id": "DOC_SPEC",
                "role": "candidate_spec",
                "path": "source/spec.md",
                "sha256": hashlib.sha256(spec_md.read_bytes()).hexdigest(),
            },
            {
                "document_id": "DOC_RUBRIC",
                "role": "evaluator_rubric",
                "path": "source/rubric.md",
                "sha256": hashlib.sha256(rubric_md.read_bytes()).hexdigest(),
            },
        ],
    }
    paths = {
        "spec_items": root / "spec_items.yaml",
        "rubric_items": root / "rubric_items.yaml",
        "trace_links": root / "trace_links.yaml",
        "source_manifest": root / "source_manifest.yaml",
    }
    paths["spec_items"].write_text(yaml.safe_dump({"spec_items": spec_items}), encoding="utf-8")
    paths["rubric_items"].write_text(
        yaml.safe_dump({"rubric_items": rubric_items}), encoding="utf-8"
    )
    paths["trace_links"].write_text(
        yaml.safe_dump({"trace_links": trace_links}), encoding="utf-8"
    )
    paths["source_manifest"].write_text(yaml.safe_dump(manifest), encoding="utf-8")
    return paths


def test_check_with_bonus_only_orphan_locks_informational_envelope_boundary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Lock the envelope informational boundary: when the only Rule 1
    trigger is a bonus orphan, the envelope must carry
    `provisional_high_count=0`, `provisional_medium_count=0`,
    `provisional_informational_count=1`, and exactly one
    `review_orphan_bonus_rubric` next_action. This isolates the case where
    the informational count is the only non-zero provisional count, so the
    caller-relevant boundary is explicit rather than incidental to the
    mixed `(1, 1, 1)` fixture.
    """
    root = tmp_path / "bonus_only"
    root.mkdir()
    paths = _write_minimal_grounded_fixture(
        root,
        spec_items=[
            {
                "id": "S1",
                "text": "placeholder spec line.",
                "requirement_level": "informational",
                "source_ref": {
                    "document_id": "DOC_SPEC",
                    "start_line": 1,
                    "end_line": 1,
                },
            }
        ],
        rubric_items=[
            {
                "id": "RB",
                "title": "Bonus axis without trace",
                "evaluation_role": "bonus",
                "source_ref": {
                    "document_id": "DOC_RUBRIC",
                    "start_line": 1,
                    "end_line": 1,
                },
            }
        ],
        trace_links=[],
        spec_md_text="placeholder spec line.\n",
        rubric_md_text="RB Bonus axis without trace\n",
    )

    out = root / "findings.json"
    diag = root / "diag.json"
    argv = [
        "--output",
        "json",
        "check",
        "--spec-items",
        str(paths["spec_items"]),
        "--rubric-items",
        str(paths["rubric_items"]),
        "--trace-links",
        str(paths["trace_links"]),
        "--source-manifest",
        str(paths["source_manifest"]),
        "--out",
        str(out),
        "--diagnostics-out",
        str(diag),
    ]
    code, envelope, _ = _run_main(argv, capsys)
    _assert_envelope(envelope)
    assert code == 0
    assert envelope["status"] == "provisional_findings"
    assert envelope["provisional_high_count"] == 0
    assert envelope["provisional_medium_count"] == 0
    assert envelope["provisional_informational_count"] == 1
    assert [a["type"] for a in envelope["next_actions"]] == [
        "review_orphan_bonus_rubric"
    ]
    assert envelope["next_actions"][0]["rubric_id"] == "RB"

    # Findings file mirrors the envelope.
    findings_doc = json.loads(out.read_text(encoding="utf-8"))
    assert len(findings_doc["findings"]) == 1
    assert findings_doc["findings"][0]["type"] == "orphan_bonus_rubric_item"
    assert findings_doc["findings"][0]["severity"] == "informational"


def test_check_documented_form_with_trailing_output(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`check ... --output json` (subcommand-trailing form) must work too."""
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    argv = [
        "check",
        "--spec-items",
        str(fixture_dir / "clean_assignment/spec_items.yaml"),
        "--rubric-items",
        str(fixture_dir / "clean_assignment/rubric_items.yaml"),
        "--trace-links",
        str(fixture_dir / "clean_assignment/trace_links.yaml"),
        "--source-manifest",
        str(fixture_dir / "clean_assignment/source_manifest.yaml"),
        "--policy",
        str(fixture_dir / "clean_assignment/policy.yaml"),
        "--out",
        str(out),
        "--diagnostics-out",
        str(diag),
        "--output",
        "json",
    ]
    code, envelope, _ = _run_main(argv, capsys)
    _assert_envelope(envelope)
    assert code == 0
    # Slice 2: clean_assignment now baselines on provisional_findings (see
    # test_check_clean_fixture_returns_success for the full rationale).
    assert envelope["status"] == "provisional_findings"


def test_subcommand_output_overrides_root_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Subcommand --output should override a root-level --output."""
    code, envelope, _ = _run_main(
        ["--output", "text", "schema", "--command", "check", "--output", "json"],
        capsys,
    )
    _assert_envelope(envelope)
    assert code == 0


def test_stderr_is_separated_from_stdout_json(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    main(
        [
            "--output",
            "json",
            "check",
            "--spec-items",
            str(tmp_path / "missing.yaml"),
            "--rubric-items",
            str(tmp_path / "missing.yaml"),
            "--trace-links",
            str(tmp_path / "missing.yaml"),
            "--source-manifest",
            str(tmp_path / "manifest-also-missing.yaml"),
            "--out",
            str(out),
            "--diagnostics-out",
            str(diag),
        ]
    )
    captured = capsys.readouterr()
    # stdout must parse as JSON cleanly; stderr carries the diagnostic message.
    json.loads(captured.out)
    assert captured.err  # human-readable error went to stderr
