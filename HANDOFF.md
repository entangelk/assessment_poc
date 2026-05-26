# Handoff

## Current Status

- Implementation plan is at v1.9 (`docs/implementation_plan_assessment_harness_poc_v1.md`) and is the canonical implementation source of truth, ahead of `docs/ideation_assessment_harness_v2.1.md`.
- **Phase 0 iteration 1.5 landed (2026-05-25)**: the three iteration-1 audit blockers are closed. Rule 0 now grounds `spec_item.text` and `source_ref.quote` (and evidence `quote` when `source_ref` is provided) against the snapshot span text, requires evidence coverage for every `trace_links.spec_ids` member, and the CLI accepts `--output` both before and after the subcommand.
- **Phase 0 iteration 2 slice 1 landed (2026-05-26)**: Rule 1 (Scored Rubric Coverage) is now partially live. `check` runs Rule 1 after a clean Rule 0 pass and emits `possible_orphan_scored_rubric_item` (`high` / `provisional`) for any `evaluation_role == scored` rubric item with zero trace links. Findings come back as `status=provisional_findings`, `exit_code=0`, `blocking_count=0`. The `unconfirmed_trace_coverage` and bonus-informational branches of Rule 1 are still pending; Rule 2, Rule 3, and the `gate` command remain pending.
- **Phase 0 iteration 2 slice 1.5 landed (2026-05-26)**: `--source-manifest` is now a required `check` input per plan §5.0 / §5.1 / §11 (decision introduced in plan v1.8; section numbers unchanged in v1.9). Omitting it returns `status=invalid_input` / exit `2` with diagnostic `source_manifest_required` and next_action `provide_source_manifest`. Both `orphan_scored_rubric` and `reference_integrity` fixtures are grounded with their own `source/spec.md`, `source/rubric.md`, and `source_manifest.yaml` (sha256-verified).
- **Phase 0 iteration 2 slice 2 landed (2026-05-26)**: Rule 1's second branch (`unconfirmed_trace_coverage`, medium / provisional) is live. Any scored rubric whose trace links have no `human_accepted` / `human_overridden` semantic_status surfaces a medium finding with `evidence={link_count, semantic_statuses}`. `clean_assignment` is now the canonical pre-review baseline: `status=provisional_findings`, two medium findings (R1, R2), `blocking_count=0`. The bonus-informational branch of Rule 1, plus Rule 2, Rule 3, and `gate`, are still pending.
- Package surface: `check` / `schema` / `report` subcommands, eight JSON Schemas, three fully-grounded fixtures (`clean_assignment`, `reference_integrity`, `orphan_scored_rubric`), and 85 passing tests. Docker is the canonical dev environment.
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

- **Canonical specification**: v1.9 implementation plan first, then `v2.1` ideation. Earlier ideation versions are historical.
- **`--source-manifest` is a required `check` input** (plan v1.9 §5.0 / §5.1 / §11): Phase 0 mandates immutable source snapshot grounding. Missing manifest → `status=invalid_input` / exit `2` / diagnostic `source_manifest_required` / next_action `provide_source_manifest`. argparse keeps the flag declared as `default=None` so caller agents always receive the structured envelope on stdout instead of argparse's usage text on stderr.
- **Rule 1 final-coverage boundary** (plan v1.9 §6 Rule 1, §5.3.1): the only `semantic_status` values that count as final coverage for Rule 1 are `human_accepted` and `human_overridden`. Everything else — pre-review (`pending_verification`, `agent_*`) and post-review non-coverage (`human_rejected`, `rerun_requested`) — surfaces as `unconfirmed_trace_coverage` (medium / provisional) in `check`. `gate` is the only stage that may promote persistent non-coverage into a confirmed `orphan_scored_rubric_item`. **This boundary applies to Rule 1 and `gate` only.** Rule 2 and Rule 3 do not consult `semantic_status` (they use the structural conditions in plan §6 Rule 2 / Rule 3).
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

## Implementation Decisions (Phase 0 iteration 1 / 1.5 / 2-slice-1)

