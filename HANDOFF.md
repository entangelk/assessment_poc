# Handoff

## Current Status

- Implementation plan is at v1.11 (`docs/implementation_plan_assessment_harness_poc_v1.md`) and is the canonical implementation source of truth, ahead of `docs/ideation_assessment_harness_v2.2.md` (revised in-place 2026-05-27, supersedes v2.1).
- **Rule 0 is live**: source snapshot grounding, evidence completeness/reference-integrity checks, mandatory `--source-manifest`, and structured invalid-input recovery are implemented.
- **Rule 1 is feature-complete** (plan v1.11 §6): `possible_orphan_scored_rubric_item`, `unconfirmed_trace_coverage`, and `orphan_bonus_rubric_item` are all implemented. The CLI exposes their review actions and provisional severity counts; slice 3.1 locks the public envelope/schema contract, including the bonus-only `(high=0, medium=0, informational=1)` boundary.
- **Pending implementation**: Rule 2, Rule 3, and `gate`. Rule 2/3 remain structural rules and must not inherit Rule 1's `semantic_status` coverage boundary.
- **Lint Rule family added to spec (plan v1.11, 2026-05-27)**: §6 of plan v1.11 now specs Rule L1 (`double_scored_spec`, medium), L5 (`bonus_grades_mandatory_only`, medium), L6 (`mandatory_spec_bonus_only_traced`, high) — all L-DET, all spec-only. Code not yet written. §5.6 adds `drift_observations[]` to Final Review Record (manual channel for Rule L8 territory). §5.7 adds `double_scoring_review` and `mandatory_spec_bonus_review` review_queue entry types. Source: ideation v2.2.
- Package surface: `check` / `schema` / `report` subcommands, eight JSON Schemas, three fully-grounded fixtures (`clean_assignment`, `reference_integrity`, `orphan_scored_rubric` with R3 bonus untraced), and 98 passing tests. Docker is the canonical dev environment.
- The PoC is an **agent-level harness**: the 1st-class caller is an AI agent (Claude Code / Codex / Gemini), not a human. Humans participate only as final reviewers.
- The final workflow is `extract --runs N -> compact -> verify --runs N -> check -> report -> review -> gate`. Compacting is a **union-based audit operation**: every valid candidate is preserved with `support` / `identity_basis` / `variants`.

## Quick Start (dev)

```bash
docker compose build
docker compose run --rm test            # full pytest suite
docker compose run --rm harness --help  # CLI help
```

End-to-end Rule 0 sanity check on the clean fixture:

```bash
docker compose run --rm harness --output json check \
  --spec-items fixtures/clean_assignment/spec_items.yaml \
  --rubric-items fixtures/clean_assignment/rubric_items.yaml \
  --trace-links fixtures/clean_assignment/trace_links.yaml \
  --source-manifest fixtures/clean_assignment/source_manifest.yaml \
  --policy fixtures/clean_assignment/policy.yaml \
  --out work/findings.json \
  --diagnostics-out work/integrity_diagnostics.json
```

## Active Decisions (Adopted)

