"""Deterministic, offline candidate extraction runner.

This is a stand-in for a real Claude Agent SDK runner so the full harness
workflow can run end-to-end on a real sample ``spec.md`` / ``rubric.md`` pair
without network access, credentials, or the SDK installed. It performs **no LLM
call**: it derives candidates deterministically from the rubric's declared
``Traceable spec quote`` hints and locates each quote inside the spec so every
emitted reference is grounding-correct against the source snapshot.

It is NOT live agent extraction. See ``docs/sdk_runner_minimal_slice_plan.md``
for the placeholder decisions this runner encodes and the path to a real SDK
runner behind the same ``AgentRunner`` protocol.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from assessment_harness.agent_runners.base import AgentRunResult
from assessment_harness.rules import _normalize

_SPEC_DOC = "DOC_SPEC"
_RUBRIC_DOC = "DOC_RUBRIC"
_HEADER_RE = re.compile(r"^##\s+([A-Za-z]+\d+)\.\s+(.*)$")
_POINTS_RE = re.compile(r"\(\s*\+?\s*(\d+)\s*points?\s*\)", re.IGNORECASE)
_QUOTE_RE = re.compile(r'Traceable spec quote:\s*"(.+?)"', re.DOTALL)
_SECTION_RE = re.compile(r"^#+\s+(.*)$")
_MAX_QUOTE_WINDOW = 12


class DeterministicExtractionRunner:
    """Offline runner that emits grounding-correct candidates from a sample."""

    name = "deterministic_extraction"

    def __init__(self, run_id: str = "deterministic_run_001") -> None:
        self.run_id = run_id

    def run(
        self,
        spec_path: Path,
        rubric_path: Path,
        tools: Sequence[Any],
        max_turns: int,
        policy: Mapping[str, Any],
    ) -> AgentRunResult:
        spec_lines = Path(spec_path).read_text(encoding="utf-8").splitlines()
        rubric_lines = Path(rubric_path).read_text(encoding="utf-8").splitlines()

        rubric_items, trace_seeds = _parse_rubric(rubric_lines)
        spec_items, spec_by_quote = _build_spec_items(trace_seeds, spec_lines)
        trace_links = _build_trace_links(trace_seeds, spec_items, spec_by_quote)

        artifacts = {
            "spec_items": {"spec_items": spec_items},
            "rubric_items": {"rubric_items": rubric_items},
            "trace_links": {"trace_links": trace_links},
        }
        audit_trace = (
            {
                "run_id": self.run_id,
                "turn": 0,
                "role": "system",
                "content_ref": "deterministic_extraction",
            },
            {
                "run_id": self.run_id,
                "finish_reason": "complete",
                "turns": 0,
                "tool_call_count": 0,
            },
        )
        raw_trace = (
            {
                "run_id": self.run_id,
                "runner": self.name,
                "spec_path": str(spec_path),
                "rubric_path": str(rubric_path),
                "max_turns": max_turns,
                "tool_count": len(tools),
                "policy_keys": sorted(policy.keys()),
            },
        )
        return AgentRunResult(
            run_id=self.run_id,
            runner_name=self.name,
            finish_reason="complete",
            artifacts=artifacts,
            audit_trace=audit_trace,
            raw_trace=raw_trace,
        )


def _parse_rubric(
    lines: list[str],
) -> tuple[list[dict[str, Any]], list[tuple[str, str]]]:
    """Return (rubric_items, [(rubric_id, normalized_quote)])."""
    headers = [
        (index, match.group(1), match.group(2).strip())
        for index, line in enumerate(lines, start=1)
        if (match := _HEADER_RE.match(line))
    ]

    rubric_items: list[dict[str, Any]] = []
    trace_seeds: list[tuple[str, str]] = []
    for position, (start_line, rubric_id, rest) in enumerate(headers):
        end_line = (
            headers[position + 1][0] - 1
            if position + 1 < len(headers)
            else len(lines)
        )
        block = "\n".join(lines[start_line - 1 : end_line])
        role, weight = _classify_role(rubric_id, rest)
        title = _POINTS_RE.sub("", rest).strip() or rubric_id

        item: dict[str, Any] = {
            "id": rubric_id,
            "title": title,
            "description": title,
            "evaluation_role": role,
            "source_ref": {
                "document_id": _RUBRIC_DOC,
                "start_line": start_line,
                "end_line": end_line,
            },
        }
        if weight is not None:
            item["weight"] = weight
        rubric_items.append(item)

        quote_match = _QUOTE_RE.search(block)
        if quote_match:
            trace_seeds.append((rubric_id, _normalize(quote_match.group(1))))

    return rubric_items, trace_seeds


def _classify_role(rubric_id: str, rest: str) -> tuple[str, float | None]:
    points_match = _POINTS_RE.search(rest)
    points = float(points_match.group(1)) if points_match else None
    lowered = rest.lower()

    if "bonus" in lowered or rubric_id.upper().startswith("RB"):
        return "bonus", points
    if "qualitative" in lowered or points is None:
        return "qualitative", None
    return "scored", points


def _build_spec_items(
    trace_seeds: list[tuple[str, str]],
    spec_lines: list[str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    spec_items: list[dict[str, Any]] = []
    spec_id_by_quote: dict[str, str] = {}

    for _rubric_id, normalized_quote in trace_seeds:
        if normalized_quote in spec_id_by_quote:
            continue
        span = _find_span(normalized_quote, spec_lines)
        if span is None:
            continue
        start_line, end_line = span
        spec_id = f"S{len(spec_items) + 1}"
        spec_id_by_quote[normalized_quote] = spec_id
        spec_items.append(
            {
                "id": spec_id,
                "source": "spec.md",
                "section": _nearest_section(spec_lines, start_line),
                "text": normalized_quote,
                "visibility": "candidate_facing",
                "requirement_level": _requirement_level(normalized_quote),
                "source_ref": {
                    "document_id": _SPEC_DOC,
                    "start_line": start_line,
                    "end_line": end_line,
                    "quote": normalized_quote,
                },
            }
        )
    return spec_items, spec_id_by_quote


def _build_trace_links(
    trace_seeds: list[tuple[str, str]],
    spec_items: list[dict[str, Any]],
    spec_id_by_quote: dict[str, str],
) -> list[dict[str, Any]]:
    source_ref_by_id = {item["id"]: item["source_ref"] for item in spec_items}
    trace_links: list[dict[str, Any]] = []
    for rubric_id, normalized_quote in trace_seeds:
        spec_id = spec_id_by_quote.get(normalized_quote)
        if spec_id is None:
            continue
        trace_links.append(
            {
                "rubric_id": rubric_id,
                "spec_ids": [spec_id],
                "rationale": (
                    f"{rubric_id} traces spec item {spec_id} via its declared "
                    "traceable spec quote."
                ),
                "evidence_quotes": [
                    {
                        "spec_id": spec_id,
                        "quote": normalized_quote,
                        "verification_mode": "token_sequence",
                        "source_ref": dict(source_ref_by_id[spec_id]),
                    }
                ],
                "semantic_status": "pending_verification",
            }
        )
    return trace_links


def _find_span(
    normalized_quote: str, spec_lines: list[str]
) -> tuple[int, int] | None:
    """Smallest 1-indexed [start, end] window whose text contains the quote."""
    total = len(spec_lines)
    best: tuple[int, int] | None = None
    for start in range(1, total + 1):
        for end in range(start, min(start + _MAX_QUOTE_WINDOW, total) + 1):
            window = "\n".join(spec_lines[start - 1 : end])
            if normalized_quote in _normalize(window):
                if best is None or (end - start) < (best[1] - best[0]):
                    best = (start, end)
                break
    return best


def _nearest_section(spec_lines: list[str], start_line: int) -> str:
    for index in range(start_line - 1, -1, -1):
        match = _SECTION_RE.match(spec_lines[index])
        if match:
            return match.group(1).strip()
    return ""


def _requirement_level(normalized_quote: str) -> str:
    return "must" if "must" in normalized_quote.lower() else "optional"