- Adopted `src/` layout (`src/assessment_harness/...`); package import name unchanged from plan §7.
- Held `agent_runners/` and `tools/` out of this iteration (Phase 2 scope per plan §3.3). No empty placeholders were created.
- `evidence_source_ref` is validated by span containment within the referenced `spec_item.source_ref` (same document, evidence span inside the spec span), not strict equality.
- Schemas allow `additionalProperties: true` at entity objects so candidate-stage fields (`confidence`, `agent_run_id`, ...) added in Phase 2 do not break Phase 0 schemas.
- `gate` was deliberately not stubbed: it depends on the final-review schema, which is Phase 3 work, and freezing a wrong contract risked later rework.
- Docker is the dev environment; the `harness` and `test` services in `docker-compose.yml` bind-mount source/schemas/fixtures/tests so iterations do not require a rebuild.
- Snapshot text grounding uses whitespace-normalized **substring** matching for `spec_item.text` (allows multi-line spans) and for all quotes. Rubric items skip `text`/`description` grounding because they are evaluator-facing summaries; only `source_ref.quote` is grounded when provided.
- `evidence_quote_missing_for_spec_id` skips spec_ids that are already dangling, so a single broken reference does not raise two diagnostics.
- CLI `--output` is registered on the root parser (default `text`) and on every subparser (default `argparse.SUPPRESS`), so both pre- and post-subcommand forms work and the subcommand value overrides the root value when both are given.
- Rule 1 is sliced by `Finding` type: each branch (`possible_orphan_scored_rubric_item`, `unconfirmed_trace_coverage`, bonus informational) lands in its own iteration with its own fixture and its own under/over-strict guards. Rule 1 only runs after Rule 0 reports no high diagnostics, so it can trust unique rubric IDs and no dangling references.
- `check` never sets `blocking_count > 0`; provisional findings (`status=provisional_findings`, `exit_code=0`) are surfaced for review but the blocking verdict is reserved for `gate` after final review.
- `next_actions` carry one entry per finding (`review_orphan_rubric` with `rubric_id`), so a caller agent can parallelise review without de-duplication logic.

## Open Decisions Before Phase 2

- Claude Agent SDK credential delivery.
- Specific `identity_basis` algorithm strings chosen in `config/policy.yaml` (candidates listed in plan §13).
- `min_valid_runs` / `default_runs` / `max_runs` numeric values and missing-quorum behaviour (error vs warn-and-proceed).
- Tool side-effect policy: read-only tools only, vs propose-tools that write directly to candidate files, vs runner that collects and emits in one batch.
- Raw trace retention / redaction / access policy (especially for non-public rubric content).
- Override usage scope: typo/omission only, or allow semantic overrides (semantic overrides should normally trigger `rerun_requested`).

## Next Tasks

1. **Rule 1 slice 3 — bonus orphan informational finding**. `evaluation_role == bonus` rubric items without trace links surface as `informational` findings; they do not block gating. Pair with an `orphan_bonus_rubric` fixture (or extend an existing one) and two-directional guards. Decide the finding `type` string before implementation — current candidates: `orphan_bonus_rubric_item`, `bonus_rubric_unreferenced`. Pick once and lock.
3. **Rule 2 — Required Spec Coverage** (plan §6 Rule 2). Medium finding when a `requirement_level: must` spec has no `scored` rubric trace. Pair with `required_spec_unscored` fixture and two-directional guards.
4. **Rule 3 — Optionality Consistency** (plan §6 Rule 3). High finding when only-optional-traced `scored` rubric weight ≥ `policy.optionality_mismatch.weight_threshold`. Pair with `optionality_mismatch` fixture and two-directional guards.
5. **`gate` and later phases**: implement after `final_review.schema.json`; then confirm real-assignment permissions and resolve Phase 2 runner/retention parameters.

## Verification

