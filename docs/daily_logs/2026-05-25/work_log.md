# Work Log - 2026-05-25

## Goals

- Review the assessment harness ideation documents for internal consistency and PoC feasibility.
- Identify decisions required before implementation begins.

## Completed Work

### Ideation document feasibility review

- Reviewed `docs/ideation_assessment_harness_v1.md`, `docs/ideation_assessment_harness_v2.md`, and `docs/ideation_assessment_harness_v2.1.md`.
- Compared `v2` and `v2.1`; `v2.1` retains the `v2` proposal and adds the LLM-agnostic PoC implementation principles in section 19.
- Confirmed that a manual, structured-input rule engine is a feasible first PoC: schema validation, missing trace detection, and report generation can operate without an LLM.
- Recorded the review outcome in `HANDOFF.md` so the outstanding product and schema decisions are visible before implementation.

Files changed:

- `docs/daily_logs/2026-05-25/work_log.md`
- `HANDOFF.md`

Effect:

- The proposal is ready for a narrowed Phase 0 specification, but not yet ready to implement unchanged because several contracts and success criteria are underspecified.

### Cross-review of independent feasibility assessment

- Compared an independent AI review supplied by the owner against the earlier document review.
- Confirmed agreement on the viable PoC core: manually approved structured inputs, deterministic rules, reports, regression fixtures, and at least one real assignment case.
- Accepted the owner's decision that business/market validation is not a blocker for a modular technical PoC; market discovery remains a later validation track rather than a Phase 0 gate.
- Identified two corrections to the independent review: the current `trace_to` list representation already supports N:M links, while Rule 5 cannot be a deterministic PoC rule until baseline version and round-state inputs are defined.

Effect:

- The recommended PoC v0 rule set is now narrower: Rule 1, Rule 2, and Rule 3 only, with Rule 5 deferred or preceded by a minimal lock-state contract.

### PoC implementation plan

- Captured the owner's clarification that excluding LLM work from Phase 0 is a sequencing decision only; the final PoC must include LLM-assisted candidate generation.
- Created `docs/implementation_plan_assessment_harness_poc_v1.md`.
- Defined a phased route from deterministic validation core, through a real-assignment manual run, to an actual LLM adapter and final human-approved end-to-end demonstration.
- Proposed implementation-specific document precedence, minimal v0 data contracts, Rule 1-3 semantics, CLI flow, tests, outputs, and final completion criteria.

Files changed:

- `docs/implementation_plan_assessment_harness_poc_v1.md`
- `docs/daily_logs/2026-05-25/work_log.md`
- `HANDOFF.md`

Effect:

- The implementation path now explicitly preserves LLM-assisted execution as a required PoC deliverable while keeping deterministic validation independently testable.

### Re-review of agent-level harness revision

- Re-read the externally revised `docs/implementation_plan_assessment_harness_poc_v1.md` after its v1.2 shift from a direct LLM adapter model to a framework-agnostic, tool-using `AgentRunner` model.
- Confirmed that the shift is conceptually appropriate if the intended consumer is an AI agent: structured CLI I/O, tool boundaries, recovery, and candidate trace are meaningful additions over a single LLM request.
- Identified implementation-blocking ambiguities without editing the plan itself:
  - The document requires human approval for completion but also allows a caller-agent approval stage; these imply different trust boundaries.
  - Rule 0 classifies broken references as blocking findings while the CLI contract classifies broken references as input errors, yielding conflicting exit-code behavior.
  - Existing LLM-adapter terminology remains in goals, artifacts, and phase gates after the agent-runner redesign.
- Identified overclaims to narrow before implementation:
  - Substring-matched `evidence_quotes` verify reference integrity, not semantic validity of a rubric-to-spec trace.
  - A mock runner contract test does not prove real cross-framework portability or one-file replacement scope.
  - `agent_trace.jsonl` should store observable actions/results and bounded summaries only; a required "reasoning summary" contract needs explicit clarification.

Effect:

