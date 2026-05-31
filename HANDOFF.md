<!-- .ko mirror created on finalize (publication_plan §7b) -->

<p align="center">
  <a href="./HANDOFF.md"><img src="https://img.shields.io/badge/Language-EN-111111?style=for-the-badge" alt="English"></a>
  <a href="./HANDOFF.ko.md"><img src="https://img.shields.io/badge/Language-KO-6B7280?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Handoff

## Current Status

- Implementation plan is at v1.30 (`docs/implementation_plan_assessment_harness_poc_v1.md`) and is the canonical implementation source of truth, ahead of `docs/ideation_assessment_harness_v2.2.md` (revised in-place 2026-05-27, supersedes v2.1).
- **Rule 0 is live**: source snapshot grounding, evidence completeness/reference-integrity checks, mandatory `--source-manifest`, and structured invalid-input recovery are implemented.
- **Rule 1 is feature-complete** (plan v1.19 §6): `possible_orphan_scored_rubric_item`, `unconfirmed_trace_coverage`, and `orphan_bonus_rubric_item` are all implemented. The CLI exposes their review actions and provisional severity counts; slice 3.1 locks the public envelope/schema contract, including the bonus-only `(high=0, medium=0, informational=1)` boundary.
- **Rule 2 is implemented** (plan v1.19 §6): `uncovered_must_spec_item` is emitted as medium/provisional when no `scored` rubric traces a `must` spec, with `review_uncovered_must_spec` exposed through `check`. It is structural only: pending scored traces cover, while bonus-only or qualitative-only traces do not.
- **Rule 3 is implemented** (plan v1.20 §6): `optionality_mismatch` is emitted as high/provisional when a scored rubric traces only optional specs at or above `rules.optionality_mismatch.weight_threshold`; it exposes `review_optionality_mismatch`. It is structural only: semantic status is not consulted, and Phase 0 `check` now rejects missing/incomplete policy instead of silently suppressing Rule 3.
- **Rule L1 is implemented** (plan v1.19 §6): `double_scored_spec` is emitted as medium/provisional when the same spec is traced by scored and bonus rubrics. The finding includes paired rubric context, and `check` writes paired `double_scoring_review` entries through the new `review_queue` contract.
- **Rule L5 is implemented** (plan v1.19 §6): `bonus_grades_mandatory_only` is emitted as medium/provisional for a traced bonus rubric whose targets are all `must`; it exposes `review_bonus_mandatory_only` and does not add a queue entry.
- **Rule L6 is implemented** (plan v1.19 §6): `mandatory_spec_bonus_only_traced` is emitted as high/provisional when a `must` spec is traced only by bonus rubrics; it exposes `bonus_rubric_ids[]`, `review_mandatory_spec_bonus_only`, and paired `mandatory_spec_bonus_review` queue entries.
- **Initial `gate` is live** (plan v1.19 §5.6): final review records can close provisional findings through `target_type: finding` with minimal generated keys. `gate` returns `pending_review` for missing/held/rerun decisions, `fail`/exit `1` for confirmed blocking findings, and `success` when all findings are closed without blocking. The v1.17 follow-up locks the conditional-pass boundary matrix from independent verification.
- **Initial `review` draft writer is live** (plan v1.19 §5.6): `review --findings ... --out-dir ... --reviewer ...` writes `review.yaml` with one minimal-key `hold` decision per finding. It accepts only `findings.status=success` or `provisional_findings`, refuses to overwrite an existing draft unless `--force` is passed, and does not auto-accept or rewrite artifacts; humans edit the draft before final `gate`.
- **AgentRunner protocol foundation is live** (plan v1.22 §7 / §9): `agent_runners/base.py` defines the framework-neutral `AgentRunner` protocol and `AgentRunResult`; `agent_runners/mock.py` deterministically replays fixture YAML for protocol contract tests only.
- **Candidate artifact schema foundation is live** (plan v1.24 §5.4): `candidates.schema.json` validates run-level spec/rubric/trace candidate arrays with `candidate_id`, `agent_runner`, `agent_run_id`, and `integrity_status`, before any compacting or runner recovery policy is chosen.
- **Candidate audit-trace attribution helper is live** (plan v1.25 §10.2): `validate_candidate_audit_trace` validates candidate/audit trace schemas and checks every candidate `agent_run_id` appears in audit trace `run_id`s, without implementing `extract`, compacting, or runner failure recovery.
- **Runner artifact normalization helper is live** (plan v1.26 §10.2): `normalize_result_candidates` converts fixture-shaped `AgentRunResult.artifacts` into candidate artifacts, attaches runner/run provenance, starts candidates at `pending_check`, and strips compacting-only fields before validation.
- **Candidate integrity staged model is live** (plan v1.28 §5.4 / §10.2): `classify_candidate_run_integrity` now marks clean structural runs as `structurally_validated`, candidate/audit schema errors as `schema_violation`, and missing audit trace run attribution as `trace_attribution_error`. `validated` is reserved for later deep candidate Rule 0 success and remains the only compacting-eligible status.
- **Deep candidate Rule 0 helper is live** (plan v1.30 §5.4 / §10.2): `classify_deep_candidate_run_integrity` reuses the Rule 0 engine on normalized candidate `proposed_item`s after structural validation. Clean runs promote to `validated`; candidate-internal reference/completeness failures isolate as `invalid_reference`; source document/hash/source_ref/snapshot-span failures isolate as `source_grounding_mismatch`; token-sequence evidence quote substring failures isolate as `quote_mismatch`. Mixed diagnostic runs use `invalid_reference > source_grounding_mismatch > quote_mismatch`.
- **Pending implementation**: `extract`, `compact`, `verify`, real SDK runners, framework tools, orchestrator workflows, trace-link override materialization, review_queue composition, and later Phase 2/3 runner workflows.
- Package surface: `check` / `schema` / `report` / `review` / `gate` subcommands, fourteen JSON Schemas, and six fully-grounded fixtures (`clean_assignment`, `reference_integrity`, `orphan_scored_rubric`, `bonus_misuse`, `uncovered_must_spec`, `optionality_mismatch`). Docker is the canonical dev environment.
- The PoC is an **agent-level harness**: the 1st-class caller is an AI agent (Claude Code / Codex / Gemini), not a human. Humans participate only as final reviewers.
- The final workflow is `extract --runs N -> compact -> verify --runs N -> check -> report -> review -> gate`. Compacting is a **union-based audit operation**: every valid candidate is preserved with `support` / `identity_basis` / `variants`.