- 85 collected tests pass locally (`docker compose run --rm test`). Slice 2 added six parametrized under-strict guards (one per non-final-coverage `semantic_status`), four over-strict guards (human_accepted/human_overridden suppression, any-link-accepted suppression, orphan/unconfirmed mutual exclusivity, bonus/qualitative out-of-scope), plus a missing-`semantic_status` variant and renamed baseline test.
- Manual smoke runs after slice 2:
  - `check` on grounded `fixtures/clean_assignment` with manifest: exit `0`, `status=provisional_findings`, two `unconfirmed_trace_coverage` findings on R1 and R2 (both scored, both with pending_verification links), `provisional_medium_count=2`.
  - `check` on grounded `fixtures/orphan_scored_rubric` with manifest: exit `0`, `status=provisional_findings`, one `possible_orphan_scored_rubric_item` (R2, high) plus one `unconfirmed_trace_coverage` (R1, medium); `provisional_high_count=1`, `provisional_medium_count=1`.
  - `check` on grounded `fixtures/reference_integrity` with manifest: exit `2`, `status=invalid_input`, all eight Rule 0 violation codes present (`high_integrity_count=9` because `evidence_quote_missing_for_spec_id` fires twice; pre-existing duplicate, not a regression).
  - `check` on `fixtures/clean_assignment` without `--source-manifest`: exit `2`, `status=invalid_input`, diagnostic `source_manifest_required`, next_action `provide_source_manifest`.
- Repository `main` is published to `origin/main` through the SSH remote `git@github.com:entangelk/assessment_poc.git`.

## Project Structure

- `README.md`: user/agent entry point.
- `AGENTS.md` / `CLAUDE.md`: behavioural guidelines for coding agents.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`: canonical dev/run environment.
- `pyproject.toml`: src-layout Python package, entry point `assessment-harness`.
- `src/assessment_harness/`: package code.
  - `cli.py`: `check`, `schema`, `report` subcommands; envelope/exit-code contract; Rule 1 wiring after a clean Rule 0 pass.
  - `models.py`: YAML+schema loader, `SourceSnapshot`/`Document` with sha256 and line/span access.
  - `rules.py`: Rule 0 reference-integrity engine and Rule 1 (`possible_orphan_scored_rubric_item` + `unconfirmed_trace_coverage`). `HUMAN_ACCEPTED_SEMANTIC_STATUSES` module constant locks the Rule-1-only final-coverage boundary. Bonus-informational branch and Rules 2-3 to follow.
  - `schemas.py`: schema loader with `ASSESSMENT_HARNESS_SCHEMA_DIR` env override.
  - `report.py`: Markdown renderer.
- `schemas/`: eight JSON Schemas (source_manifest, spec_items, rubric_items, trace_links, policy, findings, integrity_diagnostics, cli_output).
- `config/policy.yaml`: default policy.
- `fixtures/clean_assignment/`: passing fixture with source manifest, sha256, spec.md, rubric.md.
- `fixtures/reference_integrity/`: grounded failing fixture covering all six Rule 0 violation classes; carries its own `source/spec.md`, `source/rubric.md`, and `source_manifest.yaml`.
- `fixtures/orphan_scored_rubric/`: grounded Rule 1 slice 1 fixture (R2 scored without trace link); same `source/` + manifest layout.
- `tests/`: `test_rules.py`, `test_cli_output_contract.py`, `test_fixtures.py`, `test_models.py`, `conftest.py`.
- `docs/implementation_plan_assessment_harness_poc_v1.md`: implementation source of truth (v1.9).
- `docs/ideation_assessment_harness_v2.1.md`: latest ideation, second in precedence.
- `docs/ideation_assessment_harness_v2.md`, `docs/ideation_assessment_harness_v1.md`: historical references.
- `docs/daily_logs/2026-05-25/work_log.md`: full record of planning iterations (v1.0 → v1.7) and Phase 0 iteration 1 / 1.5.
- `docs/daily_logs/2026-05-26/work_log.md`: Phase 0 iteration 2 slice 1 (Rule 1 no-trace branch).
- `CHANGELOG.md`: major milestones.
- `HANDOFF.md`: this file.
