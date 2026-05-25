"""Agent-consumable CLI entry point.

Subcommands implemented in Phase 0:

- ``check``   : run Rule 0 over the supplied compacted YAML and emit JSON
                findings + integrity diagnostics.
- ``schema``  : self-discovery for the stable contract; lets caller agents
                read the current `cli_output` shape without docs.
- ``report``  : render findings + diagnostics into a Markdown report.

Subcommands ``compact``, ``extract``, ``verify``, ``review``, and ``gate`` are
defined as placeholders so the surface is stable; they will gain real
behaviour in later phases.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import HarnessInputError, load_source_snapshot, load_validated, load_policy
from .report import render_markdown
from .rules import run_rule_zero, severity_counts
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
    for key in ("findings_path", "diagnostics_path", "report_path", "blocking_count"):
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

    try:
        spec_doc = load_validated(Path(args.spec_items), "spec_items")
        rubric_doc = load_validated(Path(args.rubric_items), "rubric_items")
        trace_doc = load_validated(Path(args.trace_links), "trace_links")
    except HarnessInputError as exc:
        return _check_invalid_input(args, exc, next_actions)

    try:
        if args.policy:
            load_policy(Path(args.policy))
    except HarnessInputError as exc:
        return _check_invalid_input(args, exc, next_actions)

    snapshot = None
    if args.source_manifest:
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

    # No Rule 0 issues. Phase 0 ships only Rule 0; Rules 1-3 will append
    # provisional findings here in the next iteration.
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
    )
    _write_json(Path(args.out), findings_payload)
    _write_json(Path(args.diagnostics_out), diagnostics_payload)
    return CommandResult(envelope=envelope, exit_code=0)


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
# schema
# ---------------------------------------------------------------------------


COMMAND_CONTRACTS: dict[str, dict[str, Any]] = {
    "check": {
        "stable_core": STABLE_CORE_FIELDS,
        "informational": [
            "findings_path",
            "diagnostics_path",
            "blocking_count",
            "high_integrity_count",
            "input_error",
        ],
        "exit_codes": {
            "0": "no Rule 0 violations; Phase 0 produces no provisional findings yet.",
            "1": "reserved for `gate` confirmed blocking finding after final review.",
            "2": "input or Rule 0 reference integrity failure (invalid_input).",
            "3": "internal error.",
        },
        "next_actions_types": ["fix_reference_integrity", "fix_input"],
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
    "schema": {
        "stable_core": STABLE_CORE_FIELDS,
        "informational": ["contract"],
        "exit_codes": {
            "0": "contract returned.",
            "2": "unknown command name.",
        },
        "next_actions_types": [],
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="assessment-harness",
        description="Assessment Spec Harness PoC (Phase 0).",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="output format on stdout (default: text)",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_check = sub.add_parser(
        "check",
        help="run Rule 0 over compacted YAML and emit findings/diagnostics JSON.",
    )
    p_check.add_argument("--spec-items", required=True)
    p_check.add_argument("--rubric-items", required=True)
    p_check.add_argument("--trace-links", required=True)
    p_check.add_argument("--source-manifest", default=None)
    p_check.add_argument("--policy", default=None)
    p_check.add_argument("--out", required=True, help="findings.json output path")
    p_check.add_argument(
        "--diagnostics-out",
        required=True,
        help="integrity_diagnostics.json output path",
    )

    p_schema = sub.add_parser(
        "schema",
        help="return the stable contract for a CLI subcommand.",
    )
    p_schema.add_argument("--command", dest="command_name", required=True)

    p_report = sub.add_parser(
        "report",
        help="render findings + diagnostics into Markdown.",
    )
    p_report.add_argument("--findings", required=True)
    p_report.add_argument("--diagnostics", required=True)
    p_report.add_argument("--out", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.subcommand == "check":
            result = _cmd_check(args)
        elif args.subcommand == "schema":
            result = _cmd_schema(args)
        elif args.subcommand == "report":
            result = _cmd_report(args)
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