- **Canonical specification**: v1.11 implementation plan first, then `v2.2` ideation (revised in-place 2026-05-27). v2.1 and earlier ideation versions are historical; v2.2 supersedes v2.1 in any overlapping area without area limits.
- **Rule 1 finding type naming convention** (plan v1.11 §6): no-trace findings follow `{prefix_}orphan_{role}_rubric_item`. `possible_` prefix marks scored items because `gate` may promote them to confirmed; bonus / qualitative have no symmetric promotion path so prefix is omitted. Any future Rule 1 extension applies the same convention without re-deciding the literal.
- **`--source-manifest` is a required `check` input** (plan v1.11 §5.0 / §5.1 / §11): Phase 0 mandates immutable source snapshot grounding. Missing manifest → `status=invalid_input` / exit `2` / diagnostic `source_manifest_required` / next_action `provide_source_manifest`. argparse keeps the flag declared as `default=None` so caller agents always receive the structured envelope on stdout instead of argparse's usage text on stderr.
- **Rule 1 final-coverage boundary** (plan v1.11 §6 Rule 1, §5.3.1): the only `semantic_status` values that count as final coverage for Rule 1 are `human_accepted` and `human_overridden`. Everything else — pre-review (`pending_verification`, `agent_*`) and post-review non-coverage (`human_rejected`, `rerun_requested`) — surfaces as `unconfirmed_trace_coverage` (medium / provisional) in `check`. `gate` is the only stage that may promote persistent non-coverage into a confirmed `orphan_scored_rubric_item`. **This boundary applies to Rule 1 and `gate` only.** Rule 2 and Rule 3 do not consult `semantic_status` (they use the structural conditions in plan §6 Rule 2 / Rule 3). Lint family (Rule L1/L5/L6) also does not consult `semantic_status` — L-DET, structural only.
- **Lint family naming convention** (plan v1.11 §6, ideation v2.2 §3): family prefix `Rule L*`; finding types follow ideation candidates verbatim (`double_scored_spec`, `bonus_grades_mandatory_only`, `mandatory_spec_bonus_only_traced`) — readability over uniformity with Rule 1's `{prefix}_{role}_rubric_item` pattern. Owner-confirmed.
- **Lint safeguard mechanism** (plan v1.11 §6 Rule L1 / L6): medium/high lint findings carry both extended payload (full context for human review) AND a paired `review_queue` entry (`double_scoring_review` for L1, `mandatory_spec_bonus_review` for L6). Single mechanism reused across L1 and L6 — adding either rule first creates the schema/code path, the other reuses it.
- **`clean_assignment` is an automation-only baseline**: trace links stay on `pending_verification` so the fixture matches the state a real agent run produces. The canonical pre-review outcome is therefore `status=provisional_findings` with N medium `unconfirmed_trace_coverage` findings, not `status=success`. Reaching `success` requires final-review evidence, which Phase 3 will supply.
- **Rule 0 evidence verification**: per-entry `verification_mode`. `token_sequence` for opt-in strict substring matching of pre-inserted quantitative markers; `ai_judgement` is the PoC default and routes semantic checks through `review_queue` and the verifier-agent stage.
- **CLI output stability**: four-field stable core (`status`, `exit_code`, `command`, `next_actions`) plus informational fields with a `schema --command <name>` self-discovery command.
- **Policy unification**: `config/policy.yaml` is the single policy file with `rules`, `compacting`, `runs`, and `verification` sections.
- **Compacting model**: union of every valid candidate with `support` / `identity_basis` / `variants` preserved. No quorum, no automatic acceptance, no automatic exclusion.
- **Final review power**: `accept` / `hold` / `rerun_requested` / `override`. `override` is recorded as a distinct `kind: human_override` provenance entry in `sources`.
- **Mock runner role**: `agent_runners/mock.py` is a deterministic fixture-replay runner used only for protocol contract tests; it is separate from `manual.py` which holds human-authored Phase 0/1 inputs.
- **Trace separation**: `agent_trace.raw.jsonl` and `agent_trace.audit.jsonl` are stored separately with distinct retention/redaction expectations.
- **Decision boundary**: `check` creates provisional findings; only `gate`, after final human review, returns an external blocking verdict.
- **Source grounding**: Phase 0 uses immutable input snapshots, document hashes, and line/span `source_ref`; DB/RAG storage is deferred.
- **Canonical IDs**: compacting remaps run-local IDs to canonical IDs and retains `id_map` provenance.
- **Semantic verifier-agent**: `ai_judgement` links are checked by separate read-only multi-run verifier execution; proposals are retained in `semantic_verifications.yaml` without rewriting compacted links.

## Implementation Decisions (Phase 0 iteration 1 / 1.5 / 2)

