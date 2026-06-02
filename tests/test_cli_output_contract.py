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
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        yaml.safe_dump(
            {"rules": {"optionality_mismatch": {"weight_threshold": 10}}}
        ),
        encoding="utf-8",
    )
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
        "--policy",
        str(policy),
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


def test_check_without_policy_returns_invalid_input(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Policy is required at check time so Rule 3 cannot be silently disabled.

    The parser still accepts the omission so caller agents receive a structured
    envelope and can retry with `--policy`.
    """
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    code, envelope, _ = _run_main(
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
            "--out",
            str(out),
            "--diagnostics-out",
            str(diag),
        ],
        capsys,
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert envelope["next_actions"][0]["type"] == "provide_policy"
    assert "--policy is required" in envelope["input_error"]

    findings_doc = json.loads(out.read_text(encoding="utf-8"))
    assert findings_doc["status"] == "invalid_input"
    assert "Rule 3" in findings_doc["input_error"]


@pytest.mark.parametrize(
    "policy_doc",
    [
        {},
        {"other": 1},
        {"rules": {}},
        {"rules": {"optionality_mismatch": {"other": 1}}},
    ],
    ids=[
        "empty_doc",
        "rules_missing",
        "rules_empty",
        "threshold_missing",
    ],
)
def test_check_policy_missing_rule_three_threshold_returns_invalid_input(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    policy_doc: dict,
) -> None:
    """Completeness guard: a schema-valid policy without Rule 3's threshold is
    invalid for Phase 0 check, not an instruction to suppress Rule 3. Locked
    across every shape that the policy schema accepts but `_validate_check_policy`
    must still reject — empty doc, missing `rules`, empty `rules`, and
    `optionality_mismatch` present without `weight_threshold` — so a refactor
    cannot let one incomplete shape silently disable Rule 3. Shapes the policy
    schema already rejects (e.g. `optionality_mismatch` typed as a string) are
    not covered here because they never reach this validator.
    """
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(yaml.safe_dump(policy_doc), encoding="utf-8")
    out = tmp_path / "findings.json"
    diag = tmp_path / "integrity_diagnostics.json"
    code, envelope, _ = _run_main(
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
            str(policy_path),
            "--out",
            str(out),
            "--diagnostics-out",
            str(diag),
        ],
        capsys,
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert envelope["next_actions"][0]["type"] == "fix_input"
    assert "rules.optionality_mismatch.weight_threshold" in envelope["input_error"]


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
    #   provide_policy               -- Phase 0 policy completeness recovery
    #   review_orphan_rubric         -- slice 1 high possible_orphan
    #   review_unconfirmed_trace_coverage -- slice 2 medium provisional
    #   review_orphan_bonus_rubric   -- slice 3 informational bonus orphan
    expected_actions = {
        "fix_reference_integrity",
        "fix_input",
        "provide_source_manifest",
        "provide_policy",
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


def test_schema_command_returns_compact_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, envelope, _ = _run_main(
        ["--output", "json", "schema", "--command", "compact"], capsys
    )
    _assert_envelope(envelope)
    assert code == 0
    contract = envelope["contract"]
    assert contract["command"] == "compact"
    assert contract["stable_core"] == STABLE_CORE_FIELDS
    assert contract["next_actions_types"] == ["fix_input"]
    assert set(contract["informational"]) == {
        "compacted_dir",
        "spec_items_path",
        "rubric_items_path",
        "trace_links_path",
        "id_map_path",
        "review_queue_path",
        "review_queue_count",
        "valid_run_count",
        "excluded_run_count",
        "input_error",
    }


def test_schema_command_returns_extract_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, envelope, _ = _run_main(
        ["--output", "json", "schema", "--command", "extract"], capsys
    )
    _assert_envelope(envelope)
    assert code == 0
    contract = envelope["contract"]
    assert contract["command"] == "extract"
    assert contract["stable_core"] == STABLE_CORE_FIELDS
    assert contract["next_actions_types"] == ["fix_input"]
    assert set(contract["informational"]) == {
        "runs_dir",
        "run_dirs",
        "run_count",
        "valid_run_count",
        "invalid_run_count",
        "runner",
        "source_manifest_path",
        "input_error",
    }


def test_schema_command_returns_verify_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, envelope, _ = _run_main(
        ["--output", "json", "schema", "--command", "verify"], capsys
    )
    _assert_envelope(envelope)
    assert code == 0
    contract = envelope["contract"]
    assert contract["command"] == "verify"
    assert contract["stable_core"] == STABLE_CORE_FIELDS
    assert contract["next_actions_types"] == ["fix_input"]
    assert set(contract["informational"]) == {
        "compacted_dir",
        "semantic_verifications_path",
        "semantic_verification_count",
        "review_queue_path",
        "review_queue_count",
        "run_count",
        "runner",
        "source_manifest_path",
        "input_error",
    }


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


def test_schema_command_returns_review_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, envelope, _ = _run_main(
        ["--output", "json", "schema", "--command", "review"], capsys
    )
    _assert_envelope(envelope)
    assert code == 0
    contract = envelope["contract"]
    assert contract["command"] == "review"
    assert contract["stable_core"] == STABLE_CORE_FIELDS
    assert contract["exit_codes"]["0"] == "draft final review record written."
    assert set(contract["informational"]) == {
        "review_path",
        "decision_count",
        "input_error",
    }


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


def _write_findings_with_status(path: Path, findings: list[dict], status: str) -> None:
    path.write_text(
        json.dumps(
            {
                "status": status,
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


def test_review_command_writes_hold_draft_with_minimal_finding_keys(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Review is a draft writer, not an auto-judge: it must copy only minimal
    finding identity keys and keep every provisional finding on `hold`.
    """
    findings_path = tmp_path / "findings.json"
    _write_findings(
        findings_path,
        [
            {
                "type": "optionality_mismatch",
                "severity": "high",
                "decision_status": "provisional",
                "rubric_id": "R_HIGH",
                "message": "optional-only scoring",
                "evidence": {"spec_ids": ["S_OPTIONAL"]},
            },
            {
                "type": "double_scored_spec",
                "severity": "medium",
                "decision_status": "provisional",
                "spec_id": "S1",
                "scored_rubric_id": "R1",
                "bonus_rubric_id": "RB1",
                "message": "double scoring",
                "evidence": {"copied": "must not enter target_key"},
            },
        ],
    )

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "review",
            "--findings",
            str(findings_path),
            "--out-dir",
            str(tmp_path / "final_review"),
            "--reviewer",
            "tester",
        ],
        capsys,
    )
    _assert_envelope(envelope)
    assert code == 0
    assert envelope["status"] == "success"
    assert envelope["decision_count"] == 2

    review_doc = yaml.safe_load(Path(envelope["review_path"]).read_text(encoding="utf-8"))
    assert validate("final_review", review_doc) == []
    assert review_doc["reviewer"] == "tester"
    assert review_doc["inputs"]["findings_path"] == str(findings_path.resolve())
    assert [decision["action"] for decision in review_doc["decisions"]] == [
        "hold",
        "hold",
    ]
    assert review_doc["decisions"][0]["target_key"] == {
        "type": "optionality_mismatch",
        "rubric_id": "R_HIGH",
    }
    assert review_doc["decisions"][1]["target_key"] == {
        "type": "double_scored_spec",
        "spec_id": "S1",
        "scored_rubric_id": "R1",
        "bonus_rubric_id": "RB1",
    }

    gate_code, gate_envelope, _ = _run_main(
        [
            "--output",
            "json",
            "gate",
            "--final-review",
            envelope["review_path"],
        ],
        capsys,
    )
    _assert_envelope(gate_envelope)
    assert gate_code == 0
    assert gate_envelope["status"] == "pending_review"
    assert gate_envelope["pending_decision_count"] == 2


