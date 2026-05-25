# Handoff

## Current Status

- Implementation plan is at v1.7 (`docs/implementation_plan_assessment_harness_poc_v1.md`) and is the canonical implementation source of truth, ahead of `docs/ideation_assessment_harness_v2.1.md` for any implementation-specific conflict.
- All Phase 0 pre-decisions are now resolved (canonical document, Rule 0 verification modes, CLI stability layering). Phase 0 implementation can start.
- The PoC is an **agent-level harness**: the 1st-class caller is an AI agent (Claude Code / Codex / Gemini), not a human. Humans participate only as final reviewers.
- The final workflow is `extract --runs N -> compact -> verify --runs N -> check -> report -> review -> gate`. Compacting is a **union-based audit operation**, not a classification: every valid candidate is preserved with `support`/`identity_basis`/`variants`.
- A new top-level `README.md` documents the quick start, flow, data contracts, policy, CLI contract, phase status, and document index for both AI agents and humans.

## Active Decisions (Adopted)

- **Canonical specification**: v1.7 implementation plan first, then `v2.1` ideation. Earlier ideation versions are historical.
- **Rule 0 evidence verification**: per-entry `verification_mode`. `token_sequence` for opt-in strict substring matching of pre-inserted quantitative markers; `ai_judgement` is PoC default and routes semantic checks through `review_queue` and the adopted verifier-agent stage.
- **CLI output stability**: four-field stable core (`status`, `exit_code`, `command`, `next_actions`) plus informational fields with a `schema --command <name>` self-discovery command. Stability is incrementally established, not declared up front.
- **Policy unification**: `config/policy.yaml` is the single policy file with `rules`, `compacting`, `runs`, and `verification` sections.
- **Compacting model**: union of every valid candidate with `support`/`identity_basis`/`variants` preserved. No quorum, no automatic acceptance, no automatic exclusion.
- **Final review power**: `accept` / `hold` / `rerun_requested` / `override`. `override` is recorded as a distinct `kind: human_override` provenance entry in `sources`.
- **Mock runner role**: `agent_runners/mock.py` is a deterministic fixture-replay runner used only for protocol contract tests; it is separate from `manual.py` which holds human-authored Phase 0/1 inputs.
- **Trace separation**: `agent_trace.raw.jsonl` (raw SDK debugging stream) and `agent_trace.audit.jsonl` (observable operational record) are stored separately with distinct retention/redaction expectations.
- **Decision boundary**: `check` creates provisional findings; only `gate`, after final human review, returns an external blocking verdict.
- **Source grounding**: Phase 0 uses immutable input snapshots, document hashes, and line/span `source_ref`; DB/RAG storage is deferred.
- **Canonical IDs**: compacting remaps run-local IDs to compacted canonical IDs and retains `id_map` provenance for future project/version expansion.
- **Semantic verifier-agent**: `ai_judgement` links are checked by separate read-only, multi-run verifier execution; proposals are retained in `semantic_verifications.yaml` without rewriting compacted links, and final human review remains authoritative.

## Open Decisions Before Phase 2

- Claude Agent SDK credential delivery.
- Specific `identity_basis` algorithm strings chosen in `config/policy.yaml` (candidates listed in plan §13).
- `min_valid_runs` / `default_runs` / `max_runs` numeric values and missing-quorum behaviour (error vs warn-and-proceed).
- Tool side-effect policy: read-only tools only, vs propose-tools that write directly to candidate files, vs runner that collects and emits in one batch.
- Raw trace retention/redaction/access policy (especially for non-public rubric content).
- Override usage scope: typo/omission only, or allow semantic overrides (semantic overrides should normally trigger `rerun_requested`).

## Cross-Review Notes

- Both feasibility reviews agreed that manual structured input, deterministic validation, fixtures, and a real assignment case are the appropriate first core.
- `trace_to` (via `spec_ids: [...]`) supports N:M cardinality; trace metadata such as rationale and evidence quotes is stored at the link-entity level.
- Rule 5 is not ready for v0: detecting a post-start rubric change requires a locked baseline, round state, and change/approval record that are not modelled yet.
- The agent-level shift is justified because the consumer is an AI agent: structured CLI I/O, tool boundaries, recovery, and structured output matter more than single-call prompt engineering.
- Manual validation is not the final PoC. The plan requires candidate/verifier multi-run execution and a real-assignment `extract -> compact -> verify -> check -> report -> review -> gate` demonstration including at least one `override`.
- Rule 0 verifies reference/quote integrity only; substring presence does not prove semantic disclosure. Semantic adequacy is forwarded to `review_queue` and final human review.
- A mock runner validates the protocol boundary only; actual Codex/Gemini portability evidence is explicitly deferred to a later MVP.
- v1.7 adds required read-only semantic verification runs after compacting; its result schema and no-mutation contract must be implemented in Phase 2.

## Next Tasks

1. Implement the Phase 0 deterministic core: package scaffold, schemas (source_manifest/id_map/spec/rubric/trace/finding/policy/integrity_diagnostics/review_queue/agent_trace/cli_output/final_review/compacting/semantic_verifications), Rule 0–3, provisional finding lifecycle, `gate` boundary, manual fixtures, JSON findings, markdown report, and the `schema` self-discovery command.
2. Verify Phase 0 against five fixtures: `clean_assignment`, `reference_integrity`, `orphan_scored_rubric`, `required_spec_unscored`, `optionality_mismatch`, each with under-strict/over-strict regression guards.
3. Confirm the first real assignment input and its permitted storage/anonymization scope before Phase 1.
4. Resolve remaining Phase 2 parameters, including credentials, identity_basis, run-count policy for both agent roles, tool side-effects, and raw-trace retention.

## Verification

- v1.7 resolves the remaining semantic-verification design decision by adopting a dedicated read-only verifier-agent stage before final review.
- Repository `main` is published to `origin/main` through the SSH remote `git@github.com:entangelk/assessment_poc.git`.
- No code or tests exist yet; verification has been limited to documentation cross-checks and structural review.
- The README.md quick start has not been executed against any implementation because the implementation does not yet exist; it documents the intended CLI contract from the plan.

## Project Structure

- `README.md`: user/agent entry point. Quick start, flow, data contracts, CLI contract, phase status, document index.
- `AGENTS.md` / `CLAUDE.md`: behavioural guidelines for coding agents.
- `docs/implementation_plan_assessment_harness_poc_v1.md`: implementation source of truth (v1.7).
- `docs/ideation_assessment_harness_v2.1.md`: latest ideation, second in precedence behind the implementation plan.
- `docs/ideation_assessment_harness_v2.md`: historical reference.
- `docs/ideation_assessment_harness_v1.md`: original broad ideation.
- `docs/daily_logs/2026-05-25/work_log.md`: full record of the planning iterations (v1.0 → v1.7).
- `HANDOFF.md`: this file.
- `CHANGELOG.md`: major planning milestones.
