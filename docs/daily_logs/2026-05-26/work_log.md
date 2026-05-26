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

## Slice 3 — `orphan_bonus_rubric_item` (Rule 1 completes; plan v1.10)

### Goals

- Close the last Rule 1 branch per plan §6: `evaluation_role == bonus` rubric items with no trace link surface as `informational` / `provisional` findings that do not block gating.
- Lock the finding type name in the plan (not just in HANDOFF) and record the naming convention so future Rule 1 / Rule 2 / Rule 3 finding types stay symmetric.

### Completed Work

#### Plan v1.9 → v1.10

- Replaced §6 Rule 1's bonus-handling line with a concrete contract: type literal `orphan_bonus_rubric_item`, severity `informational`, decision_status `provisional`, condition "trace link 없음", `semantic_status` is not consulted.
- Added a "Finding type naming convention" memo at the bottom of §6 Rule 1. Rule 1 no-trace findings share the `_rubric_item` suffix and differ only by prefix: `possible_orphan_scored` (scored, because `gate` may promote to confirmed) vs `orphan_bonus` (bonus, no symmetric promotion path). Any future Rule 1 extension (e.g. qualitative orphan, if scope grows) must follow the same convention without re-deciding.
- §15 v1.10 entry documents the change and notes that implementation in this slice matches the new plan body.

#### Rule 1 third branch

- Restructured the per-rubric loop in `run_rule_one`. The dispatch is now `evaluation_role == bonus` → bonus branch; `evaluation_role == scored` → scored branches; else continue. Bonus branch fires `orphan_bonus_rubric_item` only when `rubric_links` is empty.
- Expanded the `run_rule_one` docstring to describe all three branches in one place. References plan v1.10 §6 explicitly so future readers do not have to cross-reference HANDOFF.
- Module constant `HUMAN_ACCEPTED_SEMANTIC_STATUSES` (introduced in slice 2) is left in place but not consulted by the bonus branch per the plan memo.

#### CLI wiring

- `_cmd_check` adds a `review_orphan_bonus_rubric` next_action per informational finding (alongside `review_orphan_rubric` and `review_unconfirmed_trace_coverage`).
- Envelope gains `provisional_informational_count` so caller agents can distinguish "had no high/medium but did surface bonus orphans" from "had genuinely no findings".
- `COMMAND_CONTRACTS["check"]`: `informational` field list adds `provisional_informational_count`; `next_actions_types` adds `review_orphan_bonus_rubric`.

#### Two-directional regression guards

- Under-strict: bonus rubric without link → exactly one `orphan_bonus_rubric_item`, severity `informational`, decision_status `provisional`.
- Over-strict A (eight parametrized): bonus rubric WITH any link (any of the eight `semantic_status` values, including `human_accepted`) must not be flagged. Locks the plan v1.10 rule "semantic_status is not consulted for bonus" against any future drift toward Rule-1-style status checks for bonus items.
- Over-strict B: scored rubric without link emits only `possible_orphan_scored_rubric_item`, never `orphan_bonus_rubric_item`. Locks the mutual exclusivity by `evaluation_role`.
- Over-strict C: qualitative rubric without link produces zero findings. Qualitative is out of Rule 1's scope per plan §6.
- Integration guard `test_three_rubrics_three_branches_coexist`: one document with all three Rule 1 trigger patterns produces exactly three findings keyed by `rubric_id` → `(type, severity)`. Locks slice 1 + slice 2 + slice 3 against each other in one fast unit test.

#### Fixture extension