- Adopted `src/` layout (`src/assessment_harness/...`); package import name unchanged from plan §7.
- Held `agent_runners/` and `tools/` out of this iteration (Phase 2 scope per plan §3.3). No empty placeholders were created.
- `evidence_source_ref` is validated by span containment within the referenced `spec_item.source_ref` (same document, evidence span inside the spec span), not strict equality.
- Schemas allow `additionalProperties: true` at entity objects so candidate-stage fields (`confidence`, `agent_run_id`, ...) added in Phase 2 do not break Phase 0 schemas.
- `gate` was deliberately not stubbed: it depends on the final-review schema, which is Phase 3 work, and freezing a wrong contract risked later rework.
- Docker is the dev environment; the `harness` and `test` services in `docker-compose.yml` bind-mount source/schemas/fixtures/tests so iterations do not require a rebuild.
- Snapshot text grounding uses whitespace-normalized **substring** matching for `spec_item.text` (allows multi-line spans) and for all quotes. Rubric items skip `text`/`description` grounding because they are evaluator-facing summaries; only `source_ref.quote` is grounded when provided.
- `evidence_quote_missing_for_spec_id` skips spec_ids that are already dangling, so a single broken reference does not raise two diagnostics.
- CLI `--output` is registered on the root parser (default `text`) and on every subparser (default `argparse.SUPPRESS`), so both pre- and post-subcommand forms work and the subcommand value overrides the root value when both are given.
- Rule 1 was sliced by `Finding` type; each branch has under/over-strict coverage, and the shared `orphan_scored_rubric` fixture exercises all three branches together. Rule 1 only runs after Rule 0 reports no high diagnostics, so it can trust unique rubric IDs and no dangling references.
- `check` never sets `blocking_count > 0`; provisional findings (`status=provisional_findings`, `exit_code=0`) are surfaced for review but the blocking verdict is reserved for `gate` after final review.
- `next_actions` carry one typed entry per finding with its `rubric_id`, so a caller agent can parallelise review without de-duplication logic.

## Open Decisions Before Phase 2

- Claude Agent SDK credential delivery.
- Specific `identity_basis` algorithm strings chosen in `config/policy.yaml` (candidates listed in plan §13).
- `min_valid_runs` / `default_runs` / `max_runs` numeric values and missing-quorum behaviour (error vs warn-and-proceed).
- Tool side-effect policy: read-only tools only, vs propose-tools that write directly to candidate files, vs runner that collects and emits in one batch.
- Raw trace retention / redaction / access policy (especially for non-public rubric content).
- Override usage scope: typo/omission only, or allow semantic overrides (semantic overrides should normally trigger `rerun_requested`).

## Next Tasks

### Publication Boundary (2026-05-26)

Slice 3.1 completed at `fbe1a78`; `fa71c7e` then added session-handoff notes. During independent review, the owner authorized publishing the verified batch. This section supersedes the earlier "push deferred / seven commits ahead" snapshot, which was already stale once the handoff-note commit existed.

### Rule 2 — Required Spec Coverage (next slice, expected smallest unit)

- **Spec source**: plan v1.11 §6 Rule 2 (`docs/implementation_plan_assessment_harness_poc_v1.md`).
- **Condition**: a `spec_item` with `requirement_level == "must"` that no `scored` rubric_item traces to.
- **Trace direction**: walk `trace_links`, collect every `spec_id` referenced from any link whose `rubric_id` resolves to a rubric with `evaluation_role == "scored"`. Then for each `must` spec, check whether its `id` is in that set. If not → finding.
- **Output contract decision required before code**: plan v1.11 fixes the condition, `medium` severity, and `provisional` status, but does not define a Rule 2 finding type literal or CLI next_action literal. `required_spec_unscored` / `review_uncovered_must_spec` are plausible candidates only. Confirm the literals with the owner and amend the plan body before implementation; do not let HANDOFF silently become the specification.
- **CRITICAL — structural only**: do NOT consult `semantic_status`. The Rule 1 final-coverage boundary does NOT transfer to Rule 2. Plan v1.11 §6 scope clause (carried unchanged from v1.10) explicitly excludes this. If you find yourself filtering trace_links by `human_accepted` here, stop and re-read §6 Rule 2.
- **Fixture**: build `fixtures/required_spec_unscored/` per plan §7. Should contain a `must` spec that no `scored` rubric traces to. Optionally include another `must` spec WITH coverage (to verify over-strict). Same source/manifest layout as `orphan_scored_rubric`.
- **Two-directional guards required** (plan §10.1, CLAUDE.md §4):
  - Under-strict: must spec without scored trace → finding emitted.
  - Over-strict A: must spec WITH scored trace (any semantic_status, including `pending_verification`) → no finding. This guard prevents accidentally applying Rule 1's final-coverage boundary to Rule 2.
  - Over-strict B: `optional` / `informational` spec without scored trace → no finding.
  - Over-strict C: must spec traced only to a `bonus` or `qualitative` rubric → finding (only `scored` traces count as coverage).
- **CLI**: after the Rule 2 action literal is fixed in the plan, append it to `COMMAND_CONTRACTS["check"].next_actions_types` and update Slice 3.1's full-set assertion in `test_schema_command_returns_check_contract`.
- **`clean_assignment` impact**: clean_assignment has S1 (must) → R1 (scored), S2 (must) → R2 (scored). Both must specs are covered, so Rule 2 should not change clean_assignment's baseline. Verify after wiring.
- **Smallest unit**: do Rule 2 as ONE slice (no sub-slicing needed; it has a single finding type). Match the Rule 1 slice 1 commit's structure as a template.

