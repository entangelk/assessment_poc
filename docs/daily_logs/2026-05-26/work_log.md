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

- Slice 2: implement `unconfirmed_trace_coverage` (medium, provisional) for scored rubrics whose links exist but contain no `human_accepted` / `human_overridden`. Decision recorded below: keep `clean_assignment` as-is (`pending_verification`) and treat the resulting medium findings as the expected pre-review state; do not synthesize human-accepted relabels.
- Slice 3: bonus-orphan informational finding for `evaluation_role == bonus` rubrics without trace links.
- After Rule 1 is complete (3 slices), proceed to Rule 2 (Required Spec Coverage) and Rule 3 (Optionality Consistency) with their own paired fixtures (`required_spec_unscored`, `optionality_mismatch`).

---

## Slice 2 — `unconfirmed_trace_coverage` finding

### Goals

- Add the second Rule 1 branch per plan §6: scored rubrics whose trace links exist but carry no final-coverage `semantic_status` (`human_accepted` / `human_overridden`) must surface as `unconfirmed_trace_coverage` (medium / provisional).
- Update the `clean_assignment` E2E baseline to reflect that the canonical pre-review state is `status=provisional_findings` with medium findings, not `status=success`. The PoC's automation flow never reaches `human_accepted` on its own, so the medium baseline is what callers will actually see.

### Completed Work

#### Rule 1 slice 2 branch

- Extended `run_rule_one` in `src/assessment_harness/rules.py` to inspect each scored rubric's trace links. The control flow is now:
  - No links for a scored rubric → `possible_orphan_scored_rubric_item` (slice 1).
  - Any link with `semantic_status in {human_accepted, human_overridden}` → coverage confirmed, no finding.
  - Otherwise → `unconfirmed_trace_coverage` (medium / provisional) with `evidence={"link_count": N, "semantic_statuses": [...]}` so caller agents can drill into which statuses are present.
- Introduced module constant `HUMAN_ACCEPTED_SEMANTIC_STATUSES` so the same boundary is reusable in slice 3 / Rule 2 / `gate`.
- The two branches are mutually exclusive: each scored rubric produces at most one Rule 1 finding.

#### CLI wiring

- `_cmd_check` appends a `review_unconfirmed_trace_coverage` next_action per medium finding (alongside the existing `review_orphan_rubric` for highs).
- `COMMAND_CONTRACTS["check"].next_actions_types` adds `review_unconfirmed_trace_coverage`.

#### Two-directional regression guards

- Six parametrized under-strict guards covering every non-final-coverage `semantic_status` (`pending_verification`, `agent_supported`, `agent_rejected`, `agent_uncertain`, `human_rejected`, `rerun_requested`). Plus a missing-`semantic_status` variant.
- Over-strict guard A (two-parametrized): `human_accepted` and `human_overridden` must suppress the finding.
- Over-strict guard B: among multiple links for the same rubric, ONE `human_accepted` is enough to suppress the finding even if the others remain pending.
- Over-strict guard C: a scored rubric with no link emits only `possible_orphan_*`, not also `unconfirmed_trace_coverage` — protects against double-counting.
- Over-strict guard D: `bonus` and `qualitative` rubrics stay out of the unconfirmed branch even with pending links (bonus orphans are slice 3 territory).
- The previous baseline test `test_rule_one_emits_no_findings_on_baseline` was renamed to `test_rule_one_baseline_emits_unconfirmed_trace_coverage` and rewritten to reflect that the baseline (R1 scored, traced with no semantic_status) is now a medium finding, not a clean pass.

#### E2E test updates

- `test_clean_assignment_yields_pre_review_unconfirmed_trace_coverage` (replacing `test_clean_assignment_passes_check_with_manifest`): asserts `status=provisional_findings`, `blocking_count=0`, exactly two `unconfirmed_trace_coverage` findings on R1 and R2 (both scored, both with pending_verification links), and that no other finding types appear (over-strict on the same baseline).
- `test_orphan_scored_rubric_fixture_emits_possible_orphan` now asserts BOTH branches: 1 high `possible_orphan_scored_rubric_item` on R2, 1 medium `unconfirmed_trace_coverage` on R1.
- `test_check_clean_fixture_returns_success` in `tests/test_cli_output_contract.py` (kept under the same name because the contract test still verifies "clean fixture → exit 0"; just the success-vs-provisional shape changed) and `test_check_documented_form_with_trailing_output` were rewritten to expect `status=provisional_findings` plus two `review_unconfirmed_trace_coverage` next_actions.

### Files Changed

- `src/assessment_harness/rules.py`
- `src/assessment_harness/cli.py`
- `tests/test_rules.py`
- `tests/test_fixtures.py`
- `tests/test_cli_output_contract.py`

### Issues Found

- Problem: `human_rejected` / `rerun_requested` are not listed in plan §6 Rule 1's literal enumeration of pre-review states (only `pending_verification` / `agent_*`). However, plan also says only `human_accepted` / `human_overridden` count as final coverage. The two enumerations don't quite match.
- Cause: plan §6 enumerates the "pre-review" states explicitly but doesn't enumerate the "post-review-rejected" states symmetrically.
- Resolution: implementation treats any `semantic_status` *outside* the human-accepted set (including post-review rejections) as triggering `unconfirmed_trace_coverage`. Rationale: such links are not coverage; only `gate` should make the confirmed `orphan_scored_rubric_item` call after final review. The parametrized under-strict tests explicitly include `human_rejected` and `rerun_requested` to lock this behaviour in. Surface this in HANDOFF Active Decisions so slice 3 / gate work uses the same boundary.
- Outcome: rule passes 85 tests; canonical `clean_assignment` baseline now reflects automation-only reality.