## Publication / Portfolio Effort (active, 2026-05-29)

The project is being prepared for public release as a portfolio piece.

- **Canonical plan:** [`docs/publication_plan_v1.md`](docs/publication_plan_v1.md) (v1.2) — governs the whole effort; completion of its inventory + Open Decisions = the publication moment. Read it first.
- **Framing (Owner):** foreground *decisions and process over code*; no overclaiming; single source of truth per fact (link, don't duplicate); AI collaboration shown honestly. EN primary + KO mirror with a language-switch header.
- **Done & committed:** publication plan (v1.0→v1.2); **Step 0 truth pass** of `README.md` (plan ref v1.28→v1.30, linear Phase table → area-based status, `extract`/`compact`/`verify` marked unimplemented).
- **WIP, uncommitted:** [`docs/decisions.md`](docs/decisions.md) — first-person draft, AI-collaboration foregrounded. **Curated to 11 vignettes** (2026-05-31, Owner chose "moderate" depth): A1 agent-as-user, A2 rejected L3/L8/L9 scope boundary, A3 check-vs-gate (now also absorbs the gate-blocking-scope point), A4 lint-mindset pivot (inverse invariant), B1 `validated`→staged→3-way, B2 union compacting, B3 verification_mode, B4 source-snapshot grounding, B5 fail-loud/no-silent-disable, C1 verification discipline + withdrawn Rule 3 verdict, C2 plan-is-SoT/HANDOFF-not-spec. **Dropped during curation** (recoverable via git/work_log): A5 gate-scope (folded into A3), A6 no-opinion-on-thresholds, B6 review-never-auto-accepts, B7 decision-record-key-minimalism, B8 raw/audit-trace-separation. **Voice is locked:** first person ("I decided"), AI collaboration explicit, honesty clarifiers (e.g. "no live incident — caught at the contract level"). Keep that voice.

### Next task: publication_plan Step 1 (bilingual scaffold) / Step 2 (case study)

The 4-section decision harvest and curation are **complete**. `decisions.md` content is frozen at 11 vignettes pending only the `.ko` mirror (Step 6.5). Next:

- **Step 1 — Bilingual scaffold (partial, 2026-05-31):**
  - **Done:** Mermaid architecture diagram embedded in `README.md` (replaced the ASCII flow under 흐름 개요; marks implemented vs foundation-only honestly). Language-switch header added to the English docs `HANDOFF.md` / `AGENTS.md` / `CLAUDE.md` (`decisions.md` already had it).
  - **Deferred — open question for Owner:** `README.md` is currently **Korean**, but publication_plan §1.5 makes `README.md` the **English** canonical file. The README language-switch header is intentionally **not** added yet (an "EN" badge on a Korean file would lie). Confirm finalization plan: current Korean `README.md` → `README.ko.md`, and author a new English `README.md`. Until then the README header + EN/KO split wait for Step 6.5.
  - **Pending creation:** `case_study.md` / `evaluation.md` get the header when authored (Steps 2/3).
- **Step 2 — Case study:** write `docs/case_study.md`, curating 3–5 decisions *from the 11 in decisions.md* (don't re-derive; link).

Harvest record (all four sources DONE — kept for audit; do not re-sweep expecting more):

1. **Daily logs** — `docs/daily_logs/2026-05-2[5-9]/work_log.md` `### Decisions`. **DONE (2026-05-31)** → yielded A4 (lint pivot, with ideation) + B5 (fail-loud) + C2 (plan-is-SoT), plus dropped-during-curation A5/A6/B6/B7/B8.
2. **Verification records** — `docs/verifications/2026-05-2[7-9]/*.md` Verdict/Issues. **DONE (2026-05-31)** → corroborated B5 + the gate-scope point + the review-safety point (policy_completeness, review_safety_guards, gate_initial_slice conditional-pass); no *new* vignette beyond the daily-log harvest.
3. **Ideation** — `docs/ideation_assessment_harness_v2.2.md` accept/reject rationale. **DONE** → L3/L8/L9 rejections became A2; the lint-mindset pivot became A4.
4. **Implementation plan change log** — §15, v1.0→v1.30. **DONE** → v1.2/v1.3/v1.4/v1.5/v1.6/v1.7 became A1/A3/B1/B2/B3/B4.

### Remaining publication steps (per publication_plan §4)

- **Step 1 — Bilingual scaffold:** EN/KO pairs + language-switch header for showcase docs (README, case_study, decisions, evaluation) and technical docs (HANDOFF/AGENTS/CLAUDE). Embed a **Mermaid architecture diagram** in README (replaces a separate arch doc).
- **Step 2 — Case study + decisions:** finish `decisions.md` (after harvest); write `docs/case_study.md` (Problem/Goal/Key decisions/What I built/Verification/Limitations/Next).
- **Step 3 — Evaluation (`docs/evaluation.md`):** test + smoke tables **built from real `docker compose run` / `pytest` output, never transcribed** (200 passing as of v1.30; recompute before publishing).
- **Step 4 — AGENTS/CLAUDE augment:** add agent workflow rules not already present; do not duplicate existing content.
- **Step 5 — Cleanup + safety:** add `LICENSE` (**Apache 2.0**, copyright `entangelk`); curated index for `daily_logs`/`verifications` (not raw-dumped); secret scan over tree **and history** (repo flips as-is); fix broken links.
- **Step 6 — Documentation Map** in README.
- **Step 6.5 — Freeze + mirror moving docs** (§7b): full EN mirror of the implementation plan, `.ko` of the publication plan, `HANDOFF.md` mirror — done once at the end so a moving target isn't translated repeatedly.
- **Step 7 — Visibility flip (Owner, manual):** `gh` unavailable here. Owner sets repo description/topics and flips to public. Ready-to-paste draft is in the response history and publication_plan §7a; description = "An agent-consumable CLI harness that validates assessment *design* … Proof-of-concept", topics = `assessment` `spec-validation` `rubric` `cli` `json-schema` `llm-agents` `agent-tooling` `design-by-contract` `python` `proof-of-concept`.

## Quick Start (dev)

```bash
docker compose build
docker compose run --rm test            # full pytest suite
docker compose run --rm harness --help  # CLI help
```

From another project directory, the harness can be invoked without installing the console script by either:

```bash
docker compose -f /workspace/assessment_poc/docker-compose.yml run --rm harness --output json schema --command check
PYTHONPATH=/workspace/assessment_poc/src python3 -m assessment_harness.cli --output json schema --command check
```

The bare `assessment-harness` executable is not currently on PATH in this environment.

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

- **Canonical specification**: v1.28 implementation plan first, then `v2.2` ideation (revised in-place 2026-05-27). v2.1 and earlier ideation versions are historical; v2.2 supersedes v2.1 in any overlapping area without area limits.
- **Final-review finding key minimalism** (plan v1.19 §5.6): `target_type: finding` decisions use only generated identifiers in `target_key`; no `message`, `evidence`, title/description/text, or other payload copies. Stale/duplicate decision keys and duplicate canonical keys inside `findings.json` are invalid input. Missing decisions or `hold`/`rerun_requested` keep `gate` at `pending_review`.
- **Review draft status guard** (Owner, 2026-05-28; plan v1.19 §5.6): `review` accepts only `findings.status=success` or `provisional_findings`. `invalid_input` findings docs are rejected before draft creation so Rule 0 invalid empty findings cannot accidentally become a `gate success`. `gate` remains status-agnostic and consumes explicit final review records for manual recovery/audit workflows.
- **Review draft overwrite guard** (Owner, 2026-05-28; plan v1.19 §5.6): `review` must not overwrite existing `<out-dir>/review.yaml` by default. Intentional regeneration requires `--force`; timestamped/versioned draft management is deferred, and callers should use a distinct `--out-dir` when they want parallel draft history.
- **Gate blocking scope** (plan v1.19 §5.6): `gate` exit `1` is limited to confirmed `orphan_scored_rubric_item`, `optionality_mismatch`, and `mandatory_spec_bonus_only_traced`. Confirmed Rule 2/L1/L5 findings are review outcomes but not v0 blocking verdicts.
- **Rule 1 finding type naming convention** (plan v1.19 §6): no-trace findings follow `{prefix_}orphan_{role}_rubric_item`. `possible_` prefix marks scored items because `gate` may promote them to confirmed; bonus / qualitative have no symmetric promotion path so prefix is omitted. Any future Rule 1 extension applies the same convention without re-deciding the literal.
- **`--source-manifest` is a required `check` input** (plan v1.19 §5.0 / §5.1 / §11): Phase 0 mandates immutable source snapshot grounding. Missing manifest → `status=invalid_input` / exit `2` / diagnostic `source_manifest_required` / next_action `provide_source_manifest`. argparse keeps the flag declared as `default=None` so caller agents always receive the structured envelope on stdout instead of argparse's usage text on stderr.
- **`--policy` is a required `check` input** (plan v1.20 §8 / §15): Phase 0 requires `rules.optionality_mismatch.weight_threshold`. Missing policy → `status=invalid_input` / exit `2` / next_action `provide_policy`; schema-valid policy missing that field → `invalid_input` / `fix_input`. This prevents Rule 3 from being silently disabled.
- **Rule 1 final-coverage boundary** (plan v1.19 §6 Rule 1, §5.3.1): the only `semantic_status` values that count as final coverage for Rule 1 are `human_accepted` and `human_overridden`. Everything else — pre-review (`pending_verification`, `agent_*`) and post-review non-coverage (`human_rejected`, `rerun_requested`) — surfaces as `unconfirmed_trace_coverage` (medium / provisional) in `check`. `gate` is the only stage that may promote persistent non-coverage into a confirmed `orphan_scored_rubric_item`. **This boundary applies to Rule 1 and `gate` only.** Rule 2 and Rule 3 do not consult `semantic_status` (they use the structural conditions in plan §6 Rule 2 / Rule 3). Lint family (Rule L1/L5/L6) also does not consult `semantic_status` — L-DET, structural only.
- **Rule 2 finding contract** (plan v1.19 §6; initially fixed in v1.14): `uncovered_must_spec_item` / `review_uncovered_must_spec` is locked as the public contract. The owner-recommended `uncovered_*_spec_item` naming reflects a spec coverage gap rather than a rubric orphan.
- **Rule 3 finding contract** (plan v1.19 §6): `optionality_mismatch` / `review_optionality_mismatch` is locked as the public contract, matching the existing fixture and policy namespace.
- **Lint family naming convention** (plan v1.19 §6, ideation v2.2 §3): family prefix `Rule L*`; finding types follow ideation candidates verbatim (`double_scored_spec`, `bonus_grades_mandatory_only`, `mandatory_spec_bonus_only_traced`) — readability over uniformity with Rule 1's `{prefix}_{role}_rubric_item` pattern. Owner-confirmed.
- **Lint safeguard mechanism** (plan v1.19 §5.7 / §6 Rule L1 / L6): medium/high lint findings carry both extended payload and a paired `review_queue` entry. Owner resolved the Phase 0/Phase 2 wording conflict by allowing deterministic lint safeguard queue artifacts in Phase 0 `check`; Rule 0 clean runs write an empty queue when no entry fires to avoid stale review state. L1 implements `double_scoring_review`; L6 implements `mandatory_spec_bonus_review`.
- **Rule L6 qualitative boundary** (Owner, 2026-05-27; plan v1.19 §6): L6 fires only when every trace of a `must` spec targets a `bonus` rubric. A `qualitative` trace, alone or mixed with bonus, suppresses L6 because qualitative is not scoring/bonus credit; no-scored-coverage is covered by implemented Rule 2.
- **`clean_assignment` is an automation-only baseline**: trace links stay on `pending_verification` so the fixture matches the state a real agent run produces. The canonical pre-review outcome is therefore `status=provisional_findings` with N medium `unconfirmed_trace_coverage` findings, not `status=success`. Reaching `success` requires final-review evidence, which Phase 3 will supply.
- **Rule 0 evidence verification**: per-entry `verification_mode`. `token_sequence` performs opt-in strict substring matching of pre-inserted quantitative markers; `ai_judgement` is the PoC default. Phase 0 keeps `ai_judgement` links pending; Phase 2 will route them through `ai_judgement_pending` queue entries and the verifier-agent stage.
- **CLI output stability**: four-field stable core (`status`, `exit_code`, `command`, `next_actions`) plus informational fields with a `schema --command <name>` self-discovery command.
- **Policy unification**: `config/policy.yaml` is the single policy file with `rules`, `compacting`, `runs`, and `verification` sections.
- **Compacting model**: union of every valid candidate with `support` / `identity_basis` / `variants` preserved. No quorum, no automatic acceptance, no automatic exclusion.
- **Trace link ID lineage** (Owner, 2026-05-28; plan v1.22 §5.0): trace link internal `rubric_id` / `spec_ids` are dependent references remapped through spec/rubric item `id_map`, while the trace link entry itself also has canonical identity as a compacted relationship artifact. `id_map.entity_type` therefore includes `trace_link` alongside `spec_item` and `rubric_item`.
- **Final review power**: `accept` / `hold` / `rerun_requested` / `override`. `override` is recorded as a distinct `kind: human_override` provenance entry in `sources`.
- **Mock runner role**: `agent_runners/mock.py` is a deterministic fixture-replay runner used only for protocol contract tests; it is separate from `manual.py` which holds human-authored Phase 0/1 inputs.
- **Trace separation**: `agent_trace.raw.jsonl` and `agent_trace.audit.jsonl` are stored separately with distinct retention/redaction expectations. `agent_trace.schema.json` currently validates one audit JSONL event at a time; raw trace retention/redaction remains a later decision.
- **Audit trace role payloads** (plan v1.23 §5.4.1): turn events must carry audit payload by role: `system` requires `content_ref`, `agent` requires `tool_call`, and `tool` requires `name` plus `result_ref`.
- **Decision boundary**: `check` creates provisional findings; only `gate`, after final human review, returns an external blocking verdict.
- **Source grounding**: Phase 0 uses immutable input snapshots, document hashes, and line/span `source_ref`; DB/RAG storage is deferred.
- **Canonical IDs**: compacting remaps run-local IDs to canonical IDs and retains `id_map` provenance.
- **Semantic verifier-agent**: `ai_judgement` links are checked by separate read-only multi-run verifier execution; proposals are retained in `semantic_verifications.yaml` without rewriting compacted links.

## Implementation Decisions (Phase 0 iteration 1 / 1.5 / 2)

- Adopted `src/` layout (`src/assessment_harness/...`); package import name unchanged from plan §7.
- Phase 0 held `agent_runners/` and `tools/` out of scope. Phase 2 has now started with the `AgentRunner` protocol, deterministic mock replay, candidate schemas, runner artifact normalization, candidate/audit trace attribution validation, and normalized candidate run integrity classification; framework tools and real SDK runners remain unimplemented.
- `evidence_source_ref` is validated by span containment within the referenced `spec_item.source_ref` (same document, evidence span inside the spec span), not strict equality.
- Schemas allow `additionalProperties: true` at entity objects so candidate-stage fields (`confidence`, `agent_run_id`, ...) added in Phase 2 do not break Phase 0 schemas. Run-level candidate artifacts are now separately validated by `candidates.schema.json`.
- `review` initial implementation deliberately writes safe `hold` drafts only. It does not collect human choices interactively, auto-accept findings, rewrite trace links, or materialize `human_override` provenance.
- `gate` initial implementation deliberately covers finding-level final decisions only. Trace-link override materialization, review_queue composition, and semantic-verification queue handling remain later Phase 2/3 work.
- `AgentRunner` protocol foundation deliberately stops at type boundary plus deterministic mock replay. It does not introduce SDK credentials, framework tools, orchestration, raw trace retention policy, or candidate compacting behavior.
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
- Review queue composition at Phase 2: Phase 0 `--review-queue-out` currently writes the lint-safeguard artifact. When `compact`/`verify` queue generation lands, add merge/update behavior that retains upstream queue entries before routing all review work through one file.

## Next Tasks

### Sequencing Decision (Owner, 2026-05-27)

**Rule 0-3 and lint family L1/L5/L6 are complete. Initial finding-level `review`/`gate` path is implemented.**

Rationale: Rule 2 and Rule 3 completed the remaining deterministic structural checks on the established lint/output pipeline. Plan v1.30 now supplies the minimal final-review finding mapping, safe review draft generation, gate boundary matrix, draft safety guards, Phase 0 policy completeness, policy schema-validation recovery clarification, trace link canonical ID lineage, audit trace role-payload requirements, candidate artifact schema foundation, candidate audit-trace attribution validation, runner artifact normalization, staged candidate run integrity classification, and deep candidate Rule 0 validation with explicit diagnostic-to-status routing.

### Publication Boundary (2026-05-27)

Rules L1 and L5 plus the plan v1.12 contract resolution have passed the owner's independent AI verification, and the owner authorized publishing these implementation batches to `origin/main`. `.serena/` remains local onboarding metadata and is not part of the published implementation batches.

Rule L6 plus plan v1.13's bonus-only/qualitative boundary resolution passed the owner's independent AI verification, and the owner authorized publishing this implementation batch to `origin/main`.

Rule 2 plus plan v1.14's `uncovered_must_spec_item` / `review_uncovered_must_spec` contract update passed the owner's independent AI verification and is published to `origin/main`.

Rule 3 plus plan v1.15's optional-only boundary reinforcement passed the owner's independent AI verification, and the owner authorized publishing it together with the verification-record guidance and audit records to `origin/main`.

### Rule 2 — Required Spec Coverage (complete)

- Rule 2 emits `uncovered_must_spec_item` (`medium`, `provisional`) and `review_uncovered_must_spec`; the literal pair is frozen in plan v1.14 §6.
- It is structural only: any `scored` trace covers a must spec regardless of `semantic_status`; bonus-only, qualitative-only, and untraced must specs remain uncovered.
- Grounded `fixtures/uncovered_must_spec/` locks untraced, pending-scored, bonus-only, qualitative-only, optional, and informational boundaries. The existing `bonus_misuse` fixture now also records intended Rule 2 + L5 + L6 co-firing for S3/RB4.

### Rule 3 — Optionality Consistency (complete)

- Rule 3 emits `optionality_mismatch` (`high`, `provisional`) and `review_optionality_mismatch`; the literal pair is frozen in plan v1.19 §6.
- It evaluates scored rubrics against `rules.optionality_mismatch.weight_threshold`; only optional-only traced scored rubrics at or above threshold fire.
- It is structural only: pending semantic status still fires; must/informational-mixed, non-scored, untraced, and below-threshold rubrics do not.
- Grounded `fixtures/optionality_mismatch/` locks high, threshold, pending-status, must/informational-mixed, bonus/qualitative-role, and below-threshold boundaries.

### `gate` and later phases

- Initial finding-level `review`/`gate` is implemented with `final_review.schema.json`. `review` produces a safe `hold` draft with minimal finding keys; `gate` is the only stage that may promote persistent `possible_orphan_scored_rubric_item` / `unconfirmed_trace_coverage` into `orphan_scored_rubric_item` (high / confirmed). Lint-family and Rule 3 findings can be confirmed/dismissed by final review; only confirmed Rule L6 and Rule 3 are currently blocking.
- Next gate/review work: materialize trace-link override provenance, support richer human decision input if needed, and compose Phase 2 compact/verifier queue entries without overwriting lint safeguard queue entries.
- Real-assignment permissions and Phase 2 runner/retention parameters resolve here too.

### Lint family (complete) — plan v1.19 §6

- **Spec status**: complete in plan v1.19 §6. Rules L1, L5, and L6 are implemented.
- **L1 landed**: introduced `findings.schema.json` payload IDs, `review_queue.schema.json`, default/overridden `--review-queue-out` artifact handling, `review_double_scoring`, and grounded `fixtures/bonus_misuse/`.
- **L5 landed**: added `bonus_grades_mandatory_only` and `review_bonus_mandatory_only`; `bonus_misuse` now locks RB1 L1+L5 co-firing, RB2 optional non-firing, and RB3 Rule 1 orphan separation.
- **L6 landed**: added high/provisional `mandatory_spec_bonus_only_traced`, paired `mandatory_spec_bonus_review`, `bonus_rubric_ids[]`, and `review_mandatory_spec_bonus_only`; qualitative participation explicitly suppresses L6 under the owner-approved v1.13 boundary, while Rule 2 now surfaces the remaining missing-scored coverage.
- **Phase 2 follow-through**: do not aim `--review-queue-out` at a future compact/verifier queue until composition preserves existing non-lint entries; the current output is the Phase 0 lint-safeguard artifact.
- **Fixture**: single shared fixture (e.g. `fixtures/bonus_misuse/`) covering all three L1/L5/L6 branches plus over-strict guards, mirroring how `orphan_scored_rubric` covers Rule 1's three branches. **Critical**: fixture and tests must visualize the mutual-exclusion / co-firing boundary between Rule 1 `orphan_bonus_rubric_item`, Rule L5 `bonus_grades_mandatory_only`, and Rule L6 `mandatory_spec_bonus_only_traced` — all three touch bonus rubrics on different conditions and reviewers must not confuse them.
- **CLI envelope**: each lint finding type adds a `next_actions` literal (`review_double_scoring`, `review_bonus_mandatory_only`, `review_mandatory_spec_bonus_only`) and may add severity counts as needed. Schema-contract test (`schema --command check`) must be extended in lockstep — see "Test-surface lessons" below.
- **`drift_observations[]` (plan v1.19 §5.6)**: represented in `final_review.schema.json` as a manual audit channel for Rule L8 drift observations. It does not affect `check`/`gate` result codes.

### Post-L6 lint extensions (owner decision required before entry)

- Rule L2 (`bonus_weight_encroachment`, policy threshold), Rule L4 (`duplicate_trace_link`, lint-independent — NOT absorbed into Rule 0 per owner), Rule L7 + C1 (`forbidden_clause_rewarded` + `requirement_level: forbidden` schema extension). All specced in ideation v2.2 §4-§6 but not in plan §6 yet.
- Sole remaining ideation §9.2 open decision: L7-DET vs L7-SEM priority (resolved at L7 plan-promotion time).

### Test-surface lessons from today's session (Slice 3.1 retrospective)

When adding any new envelope field, next_action type, or schema-contract entry, also add a regression that **explicitly** asserts on it. The CLI's primary user is an AI agent; the envelope (stdout JSON) is the public contract, not the on-disk `findings.json`. Tests that only read findings.json miss envelope-shape regressions — slice 3 shipped three new envelope surfaces with no test for any of them, and the gap only surfaced via owner review. `_run_check` in `tests/test_fixtures.py` now returns the envelope as a 4-tuple to make this easy. Use it.

When a **verifier** claims branch coverage from probes, measure at the level that distinguishes the branches — usually the error message, not just exit code and `next_action` type. Two different code paths (e.g. policy schema validation vs `_validate_check_policy`) can converge on the same envelope outcome (`exit 2` / `fix_input` / `status=invalid_input`) while exercising entirely different functions. The v1.20 policy completeness verification probed 8 input shapes and reported "8/8 PASS" using only exit code and `next_action`; the v1.21 strengthening follow-up surfaced that one of those shapes never reached the named validator at all — same outcome, different path. The fix is on the verifier side: include the rejection message (or a path-attributing assertion) in any probe table that claims branch coverage. Probes that only check the outcome can give a false sense of coverage when defensive depth and primary checks both lead to the same envelope.

## Verification

- 200 tests pass after the v1.30 source-grounding status reconciliation (`python3 -m pytest -q`). Collection reports 27 agent-runner contract, 48 CLI contract, 8 fixture, 22 model, and 95 rule tests. The candidate schema regressions lock missing candidate provenance, invalid integrity status, the new `source_grounding_mismatch` enum literal, and invalid embedded `proposed_item` shapes across spec/rubric/trace candidates; candidate audit-trace regressions lock matching run IDs, missing trace attribution, schema errors, and all three candidate sections; normalization regressions lock candidate schema validity, audit-trace attribution compatibility, provenance fields, default `pending_check`, and compacting-only field stripping across spec/rubric/trace candidates; integrity regressions lock clean structural `structurally_validated`, candidate/audit schema `schema_violation`, missing trace attribution `trace_attribution_error`, no mutation of original normalized candidates, deep Rule 0 clean promotion to `validated`, evidence spec-id mismatch/dangling internal references to `invalid_reference`, source grounding failure to `source_grounding_mismatch`, token-sequence quote mismatch to `quote_mismatch`, `invalid_reference > source_grounding_mismatch > quote_mismatch` precedence, and the `ai_judgement` over-strict guard. The policy-incomplete regression is parametrized across the four shapes `_validate_check_policy` must catch (empty doc, missing `rules`, empty `rules`, threshold absent) so a refactor cannot silently let one through.
- `schema --command review --output json` exposes informational `review_path`, `decision_count`, and `input_error`.
- `schema --command gate --output json` exposes `complete_final_review`, `fix_final_review`, `revise_assessment`, plus informational `final_review_path`, `findings_path`, `blocking_count`, `confirmed_finding_count`, `dismissed_finding_count`, `pending_decision_count`, `blocking_findings`, and `input_error`.
- `schema --command check --output json` exposes `provide_policy`, `review_double_scoring`, `review_bonus_mandatory_only`, `review_mandatory_spec_bonus_only`, `review_uncovered_must_spec`, `review_optionality_mismatch`, plus informational `review_queue_path` and `review_queue_count`.
- Smoke runs for the current state:
  - `gate` on a final review record with no decision for a provisional `optionality_mismatch`: exit `0`, `status=pending_review`, `pending_decision_count=1`, and `complete_final_review`.
  - `review` on grounded `fixtures/orphan_scored_rubric` findings writes three `hold` decisions with minimal finding keys; passing that draft to `gate` yields `pending_review` with `pending_decision_count=3`.
  - `gate` on grounded `fixtures/orphan_scored_rubric` after a minimal-key final review that accepts R2 and overrides R1/R3: exit `1`, `status=fail`; R2 promotes to confirmed `orphan_scored_rubric_item`; `(blocking_count=1, confirmed_finding_count=1, dismissed_finding_count=2)`.
  - `check` on grounded `fixtures/optionality_mismatch`: exit `0`, `status=provisional_findings`; Rule 3 yields `optionality_mismatch` on R_HIGH and R_PENDING only; below-threshold R_LOW, must-mixed R_MIXED, informational-mixed R_INFO_MIXED, bonus R_BONUS, and qualitative R_QUAL suppress correctly; R_PENDING also preserves Rule 1 `unconfirmed_trace_coverage`; `review_queue_count=0`; `(high=2, medium=1, informational=0)`.
  - `check` on grounded `fixtures/uncovered_must_spec`: exit `0`, `status=provisional_findings`; Rule 2 yields `uncovered_must_spec_item` on S_UNTRACED, S_BONUS_ONLY, and S_QUAL_ONLY while pending scored S_COVERED is covered; S_BONUS_ONLY co-fires L5/L6; `review_queue_count=1`; `(high=1, medium=5, informational=0)`.
  - `check` on grounded `fixtures/bonus_misuse`: exit `0`, `status=provisional_findings`; existing R1/RB1/RB3 boundaries remain, and S3/RB4 now intentionally co-fires Rule 2 + L5 + L6; `review_queue_count=2`; `(high=1, medium=5, informational=1)`.
  - `check` on grounded `fixtures/orphan_scored_rubric` with manifest: exit `0`, `status=provisional_findings`, all three Rule 1 branches visible — `unconfirmed_trace_coverage` on R1 (medium), `possible_orphan_scored_rubric_item` on R2 (high), `orphan_bonus_rubric_item` on R3 (informational). `provisional_high_count=1`, `provisional_medium_count=1`, `provisional_informational_count=1`.
  - `check` on grounded `fixtures/clean_assignment` with manifest: exit `0`, `status=provisional_findings`, two `unconfirmed_trace_coverage` findings on R1 and R2.
  - `check` on grounded `fixtures/reference_integrity` with manifest: exit `2`, `status=invalid_input`, all eight Rule 0 violation codes present (`high_integrity_count=9` because `evidence_quote_missing_for_spec_id` fires twice; pre-existing duplicate, not a regression).
  - `check` on `fixtures/clean_assignment` without `--source-manifest`: exit `2`, `status=invalid_input`, diagnostic `source_manifest_required`, next_action `provide_source_manifest`.
- Publishing authorization was received from the owner after independent AI review of L1, L5, L6, Rule 2, and the boundary-reinforced Rule 3 batch; the Rule 3 batch and accompanying verification-guidance/audit documents are authorized for publication to `origin/main`.

## Project Structure

- `README.md`: user/agent entry point.
- `AGENTS.md` / `CLAUDE.md`: behavioural guidelines for coding agents.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`: canonical dev/run environment.
- `pyproject.toml`: src-layout Python package, entry point `assessment-harness`.
- `src/assessment_harness/`: package code.
  - `cli.py`: `check`, `schema`, `report`, `review`, `gate` subcommands; envelope/exit-code contract; Rule 1/2/3 and lint-family wiring after a clean Rule 0 pass; finding-level final review draft/gate decisions.
  - `models.py`: YAML+schema loader, `SourceSnapshot`/`Document` with sha256 and line/span access.
  - `rules.py`: Rule 0 reference-integrity engine; complete Rule 1, Rule 2, and Rule 3 implementations; lint Rule L1/L5/L6 implementations. `HUMAN_ACCEPTED_SEMANTIC_STATUSES` locks the Rule-1-only final-coverage boundary.
  - `schemas.py`: schema loader with `ASSESSMENT_HARNESS_SCHEMA_DIR` env override.
  - `report.py`: Markdown renderer.
  - `agent_runners/`: framework-neutral runner boundary.
    - `base.py`: `AgentRunner` protocol and `AgentRunResult`.
    - `integrity.py`: structural and deep Rule 0 candidate run integrity classification helpers.
    - `mock.py`: deterministic fixture replay runner for protocol contract tests only.
    - `normalization.py`: runner artifact to candidate artifact normalization helpers.
    - `validation.py`: candidate artifact / audit trace attribution validation helpers.
- `schemas/`: fourteen JSON Schemas, including `review_queue.schema.json` introduced with Rule L1, `final_review.schema.json` introduced with initial `gate`, and Phase 2 contract foundations `candidates.schema.json` / `id_map.schema.json` / `semantic_verifications.schema.json` / `agent_trace.schema.json`.
- `config/policy.yaml`: default policy.
- `fixtures/clean_assignment/`: passing fixture with source manifest, sha256, spec.md, rubric.md.
- `fixtures/reference_integrity/`: grounded failing fixture covering all eight current Rule 0 diagnostic codes; carries its own `source/spec.md`, `source/rubric.md`, and `source_manifest.yaml`.
- `fixtures/orphan_scored_rubric/`: grounded Rule 1 end-to-end fixture exercising all three branches: R1 (scored, traced with pending_verification) → unconfirmed_trace_coverage, R2 (scored, untraced) → possible_orphan_scored_rubric_item, R3 (bonus, untraced) → orphan_bonus_rubric_item. Same `source/` + manifest layout.
- `fixtures/bonus_misuse/`: grounded lint fixture; exercises L1/L5 via S1/R1/RB1, RB2/S2 optional non-firing, RB3 untraced Rule 1 informational separation, and Rule 2/L5/L6 co-firing via bonus-only mandatory S3/RB4.
- `fixtures/uncovered_must_spec/`: grounded Rule 2 fixture covering untraced, pending-scored-covered, bonus-only, qualitative-only, optional, and informational spec boundaries.
- `fixtures/optionality_mismatch/`: grounded Rule 3 fixture covering optional-only high weight, policy threshold, pending-status structural emission, must/informational-mixed suppression, bonus/qualitative-role exclusion, and below-threshold suppression.
- `tests/`: `test_rules.py`, `test_cli_output_contract.py`, `test_fixtures.py`, `test_models.py`, `test_agent_runner_contract.py`, `conftest.py`.
- `docs/implementation_plan_assessment_harness_poc_v1.md`: implementation source of truth (v1.28).
- `docs/ideation_assessment_harness_v2.2.md`: latest ideation (final 2026-05-27, in-place revised same day). Adds Rubric Lint Rules family — 6 accepted (L1, L2, L4, L5, L6, L7), 3 rejected. Source for plan v1.19's §6 lint family.
- `docs/ideation_assessment_harness_v2.1.md`: latest ideation, second in precedence.
- `docs/ideation_assessment_harness_v2.md`, `docs/ideation_assessment_harness_v1.md`: historical references.
- `docs/verifications/YYYY-MM-DD/<slug>.md`: independent audit records in date-based subdirectories (mirroring `docs/daily_logs/`); the Rule 3 boundary-tightening record supersedes the initial withdrawn Rule 3 verdict.
- `docs/daily_logs/2026-05-25/work_log.md`: full record of planning iterations (v1.0 → v1.7) and Phase 0 iteration 1 / 1.5.
- `docs/daily_logs/2026-05-26/work_log.md`: Phase 0 iteration 2 Rule 1 slices, contract regression follow-up, and publication review record.
- `CHANGELOG.md`: major milestones.
- `HANDOFF.md`: this file.
