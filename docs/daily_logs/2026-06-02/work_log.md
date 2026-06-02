# Work Log - 2026-06-02

## Phase 2 Initial `verify` CLI Orchestration (`mock_fixture`)

### Goals

- Continue Phase 2 from the existing `extract -> compact` foundation with the smallest slice that does not require external SDK credentials.
- Add a deterministic `verify` CLI surface that writes semantic-verification artifacts and composes review queue entries without claiming final semantic acceptance.

### Completed work

- Added `verify` to `src/assessment_harness/cli.py`.
  - Inputs: `--compacted-dir`, `--source-manifest`, `--runner`, `--runs`, `--policy`, `--out-dir`, optional `--review-queue-in`, optional `--review-queue-out`.
  - Current runner: `mock_fixture` only. Real SDK verifier runners are rejected with structured `invalid_input`.
  - Outputs: `semantic_verifications.yaml` and `review_queue.json`.
  - Behavior: reads compacted artifacts, validates source manifest and policy, emits conservative `agent_uncertain` proposals for compacted trace links containing `verification_mode: ai_judgement`, and does not rewrite compacted trace links.
- Added schema self-discovery for `schema --command verify`.
  - Public informational fields now include `semantic_verifications_path`, `semantic_verification_count`, queue path/count, runner, run count, compacted dir, source manifest path, and input errors.
- Added CLI regressions in `tests/test_cli_output_contract.py`.
  - Locks `verify` schema self-discovery.
  - Locks mock semantic-verification output and schema validity.
  - Locks `ai_judgement_pending` review_queue entry generation.
  - Locks preservation of incoming queue metadata/entries and duplicate pending-entry suppression.
  - Locks unsupported SDK verifier rejection.
- Updated `README.md`, `docs/case_study.md`, `HANDOFF.md`, `CHANGELOG.md`, and package docstring so publication-facing status no longer says `verify` is fully unimplemented.

### Issues found

- Problem: compacted `trace_links.yaml` currently does not carry an explicit trace-link `id`, while `semantic_verifications.schema.json` requires `trace_link_id`.
  Cause: trace link canonical identity is represented in compacting/id_map lineage, but the trace link item itself has no required `id` field.
  Resolution: initial `verify` derives `T{index}` from compacted trace-link order, matching the current compacting helper's canonical trace ID assignment. It also uses a trace-link `id` if one is present later.
  Outcome: semantic-verification artifacts can be produced now without changing existing trace-link schemas; a future slice can make `id_map.yaml` an explicit `verify` input if needed.
- Problem: a mock verifier could accidentally sound like a real semantic judgment.
  Cause: `verify` is the semantic-verifier stage name, but this slice deliberately avoids SDK/model execution.
  Resolution: mock proposals use `status_proposal: agent_uncertain` and a rationale that says the compacted link is queued for human review without rewriting it.
  Outcome: the pipeline contract is exercised without overclaiming semantic support.

### Decisions

- **Implementation slice boundary:** initial `verify` is mock-only CLI orchestration. It writes proposal and review queue artifacts, but does not apply semantic proposals to `check`, rewrite trace links, or run a real SDK verifier.
- **Queue composition:** `verify` mirrors the `compact` queue discipline: preserve incoming top-level metadata and entries, append deterministic entries, and skip entries whose `entry_id` already exists.
- **Trace-link ID derivation:** until trace links carry explicit IDs or `verify` consumes `id_map.yaml`, use `T{index}` from compacted trace-link order with an override if a trace link already has `id`.

### Next steps

1. Teach `check` / `report` / `review` how to consume `semantic_verifications.yaml` and the unified review queue without rewriting compacted links.
2. Add real SDK verifier runner support when a runnable sample assignment and credential path are ready.
3. Recompute publication-facing evaluation tables after the semantic-verification consumption path stabilizes.

### Verification

- `python3 -m py_compile src/assessment_harness/cli.py`
- `python3 -m pytest tests/test_cli_output_contract.py::test_schema_command_returns_verify_contract tests/test_cli_output_contract.py::test_verify_mock_fixture_writes_semantic_verifications_and_queue tests/test_cli_output_contract.py::test_verify_preserves_existing_queue_and_does_not_duplicate_pending_entry tests/test_cli_output_contract.py::test_verify_rejects_unknown_runner -q` → 4 passed.
- `python3 -m pytest tests/test_cli_output_contract.py tests/test_compacting.py tests/test_models.py -q` → 95 passed.
- `python3 -m pytest -q` → full suite passed.
- `python3 -m pytest --collect-only -q` → 225 tests collected: agent-runner 27, CLI 66, compacting 7, fixtures 8, models 22, rules 95.
- `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command verify` → `status=success`, contract exposes `verify`.