- The architecture direction is accepted for further planning, but Phase 0 contract implementation should wait until approval authority and exit-code semantics are resolved.

### Multi-run agent harness clarification and plan v1.3

- Received owner clarification that intermediate candidate approval is not the final operating model: the harness must execute agents multiple times, validate each output, aggregate results, and leave human involvement at final review.
- Updated `docs/implementation_plan_assessment_harness_poc_v1.md` to v1.3:
  - Replaced intermediate `approve` flow with `extract --runs N -> aggregate -> check -> report -> review`.
  - Recast artifacts from `approved` to `consolidated` plus final review metadata.
  - Defined dual Rule 0 behavior: preserve reference-integrity diagnostics while invalid inputs/runs are excluded and single `check` uses exit `2`.
  - Split raw debugging trace from audit trace and avoided requiring model internal reasoning as an interface contract.
  - Narrowed PoC portability evidence to protocol separation using a mock runner; actual second-framework integration moves to a later MVP.
- Added aggregation policy and final-review/trace-retention policies as remaining design decisions.

Files changed:

- `docs/implementation_plan_assessment_harness_poc_v1.md`
- `docs/daily_logs/2026-05-25/work_log.md`
- `HANDOFF.md`
- `CHANGELOG.md`

Effect:

- The plan now represents an agent-level harness for repeated probabilistic executions rather than a one-shot LLM call or intermediate human approval workflow.

### Compacting model and plan v1.4

- Received owner clarification that aggregation must be a compacting operation, not a classification: every valid candidate stays as an entry; only duplicates collapse, with `support`, `identity_basis`, and `variants` preserved. No automatic acceptance or rejection.
- Updated `docs/implementation_plan_assessment_harness_poc_v1.md` to v1.4:
  - Renamed `aggregate`/`consolidated` to `compact`/`compacted` throughout artifacts, CLI, modules, schemas, and tests.
  - Added `support` (`total_valid_runs`, `found_in_runs`), `identity_basis`, and `variants` fields to spec_items, rubric_items, and trace_links (§5.1–5.3).
  - Specified the `integrity_status` enum (six values) on candidates (§5.4) and added a new §5.6 Final Review Record schema with action enum `accept`/`hold`/`rerun_requested`/`override` and `human_override` provenance.
  - Unified naming: `disagreement queue` references replaced by `review_queue`.
  - Reframed §13 Phase 2/3 decisions: removed quorum/threshold (incompatible with no-auto-acceptance), added identity_basis algorithm candidates, single-runner repeated execution as the PoC run shape, and reproducibility scope ("same compacted YAML → same findings" only).
  - Replaced `aggregation.py`/`aggregation.schema.json` with `compacting.py`/`compacting.schema.json`.

Files changed:

- `docs/implementation_plan_assessment_harness_poc_v1.md`
- `docs/daily_logs/2026-05-25/work_log.md`

Effect:

- The plan now expresses an auditable compacting pipeline that preserves every probabilistic finding for human review, including single-run entries that would have been silently dropped by a quorum-based approach.

### Verification mode, stable CLI contract, and plan v1.5

- Received owner answers on the three pre-Phase-0 decisions:
  1. Adopt the implementation plan and `v2.1` as the canonical specification pair.
  2. Split Rule 0 evidence verification per entry: `token_sequence` for pre-inserted quantitative markers, `ai_judgement` for everything else, with `ai_judgement` as the PoC default.
  3. Treat `cli_output.schema.json` stability as an incrementally established contract rather than a frozen one; provide a self-discovery command so caller agents do not depend on documentation drift.
