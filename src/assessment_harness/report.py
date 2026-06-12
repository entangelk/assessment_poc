"""Human-readable report renderers.

Phase 0 scope: render the diagnostics + findings payload produced by `check`
into a human-readable report. Sections expand naturally as Rules 1-3 land.
"""

from __future__ import annotations

import html
import json
from typing import Any


def render_markdown(
    findings_doc: dict[str, Any],
    diagnostics_doc: dict[str, Any],
    semantic_verifications_doc: dict[str, Any] | None = None,
    review_queue_doc: dict[str, Any] | None = None,
    policy_doc: dict[str, Any] | None = None,
) -> str:
    lines: list[str] = []
    lines.append("# Assessment Harness Report")
    lines.append("")
    lines.append(f"- status: `{findings_doc.get('status', 'unknown')}`")
    lines.append(f"- blocking_count: {findings_doc.get('blocking_count', 0)}")
    if findings_doc.get("generated_at"):
        lines.append(f"- generated_at: {findings_doc['generated_at']}")
    lines.append("")

    lines.append("## Rule Catalog")
    for rule in _rule_catalog(policy_doc):
        lines.append(f"- **{rule['id']} — {rule['title']}**: {rule['summary']}")
        if rule.get("policy"):
            lines.append(f"  - policy: {rule['policy']}")

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
            rule = _finding_rule_context(finding)
            rule_text = f" ({rule})" if rule else ""
            lines.append(
                f"- **[{finding.get('severity', '?')}/{finding.get('decision_status', '?')}] "
                f"{finding.get('type', '?')}**{rule_text} — "
                f"{finding.get('message', '').strip()}"
            )

    if semantic_verifications_doc is not None:
        lines.append("")
        lines.append("## Semantic Verifications")
        proposals = semantic_verifications_doc.get("semantic_verifications", [])
        if not proposals:
            lines.append("- No semantic verification proposals.")
        else:
            for proposal in proposals:
                lines.append(
                    f"- **{proposal.get('trace_link_id', '?')}** — "
                    f"{proposal.get('status_proposal', '?')}: "
                    f"{proposal.get('rationale', '').strip()}"
                )

    if review_queue_doc is not None:
        lines.append("")
        lines.append("## Review Queue")
        entries = review_queue_doc.get("review_queue", [])
        if not entries:
            lines.append("- No review queue entries.")
        else:
            for entry in entries:
                lines.append(
                    f"- **{entry.get('entry_id', '?')}** "
                    f"({entry.get('type', '?')}/{entry.get('status', '?')}) — "
                    f"{entry.get('reason', '').strip()}"
                )

    lines.append("")
    return "\n".join(lines)


def render_html(
    findings_doc: dict[str, Any],
    diagnostics_doc: dict[str, Any],
    semantic_verifications_doc: dict[str, Any] | None = None,
    review_queue_doc: dict[str, Any] | None = None,
    policy_doc: dict[str, Any] | None = None,
) -> str:
    findings = findings_doc.get("findings", [])
    diagnostics = diagnostics_doc.get("diagnostics", [])
    proposals = (
        semantic_verifications_doc.get("semantic_verifications", [])
        if semantic_verifications_doc is not None
        else []
    )
    queue_entries = (
        review_queue_doc.get("review_queue", [])
        if review_queue_doc is not None
        else []
    )
    diagnostic_summary = diagnostics_doc.get("summary", {})
    finding_counts = _count_by(findings, "severity")
    queue_counts = _count_by(queue_entries, "status")

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>Assessment Harness Report</title>",
            f"<style>{_HTML_STYLE}</style>",
            "</head>",
            "<body>",
            '<main class="shell">',
            _render_header(findings_doc, diagnostic_summary, findings, queue_entries),
            _render_summary_band(diagnostic_summary, finding_counts, queue_counts, proposals),
            _render_filter_bar(),
            _render_rule_catalog_section(_rule_catalog(policy_doc)),
            _render_diagnostics_section(diagnostics),
            _render_findings_section(findings),
            _render_semantic_section(proposals)
            if semantic_verifications_doc is not None
            else "",
            _render_review_queue_section(queue_entries) if review_queue_doc is not None else "",
            "</main>",
            f"<script>{_HTML_SCRIPT}</script>",
            "</body>",
            "</html>",
        ]
    )