### Rule 3 — Optionality Consistency (after Rule 2)

- Plan §6 Rule 3. High finding when only-optional-traced `scored` rubric weight ≥ `policy.optionality_mismatch.weight_threshold` (PoC default `10` in `config/policy.yaml`).
- "Only optional traced" = every `spec_id` linked from this scored rubric has `requirement_level == "optional"`. If even one is `must`, no finding.
- Structural only — `semantic_status` not consulted (same scope clause as Rule 2).
- Fixture: `fixtures/optionality_mismatch/`.
- Policy threshold: read from `policy.optionality_mismatch.weight_threshold`. The CLI already loads policy; thread it into `run_rule_three`.

### `gate` and later phases

- Implement after `final_review.schema.json` (Phase 3 entry point). `gate` is the only stage that may promote persistent `unconfirmed_trace_coverage` (medium / provisional) into `orphan_scored_rubric_item` (high / confirmed). Same promotion path applies to lint-family `provisional` → `confirmed` (Rule L1/L5 medium → confirmed, Rule L6 high → confirmed).
- Real-assignment permissions and Phase 2 runner/retention parameters resolve here too.

### Lint family (Rule L1 / L5 / L6) — plan v1.11 §6 (sequencing open)

- **Spec status**: complete in plan v1.11 §6 (each rule has condition/result/safeguard/regression guards). Code not started.
- **Sequencing decision pending**: owner has not yet decided whether lint family enters before, after, or in parallel with Rule 2/3. Current Rule 2/3 entries above remain queued; lint family is a parallel spec-ready track. Surface this to owner before picking the next slice.
- **Slice order if lint family is picked**: L1 → L5 → L6 (Rule 1 slice 1/2/3 pattern). L1 and L6 each require schema extension to `findings.schema.json` (payload fields) and `review_queue` schema (new entry types). L5 reuses L1's mechanism — minimal incremental surface.
- **Fixture**: design as a single shared fixture (`fixtures/bonus_misuse/` or similar) covering all three L1/L5/L6 branches plus over-strict guards, mirroring how `orphan_scored_rubric` covers Rule 1's three branches.
- **CLI envelope**: each lint finding type adds a `next_actions` literal (`review_double_scoring`, `review_bonus_mandatory_only`, `review_mandatory_spec_bonus_only`) and severity counts as appropriate. Schema-contract test (`schema --command check`) must be extended in lockstep — see "Test-surface lessons" below.
- **`drift_observations[]` (plan v1.11 §5.6)**: spec-only addition for Rule L8 manual-discovery channel. No code path in `check`/`gate` — purely a `final_review_record` field. Implementation lands when Phase 3 (`gate`/final_review) lands, not in lint slices.

### v1.12+ lint extensions (post-v1.11, owner decision required before entry)

- Rule L2 (`bonus_weight_encroachment`, policy threshold), Rule L4 (`duplicate_trace_link`, lint-independent — NOT absorbed into Rule 0 per owner), Rule L7 + C1 (`forbidden_clause_rewarded` + `requirement_level: forbidden` schema extension). All specced in ideation v2.2 §4-§6 but not in plan §6 yet.
- Sole remaining ideation §9.2 open decision: L7-DET vs L7-SEM priority (resolved at L7 plan-promotion time).

### Test-surface lessons from today's session (Slice 3.1 retrospective)

When adding any new envelope field, next_action type, or schema-contract entry, also add a regression that **explicitly** asserts on it. The CLI's primary user is an AI agent; the envelope (stdout JSON) is the public contract, not the on-disk `findings.json`. Tests that only read findings.json miss envelope-shape regressions — slice 3 shipped three new envelope surfaces with no test for any of them, and the gap only surfaced via owner review. `_run_check` in `tests/test_fixtures.py` now returns the envelope as a 4-tuple to make this easy. Use it.

## Verification

