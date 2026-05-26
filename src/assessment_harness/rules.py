"""Deterministic rule engine.

Phase 0 ships Rule 0 (Reference Integrity Diagnostic) plus a first slice of
Rule 1 (Scored Rubric Coverage). Remaining Rule 1 branches (unconfirmed
coverage, bonus informational) and Rules 2-3 land in following iterations.

Each rule consumes already-schema-validated dict inputs and returns a list of
:class:`Diagnostic` or :class:`Finding` records. Severity and decision status
are encoded per spec §6.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from .models import SourceSnapshot


@dataclass
class Diagnostic:
    code: str
    severity: str
    message: str
    location: dict[str, Any] = field(default_factory=dict)
    hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.hint is None:
            data.pop("hint")
        return data


@dataclass
class Finding:
    type: str
    severity: str
    decision_status: str
    message: str
    rubric_id: str | None = None
    spec_id: str | None = None
    trace_link_ref: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": self.type,
            "severity": self.severity,
            "decision_status": self.decision_status,
            "message": self.message,
        }
        if self.rubric_id is not None:
            data["rubric_id"] = self.rubric_id
        if self.spec_id is not None:
            data["spec_id"] = self.spec_id
        if self.trace_link_ref is not None:
            data["trace_link_ref"] = self.trace_link_ref
        if self.evidence is not None:
            data["evidence"] = self.evidence
        return data


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _is_token_subsequence(needle: str, haystack: str) -> bool:
    n = _normalize(needle)
    if not n:
        return False
    return n in _normalize(haystack)


def _span_contained(
    inner: dict[str, Any], outer: dict[str, Any]
) -> bool:
    if inner.get("document_id") != outer.get("document_id"):
        return False
    try:
        return (
            int(inner["start_line"]) >= int(outer["start_line"])
            and int(inner["end_line"]) <= int(outer["end_line"])
        )
    except (KeyError, TypeError, ValueError):
        return False


def run_rule_zero(
    spec_items_doc: dict[str, Any],
    rubric_items_doc: dict[str, Any],
    trace_links_doc: dict[str, Any],
    snapshot: SourceSnapshot | None,
) -> list[Diagnostic]:
    """Reference Integrity Diagnostic (spec §6 Rule 0).

    All issues surface as ``high`` severity diagnostics. The caller turns the
    presence of any high diagnostic into ``status=invalid_input`` and exit
    code ``2``.
    """

    diagnostics: list[Diagnostic] = []
    spec_items: list[dict[str, Any]] = spec_items_doc.get("spec_items", [])
    rubric_items: list[dict[str, Any]] = rubric_items_doc.get("rubric_items", [])
    trace_links: list[dict[str, Any]] = trace_links_doc.get("trace_links", [])

    # --- duplicate IDs ---------------------------------------------------
    for code, items in (
        ("duplicate_spec_id", spec_items),
        ("duplicate_rubric_id", rubric_items),
    ):
        ids = [item.get("id") for item in items if item.get("id")]
        for dup_id, count in Counter(ids).items():
            if count > 1:
                diagnostics.append(
                    Diagnostic(
                        code=code,
                        severity="high",
                        message=f"id {dup_id!r} appears {count} times; ids must be unique.",
                        location={"id": dup_id, "count": count},
                        hint="Rename one of the duplicates or merge the entries.",
                    )
                )

    spec_by_id = {item["id"]: item for item in spec_items if item.get("id")}
    rubric_by_id = {item["id"]: item for item in rubric_items if item.get("id")}

    # --- snapshot grounding for spec / rubric items ----------------------
    if snapshot is not None:
        _check_document_integrity(snapshot, diagnostics)
        for spec in spec_items:
            _check_source_ref(
                source_ref=spec.get("source_ref") or {},
                snapshot=snapshot,
                diagnostics=diagnostics,
                unknown_code="spec_source_ref_unknown_document",
                span_code="spec_source_ref_span_invalid",
                text_mismatch_code="spec_text_not_in_snapshot_span",
                quote_mismatch_code="spec_quote_not_in_snapshot_span",
                owner_kind="spec_item",
                owner_id=spec.get("id"),
                expected_text=spec.get("text"),
            )
        for rubric in rubric_items:
            _check_source_ref(
                source_ref=rubric.get("source_ref") or {},
                snapshot=snapshot,
                diagnostics=diagnostics,
                unknown_code="rubric_source_ref_unknown_document",
                span_code="rubric_source_ref_span_invalid",
                text_mismatch_code=None,
                quote_mismatch_code="rubric_quote_not_in_snapshot_span",
                owner_kind="rubric_item",
                owner_id=rubric.get("id"),
                expected_text=None,
            )

    # --- trace link references and evidence quotes -----------------------
    for link_index, link in enumerate(trace_links):
        rubric_id = link.get("rubric_id")
        spec_ids = list(link.get("spec_ids") or [])
        link_ref = {"rubric_id": rubric_id, "spec_ids": list(spec_ids)}

        if rubric_id not in rubric_by_id:
            diagnostics.append(
                Diagnostic(
                    code="dangling_rubric_reference",
                    severity="high",
                    message=(
                        f"trace_links[{link_index}].rubric_id={rubric_id!r} "
                        "does not match any rubric item."
                    ),
                    location={"trace_link_index": link_index, "rubric_id": rubric_id},
                    hint=f"Add rubric_item {rubric_id!r} or correct the reference.",
                )
            )

        for spec_ref in spec_ids:
            if spec_ref not in spec_by_id:
                diagnostics.append(
                    Diagnostic(
                        code="dangling_spec_reference",
                        severity="high",
                        message=(
                            f"trace_links[{link_index}].spec_ids contains "
                            f"{spec_ref!r}, which is not a known spec item."
                        ),
                        location={
                            "trace_link_index": link_index,
                            "spec_id": spec_ref,
                            "trace_link_ref": link_ref,
                        },
                        hint=f"Add spec_item {spec_ref!r} or correct the reference.",
                    )
                )

        # Every spec_id in spec_ids must appear as some evidence_quote.spec_id.
        evidence_spec_ids = {
            (quote_entry.get("spec_id"))
            for quote_entry in (link.get("evidence_quotes") or [])
            if quote_entry.get("spec_id")
        }
        for spec_ref in spec_ids:
            if spec_ref not in spec_by_id:
                # already reported as dangling; don't double-report.
                continue
            if spec_ref not in evidence_spec_ids:
                diagnostics.append(
                    Diagnostic(
                        code="evidence_quote_missing_for_spec_id",
                        severity="high",
                        message=(
                            f"trace_links[{link_index}].spec_ids contains "
                            f"{spec_ref!r} but no evidence_quote covers it."
                        ),
                        location={
                            "trace_link_index": link_index,
                            "spec_id": spec_ref,
                            "trace_link_ref": link_ref,
                        },
                        hint=(
                            "Add an evidence_quote entry whose spec_id is this "
                            "value, or drop the spec_id from spec_ids."
                        ),
                    )
                )

        for quote_index, quote_entry in enumerate(link.get("evidence_quotes") or []):
            quote_text = quote_entry.get("quote", "")
            quote_spec_id = quote_entry.get("spec_id")
            mode = quote_entry.get("verification_mode")
            quote_loc = {
                "trace_link_index": link_index,
                "evidence_quote_index": quote_index,
                "trace_link_ref": link_ref,
            }

            if not quote_text.strip():
                diagnostics.append(
                    Diagnostic(
                        code="evidence_quote_empty",
                        severity="high",
                        message=(
                            f"trace_links[{link_index}].evidence_quotes[{quote_index}].quote "
                            "is empty."
                        ),
                        location=quote_loc,
                        hint="Provide the spec excerpt that justifies the trace link.",
                    )
                )

            if quote_spec_id not in spec_ids:
                diagnostics.append(
                    Diagnostic(
                        code="evidence_quote_spec_id_mismatch",
                        severity="high",
                        message=(
                            f"trace_links[{link_index}].evidence_quotes[{quote_index}].spec_id "
                            f"={quote_spec_id!r} is not listed in spec_ids."
                        ),
                        location={**quote_loc, "spec_id": quote_spec_id},
                        hint="Add the spec_id to spec_ids or change the evidence quote.",
                    )
                )
                continue

            target_spec = spec_by_id.get(quote_spec_id)
            if target_spec is None:
                # dangling spec; already reported above
                continue

            if snapshot is not None:
                evidence_ref = quote_entry.get("source_ref") or {}
                if evidence_ref:
                    _check_evidence_source_ref(
                        evidence_ref=evidence_ref,
                        spec_source_ref=target_spec.get("source_ref") or {},
                        snapshot=snapshot,
                        diagnostics=diagnostics,
                        location=quote_loc,
                        quote_text=quote_text,
                    )

            if mode == "token_sequence" and quote_text.strip():
                if not _is_token_subsequence(quote_text, target_spec.get("text", "")):
                    diagnostics.append(
                        Diagnostic(
                            code="evidence_quote_token_sequence_mismatch",
                            severity="high",
                            message=(
                                f"trace_links[{link_index}].evidence_quotes[{quote_index}] "
                                f"(verification_mode=token_sequence) is not a "
                                f"substring of spec_item {quote_spec_id!r}.text."
                            ),
                            location={
                                **quote_loc,
                                "spec_id": quote_spec_id,
                                "quote": quote_text,
                            },
                            hint=(
                                "Fix the quote to match the spec text verbatim "
                                "(whitespace-normalized) or switch verification_mode "
                                "to ai_judgement."
                            ),
                        )
                    )

    return diagnostics


def _check_document_integrity(
    snapshot: SourceSnapshot, diagnostics: list[Diagnostic]
) -> None:
    for doc in snapshot.documents.values():
        if not doc.path.exists():
            diagnostics.append(
                Diagnostic(
                    code="source_document_missing",
                    severity="high",
                    message=(
                        f"source document {doc.document_id!r} not found at {doc.path}."
                    ),
                    location={"document_id": doc.document_id, "path": str(doc.path)},
                    hint="Restore the snapshot file or fix the manifest path.",
                )
            )
            continue
        if not doc.hash_matches:
            diagnostics.append(
                Diagnostic(
                    code="source_document_hash_mismatch",
                    severity="high",
                    message=(
                        f"sha256 mismatch for {doc.document_id!r}: "
                        f"expected {doc.expected_sha256[:12]}..., "
                        f"actual {doc.actual_sha256[:12]}..."
                    ),
                    location={
                        "document_id": doc.document_id,
                        "path": str(doc.path),
                        "expected_sha256": doc.expected_sha256,
                        "actual_sha256": doc.actual_sha256,
                    },
                    hint="Re-snapshot the document or update the manifest hash.",
                )
            )


def _check_source_ref(
    *,
    source_ref: dict[str, Any],
    snapshot: SourceSnapshot,
    diagnostics: list[Diagnostic],
    unknown_code: str,
    span_code: str,
    text_mismatch_code: str | None,
    quote_mismatch_code: str | None,
    owner_kind: str,
    owner_id: str | None,
    expected_text: str | None,
) -> None:
    document_id = source_ref.get("document_id")
    doc = snapshot.get(document_id) if document_id else None
    if doc is None:
        diagnostics.append(
            Diagnostic(
                code=unknown_code,
                severity="high",
                message=(
                    f"{owner_kind} {owner_id!r} has source_ref.document_id="
                    f"{document_id!r} which is not in the source manifest."
                ),
                location={
                    "owner_kind": owner_kind,
                    "owner_id": owner_id,
                    "document_id": document_id,
                },
                hint="Add the document to the manifest or correct document_id.",
            )
        )
        return

    if not doc.path.exists() or not doc.hash_matches:
        # document-level issues already reported; skip span check.
        return

    start = source_ref.get("start_line")
    end = source_ref.get("end_line")
    try:
        start_i = int(start)
        end_i = int(end)
    except (TypeError, ValueError):
        diagnostics.append(
            Diagnostic(
                code=span_code,
                severity="high",
                message=(
                    f"{owner_kind} {owner_id!r} has non-integer source_ref span "
                    f"({start!r}, {end!r})."
                ),
                location={
                    "owner_kind": owner_kind,
                    "owner_id": owner_id,
                    "start_line": start,
                    "end_line": end,
                },
            )
        )
        return

    if not doc.has_span(start_i, end_i):
        diagnostics.append(
            Diagnostic(
                code=span_code,
                severity="high",
                message=(
                    f"{owner_kind} {owner_id!r} source_ref span {start_i}-{end_i} "
                    f"out of range for {document_id!r} (document has {len(doc.lines)} lines)."
                ),
                location={
                    "owner_kind": owner_kind,
                    "owner_id": owner_id,
                    "document_id": document_id,
                    "start_line": start_i,
                    "end_line": end_i,
                    "document_line_count": len(doc.lines),
                },
                hint="Adjust source_ref to a valid range or re-snapshot.",
            )
        )
        return

    # Span is valid. Compare content against snapshot when applicable.
    span_text = doc.span_text(start_i, end_i)

    if text_mismatch_code and expected_text and expected_text.strip():
        if not _is_token_subsequence(expected_text, span_text):
            diagnostics.append(
                Diagnostic(
                    code=text_mismatch_code,
                    severity="high",
                    message=(
                        f"{owner_kind} {owner_id!r} text is not present in the "
                        f"snapshot span {document_id!r}:{start_i}-{end_i}."
                    ),
                    location={
                        "owner_kind": owner_kind,
                        "owner_id": owner_id,
                        "document_id": document_id,
                        "start_line": start_i,
                        "end_line": end_i,
                    },
                    hint=(
                        "Make the item's text match the snapshot span "
                        "(whitespace-normalized) or correct source_ref."
                    ),
                )
            )

    if quote_mismatch_code:
        quote_text = source_ref.get("quote") or ""
        if quote_text.strip() and not _is_token_subsequence(quote_text, span_text):
            diagnostics.append(
                Diagnostic(
                    code=quote_mismatch_code,
                    severity="high",
                    message=(
                        f"{owner_kind} {owner_id!r} source_ref.quote is not "
                        f"contained in the snapshot span {document_id!r}:"
                        f"{start_i}-{end_i}."
                    ),
                    location={
                        "owner_kind": owner_kind,
                        "owner_id": owner_id,
                        "document_id": document_id,
                        "start_line": start_i,
                        "end_line": end_i,
                    },
                    hint=(
                        "Make source_ref.quote a substring of the snapshot span "
                        "(whitespace-normalized) or remove it."
                    ),
                )
            )


def _check_evidence_source_ref(
    *,
    evidence_ref: dict[str, Any],
    spec_source_ref: dict[str, Any],
    snapshot: SourceSnapshot,
    diagnostics: list[Diagnostic],
    location: dict[str, Any],
    quote_text: str,
) -> None:
    document_id = evidence_ref.get("document_id")
    doc = snapshot.get(document_id) if document_id else None
    if doc is None:
        diagnostics.append(
            Diagnostic(
                code="evidence_source_ref_unknown_document",
                severity="high",
                message=(
                    f"evidence_quote source_ref.document_id={document_id!r} "
                    "is not in the source manifest."
                ),
                location={**location, "document_id": document_id},
            )
        )
        return

    if not _span_contained(evidence_ref, spec_source_ref):
        diagnostics.append(
            Diagnostic(
                code="evidence_source_ref_mismatch_with_spec",
                severity="high",
                message=(
                    "evidence_quote source_ref must be contained within the "
                    "referenced spec_item.source_ref span."
                ),
                location={
                    **location,
                    "evidence_source_ref": evidence_ref,
                    "spec_source_ref": spec_source_ref,
                },
                hint=(
                    "Set evidence source_ref to the same document and a span "
                    "inside the spec_item span."
                ),
            )
        )
        return

    if not doc.path.exists() or not doc.hash_matches:
        return
    start = evidence_ref.get("start_line")
    end = evidence_ref.get("end_line")
    try:
        start_i, end_i = int(start), int(end)
    except (TypeError, ValueError):
        return
    if not doc.has_span(start_i, end_i):
        return
    if not quote_text.strip():
        return
    span_text = doc.span_text(start_i, end_i)
    if not _is_token_subsequence(quote_text, span_text):
        diagnostics.append(
            Diagnostic(
                code="evidence_quote_not_in_snapshot_span",
                severity="high",
                message=(
                    "evidence_quote.quote is not present in the snapshot span "
                    f"{document_id!r}:{start_i}-{end_i}."
                ),
                location={
                    **location,
                    "document_id": document_id,
                    "start_line": start_i,
                    "end_line": end_i,
                },
                hint=(
                    "Make the evidence quote a substring of the snapshot span "
                    "(whitespace-normalized) or correct evidence source_ref."
                ),
            )
        )


HUMAN_ACCEPTED_SEMANTIC_STATUSES: frozenset[str] = frozenset(
    {"human_accepted", "human_overridden"}
)


def run_rule_one(
    rubric_items_doc: dict[str, Any],
    trace_links_doc: dict[str, Any],
) -> list[Finding]:
    """Scored Rubric Coverage (plan v1.10 §6 Rule 1).

    Phase 0 emits three provisional branches:

    - ``possible_orphan_scored_rubric_item`` (``high`` / ``provisional``)
      for any ``evaluation_role == scored`` rubric item with no compacted
      trace link. The ``possible_`` prefix marks scored items because
      ``gate`` (not ``check``) may later promote the same rubric to
      ``orphan_scored_rubric_item`` (``high`` / ``confirmed``) after
      final review.
    - ``unconfirmed_trace_coverage`` (``medium`` / ``provisional``) when a
      scored rubric has at least one trace link but none carry a
      final-coverage ``semantic_status``
      (``human_accepted`` / ``human_overridden``). Per plan §5.3.1 and
      §6 Rule 1, pre-review (``pending_verification`` / ``agent_*``) and
      post-review non-coverage (``human_rejected`` / ``rerun_requested``)
      states all fall here; only ``gate`` may promote persistent
      non-coverage into the confirmed orphan finding.
    - ``orphan_bonus_rubric_item`` (``informational`` / ``provisional``)
      for any ``evaluation_role == bonus`` rubric item with no compacted
      trace link. Bonus orphans never block gating; the ``possible_``
      prefix is omitted because there is no symmetric confirmed promotion
      path (plan §6 Rule 1 bonus 처리 + naming convention memo).
      ``semantic_status`` is not consulted for bonus items.

    Rule 0 already guarantees rubric IDs are unique and that every trace
    link references an existing rubric, so this rule trusts those
    invariants.
    """

    findings: list[Finding] = []
    rubric_items: list[dict[str, Any]] = rubric_items_doc.get("rubric_items", [])
    trace_links: list[dict[str, Any]] = trace_links_doc.get("trace_links", [])

    links_by_rubric: dict[str, list[dict[str, Any]]] = {}
    for link in trace_links:
        rid = link.get("rubric_id")
        if rid:
            links_by_rubric.setdefault(rid, []).append(link)

    for rubric in rubric_items:
        evaluation_role = rubric.get("evaluation_role")
        rid = rubric.get("id")
        if not rid:
            continue
        rubric_links = links_by_rubric.get(rid, [])

        if evaluation_role == "bonus":
            if not rubric_links:
                findings.append(
                    Finding(
                        type="orphan_bonus_rubric_item",
                        severity="informational",
                        decision_status="provisional",
                        rubric_id=rid,
                        message=(
                            f"bonus rubric_item {rid!r} has no trace_link to "
                            "any spec_item; informational only — bonus orphans "
                            "do not block gating."
                        ),
                    )
                )
            continue

        if evaluation_role != "scored":
            continue

        if not rubric_links:
            findings.append(
                Finding(
                    type="possible_orphan_scored_rubric_item",
                    severity="high",
                    decision_status="provisional",
                    rubric_id=rid,
                    message=(
                        f"scored rubric_item {rid!r} has no trace_link to any "
                        "spec_item; possible orphan pending final review."
                    ),
                )
            )
            continue

        statuses = [link.get("semantic_status") for link in rubric_links]
        if any(s in HUMAN_ACCEPTED_SEMANTIC_STATUSES for s in statuses):
            continue

        findings.append(
            Finding(
                type="unconfirmed_trace_coverage",
                severity="medium",
                decision_status="provisional",
                rubric_id=rid,
                message=(
                    f"scored rubric_item {rid!r} has {len(rubric_links)} "
                    "trace_link(s) but none carry a final-coverage "
                    "semantic_status (human_accepted / human_overridden); "
                    "coverage is not confirmed (pending verifier-agent "
                    "results, final human review, or gate disposition)."
                ),
                evidence={
                    "link_count": len(rubric_links),
                    "semantic_statuses": statuses,
                },
            )
        )

    return findings


def severity_counts(diagnostics: list[Diagnostic]) -> dict[str, int]:
    counts = {"informational": 0, "low": 0, "medium": 0, "high": 0, "total": 0}
    for diag in diagnostics:
        counts[diag.severity] = counts.get(diag.severity, 0) + 1
        counts["total"] += 1
    return counts


def finding_severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts = {"informational": 0, "low": 0, "medium": 0, "high": 0, "total": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
        counts["total"] += 1
    return counts