## External Verification Feedback Check

### Goals

- Check the Owner-provided external AI verification findings for the initial `verify` CLI slice.
- Identify which items require Owner confirmation before follow-up implementation.

### Completed work

- Added an independent verification note at `docs/verifications/2026-06-02/verify_cli_feedback_codex_check.md`.
  - Key result: agreed with the external conditional-pass verdict.
  - Effect: F1 is confirmed as the blocking follow-up before closing the slice; F2/F3 are confirmed as lower-risk contract/documentation decisions.

### Issues found

- Detailed findings are kept in the verification record rather than duplicated here.

### Decisions

- No new Owner decision yet. The next implementation step depends on the Owner choosing how to handle F1 and F2.

### Next steps

1. Owner decision: lock `verify` trace-link IDs through `id_map.yaml`, or explicitly accept current order-coupled `T{index}` for the initial mock slice.
2. Owner decision: decide whether `ai_judgement` evidence without `source_ref` should still emit an `agent_uncertain` proposal or only queue review.
3. If accepted, implement the chosen F1/F2 follow-up and update the existing tests/docs.

### Verification

- Source/spec/test inspection only; no code behavior changed in this check.

## External Verification Follow-up: F1/F2 Closure

### Goals

- Close the conditional-pass F1 trace-link identity gap.
- Apply the Owner decision for F2: keep uncertainty visible by emitting a semantic proposal even when `ai_judgement` evidence lacks quote-level `source_ref`.

### Completed work

- Updated `verify` trace-link ID resolution in `src/assessment_harness/cli.py`.
  - Key change: when `compacted-dir/id_map.yaml` exists, `verify` resolves `trace_link_id` by matching trace-link `variants` (`run_id`, `candidate_id`) to `id_map.run_refs`.
  - Effect: `trace_link_id` no longer depends on compacted `trace_links.yaml` file order for official compact output.
- Updated mock semantic proposal generation.
  - Key change: any `ai_judgement` evidence now creates an `agent_uncertain` proposal.
  - Key change: if quote-level `source_ref` is missing, the proposal keeps `source_refs: []` and uses a separate rationale explaining that no quote-level source reference was available.
  - Effect: `semantic_verifications.yaml` and `review_queue.json` stay joinable by `trace_link_id` while preserving uncertainty.
- Added CLI regressions.
  - `test_verify_uses_id_map_trace_link_canonical_id_when_trace_order_changes` locks F1 by deliberately reordering `trace_links.yaml` after compacting and asserting `T2` still comes from id_map lineage.
  - `test_verify_ai_judgement_without_source_ref_still_records_uncertain_proposal` locks F2 A.
  - `test_verify_token_sequence_only_links_do_not_create_semantic_proposals` adds the over-strict guard that `token_sequence` links do not receive semantic proposals.
- Updated `README.md`, `HANDOFF.md`, and `CHANGELOG.md` for the resolved behavior.

### Issues found

- Problem: `verify` previously used `T{index}` as the only fallback for compacted trace links that lacked an explicit `id`.
  Cause: `trace_links.yaml` does not carry trace-link IDs, while `id_map.yaml` carries trace-link canonical lineage.
  Resolution: load optional `id_map.yaml` from `--compacted-dir` and resolve trace-link IDs by variant/run-ref lineage when present.
  Outcome: official compact output is no longer order-coupled for semantic proposal and queue IDs.
- Problem: `ai_judgement` evidence without `source_ref` previously created a queue entry but no semantic proposal.
  Cause: proposal generation required non-empty `source_refs`, while queue generation only required `verification_mode: ai_judgement`.
  Resolution: proposal generation now keys on `ai_judgement` evidence presence, not source-ref presence.
  Outcome: missing `source_ref` is represented as `agent_uncertain` with `source_refs: []`, matching the Owner's uncertainty-visible direction.

### Decisions