def test_review_command_empty_findings_draft_gates_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings_path = tmp_path / "findings.json"
    _write_findings(findings_path, [])
    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "review",
            "--findings",
            str(findings_path),
            "--out-dir",
            str(tmp_path / "final_review"),
            "--reviewer",
            "tester",
        ],
        capsys,
    )
    _assert_envelope(envelope)
    assert code == 0
    assert envelope["decision_count"] == 0

    gate_code, gate_envelope, _ = _run_main(
        ["--output", "json", "gate", "--final-review", envelope["review_path"]],
        capsys,
    )
    _assert_envelope(gate_envelope)
    assert gate_code == 0
    assert gate_envelope["status"] == "success"


@pytest.mark.parametrize(
    "findings_status",
    [
        "invalid_input",
        "internal_error",
        None,
    ],
)
def test_review_command_rejects_non_draftable_findings_status(
    findings_status: str | None,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Whitelist guard: only success/provisional_findings may become a draft.

    This must fail if review is weakened into rejecting only invalid_input.
    """
    findings_path = tmp_path / "findings.json"
    if findings_status is None:
        findings_path.write_text(
            json.dumps(
                {
                    "findings": [],
                    "blocking_count": 0,
                    "generated_at": "2026-05-28T00:00:00Z",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    else:
        _write_findings_with_status(findings_path, [], findings_status)
    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "review",
            "--findings",
            str(findings_path),
            "--out-dir",
            str(tmp_path / "final_review"),
            "--reviewer",
            "tester",
        ],
        capsys,
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    if findings_status is None:
        assert "schema validation failed" in envelope["input_error"]
    else:
        assert "findings.status" in envelope["input_error"]


def test_review_command_refuses_to_overwrite_existing_draft_without_force(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings_path = tmp_path / "findings.json"
    out_dir = tmp_path / "final_review"
    _write_findings(findings_path, [])
    first_code, first_envelope, _ = _run_main(
        [
            "--output",
            "json",
            "review",
            "--findings",
            str(findings_path),
            "--out-dir",
            str(out_dir),
            "--reviewer",
            "tester",
        ],
        capsys,
    )
    _assert_envelope(first_envelope)
    assert first_code == 0
    review_path = Path(first_envelope["review_path"])
    review_path.write_text("human edited draft\n", encoding="utf-8")

    second_code, second_envelope, _ = _run_main(
        [
            "--output",
            "json",
            "review",
            "--findings",
            str(findings_path),
            "--out-dir",
            str(out_dir),
            "--reviewer",
            "tester",
        ],
        capsys,
    )
    _assert_envelope(second_envelope)
    assert second_code == 2
    assert second_envelope["status"] == "invalid_input"
    assert "already exists" in second_envelope["input_error"]
    assert review_path.read_text(encoding="utf-8") == "human edited draft\n"


def test_review_command_force_overwrites_existing_draft(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings_path = tmp_path / "findings.json"
    out_dir = tmp_path / "final_review"
    _write_findings(findings_path, [])
    review_path = out_dir / "review.yaml"
    out_dir.mkdir()
    review_path.write_text("old draft\n", encoding="utf-8")

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "review",
            "--findings",
            str(findings_path),
            "--out-dir",
            str(out_dir),
            "--reviewer",
            "tester",
            "--force",
        ],
        capsys,
    )
    _assert_envelope(envelope)
    assert code == 0
    assert envelope["status"] == "success"
    assert "old draft" not in review_path.read_text(encoding="utf-8")


def test_review_command_rejects_unknown_finding_type(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    findings_path = tmp_path / "findings.json"
    _write_findings(
        findings_path,
        [
            {
                "type": "made_up_finding",
                "severity": "medium",
                "decision_status": "provisional",
                "message": "unknown",
            }
        ],
    )
    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "review",
            "--findings",
            str(findings_path),
            "--out-dir",
            str(tmp_path / "final_review"),
            "--reviewer",
            "tester",
        ],
        capsys,
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "unknown finding type" in envelope["input_error"]


def test_review_command_rejects_known_finding_missing_key_field(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Boundary guard paired with unknown-type rejection: findings schema
    allows key fields to be absent, but review cannot draft a gate-safe
    target_key without the canonical field.
    """
    findings_path = tmp_path / "findings.json"
    _write_findings(
        findings_path,
        [
            {
                "type": "optionality_mismatch",
                "severity": "high",
                "decision_status": "provisional",
                "message": "known type but missing rubric_id",
            }
        ],
    )
    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "review",
            "--findings",
            str(findings_path),
            "--out-dir",
            str(tmp_path / "final_review"),
            "--reviewer",
            "tester",
        ],
        capsys,
    )
    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "missing gate key field" in envelope["input_error"]


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


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_extract_mock_fixture_writes_validated_candidate_runs(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out_dir = tmp_path / "runs"

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "extract",
            "--spec",
            str(fixture_dir / "clean_assignment" / "source" / "spec.md"),
            "--rubric",
            str(fixture_dir / "clean_assignment" / "source" / "rubric.md"),
            "--runner",
            "mock_fixture",
            "--fixture-dir",
            str(fixture_dir / "clean_assignment"),
            "--runs",
            "2",
            "--out-dir",
            str(out_dir),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    assert envelope["status"] == "success"
    assert envelope["command"] == "extract"
    assert envelope["run_count"] == 2
    assert envelope["valid_run_count"] == 2
    assert envelope["invalid_run_count"] == 0
    assert envelope["source_manifest_path"].endswith(
        "clean_assignment/source_manifest.yaml"
    )

    for run_id in ("run_001", "run_002"):
        run_dir = out_dir / run_id
        candidates = yaml.safe_load(
            (run_dir / "candidates.yaml").read_text(encoding="utf-8")
        )
        audit_trace = _read_jsonl(run_dir / "agent_trace.audit.jsonl")
        raw_trace = _read_jsonl(run_dir / "agent_trace.raw.jsonl")
        assert validate("candidates", candidates) == []
        assert all(validate("agent_trace", event) == [] for event in audit_trace)
        assert {
            candidate["integrity_status"]
            for section in candidates.values()
            for candidate in section
        } == {"validated"}
        assert {
            candidate["agent_run_id"]
            for section in candidates.values()
            for candidate in section
        } == {run_id}
        assert {event["run_id"] for event in audit_trace} == {run_id}
        assert {event["run_id"] for event in raw_trace} == {run_id}


def test_extract_mock_fixture_output_feeds_compact_runs_dir(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runs_dir = tmp_path / "runs"
    code, extract_envelope, _ = _run_main(
        [
            "--output",
            "json",
            "extract",
            "--spec",
            str(fixture_dir / "clean_assignment" / "source" / "spec.md"),
            "--rubric",
            str(fixture_dir / "clean_assignment" / "source" / "rubric.md"),
            "--runner",
            "mock_fixture",
            "--fixture-dir",
            str(fixture_dir / "clean_assignment"),
            "--runs",
            "2",
            "--out-dir",
            str(runs_dir),
        ],
        capsys,
    )
    assert code == 0
    assert extract_envelope["valid_run_count"] == 2

    out_dir = tmp_path / "compacted"
    code, compact_envelope, _ = _run_main(
        [
            "--output",
            "json",
            "compact",
            "--runs-dir",
            str(runs_dir),
            "--policy",
            str(fixture_dir / "clean_assignment" / "policy.yaml"),
            "--out-dir",
            str(out_dir),
        ],
        capsys,
    )

    _assert_envelope(compact_envelope)
    assert code == 0
    assert compact_envelope["status"] == "success"
    assert compact_envelope["valid_run_count"] == 2
    spec_doc = yaml.safe_load((out_dir / "spec_items.yaml").read_text(encoding="utf-8"))
    assert spec_doc["spec_items"][0]["support"]["found_in_runs"] == [
        "run_001",
        "run_002",
    ]


def test_extract_mock_fixture_isolates_invalid_run_with_diagnostics(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    out_dir = tmp_path / "runs"

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "extract",
            "--spec",
            str(fixture_dir / "reference_integrity" / "source" / "spec.md"),
            "--rubric",
            str(fixture_dir / "reference_integrity" / "source" / "rubric.md"),
            "--runner",
            "mock_fixture",
            "--fixture-dir",
            str(fixture_dir / "reference_integrity"),
            "--runs",
            "1",
            "--out-dir",
            str(out_dir),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    assert envelope["valid_run_count"] == 0
    assert envelope["invalid_run_count"] == 1

    run_dir = out_dir / "run_001"
    candidates = yaml.safe_load((run_dir / "candidates.yaml").read_text(encoding="utf-8"))
    diagnostics = json.loads(
        (run_dir / "integrity_diagnostics.json").read_text(encoding="utf-8")
    )
    assert validate("candidates", candidates) == []
    assert validate("integrity_diagnostics", diagnostics) == []
    assert {
        candidate["integrity_status"]
        for section in candidates.values()
        for candidate in section
    } != {"validated"}
    assert diagnostics["run_id"] == "run_001"
    assert diagnostics["summary"]["high"] > 0
    assert diagnostics["diagnostics"]
    assert not (run_dir / "integrity_errors.json").exists()


def test_extract_validates_generated_candidates_before_write(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = tmp_path / "bad_fixture"
    fixture.mkdir()
    (fixture / "spec_items.yaml").write_text(
        yaml.safe_dump(
            {
                "spec_items": [
                    {
                        "text": "Missing an id on purpose.",
                        "requirement_level": "must",
                        "source_ref": {
                            "document_id": "DOC_SPEC",
                            "start_line": 1,
                            "end_line": 1,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (fixture / "rubric_items.yaml").write_text(
        (fixture_dir / "clean_assignment" / "rubric_items.yaml").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    (fixture / "trace_links.yaml").write_text(
        (fixture_dir / "clean_assignment" / "trace_links.yaml").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "runs"

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "extract",
            "--spec",
            str(fixture_dir / "clean_assignment" / "source" / "spec.md"),
            "--rubric",
            str(fixture_dir / "clean_assignment" / "source" / "rubric.md"),
            "--source-manifest",
            str(fixture_dir / "clean_assignment" / "source_manifest.yaml"),
            "--runner",
            "mock_fixture",
            "--fixture-dir",
            str(fixture),
            "--runs",
            "1",
            "--out-dir",
            str(out_dir),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert (
        "generated candidate output failed schema validation"
        in envelope["input_error"]
    )
    assert not (out_dir / "run_001" / "candidates.yaml").exists()


def test_extract_mock_fixture_rejects_unknown_runner(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, envelope, stderr = _run_main(
        [
            "--output",
            "json",
            "extract",
            "--spec",
            str(fixture_dir / "clean_assignment" / "source" / "spec.md"),
            "--rubric",
            str(fixture_dir / "clean_assignment" / "source" / "rubric.md"),
            "--source-manifest",
            str(fixture_dir / "clean_assignment" / "source_manifest.yaml"),
            "--runner",
            "claude_sdk",
            "--runs",
            "1",
            "--out-dir",
            str(tmp_path / "runs"),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "real SDK runners are deferred" in envelope["input_error"]
    assert "real SDK runners are deferred" in stderr


def test_extract_rejects_runs_outside_plan_limit(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "extract",
            "--spec",
            str(fixture_dir / "clean_assignment" / "source" / "spec.md"),
            "--rubric",
            str(fixture_dir / "clean_assignment" / "source" / "rubric.md"),
            "--source-manifest",
            str(fixture_dir / "clean_assignment" / "source_manifest.yaml"),
            "--runner",
            "mock_fixture",
            "--fixture-dir",
            str(fixture_dir / "clean_assignment"),
            "--runs",
            "8",
            "--out-dir",
            str(tmp_path / "runs"),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "--runs must be between 1 and 7" in envelope["input_error"]


def test_verify_mock_fixture_writes_semantic_verifications_and_queue(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture_path = fixture_dir / "clean_assignment"
    candidates = _write_candidate_artifact(
        tmp_path / "candidates.yaml",
        _candidate_artifact_from_fixture(fixture_path, "run_1"),
    )
    compacted_dir = tmp_path / "compacted"
    compact_code, compact_envelope, _ = _run_main(
        [
            "--output",
            "json",
            "compact",
            "--candidates",
            str(candidates),
            "--policy",
            str(fixture_path / "policy.yaml"),
            "--out-dir",
            str(compacted_dir),
        ],
        capsys,
    )
    _assert_envelope(compact_envelope)
    assert compact_code == 0

    verify_dir = tmp_path / "semantic_verification"
    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "verify",
            "--compacted-dir",
            str(compacted_dir),
            "--source-manifest",
            str(fixture_path / "source_manifest.yaml"),
            "--runner",
            "mock_fixture",
            "--runs",
            "2",
            "--policy",
            str(fixture_path / "policy.yaml"),
            "--out-dir",
            str(verify_dir),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    assert envelope["status"] == "success"
    assert envelope["command"] == "verify"
    assert envelope["semantic_verification_count"] == 1
    assert envelope["review_queue_count"] == 1
    semantic_doc = yaml.safe_load(
        (verify_dir / "semantic_verifications.yaml").read_text(encoding="utf-8")
    )
    queue_doc = json.loads((verify_dir / "review_queue.json").read_text(encoding="utf-8"))
    assert validate("semantic_verifications", semantic_doc) == []
    assert validate("review_queue", queue_doc) == []
    assert semantic_doc["semantic_verifications"][0]["trace_link_id"] == "T2"
    assert semantic_doc["semantic_verifications"][0]["status_proposal"] == (
        "agent_uncertain"
    )
    assert semantic_doc["semantic_verifications"][0]["support"] == {
        "total_valid_runs": 2,
        "found_in_runs": ["verify_001", "verify_002"],
    }
    assert queue_doc["review_queue"][0]["type"] == "ai_judgement_pending"
    assert queue_doc["review_queue"][0]["target"] == {
        "trace_link_id": "T2",
        "rubric_id": "R2",
        "spec_ids": ["S2"],
        "evidence_quote_index": 0,
    }
    assert queue_doc["review_queue"][0]["related_runs"] == ["run_1"]


def test_verify_uses_id_map_trace_link_canonical_id_when_trace_order_changes(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture_path = fixture_dir / "clean_assignment"
    candidates = _write_candidate_artifact(
        tmp_path / "candidates.yaml",
        _candidate_artifact_from_fixture(fixture_path, "run_1"),
    )
    compacted_dir = tmp_path / "compacted"
    compact_code, compact_envelope, _ = _run_main(
        [
            "--output",
            "json",
            "compact",
            "--candidates",
            str(candidates),
            "--policy",
            str(fixture_path / "policy.yaml"),
            "--out-dir",
            str(compacted_dir),
        ],
        capsys,
    )
    _assert_envelope(compact_envelope)
    assert compact_code == 0

    trace_doc = yaml.safe_load(
        (compacted_dir / "trace_links.yaml").read_text(encoding="utf-8")
    )
    trace_doc["trace_links"] = [
        trace_doc["trace_links"][1],
        trace_doc["trace_links"][0],
        trace_doc["trace_links"][2],
    ]
    (compacted_dir / "trace_links.yaml").write_text(
        yaml.safe_dump(trace_doc, sort_keys=False),
        encoding="utf-8",
    )

    verify_dir = tmp_path / "semantic_verification"
    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "verify",
            "--compacted-dir",
            str(compacted_dir),
            "--source-manifest",
            str(fixture_path / "source_manifest.yaml"),
            "--runner",
            "mock_fixture",
            "--runs",
            "1",
            "--policy",
            str(fixture_path / "policy.yaml"),
            "--out-dir",
            str(verify_dir),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    semantic_doc = yaml.safe_load(
        (verify_dir / "semantic_verifications.yaml").read_text(encoding="utf-8")
    )
    queue_doc = json.loads((verify_dir / "review_queue.json").read_text(encoding="utf-8"))
    assert semantic_doc["semantic_verifications"][0]["trace_link_id"] == "T2"
    assert queue_doc["review_queue"][0]["target"]["trace_link_id"] == "T2"


def test_verify_ai_judgement_without_source_ref_still_records_uncertain_proposal(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    compacted_dir = tmp_path / "compacted"
    compacted_dir.mkdir()
    for filename in ("spec_items.yaml", "rubric_items.yaml", "trace_links.yaml"):
        (compacted_dir / filename).write_text(
            (fixture_dir / "clean_assignment" / filename).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    trace_doc = yaml.safe_load(
        (compacted_dir / "trace_links.yaml").read_text(encoding="utf-8")
    )
    del trace_doc["trace_links"][1]["evidence_quotes"][0]["source_ref"]
    (compacted_dir / "trace_links.yaml").write_text(
        yaml.safe_dump(trace_doc, sort_keys=False),
        encoding="utf-8",
    )

    verify_dir = tmp_path / "verify"
    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "verify",
            "--compacted-dir",
            str(compacted_dir),
            "--source-manifest",
            str(fixture_dir / "clean_assignment" / "source_manifest.yaml"),
            "--runner",
            "mock_fixture",
            "--runs",
            "1",
            "--policy",
            str(fixture_dir / "clean_assignment" / "policy.yaml"),
            "--out-dir",
            str(verify_dir),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    assert envelope["semantic_verification_count"] == 1
    assert envelope["review_queue_count"] == 1
    semantic_doc = yaml.safe_load(
        (verify_dir / "semantic_verifications.yaml").read_text(encoding="utf-8")
    )
    proposal = semantic_doc["semantic_verifications"][0]
    assert proposal["status_proposal"] == "agent_uncertain"
    assert proposal["source_refs"] == []
    assert "No quote-level source_ref was available" in proposal["rationale"]


def test_verify_token_sequence_only_links_do_not_create_semantic_proposals(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    compacted_dir = tmp_path / "compacted"
    compacted_dir.mkdir()
    for filename in ("spec_items.yaml", "rubric_items.yaml", "trace_links.yaml"):
        (compacted_dir / filename).write_text(
            (fixture_dir / "clean_assignment" / filename).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    trace_doc = yaml.safe_load(
        (compacted_dir / "trace_links.yaml").read_text(encoding="utf-8")
    )
    for trace_link in trace_doc["trace_links"]:
        for quote in trace_link["evidence_quotes"]:
            quote["verification_mode"] = "token_sequence"
    (compacted_dir / "trace_links.yaml").write_text(
        yaml.safe_dump(trace_doc, sort_keys=False),
        encoding="utf-8",
    )

    verify_dir = tmp_path / "verify"
    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "verify",
            "--compacted-dir",
            str(compacted_dir),
            "--source-manifest",
            str(fixture_dir / "clean_assignment" / "source_manifest.yaml"),
            "--runner",
            "mock_fixture",
            "--runs",
            "1",
            "--policy",
            str(fixture_dir / "clean_assignment" / "policy.yaml"),
            "--out-dir",
            str(verify_dir),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    assert envelope["semantic_verification_count"] == 0
    assert envelope["review_queue_count"] == 0


def test_verify_preserves_existing_queue_and_does_not_duplicate_pending_entry(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    compacted_dir = tmp_path / "compacted"
    compacted_dir.mkdir()
    for filename in ("spec_items.yaml", "rubric_items.yaml", "trace_links.yaml"):
        (compacted_dir / filename).write_text(
            (fixture_dir / "clean_assignment" / filename).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    queue_in = tmp_path / "review_queue_in.json"
    queue_in.write_text(
        json.dumps(
            {
                "source": "preexisting",
                "review_queue": [
                    {
                        "entry_id": "ai_judgement_pending_T2_0",
                        "type": "ai_judgement_pending",
                        "target": {"trace_link_id": "T2"},
                        "reason": "already queued",
                        "related_runs": ["manual"],
                        "status": "open",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "verify",
            "--compacted-dir",
            str(compacted_dir),
            "--source-manifest",
            str(fixture_dir / "clean_assignment" / "source_manifest.yaml"),
            "--runner",
            "mock_fixture",
            "--runs",
            "1",
            "--policy",
            str(fixture_dir / "clean_assignment" / "policy.yaml"),
            "--out-dir",
            str(tmp_path / "verify"),
            "--review-queue-in",
            str(queue_in),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    assert envelope["review_queue_count"] == 1
    queue_doc = json.loads(
        (tmp_path / "verify" / "review_queue.json").read_text(encoding="utf-8")
    )
    assert queue_doc["source"] == "preexisting"
    assert [entry["entry_id"] for entry in queue_doc["review_queue"]] == [
        "ai_judgement_pending_T2_0"
    ]


def test_verify_rejects_unknown_runner(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    compacted_dir = tmp_path / "compacted"
    compacted_dir.mkdir()
    for filename in ("spec_items.yaml", "rubric_items.yaml", "trace_links.yaml"):
        (compacted_dir / filename).write_text(
            (fixture_dir / "clean_assignment" / filename).read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    code, envelope, stderr = _run_main(
        [
            "--output",
            "json",
            "verify",
            "--compacted-dir",
            str(compacted_dir),
            "--source-manifest",
            str(fixture_dir / "clean_assignment" / "source_manifest.yaml"),
            "--runner",
            "claude_sdk",
            "--runs",
            "1",
            "--policy",
            str(fixture_dir / "clean_assignment" / "policy.yaml"),
            "--out-dir",
            str(tmp_path / "verify"),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "real SDK verifier runners are deferred" in envelope["input_error"]
    assert "real SDK verifier runners are deferred" in stderr


def _candidate_artifact(
    *,
    run_id: str,
    spec_id: str,
    rubric_id: str,
    integrity_status: str = "validated",
) -> dict:
    return {
        "spec_item_candidates": [
            {
                "candidate_id": "SC1",
                "proposed_item": {
                    "id": spec_id,
                    "text": "Implement refund handling for cancelled orders.",
                    "requirement_level": "must",
                    "source_ref": {
                        "document_id": "DOC_SPEC",
                        "start_line": 1,
                        "end_line": 1,
                    },
                },
                "agent_runner": "mock_fixture",
                "agent_run_id": run_id,
                "integrity_status": integrity_status,
            }
        ],
        "rubric_item_candidates": [
            {
                "candidate_id": "RC1",
                "proposed_item": {
                    "id": rubric_id,
                    "title": "Refund policy handling",
                    "description": "Checks the refund requirement.",
                    "evaluation_role": "scored",
                    "source_ref": {
                        "document_id": "DOC_RUBRIC",
                        "start_line": 1,
                        "end_line": 1,
                    },
                },
                "agent_runner": "mock_fixture",
                "agent_run_id": run_id,
                "integrity_status": integrity_status,
            }
        ],
        "trace_link_candidates": [
            {
                "candidate_id": "TC1",
                "proposed_item": {
                    "rubric_id": rubric_id,
                    "spec_ids": [spec_id],
                    "evidence_quotes": [
                        {
                            "spec_id": spec_id,
                            "quote": "Implement refund handling for cancelled orders.",
                            "verification_mode": "token_sequence",
                        }
                    ],
                    "semantic_status": "pending_verification",
                },
                "agent_runner": "mock_fixture",
                "agent_run_id": run_id,
                "integrity_status": integrity_status,
            }
        ],
    }


def _write_candidate_artifact(path: Path, payload: dict) -> Path:
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def _write_compact_policy(path: Path) -> Path:
    path.write_text(
        yaml.safe_dump(
            {
                "rules": {"optionality_mismatch": {"weight_threshold": 10}},
                "compacting": {
                    "identity_basis": {
                        "spec_item": "source+section+normalized_text",
                        "rubric_item": "title+normalized_description",
                        "trace_link": "rubric_id+sorted(spec_ids)",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_compact_cli_writes_canonical_yaml_and_id_map_wrapper(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_1 = _write_candidate_artifact(
        tmp_path / "run_1.yaml",
        _candidate_artifact(run_id="run_1", spec_id="S_A", rubric_id="R_A"),
    )
    run_2 = _write_candidate_artifact(
        tmp_path / "run_2.yaml",
        _candidate_artifact(run_id="run_2", spec_id="S_B", rubric_id="R_B"),
    )
    policy = _write_compact_policy(tmp_path / "policy.yaml")
    out_dir = tmp_path / "compacted"

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "compact",
            "--candidates",
            str(run_1),
            str(run_2),
            "--policy",
            str(policy),
            "--out-dir",
            str(out_dir),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    assert envelope["status"] == "success"
    assert envelope["valid_run_count"] == 2
    assert envelope["excluded_run_count"] == 0
    assert envelope["review_queue_count"] == 0

    spec_doc = yaml.safe_load((out_dir / "spec_items.yaml").read_text(encoding="utf-8"))
    trace_doc = yaml.safe_load((out_dir / "trace_links.yaml").read_text(encoding="utf-8"))
    id_map_doc = yaml.safe_load((out_dir / "id_map.yaml").read_text(encoding="utf-8"))
    assert validate("spec_items", spec_doc) == []
    assert validate("trace_links", trace_doc) == []
    assert validate("id_map", id_map_doc) == []
    assert spec_doc["spec_items"][0]["support"] == {
        "total_valid_runs": 2,
        "found_in_runs": ["run_1", "run_2"],
    }
    assert trace_doc["trace_links"][0]["rubric_id"] == "R1"
    assert trace_doc["trace_links"][0]["spec_ids"] == ["S1"]


def test_compact_cli_accepts_plan_canonical_runs_dir(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_dir = tmp_path / "runs" / "run_001"
    run_dir.mkdir(parents=True)
    _write_candidate_artifact(
        run_dir / "candidates.yaml",
        _candidate_artifact(run_id="run_1", spec_id="S_A", rubric_id="R_A"),
    )
    policy = _write_compact_policy(tmp_path / "policy.yaml")
    out_dir = tmp_path / "compacted"

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "compact",
            "--runs-dir",
            str(tmp_path / "runs"),
            "--policy",
            str(policy),
            "--out-dir",
            str(out_dir),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    assert envelope["valid_run_count"] == 1
    assert validate(
        "id_map",
        yaml.safe_load((out_dir / "id_map.yaml").read_text(encoding="utf-8")),
    ) == []


def test_compact_cli_preserves_existing_queue_and_records_invalid_run(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    valid_run = _write_candidate_artifact(
        tmp_path / "run_1.yaml",
        _candidate_artifact(run_id="run_1", spec_id="S_A", rubric_id="R_A"),
    )
    mixed_payload = _candidate_artifact(run_id="run_2", spec_id="S_B", rubric_id="R_B")
    mixed_payload["trace_link_candidates"][0]["integrity_status"] = "invalid_reference"
    mixed_run = _write_candidate_artifact(tmp_path / "run_2.yaml", mixed_payload)
    policy = _write_compact_policy(tmp_path / "policy.yaml")
    queue_in = tmp_path / "review_queue_in.json"
    queue_in.write_text(
        json.dumps(
            {
                "generated_at": "2026-06-01T00:00:00Z",
                "source": "preexisting",
                "review_queue": [
                    {
                        "entry_id": "existing_double_scoring",
                        "type": "double_scoring_review",
                        "target": {"spec_id": "S1"},
                        "reason": "pre-existing lint safeguard",
                        "related_runs": [],
                        "status": "open",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "compacted"

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "compact",
            "--candidates",
            str(valid_run),
            str(mixed_run),
            "--policy",
            str(policy),
            "--out-dir",
            str(out_dir),
            "--review-queue-in",
            str(queue_in),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    assert envelope["valid_run_count"] == 1
    assert envelope["excluded_run_count"] == 1
    assert envelope["review_queue_count"] == 2
    queue_doc = json.loads((out_dir / "review_queue.json").read_text(encoding="utf-8"))
    assert validate("review_queue", queue_doc) == []
    assert queue_doc["source"] == "preexisting"
    assert [entry["type"] for entry in queue_doc["review_queue"]] == [
        "double_scoring_review",
        "invalid_run",
    ]
    assert queue_doc["review_queue"][1]["related_runs"] == ["run_2"]


def test_compact_cli_does_not_duplicate_existing_invalid_run_entry(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mixed_payload = _candidate_artifact(run_id="run_2", spec_id="S_B", rubric_id="R_B")
    mixed_payload["trace_link_candidates"][0]["integrity_status"] = "invalid_reference"
    mixed_run = _write_candidate_artifact(tmp_path / "run_2.yaml", mixed_payload)
    policy = _write_compact_policy(tmp_path / "policy.yaml")
    queue_in = tmp_path / "review_queue_in.json"
    queue_in.write_text(
        json.dumps(
            {
                "review_queue": [
                    {
                        "entry_id": "invalid_run_1",
                        "type": "invalid_run",
                        "target": {"candidate_path": str(mixed_run)},
                        "reason": "already recorded",
                        "related_runs": ["run_2"],
                        "status": "open",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "compacted"

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "compact",
            "--candidates",
            str(mixed_run),
            "--policy",
            str(policy),
            "--out-dir",
            str(out_dir),
            "--review-queue-in",
            str(queue_in),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 0
    assert envelope["review_queue_count"] == 1
    queue_doc = json.loads((out_dir / "review_queue.json").read_text(encoding="utf-8"))
    assert [entry["entry_id"] for entry in queue_doc["review_queue"]] == [
        "invalid_run_1"
    ]


def test_compact_cli_rejects_runs_dir_and_candidates_together(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    candidate = _write_candidate_artifact(
        tmp_path / "run.yaml",
        _candidate_artifact(run_id="run_1", spec_id="S_A", rubric_id="R_A"),
    )
    policy = _write_compact_policy(tmp_path / "policy.yaml")

    code, envelope, _ = _run_main(
        [
            "--output",
            "json",
            "compact",
            "--runs-dir",
            str(tmp_path),
            "--candidates",
            str(candidate),
            "--policy",
            str(policy),
            "--out-dir",
            str(tmp_path / "out"),
        ],
        capsys,
    )

    _assert_envelope(envelope)
    assert code == 2
    assert envelope["status"] == "invalid_input"
    assert "either --runs-dir or --candidates" in envelope["input_error"]


def _candidate_artifact_from_fixture(fixture_path: Path, run_id: str) -> dict:
    spec_doc = yaml.safe_load((fixture_path / "spec_items.yaml").read_text(encoding="utf-8"))
    rubric_doc = yaml.safe_load(
        (fixture_path / "rubric_items.yaml").read_text(encoding="utf-8")
    )
    trace_doc = yaml.safe_load(
        (fixture_path / "trace_links.yaml").read_text(encoding="utf-8")
    )

    return {
        "spec_item_candidates": [
            {
                "candidate_id": f"SC{index}",
                "proposed_item": item,
                "agent_runner": "fixture",
                "agent_run_id": run_id,
                "integrity_status": "validated",
            }
            for index, item in enumerate(spec_doc["spec_items"], start=1)
        ],
        "rubric_item_candidates": [
            {
                "candidate_id": f"RC{index}",
                "proposed_item": item,
                "agent_runner": "fixture",
                "agent_run_id": run_id,
                "integrity_status": "validated",
            }
            for index, item in enumerate(rubric_doc["rubric_items"], start=1)
        ],
        "trace_link_candidates": [
            {
                "candidate_id": f"TC{index}",
                "proposed_item": item,
                "agent_runner": "fixture",
                "agent_run_id": run_id,
                "integrity_status": "validated",
            }
            for index, item in enumerate(trace_doc["trace_links"], start=1)
        ],
    }


def test_compact_output_feeds_existing_check_flow(
    fixture_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture_path = fixture_dir / "clean_assignment"
    candidates = _write_candidate_artifact(
        tmp_path / "candidates.yaml",
        _candidate_artifact_from_fixture(fixture_path, "run_1"),
    )
    compacted_dir = tmp_path / "compacted"
    compact_code, compact_envelope, _ = _run_main(
        [
            "--output",
            "json",
            "compact",
            "--candidates",
            str(candidates),
            "--policy",
            str(fixture_path / "policy.yaml"),
            "--out-dir",
            str(compacted_dir),
        ],
        capsys,
    )
    _assert_envelope(compact_envelope)
    assert compact_code == 0

    findings = tmp_path / "findings.json"
    diagnostics = tmp_path / "diagnostics.json"
    check_code, check_envelope, _ = _run_main(
        [
            "--output",
            "json",
            "check",
            "--spec-items",
            str(compacted_dir / "spec_items.yaml"),
            "--rubric-items",
            str(compacted_dir / "rubric_items.yaml"),
            "--trace-links",
            str(compacted_dir / "trace_links.yaml"),
            "--source-manifest",
            str(fixture_path / "source_manifest.yaml"),
            "--policy",
            str(fixture_path / "policy.yaml"),
            "--out",
            str(findings),
            "--diagnostics-out",
            str(diagnostics),
        ],
        capsys,
    )

    _assert_envelope(check_envelope)
    assert check_code == 0
    assert check_envelope["status"] == "provisional_findings"
    assert check_envelope["provisional_medium_count"] == 2
    assert check_envelope["review_queue_count"] == 0


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
        "policy": root / "policy.yaml",
    }
    paths["spec_items"].write_text(yaml.safe_dump({"spec_items": spec_items}), encoding="utf-8")
    paths["rubric_items"].write_text(
        yaml.safe_dump({"rubric_items": rubric_items}), encoding="utf-8"
    )
    paths["trace_links"].write_text(
        yaml.safe_dump({"trace_links": trace_links}), encoding="utf-8"
    )
    paths["source_manifest"].write_text(yaml.safe_dump(manifest), encoding="utf-8")
    paths["policy"].write_text(
        yaml.safe_dump(
            {"rules": {"optionality_mismatch": {"weight_threshold": 10}}}
        ),
        encoding="utf-8",
    )
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
        "--policy",
        str(paths["policy"]),
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