def _render_header(
    findings_doc: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    findings: list[dict[str, Any]],
    queue_entries: list[dict[str, Any]],
) -> str:
    status = _text(findings_doc.get("status", "unknown"))
    generated_at = findings_doc.get("generated_at") or ""
    blocking_count = findings_doc.get("blocking_count", 0)
    high_integrity_count = diagnostic_summary.get("high", 0)
    tone = "ok" if status == "success" and not high_integrity_count else "attention"
    return f"""
<header class="report-head">
  <div>
    <p class="eyebrow">Assessment Harness</p>
    <h1>Verification Report</h1>
    <p class="lead">Deterministic validation output for assessment design review.</p>
  </div>
  <div class="status-panel {tone}">
    <span class="status-label">status</span>
    <strong>{status}</strong>
    <span>{_text(generated_at) if generated_at else "generated_at unavailable"}</span>
  </div>
  <dl class="headline-metrics">
    {_metric("blocking", blocking_count)}
    {_metric("findings", len(findings))}
    {_metric("queue", len(queue_entries))}
  </dl>
</header>
"""


def _render_summary_band(
    diagnostic_summary: dict[str, Any],
    finding_counts: dict[str, int],
    queue_counts: dict[str, int],
    proposals: list[dict[str, Any]],
) -> str:
    return f"""
<section class="summary-band" aria-label="Summary">
  {_metric_block("Rule 0", [
        ("total", diagnostic_summary.get("total", 0)),
        ("high", diagnostic_summary.get("high", 0)),
        ("medium", diagnostic_summary.get("medium", 0)),
        ("info", diagnostic_summary.get("informational", 0)),
    ])}
  {_metric_block("Findings", [
        ("high", finding_counts.get("high", 0)),
        ("medium", finding_counts.get("medium", 0)),
        ("low", finding_counts.get("low", 0)),
        ("info", finding_counts.get("informational", 0)),
    ])}
  {_metric_block("Review", [
        ("open", queue_counts.get("open", 0)),
        ("held", queue_counts.get("held", 0)),
        ("rerun", queue_counts.get("rerun_pending", 0)),
        ("semantic", len(proposals)),
    ])}
</section>
"""


def _render_filter_bar() -> str:
    buttons = [
        ("all", "All"),
        ("configured", "Rules"),
        ("high", "High"),
        ("medium", "Medium"),
        ("informational", "Info"),
        ("open", "Open queue"),
    ]
    rendered = "\n".join(
        f'<button type="button" data-filter="{_attr(value)}">{_text(label)}</button>'
        for value, label in buttons
    )
    return f"""
<nav class="filter-bar" aria-label="Report filters">
  {rendered}
</nav>
"""


def _render_diagnostics_section(diagnostics: list[dict[str, Any]]) -> str:
    if not diagnostics:
        body = '<p class="empty">No integrity diagnostics.</p>'
    else:
        body = "\n".join(
            _render_record(
                "diagnostic",
                diag.get("severity", "unknown"),
                diag.get("code", "?"),
                diag.get("message", ""),
                [
                    ("location", diag.get("location")),
                    ("hint", diag.get("hint")),
                ],
            )
            for diag in diagnostics
        )
    return f"""
<section class="report-section" id="diagnostics">
  <div class="section-heading">
    <p>Rule 0</p>
    <h2>Integrity Diagnostics</h2>
  </div>
  <div class="record-list">{body}</div>
</section>
"""


def _render_rule_catalog_section(rules: list[dict[str, str]]) -> str:
    body = "\n".join(
        _render_record(
            "rule",
            "configured",
            f"{rule['id']} - {rule['title']}",
            rule["summary"],
            [
                ("emits", rule["emits"]),
                ("review", rule["review"]),
                ("policy", rule.get("policy")),
            ],
        )
        for rule in rules
    )
    return f"""
<section class="report-section" id="rule-catalog">
  <div class="section-heading">
    <p>Catalog</p>
    <h2>Rule Meaning</h2>
  </div>
  <div class="record-list">{body}</div>
</section>
"""


def _render_findings_section(findings: list[dict[str, Any]]) -> str:
    if not findings:
        body = '<p class="empty">No findings.</p>'
    else:
        body = "\n".join(
            _render_record(
                "finding",
                finding.get("severity", "unknown"),
                finding.get("type", "?"),
                finding.get("message", ""),
                [
                    ("rule_context", _finding_rule_context(finding)),
                    ("decision_status", finding.get("decision_status")),
                    ("rubric_id", finding.get("rubric_id")),
                    ("spec_id", finding.get("spec_id")),
                    ("scored_rubric_id", finding.get("scored_rubric_id")),
                    ("bonus_rubric_id", finding.get("bonus_rubric_id")),
                    ("bonus_rubric_ids", finding.get("bonus_rubric_ids")),
                    ("trace_link_ref", finding.get("trace_link_ref")),
                    ("evidence", finding.get("evidence")),
                ],
            )
            for finding in findings
        )
    return f"""
<section class="report-section" id="findings">
  <div class="section-heading">
    <p>Check</p>
    <h2>Findings</h2>
  </div>
  <div class="record-list">{body}</div>
</section>
"""


