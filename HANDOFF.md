# Handoff

## Current Status

- Implementation plan is at v1.7 (`docs/implementation_plan_assessment_harness_poc_v1.md`) and is the canonical implementation source of truth, ahead of `docs/ideation_assessment_harness_v2.1.md`.
- **Phase 0 iteration 1 has landed**: package scaffold, Rule 0 reference-integrity engine, `check` / `schema` / `report` CLI subcommands, eight JSON Schemas, two fixtures (`clean_assignment`, `reference_integrity`), and 31 passing tests. Docker is the canonical dev environment.
- Phase 0 is not finished: Rule 1, Rule 2, Rule 3, three more fixtures (`orphan_scored_rubric`, `required_spec_unscored`, `optionality_mismatch`), and the `gate` command are still pending.
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

- **Canonical specification**: v1.7 implementation plan first, then `v2.1` ideation. Earlier ideation versions are historical.
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

## Implementation Decisions (Phase 0 iteration 1)

- Adopted `src/` layout (`src/assessment_harness/...`); package import name unchanged from plan §7.
- Held `agent_runners/` and `tools/` out of this iteration (Phase 2 scope per plan §3.3). No empty placeholders were created.
- `evidence_source_ref` is validated by span containment within the referenced `spec_item.source_ref` (same document, evidence span inside the spec span), not strict equality.
- Schemas allow `additionalProperties: true` at entity objects so candidate-stage fields (`confidence`, `agent_run_id`, ...) added in Phase 2 do not break Phase 0 schemas.
- `gate` was deliberately not stubbed: it depends on the final-review schema, which is Phase 3 work, and freezing a wrong contract risked later rework.
- Docker is the dev environment; the `harness` and `test` services in `docker-compose.yml` bind-mount source/schemas/fixtures/tests so iterations do not require a rebuild.

## Open Decisions Before Phase 2

- Claude Agent SDK credential delivery.
- Specific `identity_basis` algorithm strings chosen in `config/policy.yaml` (candidates listed in plan §13).
- `min_valid_runs` / `default_runs` / `max_runs` numeric values and missing-quorum behaviour (error vs warn-and-proceed).
- Tool side-effect policy: read-only tools only, vs propose-tools that write directly to candidate files, vs runner that collects and emits in one batch.
- Raw trace retention / redaction / access policy (especially for non-public rubric content).
- Override usage scope: typo/omission only, or allow semantic overrides (semantic overrides should normally trigger `rerun_requested`).

## Next Tasks

1. **Rule 1 — Scored Rubric Coverage** (plan §6 Rule 1). Adds `possible_orphan_scored_rubric_item` / `unconfirmed_trace_coverage` / `orphan_scored_rubric_item` findings; consumes `semantic_status` once `verify` ships. Phase 0 cut: treat `pending_verification` and any non-human-accepted status as not-final-coverage.
2. **Rule 2 — Required Spec Coverage** (plan §6 Rule 2). `medium` provisional finding for `must` spec items without a `scored` rubric link.
3. **Rule 3 — Optionality Consistency** (plan §6 Rule 3). `high` provisional finding when `optional`-only scored rubric weight crosses `policy.rules.optionality_mismatch.weight_threshold` (default 10).
4. **Fixtures**: `orphan_scored_rubric`, `required_spec_unscored`, `optionality_mismatch`. Each needs under-strict / over-strict regression tests per plan §10.1.
5. **`gate` subcommand**: implement after `final_review.schema.json` is committed. Wire exit code `1` exclusively to `gate`-confirmed blocking findings; `check` keeps emitting only provisional findings with exit `0`.
6. **Confirm Phase 1 inputs**: real-assignment source location, NDA/anonymization scope.
7. **Resolve Phase 2 parameters**: credentials, identity_basis, run-count policy for both agent roles, tool side-effects, raw-trace retention.

## Verification

- 31 pytest tests pass in the Docker `test` service (`docker compose run --rm test`).
- Smoke checks executed in the `harness` service: `clean_assignment` → exit 0 / `status: success`; `reference_integrity` → exit 2 with six high diagnostics; `schema --command check` returns the stable contract; `report` renders Markdown.
- Repository `main` is published to `origin/main` through the SSH remote `git@github.com:entangelk/assessment_poc.git`.
- The README.md quick start command set documents the intended CLI contract; the Phase 0 subset (`check`, `schema`, `report`) is now actually runnable.

## Project Structure

- `README.md`: user/agent entry point.
- `AGENTS.md` / `CLAUDE.md`: behavioural guidelines for coding agents.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`: canonical dev/run environment.
- `pyproject.toml`: src-layout Python package, entry point `assessment-harness`.
- `src/assessment_harness/`: package code.
  - `cli.py`: `check`, `schema`, `report` subcommands; envelope/exit-code contract.
  - `models.py`: YAML+schema loader, `SourceSnapshot`/`Document` with sha256 and line/span access.
  - `rules.py`: Rule 0 reference-integrity engine; Rules 1-3 to follow.
  - `schemas.py`: schema loader with `ASSESSMENT_HARNESS_SCHEMA_DIR` env override.
  - `report.py`: Markdown renderer.
- `schemas/`: eight JSON Schemas (source_manifest, spec_items, rubric_items, trace_links, policy, findings, integrity_diagnostics, cli_output).
- `config/policy.yaml`: default policy.
- `fixtures/clean_assignment/`: passing fixture with source manifest, sha256, spec.md, rubric.md.
- `fixtures/reference_integrity/`: failing fixture covering all six Rule 0 violation classes.
- `tests/`: `test_rules.py`, `test_cli_output_contract.py`, `test_fixtures.py`, `conftest.py`.
- `docs/implementation_plan_assessment_harness_poc_v1.md`: implementation source of truth (v1.7).
- `docs/ideation_assessment_harness_v2.1.md`: latest ideation, second in precedence.
- `docs/ideation_assessment_harness_v2.md`, `docs/ideation_assessment_harness_v1.md`: historical references.
- `docs/daily_logs/2026-05-25/work_log.md`: full record of planning iterations (v1.0 → v1.7) and Phase 0 iteration 1.
- `CHANGELOG.md`: major milestones.
- `HANDOFF.md`: this file.
