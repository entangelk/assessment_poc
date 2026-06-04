"""Read-only source-spec tools for framework-neutral agent runners."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from assessment_harness.models import HarnessInputError


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def list_sections(spec_path: Path) -> list[dict[str, Any]]:
    """Return Markdown heading sections with stable line spans."""
    sections = _markdown_sections(spec_path)
    return [
        {
            "title": section["title"],
            "level": section["level"],
            "start_line": section["start_line"],
            "content_start_line": section["content_start_line"],
            "end_line": section["end_line"],
        }
        for section in sections
    ]


def read_spec_section(spec_path: Path, section: str) -> dict[str, Any]:
    """Return one Markdown section by exact title, case-insensitive."""
    requested = _normalize_title(section)
    matches = [
        item
        for item in _markdown_sections(spec_path)
        if _normalize_title(str(item["title"])) == requested
    ]
    if not matches:
        raise HarnessInputError(f"section not found: {section}")
    if len(matches) > 1:
        raise HarnessInputError(f"section title is ambiguous: {section}")
    return matches[0]


def _markdown_sections(spec_path: Path) -> list[dict[str, Any]]:
    if not spec_path.exists():
        raise HarnessInputError(f"spec file not found: {spec_path}")
    lines = spec_path.read_text(encoding="utf-8").splitlines()
    headings: list[tuple[int, str, int]] = []
    for index, line in enumerate(lines, start=1):
        match = _HEADING_RE.match(line)
        if match:
            headings.append((len(match.group(1)), match.group(2).strip(), index))

    sections: list[dict[str, Any]] = []
    for heading_index, (level, title, start_line) in enumerate(headings):
        raw_end_line = len(lines)
        for next_level, _next_title, next_line in headings[heading_index + 1 :]:
            if next_level <= level:
                raw_end_line = next_line - 1
                break
        content_start_line = start_line + 1
        end_line = raw_end_line
        while content_start_line <= raw_end_line and not lines[
            content_start_line - 1
        ].strip():
            content_start_line += 1
        while end_line >= content_start_line and not lines[end_line - 1].strip():
            end_line -= 1
        if content_start_line > end_line:
            content_start_line = raw_end_line
            end_line = raw_end_line
            content_lines: list[str] = []
        else:
            content_lines = lines[content_start_line - 1 : end_line]
        sections.append(
            {
                "title": title,
                "level": level,
                "start_line": start_line,
                "content_start_line": content_start_line,
                "end_line": end_line,
                "text": "\n".join(content_lines).strip(),
            }
        )
    return sections


def _normalize_title(title: str) -> str:
    return " ".join(title.strip().lower().split())