- **Owner decision (2026-06-02): F2 uses option A.** `ai_judgement` evidence without quote-level `source_ref` should still emit an `agent_uncertain` proposal with `source_refs: []`. Rationale: keeping an explicit uncertain proposal preserves the clue for downstream interpretation and keeps queue/proposal joins complete.
- **F1 implementation direction:** use `id_map.yaml` lineage when available rather than accepting order-coupled `T{index}` for official compact output.

### Next steps

1. Teach `check` / `report` / `review` how to consume `semantic_verifications.yaml` and the unified review queue without rewriting compacted links.
2. Add real SDK verifier runner support when a runnable sample assignment and credential path are ready.

### Verification

- `python3 -m pytest tests/test_cli_output_contract.py::test_verify_mock_fixture_writes_semantic_verifications_and_queue tests/test_cli_output_contract.py::test_verify_uses_id_map_trace_link_canonical_id_when_trace_order_changes tests/test_cli_output_contract.py::test_verify_ai_judgement_without_source_ref_still_records_uncertain_proposal tests/test_cli_output_contract.py::test_verify_token_sequence_only_links_do_not_create_semantic_proposals tests/test_cli_output_contract.py::test_verify_preserves_existing_queue_and_does_not_duplicate_pending_entry -q` → 5 passed.
- `python3 -m py_compile src/assessment_harness/cli.py`
- `python3 -m pytest tests/test_cli_output_contract.py tests/test_compacting.py tests/test_models.py -q` → 98 passed.
- `python3 -m pytest -q` → full suite passed.
- `python3 -m pytest --collect-only -q` → 228 tests collected: agent-runner 27, CLI 69, compacting 7, fixtures 8, models 22, rules 95.

## Phase 2 Initial Semantic-Verification Consumption

### Goals

- Wire the new `semantic_verifications.yaml` artifact into downstream commands without rewriting compacted trace links.
- Keep final authority with human review/gate: verifier proposals may affect provisional Rule 1 evidence, but do not create final coverage.

### Completed work

- Added `check --semantic-verifications`.
  - Key change: valid semantic verification proposals are applied to an in-memory copy of `trace_links` as effective `semantic_status` for Rule 1 evidence only.
  - Effect: `findings.json` can show `agent_supported` / `agent_uncertain` in Rule 1 evidence while the input `trace_links.yaml` remains unchanged.
- Added optional semantic/review queue consumption to `report`.
  - Key change: `report --semantic-verifications ... --review-queue ...` schema-validates those artifacts and renders separate "Semantic Verifications" / "Review Queue" sections.
  - Effect: human-facing reports can include verifier proposals and queued review work in the same document.
- Strengthened `review` optional input handling.
  - Key change: `review --semantic-verifications ... --review-queue ...` now validates those artifacts before writing `review.yaml`.
  - Effect: final-review drafts cannot silently record malformed semantic/review queue inputs.
- Updated CLI schema self-discovery for `check`, `report`, and `review`.
- Added CLI regressions covering semantic proposal application, unrelated proposal suppression, report rendering/invalid input, and review validation/path recording.

### Issues found

- Problem: `check` previously accepted no `--semantic-verifications` argument even though the plan flow already included it.
  Cause: the mock `verify` producer landed first; downstream consumption had remained pending.
  Resolution: added the argument and in-memory effective status application.
  Outcome: the plan-canonical `verify -> check` path is now connected at the artifact level.
- Problem: `report` and `review` could not validate or render/record semantic verification and unified queue artifacts.
  Cause: earlier implementations were Phase 0 finding/diagnostic only, while optional arguments existed only on `review` as path metadata.
  Resolution: added schema validation and report rendering for those optional artifacts.
  Outcome: downstream commands fail loud on malformed semantic/review queue inputs.

### Decisions

- **No trace rewrite:** semantic proposals are applied only to an in-memory copy for Rule 1 evidence. The compacted trace link remains unchanged, preserving the plan's "proposal, not rewrite" boundary.
- **Rule scope:** Rule 2, Rule 3, and lint family remain structural and continue to use the original trace document rather than effective semantic status.

### Next steps

1. Implement final-review handling for review_queue entries beyond finding-level hold drafts.
2. Add real SDK verifier runner support when a runnable sample assignment and credential path are ready.
3. Recompute publication-facing evaluation tables after the semantic-consumption path is stable.

### Verification