def _render_semantic_section(proposals: list[dict[str, Any]]) -> str:
    if not proposals:
        body = '<p class="empty">No semantic verification proposals.</p>'
    else:
        body = "\n".join(
            _render_record(
                "semantic",
                proposal.get("status_proposal", "unknown"),
                proposal.get("trace_link_id", "?"),
                proposal.get("rationale", ""),
                [
                    ("source_refs", proposal.get("source_refs")),
                    ("support", proposal.get("support")),
                    ("variants", proposal.get("variants")),
                ],
            )
            for proposal in proposals
        )
    return f"""
<section class="report-section" id="semantic-verifications">
  <div class="section-heading">
    <p>Verify</p>
    <h2>Semantic Verifications</h2>
  </div>
  <div class="record-list">{body}</div>
</section>
"""


def _render_review_queue_section(entries: list[dict[str, Any]]) -> str:
    if not entries:
        body = '<p class="empty">No review queue entries.</p>'
    else:
        body = "\n".join(
            _render_record(
                "queue",
                entry.get("status", "unknown"),
                entry.get("entry_id", "?"),
                entry.get("reason", ""),
                [
                    ("type", entry.get("type")),
                    ("target", entry.get("target")),
                    ("related_runs", entry.get("related_runs")),
                ],
            )
            for entry in entries
        )
    return f"""
<section class="report-section" id="review-queue">
  <div class="section-heading">
    <p>Human Review</p>
    <h2>Review Queue</h2>
  </div>
  <div class="record-list">{body}</div>
</section>
"""


def _render_record(
    kind: str,
    status: Any,
    title: Any,
    message: Any,
    details: list[tuple[str, Any]],
) -> str:
    normalized_status = str(status)
    detail_rows = "\n".join(_detail_row(label, value) for label, value in details)
    details_block = f"<dl>{detail_rows}</dl>" if detail_rows else ""
    return f"""
<article class="record {kind} {_status_class(normalized_status)}" data-status="{_attr(normalized_status)}">
  <div class="record-main">
    <span class="badge">{_text(normalized_status)}</span>
    <h3>{_text(title)}</h3>
    <p>{_text(message)}</p>
  </div>
  {details_block}
</article>
"""


def _metric(label: str, value: Any) -> str:
    return f"<div><dt>{_text(label)}</dt><dd>{_text(value)}</dd></div>"


def _metric_block(title: str, metrics: list[tuple[str, Any]]) -> str:
    items = "\n".join(_metric(label, value) for label, value in metrics)
    return f"""
<div class="metric-block">
  <h2>{_text(title)}</h2>
  <dl>{items}</dl>
</div>
"""