- Owner also confirmed instructing the harness to keep both raw and audit traces, allow human override at final review, and complete missing schemas (`review_queue` entries, mock runner, policy unification, README, work logs).
- Updated `docs/implementation_plan_assessment_harness_poc_v1.md` to v1.5:
  - Added `verification_mode: token_sequence | ai_judgement` to `evidence_quotes` (§5.3) and split Rule 0 behaviour accordingly (§6 Rule 0). Strict substring is opt-in; ai_judgement entries are forwarded to `review_queue` as `ai_judgement_pending`.
  - Specified that `findings.json` is always written, even on `invalid_input`, so caller agents can rely on its presence (§6 Rule 0).
  - Added §5.7 Review Queue Entry schema with five entry types (`invalid_run`, `ai_judgement_pending`, `identity_collision`, `low_support`, `semantic_disclosure`) and `status: open | resolved` transition.
  - Added `agent_runners/mock.py` as a dedicated fake runner for protocol contract tests, distinct from `manual.py` which is for human-authored Phase 0/1 inputs (§7).
  - Unified all policy files into a single `config/policy.yaml` with `rules`, `compacting`, `runs`, and `verification` sections (§7, §8). Removed v1.4's `--identity-basis-config` flag.
  - Defined the CLI stable-core contract (`status`, `exit_code`, `command`, `next_actions`) vs informational fields (§8.1.1) and added `assessment-harness schema --command <name>` self-discovery (§8.1.2).
  - Marked all three Phase 0 pre-decisions as adopted in §13 and added new tracked-but-tunable items (informational → stable promotion, default verification mode promotion, mock runner fixture format).
- Created supporting documents per CLAUDE.md §5:
  - `README.md`: user/agent quick start, flow overview, data contracts summary, policy, CLI contract, phase status, document index.
  - This work_log entry, HANDOFF refresh, CHANGELOG refresh.

Files changed:

- `docs/implementation_plan_assessment_harness_poc_v1.md`
- `README.md` (new)
- `docs/daily_logs/2026-05-25/work_log.md`
- `HANDOFF.md`
- `CHANGELOG.md`

Effect:

- All Phase 0 entry gates are now satisfied. Implementation of the deterministic core (Rule 0–3 against manual compacted fixtures) can start immediately. Phase 2/3 decisions remain open but do not block Phase 0.

### Codex re-review of v1.5

- Reviewed the v1.5 implementation plan, updated README, HANDOFF, and CHANGELOG after external AI revisions.
- Confirmed meaningful improvements: auditable compacting instead of quorum classification, explicit final-review actions, per-entry verification modes, unified policy input, and CLI schema introspection.
- Identified unresolved implementation semantics that must be answered before Phase 2 and may affect the Phase 0 model:
  - All valid candidate entries are preserved before human review, yet Rule 1–3 currently emit blocking findings from those unreviewed entries. A one-run false candidate can therefore generate a blocking failure unless findings are marked provisional until review or validated again after review.
  - `verification_mode: ai_judgement` is the default and forwards semantic checking to review, but Rule 1 currently treats the presence of a validated compacted trace link as coverage. A semantically unconfirmed link may suppress an orphan finding.
  - Cross-run trace-link compacting uses run-produced `rubric_id`/`spec_ids`; independent agents can assign different IDs for the same extracted entities unless canonical ID remapping is specified.
  - Rule 0 quote checks are defined against `spec_item.text`; source anchoring back to original `spec.md`/rubric tool-result ranges is not yet specified, so agent-copied or hallucinated source items may pass local integrity.
- Noted smaller contract inconsistencies to correct when revising the plan: `next_actions` is described as both mandatory and optional in the stable core, `hold`/`rerun_requested` do not naturally imply resolved review-queue status, `compacting.schema.json` is referenced in tests but omitted from the module tree, and the Phase 0 policy example does not use the unified `rules:` wrapper.

Effect:

- Phase 0 deterministic mechanics remain feasible, but before treating its output contract as final the project should distinguish provisional pre-review diagnostics from final reviewed findings and specify source/ID grounding rules needed by the agent phase.

### Decision boundary, source grounding, and plan v1.6