- 98 collected tests pass independently re-run during post-slice-3.1 review (`docker compose run --rm test`). Slice 3.1 correctly adds envelope-shape assertions to all three fixture E2E tests, full-set assertions on the `schema --command check` contract, and a bonus-only boundary E2E that locks `(high=0, medium=0, informational=1)`.
- Smoke runs independently repeated during the same review:
  - `check` on grounded `fixtures/orphan_scored_rubric` with manifest: exit `0`, `status=provisional_findings`, all three Rule 1 branches visible — `unconfirmed_trace_coverage` on R1 (medium), `possible_orphan_scored_rubric_item` on R2 (high), `orphan_bonus_rubric_item` on R3 (informational). `provisional_high_count=1`, `provisional_medium_count=1`, `provisional_informational_count=1`.
  - `check` on grounded `fixtures/clean_assignment` with manifest: exit `0`, `status=provisional_findings`, two `unconfirmed_trace_coverage` findings on R1 and R2.
  - `check` on grounded `fixtures/reference_integrity` with manifest: exit `2`, `status=invalid_input`, all eight Rule 0 violation codes present (`high_integrity_count=9` because `evidence_quote_missing_for_spec_id` fires twice; pre-existing duplicate, not a regression).
  - `check` on `fixtures/clean_assignment` without `--source-manifest`: exit `2`, `status=invalid_input`, diagnostic `source_manifest_required`, next_action `provide_source_manifest`.
- Publishing authorization was received from the owner during post-slice-3.1 review; verified `main` has been published to `origin/main`.

## Project Structure

- `README.md`: user/agent entry point.
- `AGENTS.md` / `CLAUDE.md`: behavioural guidelines for coding agents.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`: canonical dev/run environment.
- `pyproject.toml`: src-layout Python package, entry point `assessment-harness`.
- `src/assessment_harness/`: package code.
  - `cli.py`: `check`, `schema`, `report` subcommands; envelope/exit-code contract; Rule 1 wiring after a clean Rule 0 pass.
  - `models.py`: YAML+schema loader, `SourceSnapshot`/`Document` with sha256 and line/span access.
  - `rules.py`: Rule 0 reference-integrity engine and Rule 1 (`possible_orphan_scored_rubric_item` + `unconfirmed_trace_coverage` + `orphan_bonus_rubric_item`; all three branches live). `HUMAN_ACCEPTED_SEMANTIC_STATUSES` module constant locks the Rule-1-only final-coverage boundary. Rules 2-3 to follow.
  - `schemas.py`: schema loader with `ASSESSMENT_HARNESS_SCHEMA_DIR` env override.
  - `report.py`: Markdown renderer.
- `schemas/`: eight JSON Schemas (source_manifest, spec_items, rubric_items, trace_links, policy, findings, integrity_diagnostics, cli_output).
- `config/policy.yaml`: default policy.
- `fixtures/clean_assignment/`: passing fixture with source manifest, sha256, spec.md, rubric.md.
- `fixtures/reference_integrity/`: grounded failing fixture covering all eight current Rule 0 diagnostic codes; carries its own `source/spec.md`, `source/rubric.md`, and `source_manifest.yaml`.
- `fixtures/orphan_scored_rubric/`: grounded Rule 1 end-to-end fixture exercising all three branches: R1 (scored, traced with pending_verification) → unconfirmed_trace_coverage, R2 (scored, untraced) → possible_orphan_scored_rubric_item, R3 (bonus, untraced) → orphan_bonus_rubric_item. Same `source/` + manifest layout.
- `tests/`: `test_rules.py`, `test_cli_output_contract.py`, `test_fixtures.py`, `test_models.py`, `conftest.py`.
- `docs/implementation_plan_assessment_harness_poc_v1.md`: implementation source of truth (v1.11).
- `docs/ideation_assessment_harness_v2.2.md`: latest ideation (final 2026-05-27, in-place revised same day). Adds Rubric Lint Rules family — 6 accepted (L1, L2, L4, L5, L6, L7), 3 rejected. Source for plan v1.11's §6 lint additions.
- `docs/ideation_assessment_harness_v2.1.md`: latest ideation, second in precedence.
- `docs/ideation_assessment_harness_v2.md`, `docs/ideation_assessment_harness_v1.md`: historical references.
- `docs/daily_logs/2026-05-25/work_log.md`: full record of planning iterations (v1.0 → v1.7) and Phase 0 iteration 1 / 1.5.
- `docs/daily_logs/2026-05-26/work_log.md`: Phase 0 iteration 2 Rule 1 slices, contract regression follow-up, and publication review record.
- `CHANGELOG.md`: major milestones.
- `HANDOFF.md`: this file.