### Decisions

- Final-coverage boundary is `{human_accepted, human_overridden}`. Everything else (including post-review `human_rejected` / `rerun_requested`) is non-coverage. `gate` is responsible for promoting persistent non-coverage into `orphan_scored_rubric_item` (confirmed) after final review.
- `unconfirmed_trace_coverage` carries `evidence={"link_count", "semantic_statuses"}` for caller-agent triage. This is the minimum needed for an agent to decide between "still in `verify` lifecycle" vs "stuck after review" without re-walking the trace_links file.
- `clean_assignment` keeps `pending_verification` on its trace links per the user's automation-first decision. The PoC's canonical clean fixture is therefore a *medium-findings* baseline; reaching `status=success` requires final-review evidence which Phase 3 will supply.

---

## Slice 1.5 — `--source-manifest` made mandatory (plan v1.8)

### Goals

- Close a spec/implementation drift surfaced during slice 1 review: the new `orphan_scored_rubric` fixture had no source manifest, and the CLI silently allowed manifest-less runs even though plan §5.0 / §5.1 / §11 declare snapshot grounding as part of the Phase 0 input contract.
- Make `--source-manifest` a Phase 0 required input, ground the two non-clean fixtures, bump the plan to v1.8, and add two-directional regression guards for the new behaviour.

### Completed Work

#### Ground `fixtures/reference_integrity/`

- Added `source/spec.md` and `source/rubric.md` so each `source_ref` resolves to a real line: `spec.md` has the three lines matching the duplicated S1, the duplicate-id-trigger sentence, and S2; `rubric.md` has five lines covering the R1 1-2 span, the R2 3-4 span, and the duplicated R1 at line 5.
- Added `source_manifest.yaml` with computed sha256 digests for both files.

#### Ground `fixtures/orphan_scored_rubric/`

- Added `source/spec.md` (S1 text on line 1), `source/rubric.md` (R1 line 1, R2 line 2), and `source_manifest.yaml`.

#### Mandate `--source-manifest` in the CLI

- `_cmd_check` now short-circuits before any YAML load when `args.source_manifest` is empty. The new `_check_missing_manifest` helper writes a single `source_manifest_required` diagnostic (severity `high`), records `input_error` on the findings payload, and returns `status=invalid_input`, exit `2`, with a `provide_source_manifest` next_action.
- argparse keeps `default=None` (not `required=True`) so callers always receive a structured envelope on stdout instead of argparse's usage text on stderr — recorded the rationale inline in `cli.py` and in plan §15 v1.8.
- `COMMAND_CONTRACTS["check"]` adds `provide_source_manifest` to `next_actions_types`.
- `schemas/integrity_diagnostics.schema.json` enum adds `source_manifest_required`.

#### Two-directional regression guards

- Under-strict guard `test_check_without_source_manifest_returns_invalid_input`: omits `--source-manifest`, asserts exit `2`, `status=invalid_input`, next_action `provide_source_manifest`, and the diagnostics file contains `source_manifest_required`.
- Over-strict guard `test_check_with_source_manifest_does_not_surface_manifest_required`: clean fixture WITH manifest must not synthesize the diagnostic; catches a regression where `source_manifest_required` fires unconditionally.
- Updated the existing missing-input and stderr-separation tests to pass a non-existent manifest path so they continue exercising the YAML not-found and stderr-separation paths after slice 1.5 (otherwise they would short-circuit on missing manifest).
- Removed `test_clean_assignment_passes_check_without_manifest` — the manifest-less happy path no longer exists.
- Flipped `test_orphan_scored_rubric_fixture_emits_possible_orphan` and `test_reference_integrity_fixture_blocks_with_exit_two` to `use_manifest=True`, exercising both grounded fixtures end-to-end.

### Files Changed

- `fixtures/reference_integrity/source/spec.md`, `source/rubric.md`, `source_manifest.yaml`
- `fixtures/orphan_scored_rubric/source/spec.md`, `source/rubric.md`, `source_manifest.yaml`
- `src/assessment_harness/cli.py`
- `schemas/integrity_diagnostics.schema.json`
- `tests/test_cli_output_contract.py`
- `tests/test_fixtures.py`
- `docs/implementation_plan_assessment_harness_poc_v1.md` (v1.7 → v1.8)

### Issues Found

- Problem: with all three fixtures grounded, `reference_integrity` reports nine high diagnostics instead of the eight unique codes the test enumerates. Cause: `evidence_quote_missing_for_spec_id` legitimately fires twice (link 2 has spec_id S2 but evidence covers only S99, and link 5 has spec_ids S1/S2 but evidence covers only S1) — the duplicate has always been present; the existing assertion used `>=` so the count went unnoticed. Outcome: no regression. Documented here so the next iteration does not chase the apparent jump from 8 to 9.

### Decisions

- argparse `--source-manifest` stays optional in the parser; mandate is enforced inside `_cmd_check`. Tradeoff: callers get the structured envelope and a typed next_action instead of argparse usage text. Cost: looser argparse usage line. Worth it because the CLI's primary user is an AI agent.
- `source_manifest_required` is a Rule 0 diagnostic, not a generic input error. Tradeoff: keeps Rule 0's "any high diagnostic → invalid_input / exit 2" boundary intact and lets agents inspect the diagnostics file for the structured cause; also keeps the integrity_diagnostics schema as the single registry of input-integrity failures.
- Plan bumped to v1.8 in the canonical implementation document rather than ammending a footnote. Rationale: the input contract change is meaningful enough that future readers need to find it in the version history rather than in a code comment.