- `fixtures/orphan_scored_rubric/`: added R3 (bonus, untraced) to `rubric_items.yaml`; appended a third line "R3 Untraced bonus axis" to `source/rubric.md`; recomputed the sha256 in `source_manifest.yaml`. The fixture's primary intent (testing Rule 1 no-trace cases on scored rubrics) is unchanged; the bonus addition is a Rule 1 sub-case that lives naturally alongside per plan §7 (which lists only `orphan_scored_rubric` and not a separate bonus fixture).
- `tests/test_fixtures.py`: replaced `test_orphan_scored_rubric_fixture_emits_possible_orphan` with `test_orphan_scored_rubric_fixture_emits_all_three_rule_one_branches`. The new test asserts a complete `rubric_id → (type, severity, decision_status)` mapping for R1/R2/R3 — stricter than the previous version and shows the three branches coexisting on one fixture.

### Files Changed

- `docs/implementation_plan_assessment_harness_poc_v1.md` (v1.9 → v1.10)
- `src/assessment_harness/rules.py`
- `src/assessment_harness/cli.py`
- `tests/test_rules.py`
- `tests/test_fixtures.py`
- `fixtures/orphan_scored_rubric/rubric_items.yaml`
- `fixtures/orphan_scored_rubric/source/rubric.md`
- `fixtures/orphan_scored_rubric/source_manifest.yaml`

### Issues Found

- Problem: in slice 2's `test_bonus_qualitative_skipped_even_with_pending_links`, bonus rubrics with pending links were correctly excluded from `unconfirmed_trace_coverage`, but the test did not assert that they were *also* not flagged by some other Rule 1 branch. After slice 3 added the bonus branch, that test still passes (bonus+link → no finding), but the gap motivated the explicit over-strict A parametrization in slice 3 that enumerates all eight `semantic_status` values plus an inline assertion that `orphan_bonus_rubric_item` is empty.
- Outcome: 97 tests pass; slice 1/2/3 are pairwise locked by mutual exclusivity tests and the new three-way integration guard.

### Decisions

- Finding type literal goes in the plan body (not just HANDOFF or rules.py) so the canonical document is the only place a future worker has to consult. The slice 2.5 lesson — "if the resolution would change what another worker implements, put it in the plan" — is now applied proactively for finding type naming.
- The naming convention memo in plan §6 is deliberately compact: it states the rule (`{prefix_}orphan_{role}_rubric_item`) and the reason for the asymmetric `possible_` prefix (`gate` promotion path). Anything more detailed belongs in §15 changelog or per-slice work logs, not in the operational rule body.
- `provisional_informational_count` is added to the CLI envelope rather than being inferred from the findings list. Reason: informational counts will become important once Rule 1 / Rule 2 / Rule 3 are all live and a caller agent needs to distinguish "noise-free clean state" from "no high/medium but still has informational items to review".

---

## Slice 2.5 — plan v1.8 → v1.9: close the §6 Rule 1 spec gap surfaced after slice 2

### Goals

- Reconcile the canonical implementation plan with the slice 2 implementation so that the 1st-priority source of truth (plan) is not lagging behind the harness. Slice 2 had introduced an extension to plan §6 Rule 1 (treating `human_rejected` / `rerun_requested` as `unconfirmed_trace_coverage` triggers) but only recorded the decision in HANDOFF, leaving the plan body inconsistent with §5.3.1's own status table.
- Correct two related documentation defects flagged after slice 2: (1) HANDOFF's "Final-coverage boundary" decision claimed the boundary applied to Rule 2 too, but plan §6 Rule 2 is purely structural and does not consult `semantic_status`; (2) README and HANDOFF status notes still described Rule 1 as "slice 1 only" after slice 2 had landed; (3) the `unconfirmed_trace_coverage` message ended with "coverage is unconfirmed until final review", which is inaccurate when applied to `human_rejected` / `rerun_requested` (those states already reflect a completed review).

### Completed Work

#### Plan v1.8 → v1.9