def _detail_row(label: str, value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    return f"<div><dt>{_text(label)}</dt><dd>{_text(_format_value(value))}</dd></div>"


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _status_class(status: str) -> str:
    if status == "high" or status == "open" or status == "agent_rejected":
        return "is-hot"
    if status == "medium" or status == "held" or status == "agent_uncertain":
        return "is-warm"
    if status == "success" or status == "resolved" or status == "agent_supported":
        return "is-cool"
    return "is-muted"


def _rule_catalog(policy_doc: dict[str, Any] | None) -> list[dict[str, str]]:
    threshold = _optionality_threshold(policy_doc)
    rule_three_policy = "rules.optionality_mismatch.weight_threshold"
    if threshold is not None:
        rule_three_policy = f"{rule_three_policy} = {threshold}"
    return [
        {
            "id": "Rule 0",
            "title": "Reference Integrity",
            "summary": (
                "Validates IDs, references, source snapshot grounding, and "
                "token-sequence evidence before later checks run."
            ),
            "emits": "integrity diagnostics; invalid inputs stop check before findings",
            "review": "fix source or generated artifacts, then rerun check",
            "policy": "source manifest required",
        },
        {
            "id": "Rule 1",
            "title": "Scored Rubric Coverage",
            "summary": (
                "Flags scored rubrics without accepted coverage, plus untraced "
                "bonus rubric items as non-blocking review context."
            ),
            "emits": (
                "possible_orphan_scored_rubric_item, "
                "unconfirmed_trace_coverage, orphan_bonus_rubric_item"
            ),
            "review": (
                "review_unconfirmed_trace_coverage or "
                "review_orphan_scored_rubric"
            ),
            "policy": "human_accepted or human_overridden counts as final coverage",
        },
        {
            "id": "Rule 2",
            "title": "Required Spec Coverage",
            "summary": "Flags must-level spec items that have no scored rubric trace.",
            "emits": "uncovered_must_spec_item",
            "review": "review_uncovered_must_spec",
            "policy": "structural only; semantic status is not consulted",
        },
        {
            "id": "Rule 3",
            "title": "Optionality Consistency",
            "summary": "Flags high-weight scored rubrics traced only to optional specs.",
            "emits": "optionality_mismatch",
            "review": "review_optionality_mismatch",
            "policy": rule_three_policy,
        },
        {
            "id": "Rule L1",
            "title": "Cross-role Double Scoring",
            "summary": "Flags the same spec being traced by scored and bonus rubrics.",
            "emits": "double_scored_spec and double_scoring_review queue entries",
            "review": "review_double_scoring",
            "policy": "lint safeguard; confirmed finding is recorded but non-blocking",
        },
        {
            "id": "Rule L5",
            "title": "Bonus Mandatory-only",
            "summary": "Flags bonus rubrics whose traced targets are all must specs.",
            "emits": "bonus_grades_mandatory_only",
            "review": "review_bonus_mandatory_only",
            "policy": "lint safeguard; untraced bonus remains Rule 1 context",
        },
        {
            "id": "Rule L6",
            "title": "Mandatory Spec Bonus-only",
            "summary": (
                "Flags must specs covered only by bonus rubrics, with paired "
                "human-review queue entries."
            ),
            "emits": (
                "mandatory_spec_bonus_only_traced and "
                "mandatory_spec_bonus_review queue entries"
            ),
            "review": "review_mandatory_spec_bonus_only",
            "policy": "bonus-only only; qualitative traces stay with Rule 2",
        },
    ]


def _optionality_threshold(policy_doc: dict[str, Any] | None) -> Any:
    if not isinstance(policy_doc, dict):
        return None
    rules = policy_doc.get("rules")
    if not isinstance(rules, dict):
        return None
    optionality = rules.get("optionality_mismatch")
    if not isinstance(optionality, dict):
        return None
    return optionality.get("weight_threshold")


def _finding_rule_context(finding: dict[str, Any]) -> str:
    mapping = {
        "possible_orphan_scored_rubric_item": "Rule 1 - scored rubric has no trace link yet",
        "unconfirmed_trace_coverage": "Rule 1 - trace exists but final coverage is not accepted",
        "orphan_bonus_rubric_item": "Rule 1 - bonus rubric has no trace link",
        "uncovered_must_spec_item": "Rule 2 - must spec has no scored rubric trace",
        "optionality_mismatch": "Rule 3 - scored rubric is optional-only at policy threshold",
        "double_scored_spec": "Rule L1 - spec is scored and bonus-traced",
        "bonus_grades_mandatory_only": "Rule L5 - bonus rubric targets only must specs",
        "mandatory_spec_bonus_only_traced": "Rule L6 - must spec is bonus-only covered",
    }
    return mapping.get(str(finding.get("type", "")), "")


def _text(value: Any) -> str:
    return html.escape(str(value), quote=False)


def _attr(value: Any) -> str:
    return html.escape(str(value), quote=True)


_HTML_STYLE = """
:root {
  color-scheme: light;
  --ink: #182027;
  --muted: #64717d;
  --line: #d7dde2;
  --paper: #f6f8f7;
  --surface: #ffffff;
  --accent: #0f766e;
  --hot: #b42318;
  --warm: #a15c07;
  --cool: #146c43;
  --violet: #5946a8;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: var(--paper);
}
.shell {
  width: min(1180px, calc(100% - 40px));
  margin: 0 auto;
  padding: 40px 0 64px;
}
.report-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 28px;
  align-items: end;
  min-height: 260px;
  border-bottom: 1px solid var(--line);
}
.eyebrow, .section-heading p, .status-label {
  margin: 0 0 8px;
  color: var(--accent);
  font-size: 0.75rem;
  font-weight: 760;
  letter-spacing: 0;
  text-transform: uppercase;
}
h1 {
  margin: 0;
  max-width: 760px;
  font-size: clamp(3rem, 8vw, 6.7rem);
  line-height: 0.9;
  letter-spacing: 0;
}
.lead {
  max-width: 560px;
  margin: 24px 0 0;
  color: var(--muted);
  font-size: 1.05rem;
}
.status-panel {
  border-left: 4px solid var(--accent);
  padding: 18px 0 18px 22px;
}
.status-panel.attention { border-color: var(--warm); }
.status-panel strong {
  display: block;
  overflow-wrap: anywhere;
  font-size: 1.7rem;
}
.status-panel span:last-child {
  display: block;
  margin-top: 6px;
  color: var(--muted);
  font-size: 0.86rem;
}
.headline-metrics {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 0;
  border-top: 1px solid var(--line);
}
.headline-metrics div,
.metric-block dl div {
  min-width: 0;
  padding: 18px 20px;
  border-right: 1px solid var(--line);
}
.headline-metrics div:last-child,
.metric-block dl div:last-child { border-right: 0; }
dt {
  color: var(--muted);
  font-size: 0.78rem;
  text-transform: uppercase;
}
dd {
  margin: 5px 0 0;
  overflow-wrap: anywhere;
  font-weight: 760;
  font-size: 1.5rem;
}
.summary-band {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  margin: 28px 0;
  border: 1px solid var(--line);
  background: var(--line);
}
.metric-block {
  background: rgba(255, 255, 255, 0.82);
}
.metric-block h2 {
  margin: 0;
  padding: 18px 20px 0;
  font-size: 1rem;
}
.metric-block dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
}
.filter-bar {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 0;
  backdrop-filter: blur(12px);
  background: rgba(246, 248, 247, 0.84);
  border-bottom: 1px solid var(--line);
}
button {
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink);
  font: inherit;
  font-size: 0.9rem;
  cursor: pointer;
}
button.is-active {
  border-color: var(--accent);
  background: var(--accent);
  color: #ffffff;
}
.report-section {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 44px;
  padding: 42px 0;
  border-bottom: 1px solid var(--line);
}
.section-heading {
  position: sticky;
  top: 70px;
  align-self: start;
}
.section-heading h2 {
  margin: 0;
  font-size: 1.8rem;
  letter-spacing: 0;
}
.record-list {
  display: grid;
  gap: 12px;
}
.record {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 0.62fr);
  gap: 24px;
  padding: 20px 0;
  border-top: 1px solid var(--line);
}
.record:first-child { border-top: 0; }
.record.is-hidden { display: none; }
.badge {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border: 1px solid currentColor;
  font-size: 0.76rem;
  font-weight: 760;
  text-transform: uppercase;
}
.is-hot .badge { color: var(--hot); }
.is-warm .badge { color: var(--warm); }
.is-cool .badge { color: var(--cool); }
.is-muted .badge { color: var(--violet); }
.record h3 {
  margin: 12px 0 8px;
  overflow-wrap: anywhere;
  font-size: 1.08rem;
}
.record p {
  margin: 0;
  color: var(--muted);
  line-height: 1.55;
}
.record dl {
  margin: 0;
  display: grid;
  gap: 10px;
}
.record dl div {
  min-width: 0;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(215, 221, 226, 0.72);
}
.record dl div:last-child { border-bottom: 0; }
.record dl dd {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.82rem;
  font-weight: 520;
  line-height: 1.45;
}
.empty {
  margin: 0;
  padding: 26px 0;
  color: var(--muted);
  border-top: 1px solid var(--line);
}
@media (max-width: 820px) {
  .shell {
    width: min(100% - 24px, 680px);
    padding-top: 26px;
  }
  .report-head,
  .summary-band,
  .report-section,
  .record {
    grid-template-columns: 1fr;
  }
  .headline-metrics { grid-template-columns: 1fr; }
  .headline-metrics div,
  .metric-block dl div {
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }
  .section-heading { position: static; }
  h1 { font-size: clamp(2.8rem, 18vw, 4.5rem); }
}
"""


_HTML_SCRIPT = """
const buttons = document.querySelectorAll('[data-filter]');
const records = document.querySelectorAll('.record');
function applyFilter(filter) {
  buttons.forEach((button) => button.classList.toggle('is-active', button.dataset.filter === filter));
  records.forEach((record) => {
    const status = record.dataset.status;
    const show = filter === 'all' || status === filter || (filter === 'open' && record.classList.contains('queue') && status === 'open');
    record.classList.toggle('is-hidden', !show);
  });
}
buttons.forEach((button) => button.addEventListener('click', () => applyFilter(button.dataset.filter)));
applyFilter('all');
"""
