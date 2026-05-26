# Work Log - 2026-05-26

## Goals

- Begin Rule 1 (Scored Rubric Coverage) in the smallest possible vertical slice.
- Land the no-trace branch of Rule 1 (`possible_orphan_scored_rubric_item`) with two-directional regression guards, leaving the `unconfirmed_trace_coverage` and bonus-informational branches for follow-up slices.

## Completed Work

### Rule 1 slice 1 — `possible_orphan_scored_rubric_item`

- Added `run_rule_one(rubric_items_doc, trace_links_doc) -> list[Finding]` to `src/assessment_harness/rules.py`. The first slice emits only the no-trace branch: any `evaluation_role == scored` rubric item that has zero compacted trace links surfaces as a `high` / `provisional` finding. The function trusts Rule 0's prior invariants (unique rubric IDs, no dangling refs) and runs only after Rule 0 reports no high diagnostics.
- Added `finding_severity_counts` helper to mirror `severity_counts` for the new `Finding`-based code path.
- Wired the CLI in `src/assessment_harness/cli.py`: after a clean Rule 0 pass, `_cmd_check` runs Rule 1, and any provisional findings yield `status=provisional_findings`, `exit_code=0`, `blocking_count=0` per plan §4.1 / §10.3 (only `gate` ever emits a final blocking verdict). Per-finding `next_actions` of type `review_orphan_rubric` are appended with the offending `rubric_id`.
- Extended the `check` command contract in `COMMAND_CONTRACTS`: added `provisional_high_count` / `provisional_medium_count` to the informational field list, added `review_orphan_rubric` to `next_actions_types`, and rewrote the exit code `0` semantics to cover both `success` (no findings) and `provisional_findings` outcomes.

Files changed:

- `src/assessment_harness/rules.py`
- `src/assessment_harness/cli.py`

Effect:

- The `check` command now produces a meaningful agent-consumable finding for the orphan-scored class, with stable next-action shape so a caller agent can drive review without parsing prose.

### Two-directional regression guards (plan §10.1, CLAUDE.md §4)

- Added four unit tests in `tests/test_rules.py`:
  - Under-strict guard: a scored rubric with no trace link must yield exactly one `possible_orphan_scored_rubric_item` finding (`severity=high`, `decision_status=provisional`, correct `rubric_id`). If the no-link branch is dropped, the rule has gone silent and this test fails.
  - Over-strict guard A: a scored rubric *with* a trace link (any `semantic_status`, including `pending_verification`) must not be flagged. If a future slice mishandles semantic status and over-promotes pending coverage into the orphan branch, this guard catches it.
  - Over-strict guard B: a `bonus` or `qualitative` rubric without a trace must not be flagged as a scored orphan. Bonus orphans get a distinct informational finding in a later slice; qualitative items are out of Rule 1's scope.
  - Baseline guard: the existing Rule 0 baseline (R1 scored, traced to S1) must produce no Rule 1 findings either, so the existing clean fixture stays clean.

Files changed:

- `tests/test_rules.py`

Effect:

- Slice 1 is locked in both directions; future slices cannot regress it silently.

### `orphan_scored_rubric` fixture and end-to-end test

- Created `fixtures/orphan_scored_rubric/` with `spec_items.yaml`, `rubric_items.yaml`, `trace_links.yaml`, and `policy.yaml`. The fixture has one spec (S1) and two scored rubrics (R1, R2) where only R1 is traced. The fixture deliberately omits `source_manifest.yaml` because Rule 0 grounding diagnostics are orthogonal to Rule 1 and adding manifest/source files would only pad the surface area for this slice.
- Added `test_orphan_scored_rubric_fixture_emits_possible_orphan` to `tests/test_fixtures.py`. The end-to-end test runs the CLI through `main(...)`, then asserts: exit code 0, `status=provisional_findings`, `blocking_count=0`, exactly one `possible_orphan_scored_rubric_item` finding on R2, and Rule 0 summary still clean.

Files changed:

- `fixtures/orphan_scored_rubric/spec_items.yaml`
- `fixtures/orphan_scored_rubric/rubric_items.yaml`
- `fixtures/orphan_scored_rubric/trace_links.yaml`
- `fixtures/orphan_scored_rubric/policy.yaml`
- `tests/test_fixtures.py`

Effect:

- The new fixture is a permanent regression artefact for the orphan-scored case. Manual smoke run via `docker compose run --rm harness ... check ...` reproduces the same envelope shape as the unit tests, confirming the agent-consumable contract.

## Issues Found

- Problem: when first sketching Rule 1, an initial interpretation would have produced `unconfirmed_trace_coverage` findings for every pre-review fixture (including `clean_assignment`, whose trace links carry `semantic_status: pending_verification`). That would invalidate the existing "clean fixture = no findings, exit 0" baseline used by callers.
- Cause: plan §6 Rule 1 only counts `human_accepted` / `human_overridden` as final coverage, and Phase 0 has no final review yet.
- Resolution: scoped slice 1 to the no-trace branch only. Slice 2 (`unconfirmed_trace_coverage`) is split out and will need a paired decision on whether `clean_assignment` should be relabelled as `human_accepted` to remain the canonical "all-green" reference. Recorded the decision as "Next Tasks" in HANDOFF.md so it is visible before slice 2 starts.
- Outcome: clean_assignment still passes with `status=success`, the orphan fixture surfaces the new finding, and no existing assertion changed.

## Decisions

- Slice Rule 1 by branch rather than by file: each `Finding` type lands in its own iteration with its own fixture and its own under/over-strict guards. Cost: one shared `run_rule_one` body grows over three iterations. Benefit: each iteration is reviewable in isolation and the regression surface stays interpretable.
- `check` never sets `blocking_count > 0`, even when high-severity provisional findings exist. Only `gate` produces blocking counts after final review. Matches plan §4.1 explicitly.
- `next_actions` carry one entry per finding rather than a roll-up. Agents drive review per-rubric, and the per-rubric shape lets them parallelise without de-dupe logic on stable core fields.

## Next Steps

- Slice 2: implement `unconfirmed_trace_coverage` (medium, provisional) for scored rubrics whose links exist but contain no `human_accepted` / `human_overridden`. Decide at slice-2 entry whether `clean_assignment` should be relabelled to `human_accepted` to remain the canonical clean baseline, or whether a separate "post-review clean" fixture is more accurate.
- Slice 3: bonus-orphan informational finding for `evaluation_role == bonus` rubrics without trace links.
- After Rule 1 is complete (3 slices), proceed to Rule 2 (Required Spec Coverage) and Rule 3 (Optionality Consistency) with their own paired fixtures (`required_spec_unscored`, `optionality_mismatch`).