- Rewrote plan §6 Rule 1's medium-provisional branch so that `unconfirmed_trace_coverage` fires for any link whose `semantic_status` is *not* `human_accepted` / `human_overridden`. The new wording explicitly names pre-review (`pending_verification`, `agent_*`) and post-review non-coverage (`human_rejected`, `rerun_requested`) states, matching §5.3.1's status table directly.
- Rewrote the confirmed-orphan third branch to clarify that `gate` (not `check`) promotes persistent medium provisional into `orphan_scored_rubric_item` (high / confirmed) after final review.
- Added a one-line scope clause: the final-coverage boundary applies to Rule 1 and `gate` only; Rule 2 / Rule 3 do not consult `semantic_status` and fire purely on §6's structural conditions.
- Added §15 v1.9 entry documenting the rationale (close §5.3.1 ↔ §6 gap) and noting that the implementation already matched the new wording (no code change needed for this slice).

#### HANDOFF Active Decisions correction

- Edited the "Rule 1 final-coverage boundary" entry to scope the boundary to Rule 1 and `gate` only. Explicitly notes that Rule 2 / Rule 3 are not affected — protects the next worker from over-implementing Rule 2 with semantic-status gates.
- Bumped canonical-spec version reference from v1.8 to v1.9.
- Updated rules.py description in the Project Structure block to reflect that `possible_orphan_scored_rubric_item` + `unconfirmed_trace_coverage` are both live; only the bonus informational branch and Rules 2-3 remain.
- Disambiguated the slice 1.5 historical entry: section numbers `§5.0 / §5.1 / §11` are unchanged in v1.9; the version reference is dropped from the historical landing note so readers do not confuse it with the current canonical version.

#### README status notes

- "Phase 0 진행 상태" row now reflects slice 2 (both Rule 1 branches live; bonus informational, Rule 2, Rule 3, and `gate` still pending).
- "문서" table canonical-version reference updated to v1.9.
- "필수 인자" callout for `--source-manifest` drops the version reference (section numbers are stable across v1.8 → v1.9).

#### Message wording generalized

- `rules.py`: `unconfirmed_trace_coverage` message tail changed from "coverage is unconfirmed until final review." to "coverage is not confirmed (pending verifier-agent results, final human review, or gate disposition).". The new wording is accurate for both pre-review and post-review non-coverage states. Verified manually on `clean_assignment` (status pending_verification): message renders correctly; pytest 85 still passes.

### Files Changed

- `docs/implementation_plan_assessment_harness_poc_v1.md` (v1.8 → v1.9)
- `HANDOFF.md`
- `README.md`
- `src/assessment_harness/rules.py`

### Issues Found

- Problem: at slice 2 entry I detected the §6 ↔ §5.3.1 gap but only recorded the resolution in HANDOFF rather than amending the plan body. This violated CLAUDE.md §1 (surface spec conflicts, do not silently pick a side). The plan was then briefly ahead of the source-of-truth document while HANDOFF carried the actual contract.
- Cause: I treated the gap as a downstream interpretation issue rather than as a spec edit. The rule-of-thumb here should be: if the resolution would change what a different worker implements, the plan body — not HANDOFF — is the right place for the resolution.
- Resolution: slice 2.5 (this work) lifts the resolution from HANDOFF into plan §6 Rule 1 and §15 v1.9. HANDOFF Active Decisions is rewritten as a *reference* to the plan rather than as the primary store of the decision. Going forward, any spec gap will surface to the user before implementation, and the plan body will be amended in the same slice that ships the implementation.
- Outcome: plan, code, and tests are now mutually consistent at v1.9.

### Decisions

- Plan is the only mechanism for changing rule semantics. HANDOFF Active Decisions becomes a curated index of where canonical decisions live in the plan, plus operational notes (smoke-run shapes, version anchoring) that have no place in the spec itself.
- Rule 2 and Rule 3 will be implemented strictly per plan §6 body — no semantic_status filtering. The Rule 1 boundary does not transfer; revisiting that decision will require a plan edit, not a HANDOFF note.
- Finding messages must be accurate for every lifecycle state the rule fires on. Future rule additions follow the same constraint.

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
