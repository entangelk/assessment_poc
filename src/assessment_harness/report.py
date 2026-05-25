"""Markdown report renderer.

Phase 0 scope: render the diagnostics + findings payload produced by `check`
into a human-readable report. Sections expand naturally as Rules 1-3 land.
"""

from __future__ import annotations

from typing import Any


def render_markdown(findings_doc: dict[str, Any], diagnostics_doc: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Assessment Harness Report")
    lines.append("")
    lines.append(f"- status: `{findings_doc.get('status', 'unknown')}`")
    lines.append(f"- blocking_count: {findings_doc.get('blocking_count', 0)}")
    if findings_doc.get("generated_at"):
        lines.append(f"- generated_at: {findings_doc['generated_at']}")
    lines.append("")

    lines.append("## Integrity Diagnostics (Rule 0)")
    summary = diagnostics_doc.get("summary", {})
    lines.append(
        "- total: {total}, high: {high}, medium: {medium}, low: {low}, informational: {info}".format(
            total=summary.get("total", 0),
            high=summary.get("high", 0),
            medium=summary.get("medium", 0),
            low=summary.get("low", 0),
            info=summary.get("informational", 0),
        )
    )
    diagnostics = diagnostics_doc.get("diagnostics", [])
    if not diagnostics:
        lines.append("- No integrity issues.")
    else:
        lines.append("")
        for diag in diagnostics:
            lines.append(
                f"- **[{diag.get('severity', 'unknown')}] {diag.get('code', '?')}** — "
                f"{diag.get('message', '').strip()}"
            )
            hint = diag.get("hint")
            if hint:
                lines.append(f"  - hint: {hint}")

    lines.append("")
    lines.append("## Findings")
    findings = findings_doc.get("findings", [])
    if not findings:
        lines.append("- No findings.")
    else:
        for finding in findings:
            lines.append(
                f"- **[{finding.get('severity', '?')}/{finding.get('decision_status', '?')}] "
                f"{finding.get('type', '?')}** — {finding.get('message', '').strip()}"
            )

    lines.append("")
    return "\n".join(lines)
