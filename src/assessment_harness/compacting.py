"""Union-based compacting for validated candidate artifacts."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


_SPEC_SECTION = "spec_item_candidates"
_RUBRIC_SECTION = "rubric_item_candidates"
_TRACE_SECTION = "trace_link_candidates"


class CompactingInputError(ValueError):
    """Raised when candidate artifacts cannot be compacted safely."""


@dataclass
class _Group:
    canonical_id: str
    entity_type: str
    identity_basis: str
    primary: dict[str, Any]
    variants: list[dict[str, Any]] = field(default_factory=list)
    run_refs: list[dict[str, str]] = field(default_factory=list)
    found_in_runs: set[str] = field(default_factory=set)


def compact_validated_candidates(
    candidate_runs: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Compact fully validated candidate runs into canonical artifacts.

    This helper deliberately does not choose winners. It groups candidates by
    the configured identity basis, preserves every grouped proposal as a
    variant, and excludes any candidate whose run has not reached
    ``integrity_status: validated``.
    """
    identity_policy = _identity_policy(policy)
    valid_run_ids = _valid_run_ids(candidate_runs)

    spec_groups, spec_id_map = _compact_item_section(
        candidate_runs=candidate_runs,
        valid_run_ids=valid_run_ids,
        section=_SPEC_SECTION,
        entity_type="spec_item",
        canonical_prefix="S",
        identity_basis=identity_policy["spec_item"],
        identity_key=_spec_identity_key,
    )
    rubric_groups, rubric_id_map = _compact_item_section(
        candidate_runs=candidate_runs,
        valid_run_ids=valid_run_ids,
        section=_RUBRIC_SECTION,
        entity_type="rubric_item",
        canonical_prefix="R",
        identity_basis=identity_policy["rubric_item"],
        identity_key=_rubric_identity_key,
    )
    trace_groups = _compact_trace_links(
        candidate_runs=candidate_runs,
        valid_run_ids=valid_run_ids,
        identity_basis=identity_policy["trace_link"],
        spec_id_map=spec_id_map,
        rubric_id_map=rubric_id_map,
    )

    return {
        "spec_items": _materialize_groups(spec_groups, valid_run_ids),
        "rubric_items": _materialize_groups(rubric_groups, valid_run_ids),
        "trace_links": _materialize_groups(trace_groups, valid_run_ids),
        "id_map": _materialize_id_map(
            [*spec_groups, *rubric_groups, *trace_groups]
        ),
    }


def _identity_policy(policy: Mapping[str, Any]) -> dict[str, str]:
    compacting = policy.get("compacting", {})
    if not isinstance(compacting, Mapping):
        compacting = {}
    basis = compacting.get("identity_basis", {})
    if not isinstance(basis, Mapping):
        basis = {}
    return {
        "spec_item": str(basis.get("spec_item", "source+section+normalized_text")),
        "rubric_item": str(basis.get("rubric_item", "title+normalized_description")),
        "trace_link": str(basis.get("trace_link", "rubric_id+sorted(spec_ids)")),
    }


def _valid_run_ids(candidate_runs: Sequence[Mapping[str, Any]]) -> set[str]:
    run_ids: set[str] = set()
    for candidate_run in candidate_runs:
        run_id = validated_candidate_run_id(candidate_run)
        if run_id is not None:
            run_ids.add(run_id)
    return run_ids


def validated_candidate_run_id(candidate_run: Mapping[str, Any]) -> str | None:
    """Return the run ID when the whole candidate-run artifact is validated."""
    seen_run_ids: set[str] = set()
    saw_candidate = False
    for section in (_SPEC_SECTION, _RUBRIC_SECTION, _TRACE_SECTION):
        entries = candidate_run.get(section, [])
        if not isinstance(entries, list):
            return None
        for entry in entries:
            if not isinstance(entry, Mapping):
                return None
            saw_candidate = True
            run_id = entry.get("agent_run_id")
            if (
                entry.get("integrity_status") != "validated"
                or not isinstance(entry.get("proposed_item"), Mapping)
                or not isinstance(entry.get("candidate_id"), str)
                or not isinstance(run_id, str)
            ):
                return None
            seen_run_ids.add(run_id)
    if not saw_candidate or len(seen_run_ids) != 1:
        return None
    return next(iter(seen_run_ids))


def _compact_item_section(
    *,
    candidate_runs: Sequence[Mapping[str, Any]],
    valid_run_ids: set[str],
    section: str,
    entity_type: str,
    canonical_prefix: str,
    identity_basis: str,
    identity_key: Any,
) -> tuple[list[_Group], dict[tuple[str, str], str]]:
    groups_by_key: dict[tuple[Any, ...], _Group] = {}
    groups: list[_Group] = []
    local_to_canonical: dict[tuple[str, str], str] = {}

    for candidate in _iter_validated_candidates(
        candidate_runs, valid_run_ids, section
    ):
        proposed_item = candidate["proposed_item"]
        key = identity_key(proposed_item, identity_basis)
        group = groups_by_key.get(key)
        if group is None:
            canonical_id = f"{canonical_prefix}{len(groups) + 1}"
            group = _Group(
                canonical_id=canonical_id,
                entity_type=entity_type,
                identity_basis=identity_basis,
                primary=_canonical_item(proposed_item, canonical_id),
            )
            groups_by_key[key] = group
            groups.append(group)
        _add_candidate_to_group(group, candidate, local_id=str(proposed_item["id"]))
        local_to_canonical[(str(candidate["agent_run_id"]), str(proposed_item["id"]))] = (
            group.canonical_id
        )

    return groups, local_to_canonical