- Received owner decisions following the v1.5 review:
  - Findings from repeated agent execution must not block before final human review; an external decision command should own blocking verdicts.
  - Semantic evidence needs separate state handling, with a better agent-first recommendation requested.
  - Original documents must be supplied and grounded without bringing DB/RAG storage into PoC scope.
  - Cross-run item/link IDs must be explicitly connected in a way extensible to future project/version management.
  - Review states should reflect intermediate versus final workflow needs.
- Updated `docs/implementation_plan_assessment_harness_poc_v1.md` to v1.6:
  - Added `gate` as the sole external verdict command; `check` findings are `provisional` before final review.
  - Added `semantic_status` lifecycle and prevented pending `ai_judgement` links from becoming final Rule 1 coverage.
  - Proposed a verifier-agent stage for semantic link suggestions before the final human review; owner confirmation remains open.
  - Added immutable document snapshot/hash/span `source_ref` grounding and Rule 0 checks against original sources, without DB/RAG.
  - Added run-local to canonical ID remapping and `id_map` provenance.
  - Refined review queue status transitions (`held`, `rerun_pending`, `resolved`) and CLI/schema/module entries.
- Updated `README.md`, `HANDOFF.md`, and `CHANGELOG.md` to the v1.6 workflow.
- Performed a consistency pass after the revision: removed a leftover Phase 0 `check` exit-`1` exception, aligned README/Phase 3 flow on `gate`, and clarified that Rule 0 exit `2` is an input-integrity error rather than an external assessment verdict.

Files changed:

- `docs/implementation_plan_assessment_harness_poc_v1.md`
- `README.md`
- `HANDOFF.md`
- `CHANGELOG.md`
- `docs/daily_logs/2026-05-25/work_log.md`

Effect:

- The plan now prevents unreviewed probabilistic output from being presented as a final failure, grounds extracted evidence in immutable input documents, and preserves ID lineage for future version-aware operation.

### Semantic verifier-agent adoption and plan v1.7

- Received owner confirmation to adopt the semantic verifier-agent recommendation because retained source/data artifacts permit later inspection while keeping people at the final review boundary.
- Updated `docs/implementation_plan_assessment_harness_poc_v1.md` to v1.7:
  - Made a separate read-only semantic verifier-agent stage mandatory for `ai_judgement` links.
  - Required multiple verifier runs and separate persisted `semantic_verifications.yaml` output rather than rewriting compacted trace links.
  - Expanded semantic proposal states with `agent_rejected` and `agent_uncertain`.
  - Finalized the PoC flow as `extract -> compact -> verify -> check -> report -> review -> gate`.
  - Added verifier module/schema/test and Phase 2/3 completion criteria.
  - Updated the deterministic invariant to require identical compacted and semantic verification artifacts as inputs to identical findings.
  - Corrected state-layer and completion wording so semantic verification is an explicit, non-blocking input before final review.
- Updated `README.md`, `HANDOFF.md`, and `CHANGELOG.md` to mark semantic verification as adopted rather than open.

Effect:

- Candidate generation, semantic checking, and human verdict now have explicit ownership and storage boundaries while preserving the multi-run strategy throughout the agent-driven part of the PoC.

### Initial GitHub publication over SSH

- Verified that the completed documentation set was already committed locally as `4c91613` (`first commit`) on `main`.
- Changed `origin` from HTTPS to `git@github.com:entangelk/assessment_poc.git`.
- Published `main` to GitHub over SSH and configured it to track `origin/main`.

Effect:

- The repository is now accessible through its SSH-backed GitHub remote, and subsequent pushes can use the configured upstream branch.

## Issues Found

### No declared canonical specification

- Problem: Three ideation versions exist, but no precedence rule marks one as the implementation source of truth.
- Cause: The documents show evolution, not a version-selection decision.
- Resolution: Flagged `v2.1` as the apparent latest candidate only; canonical selection remains a user decision.
- Outcome: Implementation should wait for an explicit canonical-document decision or a consolidated spec.

### Trace presence is weaker than trace validity