- `python3 -m pytest tests/test_cli_output_contract.py::test_check_applies_semantic_verification_proposals_without_rewriting_trace_links tests/test_cli_output_contract.py::test_check_token_sequence_links_not_changed_by_unrelated_semantic_verification tests/test_cli_output_contract.py::test_report_command_includes_semantic_verifications_and_review_queue tests/test_cli_output_contract.py::test_report_command_rejects_invalid_semantic_verifications tests/test_cli_output_contract.py::test_review_command_validates_and_records_semantic_review_inputs tests/test_cli_output_contract.py::test_review_command_rejects_invalid_review_queue_input tests/test_cli_output_contract.py::test_schema_command_returns_check_contract tests/test_cli_output_contract.py::test_schema_command_returns_report_contract tests/test_cli_output_contract.py::test_schema_command_returns_review_contract -q` → 9 passed.
- `python3 -m py_compile src/assessment_harness/cli.py src/assessment_harness/report.py`
- `python3 -m pytest tests/test_cli_output_contract.py tests/test_models.py -q` → 98 passed.
- `python3 -m pytest -q` → full suite passed.
- `python3 -m pytest --collect-only -q` → 235 tests collected: agent-runner 27, CLI 76, compacting 7, fixtures 8, models 22, rules 95.

## External Verification Follow-up: Semantic Consumption F1'/F2' Closure

### Goals

- Close the check-side trace-link identity asymmetry found after the initial semantic-consumption slice.
- Guard the boundary that agent proposals must not downgrade human-finalized semantic statuses.

### Completed work

- Added `check --id-map`.
  - Key change: when `id_map.yaml` is provided, `check` resolves trace-link IDs with the same variant/run-ref lineage resolver used by `verify`.
  - Effect: semantic proposals remain attached to the canonical trace link even if compacted `trace_links.yaml` order changes.
- Updated semantic proposal application.
  - Key change: agent proposals are skipped for `human_accepted` and `human_overridden` trace links.
  - Effect: post-human-review semantic statuses cannot be downgraded by later or accidentally replayed verifier proposals.
- Added CLI regressions.
  - `test_check_uses_id_map_for_semantic_verification_when_trace_order_changes` locks the lineage join by compacting, reordering trace links, verifying, then checking with `--id-map`.
  - `test_check_semantic_verification_does_not_downgrade_human_final_status` locks the human-finalized status guard.
- Updated `README.md`, `HANDOFF.md`, and `CHANGELOG.md` for the new `--id-map` check input and preserved-human-status behavior.

### Issues found

- Problem: `check` initially applied semantic proposals by explicit trace-link `id` or fallback `T{index}`, while `verify` already used `id_map.yaml` lineage when available.
  Cause: the downstream consumption slice did not expose an id-map input, so it could not reuse the lineage resolver.
  Resolution: add optional `--id-map`, schema-validate it, expose `id_map_path` in the check envelope/schema contract, and resolve effective semantic status with the shared trace-link ID helper.
  Outcome: the F1 identity fix is symmetric across `verify` and `check` when compacted lineage is supplied.
- Problem: agent proposals could overwrite an existing human-finalized semantic status in the in-memory effective trace document.
  Cause: semantic proposal application treated every matched trace link as pre-human-review.
  Resolution: skip proposal application when the current status is `human_accepted` or `human_overridden`.
  Outcome: semantic verifier output remains advisory and cannot demote human final decisions.

### Decisions

- `--id-map` is optional for backward compatibility, but plan-canonical `verify -> check` flows should pass `work/compacted/id_map.yaml` so proposal joins are lineage-based rather than order-based.
- Human-finalized semantic statuses are authoritative over agent proposals in `check` effective-status application.

### Next steps

1. Implement final-review handling for review_queue entries beyond finding-level hold drafts.
2. Add real SDK verifier runner support when a runnable sample assignment and credential path are ready.
3. Recompute publication-facing evaluation tables after the semantic-consumption path is stable.

### Verification

> Superseded by the later "Semantic Consumption Low-Risk Residual Closure" verification below, which broadens the status guard and updates the final suite count to 241.