def _compact_trace_links(
    *,
    candidate_runs: Sequence[Mapping[str, Any]],
    valid_run_ids: set[str],
    identity_basis: str,
    spec_id_map: Mapping[tuple[str, str], str],
    rubric_id_map: Mapping[tuple[str, str], str],
) -> list[_Group]:
    groups_by_key: dict[tuple[Any, ...], _Group] = {}
    groups: list[_Group] = []

    for candidate in _iter_validated_candidates(
        candidate_runs, valid_run_ids, _TRACE_SECTION
    ):
        proposed_item = candidate["proposed_item"]
        run_id = str(candidate["agent_run_id"])
        remapped = _remap_trace_link(proposed_item, run_id, spec_id_map, rubric_id_map)
        key = _trace_identity_key(remapped, identity_basis)
        group = groups_by_key.get(key)
        if group is None:
            group = _Group(
                canonical_id=f"T{len(groups) + 1}",
                entity_type="trace_link",
                identity_basis=identity_basis,
                primary=remapped,
            )
            groups_by_key[key] = group
            groups.append(group)
        _add_candidate_to_group(
            group, candidate, local_id=str(candidate["candidate_id"])
        )

    return groups


def _iter_validated_candidates(
    candidate_runs: Sequence[Mapping[str, Any]],
    valid_run_ids: set[str],
    section: str | None = None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    sections = [section] if section else [_SPEC_SECTION, _RUBRIC_SECTION, _TRACE_SECTION]
    for candidate_run in candidate_runs:
        for current_section in sections:
            entries = candidate_run.get(current_section, [])
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if (
                    isinstance(entry, Mapping)
                    and entry.get("integrity_status") == "validated"
                    and isinstance(entry.get("proposed_item"), Mapping)
                    and isinstance(entry.get("agent_run_id"), str)
                    and isinstance(entry.get("candidate_id"), str)
                    and entry.get("agent_run_id") in valid_run_ids
                ):
                    candidates.append(copy.deepcopy(dict(entry)))
    return candidates


def _canonical_item(proposed_item: Mapping[str, Any], canonical_id: str) -> dict[str, Any]:
    item = copy.deepcopy(dict(proposed_item))
    item["id"] = canonical_id
    return item


def _add_candidate_to_group(
    group: _Group,
    candidate: Mapping[str, Any],
    *,
    local_id: str,
) -> None:
    run_id = str(candidate["agent_run_id"])
    group.found_in_runs.add(run_id)
    group.run_refs.append({"run_id": run_id, "local_id": local_id})
    group.variants.append(
        {
            "run_id": run_id,
            "candidate_id": candidate["candidate_id"],
            "proposed_item": copy.deepcopy(dict(candidate["proposed_item"])),
        }
    )


def _materialize_groups(
    groups: Sequence[_Group],
    valid_run_ids: set[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for group in groups:
        item = copy.deepcopy(group.primary)
        item["support"] = {
            "total_valid_runs": len(valid_run_ids),
            "found_in_runs": sorted(group.found_in_runs),
        }
        item["identity_basis"] = group.identity_basis
        item["variants"] = group.variants
        item["sources"] = [
            {"kind": "agent_run", "run_id": run_id}
            for run_id in sorted(group.found_in_runs)
        ]
        if group.entity_type == "trace_link":
            item["reviewed_by"] = None
            item["reviewed_at"] = None
        items.append(item)
    return items


def _materialize_id_map(groups: Sequence[_Group]) -> list[dict[str, Any]]:
    return [
        {
            "canonical_id": group.canonical_id,
            "entity_type": group.entity_type,
            "run_refs": group.run_refs,
        }
        for group in groups
    ]


def _remap_trace_link(
    proposed_item: Mapping[str, Any],
    run_id: str,
    spec_id_map: Mapping[tuple[str, str], str],
    rubric_id_map: Mapping[tuple[str, str], str],
) -> dict[str, Any]:
    rubric_id = rubric_id_map.get((run_id, str(proposed_item.get("rubric_id"))))
    spec_ids = [
        spec_id_map.get((run_id, str(spec_id)))
        for spec_id in proposed_item.get("spec_ids", [])
    ]
    if rubric_id is None:
        raise CompactingInputError(
            f"trace link in run {run_id} references unmapped rubric_id "
            f"{proposed_item.get('rubric_id')!r}"
        )
    if any(spec_id is None for spec_id in spec_ids):
        raise CompactingInputError(
            f"trace link in run {run_id} references unmapped spec_ids "
            f"{proposed_item.get('spec_ids', [])!r}"
        )

    remapped = copy.deepcopy(dict(proposed_item))
    remapped["rubric_id"] = rubric_id
    remapped["spec_ids"] = [str(spec_id) for spec_id in spec_ids]
    for quote in remapped.get("evidence_quotes", []):
        if isinstance(quote, dict):
            spec_id = spec_id_map.get((run_id, str(quote.get("spec_id"))))
            if spec_id is not None:
                quote["spec_id"] = spec_id
    return remapped


def _spec_identity_key(item: Mapping[str, Any], identity_basis: str) -> tuple[Any, ...]:
    source_ref = item.get("source_ref", {})
    if not isinstance(source_ref, Mapping):
        source_ref = {}
    return (
        identity_basis,
        source_ref.get("document_id", item.get("source", "")),
        item.get("section", ""),
        _normalize_text(str(item.get("text", ""))),
    )


def _rubric_identity_key(item: Mapping[str, Any], identity_basis: str) -> tuple[Any, ...]:
    return (
        identity_basis,
        _normalize_text(str(item.get("title", ""))),
        _normalize_text(str(item.get("description", ""))),
    )


def _trace_identity_key(item: Mapping[str, Any], identity_basis: str) -> tuple[Any, ...]:
    return (
        identity_basis,
        item.get("rubric_id", ""),
        tuple(sorted(str(spec_id) for spec_id in item.get("spec_ids", []))),
    )


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()