- Problem: The proposed deterministic rule can detect an empty `trace_to`, but a superficial or incorrect link can still pass while hiding an evaluation criterion.
- Cause: Trace semantic validity is a human-review concern, while the document sometimes speaks as if CI structurally ensures fairness.
- Resolution: Store rationale/evidence on consolidated trace links, use Rule 0 for reference integrity only, and reserve semantic adequacy for final human review.
- Outcome: The Phase 0 claim remains viable if narrowed to integrity and consistency checks on consolidated mappings.

### Data model does not support all proposed rules

- Problem: Bonus/qualitative items, round locking/audit state, and expected full-score effort are referenced by rules but are not represented sufficiently in the shown schema or CLI contract.
- Cause: The MVP and later PoC section were written at different levels of detail.
- Resolution: Recommend reducing Phase 0 rules or adding explicit fields and inputs before implementation.
- Outcome: Reference integrity, orphan, required coverage, and basic optionality checks are feasible first; version lock and calibrated time-budget checks need additional design.

### Success criterion does not validate product value

- Problem: Detecting a finding in a designed fixture proves rule behavior, not that the product catches real assessment defects or is useful to assessment owners.
- Cause: Technical regression criteria and product validation criteria are mixed.
- Resolution: Recommend separating fixture-based correctness from an anonymized real-case review with a human assessment owner.
- Outcome: A PoC can be technically successful without yet validating demand or fairness impact.

### Independent review overstates two design gaps

- Problem: The supplied cross-review characterized N:M trace representation as unsupported and suggested Rule 5 as ready for deterministic PoC validation.
- Cause: It did not distinguish link cardinality from link metadata, and it assumed missing version/round inputs.
- Resolution: Treated `rubric.trace_to: [spec_id, ...]` as enough for N:M cardinality in v0; retained trace rationale as optional future metadata. Deferred Rule 5 until baseline and current-round change state are modeled.
- Outcome: The PoC can stay smaller without losing its first validation objective.

## Decisions

- Treated `v2.1` as the latest review target for analysis only, because it extends `v2` with implementation guidance; did not declare it canonical.
- Accepted that modular technical feasibility can be tested before business/market demand validation.
- Superseded the earlier Rule 1-3 recommendation by adding Rule 0 as a dual-surface integrity diagnostic/input-error check; Rule 5 still requires a version-lock contract.
- Superseded the earlier single-run LLM completion definition: final PoC now requires agent multi-run compacting and `extract -> compact -> check -> report -> review` on a real assignment.
- Accepted the revised goal of an agent-level harness rather than a one-shot LLM call; human involvement is a final review gate rather than intermediate candidate approval.
- Defined Rule 0 reference-integrity failures as both preserved diagnostics and invalid-run/input failures.
- Did not edit the ideation proposal during review, because the requested task was evaluation and the unresolved items require owner decisions.
- Updated `CHANGELOG.md` once the plan changed materially to a multi-run agent harness with final human review.
- (v1.4) Replaced "aggregation as classification" with "compacting as auditable union": every valid candidate is preserved as a reviewable entry; only duplicates collapse with `support`/`identity_basis`/`variants` provenance. No quorum, no automatic acceptance.
- (v1.5) Adopted the implementation plan + `v2.1` as the canonical specification pair (§1 precedence).
- (v1.5) Split Rule 0 evidence verification per entry: `token_sequence` is opt-in for pre-inserted quantitative markers; `ai_judgement` is the PoC default and forwards semantic checks to `review_queue` instead of failing Rule 0.
- (v1.5) Treated CLI output stability as a layered, incrementally established contract: only four stable-core fields are frozen, with a `schema` self-discovery command so caller agents can avoid documentation drift.
- (v1.5) Unified all policy files into `config/policy.yaml` with `rules`/`compacting`/`runs`/`verification` sections; removed the separate `--identity-basis-config` flag.
- (v1.5) Distinguished `manual.py` (Phase 0/1 human-authored input) from `mock.py` (Phase 2 protocol contract test fake) as separate runner roles, not a single fallback runner.
- (v1.6) Moved external pass/fail responsibility to a post-review `gate` command; pre-review findings are provisional.
- (v1.6) Adopted immutable snapshot/hash/span source grounding and canonical ID remapping with `id_map` provenance.
- (v1.6) Recommended, pending owner confirmation, a semantic verifier-agent stage before final human review for `ai_judgement` links.
- (v1.7) Adopted the read-only semantic verifier-agent as a required multi-run phase; its proposals are persisted separately and never become final coverage before human review.