- `python3 -m pytest tests/test_cli_output_contract.py::test_check_uses_id_map_for_semantic_verification_when_trace_order_changes tests/test_cli_output_contract.py::test_check_semantic_verification_does_not_downgrade_human_final_status tests/test_cli_output_contract.py::test_schema_command_returns_check_contract -q` → 3 passed.
- `python3 -m py_compile src/assessment_harness/cli.py`
- `python3 -m pytest tests/test_cli_output_contract.py tests/test_models.py -q` → related suite passed.
- `python3 -m py_compile src/assessment_harness/cli.py src/assessment_harness/report.py`
- `python3 -m pytest -q` → full suite passed.
- `python3 -m pytest --collect-only -q` → 237 tests collected: agent-runner 27, CLI 78, compacting 7, fixtures 8, models 22, rules 95.
- `PYTHONPATH=src python3 -m assessment_harness.cli schema --command check --output json` → check contract exposes `id_map_path`.

## Semantic Consumption Low-Risk Residual Closure

### Goals

- Remove the remaining silent-misattribution path when semantic proposals are supplied to compacted lineage traces without `--id-map`.
- Clarify and broaden the proposal overwrite guard for post-review semantic statuses.

### Completed work

- Made `check --semantic-verifications` fail loud when trace links contain compacting lineage variants but `--id-map` is omitted.
  - Effect: compacted outputs can no longer silently fall back to order-based `T{index}` proposal joins.
- Broadened the overwrite guard from final-coverage-only statuses to all post-review statuses: `human_accepted`, `human_rejected`, `human_overridden`, and `rerun_requested`.
  - Effect: agent proposals remain pre-review advice and cannot rewrite reviewer outcomes, including non-coverage outcomes.
- Updated plan §8, `README.md`, `HANDOFF.md`, and `CHANGELOG.md` to state that compacted lineage flows pass `--id-map` with `--semantic-verifications`.
- Added regressions for missing `--id-map` on lineage traces and for all four post-review semantic statuses.

### Issues found

- Problem: `--id-map` was optional even for compacted lineage traces, leaving a silent order-based fallback if callers passed reordered trace links.
  Cause: backward-compatible optional input did not distinguish simple non-lineage fixtures from compacted lineage output.
  Resolution: detect trace-link `variants` and require `--id-map` when semantic proposals are supplied.
  Outcome: lineage-bearing compacted traces either join proposals by canonical id_map lineage or fail with `invalid_input`.
- Problem: the previous helper name and behavior protected only final-coverage statuses (`human_accepted`, `human_overridden`).
  Cause: it reused the Rule 1 coverage boundary rather than the broader post-review lifecycle boundary.
  Resolution: rename behavior around post-review status and protect `human_rejected` / `rerun_requested` as well.
  Outcome: no human review outcome is overwritten by an agent proposal in check's effective trace copy.

### Decisions

- Simple non-lineage inputs may still use the explicit trace-link `id` / `T{index}` fallback for compatibility.
- Compacting lineage traces are stricter: `--semantic-verifications` without `--id-map` is invalid input.
- Post-review statuses are authoritative over verifier proposals regardless of whether they contribute Rule 1 coverage.

### Next steps

1. Implement final-review handling for review_queue entries beyond finding-level hold drafts.
2. Add real SDK verifier runner support when a runnable sample assignment and credential path are ready.
3. Recompute publication-facing evaluation tables after the semantic-consumption path is stable.

### Verification

- `python3 -m pytest tests/test_cli_output_contract.py::test_check_uses_id_map_for_semantic_verification_when_trace_order_changes tests/test_cli_output_contract.py::test_check_rejects_semantic_verifications_for_lineage_trace_without_id_map tests/test_cli_output_contract.py::test_check_semantic_verification_does_not_downgrade_post_review_status tests/test_cli_output_contract.py::test_schema_command_returns_check_contract -q` → 7 passed.
- `python3 -m py_compile src/assessment_harness/cli.py`
- `python3 -m pytest tests/test_cli_output_contract.py tests/test_models.py -q` → related suite passed.
- `python3 -m py_compile src/assessment_harness/cli.py src/assessment_harness/report.py`
- `python3 -m pytest -q` → full suite passed.
- `python3 -m pytest --collect-only -q` → 241 tests collected: agent-runner 27, CLI 82, compacting 7, fixtures 8, models 22, rules 95.
- `git diff --check`
- `PYTHONPATH=src python3 -m assessment_harness.cli schema --command check --output json` → check contract still exposes `id_map_path`.
