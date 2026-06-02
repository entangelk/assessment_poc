"""Agent-consumable CLI entry point.

Subcommands implemented in Phase 0:

- ``check``   : run deterministic rules over the supplied compacted YAML and
                emit JSON findings + integrity diagnostics.
- ``compact`` : compact validated candidate runs into canonical YAML artifacts.
- ``extract`` : run fixture-backed candidate extraction into isolated run dirs.
- ``verify``  : create read-only semantic verification proposals for compacted
                trace links.
- ``schema``  : self-discovery for the stable contract; lets caller agents
                read the current `cli_output` shape without docs.
- ``report``  : render findings + diagnostics into a Markdown report.
- ``review``  : write a safe final-review draft with hold decisions.
- ``gate``    : consume final review and emit the external verdict.

Real SDK runners for ``extract`` / ``verify`` are later-phase scope.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from .agent_runners import (
    MockFixtureRunner,
    classify_deep_candidate_run_integrity,
    normalize_result_candidates,
)
from .compacting import (
    CompactingInputError,
    compact_validated_candidates,
    validated_candidate_run_id,
)
from .models import HarnessInputError, load_source_snapshot, load_validated, load_policy
from .report import render_markdown
from .rules import (
    finding_severity_counts,
    run_rule_l1,
    run_rule_l5,
    run_rule_l6,
    run_rule_one,
    run_rule_three,
    run_rule_two,
    run_rule_zero,
    severity_counts,
)
from .schemas import validate


STABLE_CORE_FIELDS = ["status", "exit_code", "command", "next_actions"]


@dataclass
class CommandResult:
    envelope: dict[str, Any]
    exit_code: int


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _emit(envelope: dict[str, Any], *, output: str) -> None:
    if output == "json":
        sys.stdout.write(json.dumps(envelope, indent=2, sort_keys=False) + "\n")
        return
    # Default human-readable summary.
    sys.stdout.write(f"status: {envelope.get('status')}\n")
    sys.stdout.write(f"exit_code: {envelope.get('exit_code')}\n")
    for key in (
        "findings_path",
        "diagnostics_path",
        "semantic_verifications_path",
        "report_path",
        "blocking_count",
    ):
        if key in envelope:
            sys.stdout.write(f"{key}: {envelope[key]}\n")
    actions = envelope.get("next_actions") or []
    if actions:
        sys.stdout.write("next_actions:\n")
        for action in actions:
            sys.stdout.write(f"  - {json.dumps(action, sort_keys=True)}\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
        fh.write("\n")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_jsonl(path: Path, events: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event, sort_keys=False) + "\n")


def _ensure_envelope_valid(envelope: dict[str, Any]) -> None:
    errors = validate("cli_output", envelope)
    if errors:
        # Internal contract bug; surface loudly via stderr but keep emitting.
        sys.stderr.write(
            "[assessment-harness] cli_output envelope failed schema validation:\n"
        )
        for err in errors:
            sys.stderr.write(f"  - {err}\n")


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


def _cmd_check(args: argparse.Namespace) -> CommandResult:
    next_actions: list[dict[str, Any]] = []
    findings_payload: dict[str, Any]
    diagnostics_payload: dict[str, Any]

    if not args.source_manifest:
        return _check_missing_manifest(args, next_actions)
    if not args.policy:
        return _check_missing_policy(args, next_actions)

    try:
        spec_doc = load_validated(Path(args.spec_items), "spec_items")
        rubric_doc = load_validated(Path(args.rubric_items), "rubric_items")
        trace_doc = load_validated(Path(args.trace_links), "trace_links")
    except HarnessInputError as exc:
        return _check_invalid_input(args, exc, next_actions)

    try:
        policy_doc = load_policy(Path(args.policy))
        _validate_check_policy(policy_doc, Path(args.policy))
    except HarnessInputError as exc:
        return _check_invalid_input(args, exc, next_actions)

    try:
        snapshot = load_source_snapshot(Path(args.source_manifest))
    except HarnessInputError as exc:
        return _check_invalid_input(args, exc, next_actions)

    diagnostics = run_rule_zero(spec_doc, rubric_doc, trace_doc, snapshot)
    counts = severity_counts(diagnostics)
    diagnostics_payload = {
        "diagnostics": [diag.to_dict() for diag in diagnostics],
        "summary": {
            "total": counts["total"],
            "high": counts["high"],
            "medium": counts.get("medium", 0),
            "low": counts.get("low", 0),
            "informational": counts.get("informational", 0),
        },
        "generated_at": _now_iso(),
    }

    if counts["high"] > 0:
        findings_payload = {
            "status": "invalid_input",
            "findings": [],
            "diagnostics_ref": str(Path(args.diagnostics_out).name),
            "blocking_count": 0,
            "generated_at": _now_iso(),
        }
        next_actions.append(
            {
                "type": "fix_reference_integrity",
                "diagnostics_path": str(args.diagnostics_out),
                "high_count": counts["high"],
            }
        )
        envelope = _build_envelope(
            status="invalid_input",
            exit_code=2,
            command="check",
            next_actions=next_actions,
            findings_path=str(args.out),
            diagnostics_path=str(args.diagnostics_out),
            blocking_count=0,
            high_integrity_count=counts["high"],
        )
        _write_json(Path(args.out), findings_payload)
        _write_json(Path(args.diagnostics_out), diagnostics_payload)
        return CommandResult(envelope=envelope, exit_code=2)

    # Rule 0 clean. Run subsequent provisional rules; check never emits
    # blocking verdicts (that is gate's job).
    rule_one_findings = run_rule_one(rubric_doc, trace_doc)
    rule_two_findings = run_rule_two(spec_doc, rubric_doc, trace_doc)
    rule_three_findings = run_rule_three(spec_doc, rubric_doc, trace_doc, policy_doc)
    lint_findings, review_queue = run_rule_l1(rubric_doc, trace_doc)
    lint_findings.extend(run_rule_l5(spec_doc, rubric_doc, trace_doc))
    l6_findings, l6_review_queue = run_rule_l6(spec_doc, rubric_doc, trace_doc)
    lint_findings.extend(l6_findings)
    review_queue.extend(l6_review_queue)
    provisional_findings = (
        rule_one_findings + rule_two_findings + rule_three_findings + lint_findings
    )
    finding_counts = finding_severity_counts(provisional_findings)
    review_queue_path = (
        Path(args.review_queue_out)
        if args.review_queue_out
        else Path(args.out).with_name("review_queue.json")
    )
    queue_payload = {
        "review_queue": review_queue,
        "generated_at": _now_iso(),
    }
    _write_json(review_queue_path, queue_payload)
    envelope_fields = {
        "review_queue_path": str(review_queue_path),
        "review_queue_count": len(review_queue),
    }

    if provisional_findings:
        for f in provisional_findings:
            if f.type == "possible_orphan_scored_rubric_item":
                next_actions.append(
                    {
                        "type": "review_orphan_rubric",
                        "rubric_id": f.rubric_id,
                        "finding_type": f.type,
                    }
                )
            elif f.type == "unconfirmed_trace_coverage":
                next_actions.append(
                    {
                        "type": "review_unconfirmed_trace_coverage",
                        "rubric_id": f.rubric_id,
                        "finding_type": f.type,
                    }
                )
            elif f.type == "orphan_bonus_rubric_item":
                next_actions.append(
                    {
                        "type": "review_orphan_bonus_rubric",
                        "rubric_id": f.rubric_id,
                        "finding_type": f.type,
                    }
                )
            elif f.type == "double_scored_spec":
                next_actions.append(
                    {
                        "type": "review_double_scoring",
                        "spec_id": f.spec_id,
                        "scored_rubric_id": f.scored_rubric_id,
                        "bonus_rubric_id": f.bonus_rubric_id,
                        "finding_type": f.type,
                    }
                )
            elif f.type == "bonus_grades_mandatory_only":
                next_actions.append(
                    {
                        "type": "review_bonus_mandatory_only",
                        "rubric_id": f.rubric_id,
                        "finding_type": f.type,
                    }
                )
            elif f.type == "mandatory_spec_bonus_only_traced":
                next_actions.append(
                    {
                        "type": "review_mandatory_spec_bonus_only",
                        "spec_id": f.spec_id,
                        "bonus_rubric_ids": f.bonus_rubric_ids,
                        "finding_type": f.type,
                    }
                )
            elif f.type == "uncovered_must_spec_item":
                next_actions.append(
                    {
                        "type": "review_uncovered_must_spec",
                        "spec_id": f.spec_id,
                        "finding_type": f.type,
                    }
                )
            elif f.type == "optionality_mismatch":
                next_actions.append(
                    {
                        "type": "review_optionality_mismatch",
                        "rubric_id": f.rubric_id,
                        "finding_type": f.type,
                    }
                )
        findings_payload = {
            "status": "provisional_findings",
            "findings": [f.to_dict() for f in provisional_findings],
            "diagnostics_ref": str(Path(args.diagnostics_out).name),
            "blocking_count": 0,
            "generated_at": _now_iso(),
        }
        envelope = _build_envelope(
            status="provisional_findings",
            exit_code=0,
            command="check",
            next_actions=next_actions,
            findings_path=str(args.out),
            diagnostics_path=str(args.diagnostics_out),
            blocking_count=0,
            high_integrity_count=0,
            provisional_high_count=finding_counts["high"],
            provisional_medium_count=finding_counts["medium"],
            provisional_informational_count=finding_counts["informational"],
            **envelope_fields,
        )
        _write_json(Path(args.out), findings_payload)
        _write_json(Path(args.diagnostics_out), diagnostics_payload)
        return CommandResult(envelope=envelope, exit_code=0)

    findings_payload = {
        "status": "success",
        "findings": [],
        "diagnostics_ref": str(Path(args.diagnostics_out).name),
        "blocking_count": 0,
        "generated_at": _now_iso(),
    }
    envelope = _build_envelope(
        status="success",
        exit_code=0,
        command="check",
        next_actions=next_actions,
        findings_path=str(args.out),
        diagnostics_path=str(args.diagnostics_out),
        blocking_count=0,
        high_integrity_count=0,
        **envelope_fields,
    )
    _write_json(Path(args.out), findings_payload)
    _write_json(Path(args.diagnostics_out), diagnostics_payload)
    return CommandResult(envelope=envelope, exit_code=0)


def _check_missing_manifest(
    args: argparse.Namespace, next_actions: list[dict[str, Any]]
) -> CommandResult:
    """`--source-manifest` is required (plan v1.8 §5.0). Emit a structured
    diagnostic so caller agents see the failure on stdout, not just argparse
    usage text on stderr.
    """
    message = (
        "--source-manifest is required: Phase 0 mandates immutable source "
        "snapshot grounding (plan §5.0 / §5.1 / §11)."
    )
    sys.stderr.write(f"[assessment-harness] {message}\n")

    diagnostic = {
        "code": "source_manifest_required",
        "severity": "high",
        "message": message,
        "location": {"argument": "--source-manifest"},
        "hint": (
            "Pass --source-manifest <path> pointing at the snapshot manifest "
            "for this assessment. See fixtures/clean_assignment/source_manifest.yaml."
        ),
    }
    diagnostics_payload = {
        "diagnostics": [diagnostic],
        "summary": {
            "total": 1,
            "high": 1,
            "medium": 0,
            "low": 0,
            "informational": 0,
        },
        "generated_at": _now_iso(),
    }
    findings_payload = {
        "status": "invalid_input",
        "findings": [],
        "diagnostics_ref": str(Path(args.diagnostics_out).name),
        "blocking_count": 0,
        "generated_at": _now_iso(),
        "input_error": message,
    }
    try:
        _write_json(Path(args.out), findings_payload)
        _write_json(Path(args.diagnostics_out), diagnostics_payload)
    except OSError:
        pass

    next_actions.append(
        {
            "type": "provide_source_manifest",
            "argument": "--source-manifest",
            "message": message,
        }
    )
    envelope = _build_envelope(
        status="invalid_input",
        exit_code=2,
        command="check",
        next_actions=next_actions,
        findings_path=str(args.out),
        diagnostics_path=str(args.diagnostics_out),
        blocking_count=0,
        high_integrity_count=1,
        input_error=message,
    )
    return CommandResult(envelope=envelope, exit_code=2)


def _check_missing_policy(
    args: argparse.Namespace, next_actions: list[dict[str, Any]]
) -> CommandResult:
    message = (
        "--policy is required: Phase 0 check needs "
        "rules.optionality_mismatch.weight_threshold so Rule 3 cannot be "
        "silently disabled."
    )
    exc = HarnessInputError(message)
    result = _check_invalid_input(args, exc, next_actions)
    result.envelope["next_actions"] = [
        {
            "type": "provide_policy",
            "argument": "--policy",
            "message": message,
        }
    ]
    return result


def _validate_check_policy(policy_doc: dict[str, Any], policy_path: Path) -> None:
    rules = policy_doc.get("rules")
    optionality = rules.get("optionality_mismatch") if isinstance(rules, dict) else None
    if not isinstance(optionality, dict) or "weight_threshold" not in optionality:
        raise HarnessInputError(
            (
                f"{policy_path}: missing required policy field "
                "rules.optionality_mismatch.weight_threshold"
            )
        )


def _check_invalid_input(
    args: argparse.Namespace, exc: HarnessInputError, next_actions: list[dict[str, Any]]
) -> CommandResult:
    sys.stderr.write(f"[assessment-harness] {exc}\n")
    for err in exc.errors:
        sys.stderr.write(f"  - {err}\n")

    findings_payload = {
        "status": "invalid_input",
        "findings": [],
        "diagnostics_ref": str(Path(args.diagnostics_out).name),
        "blocking_count": 0,
        "generated_at": _now_iso(),
        "input_error": str(exc),
        "input_error_details": exc.errors,
    }
    diagnostics_payload = {
        "diagnostics": [],
        "summary": {
            "total": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "informational": 0,
        },
        "generated_at": _now_iso(),
        "input_error": str(exc),
    }
    try:
        _write_json(Path(args.out), findings_payload)
        _write_json(Path(args.diagnostics_out), diagnostics_payload)
    except OSError:
        pass

    next_actions.append(
        {
            "type": "fix_input",
            "message": str(exc),
        }
    )
    envelope = _build_envelope(
        status="invalid_input",
        exit_code=2,
        command="check",
        next_actions=next_actions,
        findings_path=str(args.out),
        diagnostics_path=str(args.diagnostics_out),
        blocking_count=0,
        input_error=str(exc),
    )
    return CommandResult(envelope=envelope, exit_code=2)


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------


def _cmd_extract(args: argparse.Namespace) -> CommandResult:
    try:
        _validate_extract_paths(args)
        runner = _extract_runner(args)
        source_manifest_path = _extract_source_manifest_path(args)
        snapshot = load_source_snapshot(source_manifest_path)
        policy_doc = load_policy(Path(args.policy)) if args.policy else {}
        run_count = _extract_run_count(args.runs)
    except HarnessInputError as exc:
        return _extract_invalid_input(args, str(exc), exc.errors)

    out_dir = Path(args.out_dir)
    run_dirs: list[str] = []
    valid_run_count = 0
    invalid_run_count = 0

    for index in range(1, run_count + 1):
        run_id = f"run_{index:03d}"
        run_dir = out_dir / run_id
        result = runner.run(
            spec_path=Path(args.spec),
            rubric_path=Path(args.rubric),
            tools=[],
            max_turns=1,
            policy=policy_doc,
        )
        if isinstance(runner, MockFixtureRunner):
            result = _with_mock_extract_run_id(result, run_id)
        candidates = normalize_result_candidates(result)
        integrity = classify_deep_candidate_run_integrity(
            candidates,
            result.audit_trace,
            snapshot,
        )
        if integrity.integrity_status == "validated":
            valid_run_count += 1
        else:
            invalid_run_count += 1

        candidate_errors = validate("candidates", integrity.candidates)
        if candidate_errors:
            return _extract_invalid_input(
                args,
                "generated candidate output failed schema validation",
                candidate_errors,
            )
        _write_yaml(run_dir / "candidates.yaml", integrity.candidates)
        audit_trace_errors = _agent_trace_errors(result.audit_trace)
        if audit_trace_errors:
            return _extract_invalid_input(
                args,
                "generated audit trace failed schema validation",
                audit_trace_errors,
            )
        _write_jsonl(run_dir / "agent_trace.audit.jsonl", tuple(result.audit_trace))
        _write_jsonl(run_dir / "agent_trace.raw.jsonl", tuple(result.raw_trace))
        if integrity.errors:
            diagnostics_payload = _extract_integrity_diagnostics_payload(
                run_id,
                integrity,
            )
            diagnostics_errors = validate(
                "integrity_diagnostics",
                diagnostics_payload,
            )
            if diagnostics_errors:
                return _extract_invalid_input(
                    args,
                    "generated integrity diagnostics failed schema validation",
                    diagnostics_errors,
                )
            _write_json(
                run_dir / "integrity_diagnostics.json",
                diagnostics_payload,
            )
        run_dirs.append(str(run_dir))

    envelope = _build_envelope(
        status="success",
        exit_code=0,
        command="extract",
        next_actions=[],
        runs_dir=str(out_dir),
        run_dirs=run_dirs,
        run_count=run_count,
        valid_run_count=valid_run_count,
        invalid_run_count=invalid_run_count,
        runner=args.runner,
        source_manifest_path=str(source_manifest_path),
    )
    return CommandResult(envelope=envelope, exit_code=0)


def _validate_extract_paths(args: argparse.Namespace) -> None:
    for label in ("spec", "rubric"):
        path = Path(getattr(args, label))
        if not path.exists():
            raise HarnessInputError(f"{label} file not found: {path}")


def _extract_runner(args: argparse.Namespace) -> MockFixtureRunner:
    if args.runner != "mock_fixture":
        raise HarnessInputError(
            "only --runner mock_fixture is implemented; real SDK runners are deferred"
        )
    if not args.fixture_dir:
        raise HarnessInputError("--fixture-dir is required when --runner mock_fixture")
    fixture_dir = Path(args.fixture_dir)
    if not fixture_dir.exists():
        raise HarnessInputError(f"fixture directory not found: {fixture_dir}")
    return MockFixtureRunner(fixture_dir)


def _extract_source_manifest_path(args: argparse.Namespace) -> Path:
    if args.source_manifest:
        return Path(args.source_manifest)
    if args.runner == "mock_fixture" and args.fixture_dir:
        fixture_manifest = Path(args.fixture_dir) / "source_manifest.yaml"
        if fixture_manifest.exists():
            return fixture_manifest
    raise HarnessInputError(
        "--source-manifest is required unless --runner mock_fixture can read "
        "source_manifest.yaml from --fixture-dir"
    )


def _extract_run_count(runs: int) -> int:
    if runs < 1 or runs > 7:
        raise HarnessInputError("--runs must be between 1 and 7")
    return runs


def _with_mock_extract_run_id(result: Any, run_id: str) -> Any:
    # MockFixtureRunner is deterministic; rewrite run IDs per extract pass so
    # each isolated run can be compacted with distinct provenance.
    return replace(
        result,
        run_id=run_id,
        audit_trace=[_event_with_run_id(event, run_id) for event in result.audit_trace],
        raw_trace=[_event_with_run_id(event, run_id) for event in result.raw_trace],
    )


def _extract_integrity_diagnostics_payload(
    run_id: str,
    integrity: Any,
) -> dict[str, Any]:
    diagnostics = [
        {
            "code": _extract_integrity_error_code(error),
            "severity": "high",
            "message": error,
            "location": {
                "run_id": run_id,
                "integrity_status": integrity.integrity_status,
            },
        }
        for error in integrity.errors
    ]
    return {
        "diagnostics": diagnostics,
        "summary": {
            "total": len(diagnostics),
            "high": len(diagnostics),
            "medium": 0,
            "low": 0,
            "informational": 0,
        },
        "generated_at": _now_iso(),
        "run_id": run_id,
        "integrity_status": integrity.integrity_status,
    }


def _extract_integrity_error_code(error: str) -> str:
    if error.startswith("rule_zero/") and ":" in error:
        return error.split(":", 1)[0].split("/", 1)[1]
    return "candidate_run_integrity_error"


def _event_with_run_id(event: Mapping[str, Any], run_id: str) -> dict[str, Any]:
    updated = dict(event)
    updated["run_id"] = run_id
    return updated


def _agent_trace_errors(events: Sequence[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, event in enumerate(events):
        errors.extend(
            f"agent_trace/{index}: {error}"
            for error in validate("agent_trace", event)
        )
    return errors


def _extract_invalid_input(
    args: argparse.Namespace,
    message: str,
    details: list[str] | None = None,
) -> CommandResult:
    sys.stderr.write(f"[assessment-harness] {message}\n")
    for detail in details or []:
        sys.stderr.write(f"  - {detail}\n")
    envelope = _build_envelope(
        status="invalid_input",
        exit_code=2,
        command="extract",
        next_actions=[{"type": "fix_input", "message": message}],
        input_error=message,
    )
    return CommandResult(envelope=envelope, exit_code=2)


# ---------------------------------------------------------------------------
# compact
# ---------------------------------------------------------------------------


def _cmd_compact(args: argparse.Namespace) -> CommandResult:
    try:
        candidate_paths = _compact_candidate_paths(args)
    except HarnessInputError as exc:
        return _compact_invalid_input(args, str(exc), exc.errors)
    try:
        candidate_runs = [
            load_validated(candidate_path, "candidates")
            for candidate_path in candidate_paths
        ]
        policy_doc = load_policy(Path(args.policy))
        review_queue = _load_review_queue(
            Path(args.review_queue_in) if args.review_queue_in else None
        )
    except HarnessInputError as exc:
        return _compact_invalid_input(args, str(exc), exc.errors)

    invalid_run_entries = _invalid_run_review_entries(candidate_runs, candidate_paths)
    try:
        compacted = compact_validated_candidates(candidate_runs, policy_doc)
    except CompactingInputError as exc:
        return _compact_invalid_input(args, str(exc))

    compacting_errors = validate("compacting", compacted)
    if compacting_errors:
        return _compact_invalid_input(
            args,
            "generated compacting output failed schema validation",
            compacting_errors,
        )

    out_dir = Path(args.out_dir)
    spec_items_path = out_dir / "spec_items.yaml"
    rubric_items_path = out_dir / "rubric_items.yaml"
    trace_links_path = out_dir / "trace_links.yaml"
    id_map_path = out_dir / "id_map.yaml"
    review_queue_path = (
        Path(args.review_queue_out)
        if args.review_queue_out
        else out_dir / "review_queue.json"
    )

    _append_review_queue_entries(review_queue, invalid_run_entries)
    review_queue["generated_at"] = _now_iso()
    review_queue_errors = validate("review_queue", review_queue)
    if review_queue_errors:
        return _compact_invalid_input(
            args,
            "generated review queue failed schema validation",
            review_queue_errors,
        )

    _write_yaml(spec_items_path, {"spec_items": compacted["spec_items"]})
    _write_yaml(rubric_items_path, {"rubric_items": compacted["rubric_items"]})
    _write_yaml(trace_links_path, {"trace_links": compacted["trace_links"]})
    _write_yaml(id_map_path, {"id_map": compacted["id_map"]})
    _write_json(review_queue_path, review_queue)

    valid_run_count = _valid_candidate_run_count(candidate_runs)
    envelope = _build_envelope(
        status="success",
        exit_code=0,
        command="compact",
        next_actions=[],
        compacted_dir=str(out_dir),
        spec_items_path=str(spec_items_path),
        rubric_items_path=str(rubric_items_path),
        trace_links_path=str(trace_links_path),
        id_map_path=str(id_map_path),
        review_queue_path=str(review_queue_path),
        review_queue_count=len(review_queue["review_queue"]),
        valid_run_count=valid_run_count,
        excluded_run_count=len(invalid_run_entries),
    )
    return CommandResult(envelope=envelope, exit_code=0)


def _compact_invalid_input(
    args: argparse.Namespace,
    message: str,
    details: list[str] | None = None,
) -> CommandResult:
    sys.stderr.write(f"[assessment-harness] {message}\n")
    for detail in details or []:
        sys.stderr.write(f"  - {detail}\n")
    envelope = _build_envelope(
        status="invalid_input",
        exit_code=2,
        command="compact",
        next_actions=[{"type": "fix_input", "message": message}],
        input_error=message,
    )
    return CommandResult(envelope=envelope, exit_code=2)


def _load_review_queue(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"review_queue": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HarnessInputError(f"cannot read review queue: {exc}") from exc
    errors = validate("review_queue", payload)
    if errors:
        raise HarnessInputError(
            f"{path}: schema validation failed (review_queue)",
            errors=errors,
        )
    preserved = dict(payload)
    preserved["review_queue"] = list(payload.get("review_queue", []))
    return preserved


def _compact_candidate_paths(args: argparse.Namespace) -> list[Path]:
    if args.candidates and args.runs_dir:
        raise HarnessInputError("compact accepts either --runs-dir or --candidates, not both")
    if args.runs_dir:
        runs_dir = Path(args.runs_dir)
        if not runs_dir.exists():
            raise HarnessInputError(f"runs directory not found: {runs_dir}")
        candidate_paths = sorted(runs_dir.glob("*/candidates.yaml"))
        candidate_paths.extend(sorted(runs_dir.glob("*.candidates.yaml")))
        if not candidate_paths:
            raise HarnessInputError(f"no candidate artifacts found in {runs_dir}")
        return candidate_paths
    if args.candidates:
        return [Path(path) for path in args.candidates]
    raise HarnessInputError("compact requires --runs-dir or --candidates")


def _invalid_run_review_entries(
    candidate_runs: list[dict[str, Any]],
    candidate_paths: list[Path],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for index, (candidate_run, candidate_path) in enumerate(
        zip(candidate_runs, candidate_paths, strict=True),
        start=1,
    ):
        run_ids = _candidate_run_ids(candidate_run)
        validated_run_id = validated_candidate_run_id(candidate_run)
        if validated_run_id is not None:
            continue
        statuses = _candidate_run_statuses(candidate_run)
        run_label = sorted(run_ids)[0] if run_ids else candidate_path.stem
        entries.append(
            {
                "entry_id": f"invalid_run_{index}",
                "type": "invalid_run",
                "target": {
                    "candidate_path": str(candidate_path),
                    "integrity_statuses": sorted(statuses),
                },
                "reason": (
                    "Candidate run was excluded from compacting because not "
                    "all candidate entries are validated."
                ),
                "related_runs": sorted(run_ids) or [run_label],
                "status": "open",
            }
        )
    return entries


def _append_review_queue_entries(
    review_queue: dict[str, Any],
    new_entries: list[dict[str, Any]],
) -> None:
    existing_ids = {
        entry.get("entry_id")
        for entry in review_queue.get("review_queue", [])
        if isinstance(entry, dict)
    }
    for entry in new_entries:
        if entry["entry_id"] in existing_ids:
            continue
        review_queue["review_queue"].append(entry)
        existing_ids.add(entry["entry_id"])


def _candidate_run_statuses(candidate_run: dict[str, Any]) -> set[str]:
    statuses: set[str] = set()
    for section in (
        "spec_item_candidates",
        "rubric_item_candidates",
        "trace_link_candidates",
    ):
        for entry in candidate_run.get(section, []):
            if isinstance(entry, dict):
                statuses.add(str(entry.get("integrity_status", "<missing>")))
    return statuses


def _candidate_run_ids(candidate_run: dict[str, Any]) -> set[str]:
    run_ids: set[str] = set()
    for section in (
        "spec_item_candidates",
        "rubric_item_candidates",
        "trace_link_candidates",
    ):
        for entry in candidate_run.get(section, []):
            if isinstance(entry, dict) and isinstance(entry.get("agent_run_id"), str):
                run_ids.add(entry["agent_run_id"])
    return run_ids


def _valid_candidate_run_count(candidate_runs: list[dict[str, Any]]) -> int:
    return sum(
        1 for candidate_run in candidate_runs if validated_candidate_run_id(candidate_run)
    )


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------


def _cmd_verify(args: argparse.Namespace) -> CommandResult:
    try:
        run_count = _extract_run_count(args.runs)
        compacted_dir = Path(args.compacted_dir)
        load_validated(compacted_dir / "spec_items.yaml", "spec_items")
        load_validated(compacted_dir / "rubric_items.yaml", "rubric_items")
        trace_doc = load_validated(compacted_dir / "trace_links.yaml", "trace_links")
        id_map_doc = _load_verify_id_map(compacted_dir)
        load_source_snapshot(Path(args.source_manifest))
        load_policy(Path(args.policy))
        review_queue = _load_review_queue(
            Path(args.review_queue_in) if args.review_queue_in else None
        )
        _validate_verify_runner(args.runner)
    except HarnessInputError as exc:
        return _verify_invalid_input(args, str(exc), exc.errors)

    try:
        trace_link_ids = _resolve_verify_trace_link_ids(trace_doc, id_map_doc)
    except HarnessInputError as exc:
        return _verify_invalid_input(args, str(exc), exc.errors)

    semantic_doc = _mock_semantic_verifications(trace_doc, trace_link_ids, run_count)
    semantic_errors = validate("semantic_verifications", semantic_doc)
    if semantic_errors:
        return _verify_invalid_input(
            args,
            "generated semantic verifications failed schema validation",
            semantic_errors,
        )

    pending_entries = _ai_judgement_pending_entries(trace_doc, trace_link_ids)
    _append_review_queue_entries(review_queue, pending_entries)
    review_queue["generated_at"] = _now_iso()
    review_queue_errors = validate("review_queue", review_queue)
    if review_queue_errors:
        return _verify_invalid_input(
            args,
            "generated review queue failed schema validation",
            review_queue_errors,
        )

    out_dir = Path(args.out_dir)
    semantic_path = out_dir / "semantic_verifications.yaml"
    review_queue_path = (
        Path(args.review_queue_out)
        if args.review_queue_out
        else out_dir / "review_queue.json"
    )
    _write_yaml(semantic_path, semantic_doc)
    _write_json(review_queue_path, review_queue)

    envelope = _build_envelope(
        status="success",
        exit_code=0,
        command="verify",
        next_actions=[],
        compacted_dir=str(compacted_dir),
        semantic_verifications_path=str(semantic_path),
        semantic_verification_count=len(semantic_doc["semantic_verifications"]),
        review_queue_path=str(review_queue_path),
        review_queue_count=len(review_queue["review_queue"]),
        run_count=run_count,
        runner=args.runner,
        source_manifest_path=str(args.source_manifest),
    )
    return CommandResult(envelope=envelope, exit_code=0)


def _validate_verify_runner(runner: str) -> None:
    if runner != "mock_fixture":
        raise HarnessInputError(
            "only --runner mock_fixture is implemented for verify; "
            "real SDK verifier runners are deferred"
        )


def _load_verify_id_map(compacted_dir: Path) -> dict[str, Any] | None:
    id_map_path = compacted_dir / "id_map.yaml"
    if not id_map_path.exists():
        return None
    return load_validated(id_map_path, "id_map")


def _mock_semantic_verifications(
    trace_doc: Mapping[str, Any],
    trace_link_ids: Sequence[str],
    run_count: int,
) -> dict[str, Any]:
    verify_run_ids = [f"verify_{index:03d}" for index in range(1, run_count + 1)]
    proposals: list[dict[str, Any]] = []
    for trace_index, trace_link in enumerate(trace_doc.get("trace_links", [])):
        if not isinstance(trace_link, Mapping):
            continue
        if not _has_ai_judgement_evidence(trace_link):
            continue
        source_refs = _ai_judgement_source_refs(trace_link)
        proposals.append(
            {
                "trace_link_id": trace_link_ids[trace_index],
                "status_proposal": "agent_uncertain",
                "rationale": _mock_semantic_rationale(source_refs),
                "source_refs": source_refs,
                "support": {
                    "total_valid_runs": run_count,
                    "found_in_runs": verify_run_ids,
                },
                "variants": [],
            }
        )
    return {"semantic_verifications": proposals}


def _has_ai_judgement_evidence(trace_link: Mapping[str, Any]) -> bool:
    for quote in trace_link.get("evidence_quotes", []):
        if isinstance(quote, Mapping) and quote.get("verification_mode") == "ai_judgement":
            return True
    return False


def _mock_semantic_rationale(source_refs: Sequence[Mapping[str, Any]]) -> str:
    if source_refs:
        return (
            "Mock verifier records ai_judgement evidence for human review "
            "without rewriting the compacted trace link."
        )
    return (
        "No quote-level source_ref was available for this ai_judgement evidence; "
        "mock verifier leaves the link agent_uncertain for human review."
    )


def _ai_judgement_source_refs(trace_link: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for quote in trace_link.get("evidence_quotes", []):
        if not isinstance(quote, Mapping):
            continue
        if quote.get("verification_mode") != "ai_judgement":
            continue
        source_ref = quote.get("source_ref")
        if isinstance(source_ref, Mapping):
            ref = dict(source_ref)
            if isinstance(quote.get("quote"), str) and "quote" not in ref:
                ref["quote"] = quote["quote"]
            refs.append(ref)
    return refs


def _ai_judgement_pending_entries(
    trace_doc: Mapping[str, Any],
    trace_link_ids: Sequence[str],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for trace_index, trace_link in enumerate(trace_doc.get("trace_links", [])):
        if not isinstance(trace_link, Mapping):
            continue
        trace_link_id = trace_link_ids[trace_index]
        related_runs = _trace_related_runs(trace_link)
        for quote_index, quote in enumerate(trace_link.get("evidence_quotes", [])):
            if not isinstance(quote, Mapping):
                continue
            if quote.get("verification_mode") != "ai_judgement":
                continue
            entries.append(
                {
                    "entry_id": f"ai_judgement_pending_{trace_link_id}_{quote_index}",
                    "type": "ai_judgement_pending",
                    "target": {
                        "trace_link_id": trace_link_id,
                        "rubric_id": trace_link.get("rubric_id"),
                        "spec_ids": list(trace_link.get("spec_ids", [])),
                        "evidence_quote_index": quote_index,
                    },
                    "reason": (
                        "verification_mode=ai_judgement; semantic disclosure "
                        "check required."
                    ),
                    "related_runs": related_runs,
                    "status": "open",
                }
            )
    return entries


def _resolve_verify_trace_link_ids(
    trace_doc: Mapping[str, Any],
    id_map_doc: Mapping[str, Any] | None,
) -> list[str]:
    trace_links = trace_doc.get("trace_links", [])
    if not isinstance(trace_links, list):
        return []
    return [
        _trace_link_id(trace_link, index, id_map_doc)
        for index, trace_link in enumerate(trace_links, start=1)
        if isinstance(trace_link, Mapping)
    ]


def _trace_link_id(
    trace_link: Mapping[str, Any],
    trace_index: int,
    id_map_doc: Mapping[str, Any] | None,
) -> str:
    if id_map_doc is not None:
        id_from_map = _trace_link_id_from_id_map(trace_link, id_map_doc)
        if id_from_map is not None:
            return id_from_map
        if _trace_link_has_compacting_variants(trace_link):
            raise HarnessInputError(
                "cannot resolve trace_link_id from id_map.yaml for trace link "
                f"at index {trace_index}"
            )
    trace_id = trace_link.get("id")
    if isinstance(trace_id, str) and trace_id:
        return trace_id
    return f"T{trace_index}"


def _trace_link_id_from_id_map(
    trace_link: Mapping[str, Any],
    id_map_doc: Mapping[str, Any],
) -> str | None:
    variant_refs = _trace_variant_refs(trace_link)
    if not variant_refs:
        return None
    for entry in id_map_doc.get("id_map", []):
        if not isinstance(entry, Mapping) or entry.get("entity_type") != "trace_link":
            continue
        canonical_id = entry.get("canonical_id")
        if not isinstance(canonical_id, str):
            continue
        for run_ref in entry.get("run_refs", []):
            if not isinstance(run_ref, Mapping):
                continue
            ref = (str(run_ref.get("run_id")), str(run_ref.get("local_id")))
            if ref in variant_refs:
                return canonical_id
    return None


def _trace_variant_refs(trace_link: Mapping[str, Any]) -> set[tuple[str, str]]:
    refs: set[tuple[str, str]] = set()
    for variant in trace_link.get("variants", []):
        if not isinstance(variant, Mapping):
            continue
        run_id = variant.get("run_id")
        candidate_id = variant.get("candidate_id")
        if isinstance(run_id, str) and isinstance(candidate_id, str):
            refs.add((run_id, candidate_id))
    return refs


def _trace_link_has_compacting_variants(trace_link: Mapping[str, Any]) -> bool:
    return bool(_trace_variant_refs(trace_link))


def _trace_related_runs(trace_link: Mapping[str, Any]) -> list[str]:
    support = trace_link.get("support")
    if isinstance(support, Mapping) and isinstance(support.get("found_in_runs"), list):
        return [str(run_id) for run_id in support["found_in_runs"]]
    related: set[str] = set()
    for source in trace_link.get("sources", []):
        if isinstance(source, Mapping) and isinstance(source.get("run_id"), str):
            related.add(source["run_id"])
    return sorted(related)


def _verify_invalid_input(
    args: argparse.Namespace,
    message: str,
    details: list[str] | None = None,
) -> CommandResult:
    sys.stderr.write(f"[assessment-harness] {message}\n")
    for detail in details or []:
        sys.stderr.write(f"  - {detail}\n")
    envelope = _build_envelope(
        status="invalid_input",
        exit_code=2,
        command="verify",
        next_actions=[{"type": "fix_input", "message": message}],
        input_error=message,
    )
    return CommandResult(envelope=envelope, exit_code=2)


# ---------------------------------------------------------------------------
# schema
# ---------------------------------------------------------------------------


COMMAND_CONTRACTS: dict[str, dict[str, Any]] = {
    "extract": {
        "stable_core": STABLE_CORE_FIELDS,
        "informational": [
            "runs_dir",
            "run_dirs",
            "run_count",
            "valid_run_count",
            "invalid_run_count",
            "runner",
            "source_manifest_path",
            "input_error",
        ],
        "exit_codes": {
            "0": "candidate runs and agent traces were written under --out-dir.",
            "2": "extract input or runner configuration is invalid.",
            "3": "internal error.",
        },
        "next_actions_types": ["fix_input"],
    },
    "compact": {
        "stable_core": STABLE_CORE_FIELDS,
        "informational": [
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
        ],
        "exit_codes": {
            "0": "validated candidate runs compacted into canonical YAML artifacts.",
            "2": "candidate, policy, or review queue input is invalid.",
            "3": "internal error.",
        },
        "next_actions_types": ["fix_input"],
    },
    "verify": {
        "stable_core": STABLE_CORE_FIELDS,
        "informational": [
            "compacted_dir",
            "semantic_verifications_path",
            "semantic_verification_count",
            "review_queue_path",
            "review_queue_count",
            "run_count",
            "runner",
            "source_manifest_path",
            "input_error",
        ],
        "exit_codes": {
            "0": "semantic verification proposals and review queue entries were written.",
            "2": "compacted inputs, source manifest, policy, or runner is invalid.",
            "3": "internal error.",
        },
        "next_actions_types": ["fix_input"],
    },
    "check": {
        "stable_core": STABLE_CORE_FIELDS,
        "informational": [
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
        ],
        "exit_codes": {
            "0": (
                "no blocking outcome; status=success when no provisional "
                "findings or status=provisional_findings when Rule 1+ raises "
                "findings pending final review."
            ),
            "1": "reserved for `gate` confirmed blocking finding after final review.",
            "2": "input or Rule 0 reference integrity failure (invalid_input).",
            "3": "internal error.",
        },
        "next_actions_types": [
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
        ],
    },
    "report": {
        "stable_core": STABLE_CORE_FIELDS,
        "informational": ["report_path"],
        "exit_codes": {
            "0": "report rendered.",
            "2": "input findings/diagnostics could not be read.",
            "3": "internal error.",
        },
        "next_actions_types": [],
    },
    "review": {
        "stable_core": STABLE_CORE_FIELDS,
        "informational": ["review_path", "decision_count", "input_error"],
        "exit_codes": {
            "0": "draft final review record written.",
            "2": "findings input could not be read, overwritten, or converted to review keys.",
            "3": "internal error.",
        },
        "next_actions_types": [],
    },
    "schema": {
        "stable_core": STABLE_CORE_FIELDS,
        "informational": ["contract"],
        "exit_codes": {
            "0": "contract returned.",
            "2": "unknown command name.",
        },
        "next_actions_types": [],
    },
    "gate": {
        "stable_core": STABLE_CORE_FIELDS,
        "informational": [
            "final_review_path",
            "findings_path",
            "blocking_count",
            "confirmed_finding_count",
            "dismissed_finding_count",
            "pending_decision_count",
            "blocking_findings",
            "input_error",
        ],
        "exit_codes": {
            "0": "status=success or pending_review; no confirmed blocking finding.",
            "1": "confirmed blocking finding exists after final review.",
            "2": "final review or findings input is invalid.",
            "3": "internal error.",
        },
        "next_actions_types": [
            "complete_final_review",
            "fix_final_review",
            "revise_assessment",
        ],
    },
}


def _cmd_schema(args: argparse.Namespace) -> CommandResult:
    command = args.command_name
    if command not in COMMAND_CONTRACTS:
        sys.stderr.write(
            f"[assessment-harness] unknown command: {command!r}. "
            f"Known: {sorted(COMMAND_CONTRACTS)}\n"
        )
        envelope = _build_envelope(
            status="invalid_input",
            exit_code=2,
            command="schema",
            next_actions=[
                {"type": "list_known_commands", "known": sorted(COMMAND_CONTRACTS)}
            ],
        )
        return CommandResult(envelope=envelope, exit_code=2)

    contract = dict(COMMAND_CONTRACTS[command])
    contract["command"] = command
    envelope = _build_envelope(
        status="success",
        exit_code=0,
        command="schema",
        next_actions=[],
        contract=contract,
    )
    return CommandResult(envelope=envelope, exit_code=0)


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def _cmd_report(args: argparse.Namespace) -> CommandResult:
    try:
        findings_doc = json.loads(Path(args.findings).read_text(encoding="utf-8"))
        diagnostics_doc = json.loads(Path(args.diagnostics).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"[assessment-harness] cannot read inputs: {exc}\n")
        envelope = _build_envelope(
            status="invalid_input",
            exit_code=2,
            command="report",
            next_actions=[{"type": "fix_input", "message": str(exc)}],
        )
        return CommandResult(envelope=envelope, exit_code=2)

    text = render_markdown(findings_doc, diagnostics_doc)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")

    envelope = _build_envelope(
        status="success",
        exit_code=0,
        command="report",
        next_actions=[],
        report_path=str(out_path),
    )
    return CommandResult(envelope=envelope, exit_code=0)


# ---------------------------------------------------------------------------
# review
# ---------------------------------------------------------------------------


def _review_invalid_input(
    args: argparse.Namespace, message: str, details: list[str] | None = None
) -> CommandResult:
    sys.stderr.write(f"[assessment-harness] {message}\n")
    for detail in details or []:
        sys.stderr.write(f"  - {detail}\n")
    envelope = _build_envelope(
        status="invalid_input",
        exit_code=2,
        command="review",
        next_actions=[{"type": "fix_input", "message": message}],
        input_error=message,
    )
    return CommandResult(envelope=envelope, exit_code=2)


def _review_target_key_for_finding(finding: dict[str, Any]) -> dict[str, Any]:
    finding_type = finding.get("type")
    fields = FINDING_KEY_FIELDS.get(finding_type)
    if fields is None:
        raise HarnessInputError(f"unknown finding type for review: {finding_type!r}")
    target_key: dict[str, Any] = {}
    for field in fields:
        if field not in finding:
            raise HarnessInputError(
                f"finding {finding_type!r} missing gate key field {field!r}"
            )
        target_key[field] = finding[field]
    return target_key


def _optional_input_path(args: argparse.Namespace, name: str) -> str | None:
    value = getattr(args, name)
    if value is None:
        return None
    return str(Path(value).resolve())


def _cmd_review(args: argparse.Namespace) -> CommandResult:
    findings_path = Path(args.findings)
    try:
        findings_doc = json.loads(findings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _review_invalid_input(args, f"cannot read findings: {exc}")
    finding_errors = validate("findings", findings_doc)
    if finding_errors:
        return _review_invalid_input(
            args,
            f"{findings_path}: schema validation failed (findings)",
            finding_errors,
        )
    if findings_doc.get("status") not in {"success", "provisional_findings"}:
        return _review_invalid_input(
            args,
            (
                "review requires findings.status to be success or "
                "provisional_findings"
            ),
        )

    decisions: list[dict[str, Any]] = []
    try:
        for finding in findings_doc.get("findings", []):
            decisions.append(
                {
                    "target_type": "finding",
                    "target_key": _review_target_key_for_finding(finding),
                    "action": "hold",
                    "note": (
                        "Draft hold generated by review; final reviewer must "
                        "choose accept, override, hold, or rerun_requested."
                    ),
                }
            )
    except HarnessInputError as exc:
        return _review_invalid_input(args, str(exc), exc.errors)

    generated_at = _now_iso()
    inputs = {
        "findings_path": str(findings_path.resolve()),
    }
    for arg_name, input_key in (
        ("compacted_dir", "compacted_dir"),
        ("diagnostics", "diagnostics_path"),
        ("semantic_verifications", "semantic_verifications_path"),
        ("review_queue", "review_queue_path"),
        ("report", "report_path"),
    ):
        value = _optional_input_path(args, arg_name)
        if value is not None:
            inputs[input_key] = value

    review_doc = {
        "review_id": f"review_{generated_at.replace('-', '').replace(':', '')}",
        "reviewer": args.reviewer,
        "reviewed_at": generated_at,
        "inputs": inputs,
        "decisions": decisions,
        "drift_observations": [],
    }
    review_errors = validate("final_review", review_doc)
    if review_errors:
        return _review_invalid_input(
            args,
            "generated final review failed schema validation",
            review_errors,
        )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    review_path = out_dir / "review.yaml"
    if review_path.exists() and not args.force:
        return _review_invalid_input(
            args,
            (
                f"review draft already exists: {review_path}. Pass --force to "
                "overwrite, or choose a new --out-dir for a separate draft."
            ),
        )
    review_path.write_text(
        yaml.safe_dump(review_doc, sort_keys=False),
        encoding="utf-8",
    )
    envelope = _build_envelope(
        status="success",
        exit_code=0,
        command="review",
        next_actions=[],
        review_path=str(review_path),
        decision_count=len(decisions),
    )
    return CommandResult(envelope=envelope, exit_code=0)


# ---------------------------------------------------------------------------
# gate
# ---------------------------------------------------------------------------


BLOCKING_CONFIRMED_FINDING_TYPES = {
    "orphan_scored_rubric_item",
    "optionality_mismatch",
    "mandatory_spec_bonus_only_traced",
}

FINDING_KEY_FIELDS: dict[str, tuple[str, ...]] = {
    "possible_orphan_scored_rubric_item": ("type", "rubric_id"),
    "unconfirmed_trace_coverage": ("type", "rubric_id"),
    "orphan_bonus_rubric_item": ("type", "rubric_id"),
    "uncovered_must_spec_item": ("type", "spec_id"),
    "optionality_mismatch": ("type", "rubric_id"),
    "double_scored_spec": (
        "type",
        "spec_id",
        "scored_rubric_id",
        "bonus_rubric_id",
    ),
    "bonus_grades_mandatory_only": ("type", "rubric_id"),
    "mandatory_spec_bonus_only_traced": ("type", "spec_id"),
}


def _resolve_relative(base_file: Path, candidate: str) -> Path:
    path = Path(candidate)
    if path.is_absolute():
        return path
    return (base_file.parent / path).resolve()


def _finding_key(finding: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    finding_type = finding.get("type")
    fields = FINDING_KEY_FIELDS.get(finding_type)
    if fields is None:
        fields = tuple(
            field
            for field in (
                "type",
                "rubric_id",
                "spec_id",
                "scored_rubric_id",
                "bonus_rubric_id",
            )
            if field in finding
        )
    return tuple((field, finding.get(field)) for field in fields)


def _decision_key(target_key: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    finding_type = target_key.get("type")
    fields = FINDING_KEY_FIELDS.get(finding_type)
    if fields is None:
        fields = tuple(sorted(target_key))
    return tuple((field, target_key.get(field)) for field in fields)


def _finding_decision_key_errors(target_key: dict[str, Any]) -> list[str]:
    finding_type = target_key.get("type")
    fields = FINDING_KEY_FIELDS.get(finding_type)
    if fields is None:
        return [f"unknown finding type in target_key: {finding_type!r}"]
    required = set(fields)
    actual = set(target_key)
    missing = sorted(required - actual)
    extra = sorted(actual - required)
    errors: list[str] = []
    if missing:
        errors.append(f"target_key for {finding_type!r} missing fields: {missing}")
    if extra:
        errors.append(
            f"target_key for {finding_type!r} has non-identity fields: {extra}"
        )
    return errors


def _confirmed_finding_from(
    finding: dict[str, Any], decision: dict[str, Any]
) -> dict[str, Any]:
    confirmed = dict(finding)
    if finding.get("type") in {
        "possible_orphan_scored_rubric_item",
        "unconfirmed_trace_coverage",
    }:
        confirmed["type"] = "orphan_scored_rubric_item"
        confirmed["severity"] = "high"
        rubric_id = finding.get("rubric_id")
        confirmed["message"] = (
            f"scored rubric_item {rubric_id!r} is confirmed orphaned after "
            "final review."
        )
    confirmed["decision_status"] = "confirmed"
    confirmed["review_decision"] = {
        "action": decision.get("action"),
        "note": decision.get("note"),
    }
    return confirmed


def _dismissed_finding_from(
    finding: dict[str, Any], decision: dict[str, Any]
) -> dict[str, Any]:
    dismissed = dict(finding)
    dismissed["decision_status"] = "dismissed"
    dismissed["review_decision"] = {
        "action": decision.get("action"),
        "note": decision.get("note"),
    }
    if "override_payload" in decision:
        dismissed["review_decision"]["override_payload"] = decision["override_payload"]
    return dismissed


def _gate_invalid_input(
    args: argparse.Namespace, message: str, details: list[str] | None = None
) -> CommandResult:
    sys.stderr.write(f"[assessment-harness] {message}\n")
    for detail in details or []:
        sys.stderr.write(f"  - {detail}\n")
    envelope = _build_envelope(
        status="invalid_input",
        exit_code=2,
        command="gate",
        next_actions=[{"type": "fix_final_review", "message": message}],
        final_review_path=str(args.final_review),
        blocking_count=0,
        input_error=message,
    )
    return CommandResult(envelope=envelope, exit_code=2)


def _cmd_gate(args: argparse.Namespace) -> CommandResult:
    final_review_path = Path(args.final_review)
    try:
        review_doc = load_validated(final_review_path, "final_review")
    except HarnessInputError as exc:
        return _gate_invalid_input(args, str(exc), exc.errors)

    findings_path = _resolve_relative(
        final_review_path, review_doc["inputs"]["findings_path"]
    )
    try:
        findings_doc = json.loads(findings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _gate_invalid_input(
            args,
            f"cannot read findings referenced by final review: {exc}",
        )
    finding_errors = validate("findings", findings_doc)
    if finding_errors:
        return _gate_invalid_input(
            args,
            f"{findings_path}: schema validation failed (findings)",
            finding_errors,
        )

    findings = findings_doc.get("findings", [])
    finding_by_key: dict[tuple[tuple[str, Any], ...], dict[str, Any]] = {}
    for finding in findings:
        key = _finding_key(finding)
        if key in finding_by_key:
            return _gate_invalid_input(
                args,
                "findings.json contains duplicate gate target keys",
                [str(dict(key))],
            )
        finding_by_key[key] = finding

    finding_decisions = [
        decision
        for decision in review_doc.get("decisions", [])
        if decision.get("target_type") == "finding"
    ]
    decisions_by_key: dict[tuple[tuple[str, Any], ...], dict[str, Any]] = {}
    for decision in finding_decisions:
        target_key = decision.get("target_key", {})
        key_errors = _finding_decision_key_errors(target_key)
        if key_errors:
            return _gate_invalid_input(
                args,
                "final review finding decision target_key is not minimal",
                key_errors,
            )
        key = _decision_key(target_key)
        if key in decisions_by_key:
            return _gate_invalid_input(
                args,
                "final review contains duplicate decisions for one finding",
                [str(dict(key))],
            )
        if key not in finding_by_key:
            return _gate_invalid_input(
                args,
                "final review contains a finding decision that matches no finding",
                [str(dict(key))],
            )
        decisions_by_key[key] = decision

    pending: list[dict[str, Any]] = []
    confirmed: list[dict[str, Any]] = []
    dismissed: list[dict[str, Any]] = []
    for key, finding in finding_by_key.items():
        decision = decisions_by_key.get(key)
        if decision is None:
            pending.append(
                {
                    "reason": "missing_final_review_decision",
                    "target_key": dict(key),
                }
            )
            continue
        action = decision.get("action")
        if action in {"hold", "rerun_requested"}:
            pending.append(
                {
                    "reason": action,
                    "target_key": dict(key),
                }
            )
        elif action == "accept":
            confirmed.append(_confirmed_finding_from(finding, decision))
        elif action == "override":
            dismissed.append(_dismissed_finding_from(finding, decision))

    if pending:
        envelope = _build_envelope(
            status="pending_review",
            exit_code=0,
            command="gate",
            next_actions=[
                {
                    "type": "complete_final_review",
                    "pending_decision_count": len(pending),
                }
            ],
            final_review_path=str(final_review_path),
            findings_path=str(findings_path),
            blocking_count=0,
            confirmed_finding_count=len(confirmed),
            dismissed_finding_count=len(dismissed),
            pending_decision_count=len(pending),
        )
        return CommandResult(envelope=envelope, exit_code=0)

    blocking_findings = [
        finding
        for finding in confirmed
        if finding.get("type") in BLOCKING_CONFIRMED_FINDING_TYPES
    ]
    blocking_count = len(blocking_findings)
    if blocking_count:
        envelope = _build_envelope(
            status="fail",
            exit_code=1,
            command="gate",
            next_actions=[
                {
                    "type": "revise_assessment",
                    "blocking_count": blocking_count,
                }
            ],
            final_review_path=str(final_review_path),
            findings_path=str(findings_path),
            blocking_count=blocking_count,
            confirmed_finding_count=len(confirmed),
            dismissed_finding_count=len(dismissed),
            pending_decision_count=0,
            blocking_findings=blocking_findings,
        )
        return CommandResult(envelope=envelope, exit_code=1)

    envelope = _build_envelope(
        status="success",
        exit_code=0,
        command="gate",
        next_actions=[],
        final_review_path=str(final_review_path),
        findings_path=str(findings_path),
        blocking_count=0,
        confirmed_finding_count=len(confirmed),
        dismissed_finding_count=len(dismissed),
        pending_decision_count=0,
    )
    return CommandResult(envelope=envelope, exit_code=0)


# ---------------------------------------------------------------------------
# envelope assembly
# ---------------------------------------------------------------------------


def _build_envelope(
    *,
    status: str,
    exit_code: int,
    command: str,
    next_actions: list[dict[str, Any]],
    **informational: Any,
) -> dict[str, Any]:
    envelope: dict[str, Any] = {
        "status": status,
        "exit_code": exit_code,
        "command": command,
        "next_actions": list(next_actions),
    }
    for key, value in informational.items():
        if value is None:
            continue
        envelope[key] = value
    _ensure_envelope_valid(envelope)
    return envelope


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------


def _add_output_arg(p: argparse.ArgumentParser, *, root: bool) -> None:
    """Accept ``--output`` both before and after the subcommand.

    Root sets the default (``text``). Subparsers use ``SUPPRESS`` so that
    omitting ``--output`` on the subcommand leaves the root value intact, but
    passing it on the subcommand overrides the root value. Both invocation
    forms (``--output json check ...`` and ``check ... --output json``) work.
    """
    p.add_argument(
        "--output",
        choices=["text", "json"],
        default="text" if root else argparse.SUPPRESS,
        dest="output",
        help="output format on stdout (default: text)",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="assessment-harness",
        description="Assessment Spec Harness PoC (Phase 0).",
    )
    _add_output_arg(parser, root=True)
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_check = sub.add_parser(
        "check",
        help="run deterministic checks over compacted YAML and emit findings/diagnostics JSON.",
    )
    _add_output_arg(p_check, root=False)
    p_check.add_argument("--spec-items", required=True)
    p_check.add_argument("--rubric-items", required=True)
    p_check.add_argument("--trace-links", required=True)
    p_check.add_argument(
        "--source-manifest",
        default=None,
        help=(
            "required: path to the immutable source snapshot manifest "
            "(plan §5.0). Omitting it returns invalid_input / exit 2 with "
            "diagnostic source_manifest_required."
        ),
    )
    p_check.add_argument("--policy", default=None)
    p_check.add_argument("--out", required=True, help="findings.json output path")
    p_check.add_argument(
        "--diagnostics-out",
        required=True,
        help="integrity_diagnostics.json output path",
    )
    p_check.add_argument(
        "--review-queue-out",
        default=None,
        help=(
            "review_queue.json output path for deterministic lint safeguards; "
            "defaults to review_queue.json beside --out when such entries exist"
        ),
    )

    p_extract = sub.add_parser(
        "extract",
        help="run candidate extraction into isolated run directories.",
    )
    _add_output_arg(p_extract, root=False)
    p_extract.add_argument("--spec", required=True)
    p_extract.add_argument("--rubric", required=True)
    p_extract.add_argument(
        "--source-manifest",
        default=None,
        help="immutable source snapshot manifest used for candidate grounding checks",
    )
    p_extract.add_argument("--runner", required=True)
    p_extract.add_argument(
        "--fixture-dir",
        default=None,
        help="fixture directory to replay when --runner mock_fixture is used",
    )
    p_extract.add_argument("--runs", type=int, default=3)
    p_extract.add_argument("--policy", default=None)
    p_extract.add_argument("--out-dir", required=True)

    p_compact = sub.add_parser(
        "compact",
        help="compact validated candidate run artifacts into canonical YAML.",
    )
    _add_output_arg(p_compact, root=False)
    p_compact.add_argument(
        "--runs-dir",
        default=None,
        help=(
            "directory produced by extract; reads */candidates.yaml and "
            "*.candidates.yaml files in sorted order"
        ),
    )
    p_compact.add_argument(
        "--candidates",
        nargs="+",
        default=None,
        help="one or more candidate run artifact YAML files",
    )
    p_compact.add_argument("--policy", required=True)
    p_compact.add_argument("--out-dir", required=True)
    p_compact.add_argument(
        "--review-queue-in",
        default=None,
        help="existing review_queue.json to preserve and append to",
    )
    p_compact.add_argument(
        "--review-queue-out",
        default=None,
        help="review_queue.json output path (defaults to --out-dir/review_queue.json)",
    )

    p_verify = sub.add_parser(
        "verify",
        help="write read-only semantic verification proposals for compacted trace links.",
    )
    _add_output_arg(p_verify, root=False)
    p_verify.add_argument("--compacted-dir", required=True)
    p_verify.add_argument("--source-manifest", required=True)
    p_verify.add_argument("--runner", required=True)
    p_verify.add_argument("--runs", type=int, default=3)
    p_verify.add_argument("--policy", required=True)
    p_verify.add_argument("--out-dir", required=True)
    p_verify.add_argument(
        "--review-queue-in",
        default=None,
        help="existing review_queue.json to preserve and append to",
    )
    p_verify.add_argument(
        "--review-queue-out",
        default=None,
        help="review_queue.json output path (defaults to --out-dir/review_queue.json)",
    )

    p_schema = sub.add_parser(
        "schema",
        help="return the stable contract for a CLI subcommand.",
    )
    _add_output_arg(p_schema, root=False)
    p_schema.add_argument("--command", dest="command_name", required=True)

    p_report = sub.add_parser(
        "report",
        help="render findings + diagnostics into Markdown.",
    )
    _add_output_arg(p_report, root=False)
    p_report.add_argument("--findings", required=True)
    p_report.add_argument("--diagnostics", required=True)
    p_report.add_argument("--out", required=True)

    p_review = sub.add_parser(
        "review",
        help="write a draft final_review/review.yaml with hold decisions for findings.",
    )
    _add_output_arg(p_review, root=False)
    p_review.add_argument("--findings", required=True)
    p_review.add_argument("--out-dir", required=True)
    p_review.add_argument("--reviewer", required=True)
    p_review.add_argument("--compacted-dir", default=None)
    p_review.add_argument("--diagnostics", default=None)
    p_review.add_argument("--semantic-verifications", default=None)
    p_review.add_argument("--review-queue", default=None)
    p_review.add_argument("--report", default=None)
    p_review.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing review.yaml in --out-dir",
    )

    p_gate = sub.add_parser(
        "gate",
        help="consume final review record and emit the external pass/fail/pending verdict.",
    )
    _add_output_arg(p_gate, root=False)
    p_gate.add_argument("--final-review", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.subcommand == "check":
            result = _cmd_check(args)
        elif args.subcommand == "extract":
            result = _cmd_extract(args)
        elif args.subcommand == "compact":
            result = _cmd_compact(args)
        elif args.subcommand == "verify":
            result = _cmd_verify(args)
        elif args.subcommand == "schema":
            result = _cmd_schema(args)
        elif args.subcommand == "report":
            result = _cmd_report(args)
        elif args.subcommand == "review":
            result = _cmd_review(args)
        elif args.subcommand == "gate":
            result = _cmd_gate(args)
        else:  # pragma: no cover - argparse guards this
            parser.error(f"unknown subcommand: {args.subcommand}")
            return 3
    except Exception as exc:  # noqa: BLE001 - top-level safety net
        sys.stderr.write(f"[assessment-harness] internal error: {exc}\n")
        envelope = _build_envelope(
            status="internal_error",
            exit_code=3,
            command=getattr(args, "subcommand", "unknown"),
            next_actions=[{"type": "report_bug", "message": str(exc)}],
        )
        _emit(envelope, output=getattr(args, "output", "text"))
        return 3

    _emit(result.envelope, output=args.output)
    return result.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