## Next Steps

- Implement Phase 0 schemas, Rule 0-3, fixtures, and report flow against manual compacted inputs.
- Include source manifest/source-ref validation, canonical ID-map fixtures, provisional finding lifecycle, and the `gate` boundary in Phase 0 contracts.
- Select the first real assignment input and its permitted storage/anonymization scope before Phase 1.
- Before Phase 2: confirm Claude Agent SDK credential delivery, identity_basis algorithm choice from `config/policy.yaml`, `min_valid_runs`/`default_runs`/`max_runs` values, tool side-effect policy (read-only vs write-on-call), and raw trace retention/redaction policy.
- Demonstrate `override` action at least once during Phase 3 final review on a real assignment.
- Continue through the multi-run agent-assisted final workflow; do not treat manual validation completion as final PoC completion.

---

## Phase 0 Implementation - Iteration 1 (scaffold + Rule 0)

### Goals

- Stand up the deterministic validation core as a runnable, testable package.
- Ship Rule 0 (Reference Integrity Diagnostic) end-to-end: schema, loader, rule engine, CLI, fixtures, and regression tests.
- Confirm the Docker-first development workflow chosen by the owner.

### Completed Work

#### Packaging and dev-environment scaffold

- Created `pyproject.toml` (setuptools, src layout), `Dockerfile` (python:3.11-slim), `docker-compose.yml` (`harness`/`test` services), `.dockerignore`, `.gitignore`.
- `assessment-harness` script entry point wired to `assessment_harness.cli:main`.
- Docker image installs the package editable and runs pytest from `/app`. Source/schema/fixture/test trees are bind-mounted in compose so iterations do not require a rebuild.

Effect: a single `docker compose run --rm test` runs the full regression in a clean environment; `docker compose run --rm harness ...` invokes the CLI.

#### JSON Schema set for Rule 0 surface

- Added eight schemas under `schemas/`: `source_manifest`, `spec_items`, `rubric_items`, `trace_links`, `policy`, `findings`, `integrity_diagnostics`, `cli_output`.
- `cli_output.schema.json` enforces the stable core (`status`, `exit_code`, `command`, `next_actions`) and leaves the rest informational, matching plan §8.1.1.
- `integrity_diagnostics.schema.json` enumerates fourteen Rule 0 diagnostic codes so future codes are an explicit schema change rather than a string typo.

Effect: schemas are the data contract for Phase 0; later phases extend rather than redefine them.

#### Package modules

- `src/assessment_harness/schemas.py` - schema loader with `ASSESSMENT_HARNESS_SCHEMA_DIR` env override (Docker `/app/schemas`).
- `src/assessment_harness/models.py` - YAML loader with schema validation, `SourceSnapshot`/`Document` with sha256 and line/span access, `HarnessInputError` for structured input failures.
- `src/assessment_harness/rules.py` - `run_rule_zero` covering: duplicate ids, dangling rubric/spec refs, evidence-quote spec_id mismatch, empty quote, source_ref hash/document/span integrity, evidence-source_ref containment within spec span, and `token_sequence` whitespace-normalized substring check. All diagnostics are emitted at `high` severity per spec §6.
- `src/assessment_harness/report.py` - markdown renderer for findings + diagnostics.
- `src/assessment_harness/cli.py` - `check`, `schema`, `report` subcommands. Exit codes follow plan §8.1: `0` clean / `2` invalid input or Rule 0 high diagnostic / `3` internal. JSON envelope is schema-validated before emission.

Key behaviours:

- `verification_mode = ai_judgement` deliberately skips the substring check (PoC default), routing semantic adequacy to the verifier-agent stage.
- `verification_mode = token_sequence` enforces whitespace-normalized substring containment against `spec_item.text`.
- On Rule 0 failure, `findings.json` is always written with `{"status": "invalid_input", "findings": []}` so caller agents can rely on the file existing.

#### Fixtures

- `fixtures/clean_assignment/`: spec.md + rubric.md with computed sha256 in `source_manifest.yaml`, four spec items (must/optional/informational), four rubric items including bonus and qualitative, three trace links (one `token_sequence`, one `ai_judgement`).
- `fixtures/reference_integrity/`: deliberately violates duplicate_spec_id, dangling_rubric_reference, dangling_spec_reference, evidence_quote_spec_id_mismatch, evidence_quote_empty, and evidence_quote_token_sequence_mismatch in a single fixture.

#### Tests (31 passing)

- `tests/test_rules.py`: per-diagnostic under-strict (caught) and over-strict (not falsely flagged) guards for each Rule 0 code, plus `ai_judgement` skip-substring guard and whitespace-normalization guard.
- `tests/test_cli_output_contract.py`: every command's stdout JSON validates against `cli_output.schema.json`; exit codes match the documented contract; stderr is separated from stdout JSON.
- `tests/test_fixtures.py`: clean fixture passes with and without `--source-manifest`; reference_integrity fixture produces all expected diagnostic codes with exit 2.
- `tests/conftest.py`: forces `ASSESSMENT_HARNESS_SCHEMA_DIR` to the repo schemas/ directory and clears the schema-loader cache between tests.

#### CLI smoke checks

- `docker compose run --rm harness --output json schema --command check` - returns the contract.
- `docker compose run --rm harness --output json check ... clean_assignment ...` - exit 0, `status: success`, empty findings.
- `docker compose run --rm harness --output json check ... reference_integrity ...` - exit 2, six high diagnostics, `next_actions: [{type: fix_reference_integrity, high_count: 6}]`.
- `docker compose run --rm harness --output json report ...` - renders Markdown.

### Issues Found

- None. The first build and full test run passed without rework.

### Decisions

- Adopted src/ layout (`src/assessment_harness/...`) instead of the top-level path shown in plan §7. Reason: cleaner test/import boundary with editable installs; the package import name is unchanged so plan references remain accurate.
- Held `agent_runners/` and `tools/` out of this iteration because both are explicitly Phase 2 per plan §3.3 and §7. Adding empty placeholders would be dead code under CLAUDE.md §2 (Simplicity First).
- Chose span containment (document_id equal, evidence span contained in spec span) for evidence_source_ref vs spec source_ref check, rather than strict equality. Reason: evidence quotes are commonly a sub-span of a multi-line spec item; strict equality would force every evidence quote to mirror the whole spec span.
- Schemas allow `additionalProperties: true` at top-level entity objects so candidate-stage informational fields (e.g., `confidence`, `agent_run_id`) can be carried through Phase 2 without a schema break.
- Did not implement `gate` in this iteration. Reason: `gate` consumes a final-review record (plan §5.6) that is itself out of Phase 0 scope; stubbing it without final-review schema risks freezing a wrong contract.
- Included `report` in this iteration. Reason: it has no dependency beyond findings + diagnostics and reading the rendered markdown is the fastest manual sanity check.

### Next Steps

- Add Rule 1 (Scored Rubric Coverage), Rule 2 (Required Spec Coverage), Rule 3 (Optionality Consistency), each with the under-strict / over-strict guards described in plan §10.1.
- Add `orphan_scored_rubric`, `required_spec_unscored`, `optionality_mismatch` fixtures.
- Add `gate` once the `final_review` schema is committed (plan §5.6), wiring exit code `1` exclusively to `gate`-confirmed blocking findings.
- Extend `schema --command` to cover `gate` once shipped.
