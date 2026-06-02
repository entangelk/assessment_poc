# Verification — Codex Check of `verify` CLI Feedback

## Subject metadata

- **Date**: 2026-06-02
- **Requester**: Owner
- **Verifier**: Codex
- **Target slice/artifact**: External AI verification feedback for the initial `verify` CLI orchestration (`mock_fixture`).
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.30 — §5.3.1 semantic verification states/flow, §5.7 review queue entries, and existing schemas `semantic_verifications.schema.json`, `review_queue.schema.json`, `trace_links.schema.json`.
- **Source of work being verified**: working tree, uncommitted.

## Scope

- Check whether the external AI findings F1/F2/F3 are factually grounded in the current implementation.
- Reconcile those findings with the canonical spec and current tests.
- Identify what requires Owner confirmation before implementation proceeds.

## Methodology

- Read the scoped plan clauses for semantic verification output and review queue entries:
  - `docs/implementation_plan_assessment_harness_poc_v1.md:344`
  - `docs/implementation_plan_assessment_harness_poc_v1.md:346`
  - `docs/implementation_plan_assessment_harness_poc_v1.md:360`
  - `docs/implementation_plan_assessment_harness_poc_v1.md:597`
  - `docs/implementation_plan_assessment_harness_poc_v1.md:603`
- Read the implemented `verify` path:
  - `src/assessment_harness/cli.py:941`
  - `src/assessment_harness/cli.py:947`
  - `src/assessment_harness/cli.py:957`
  - `src/assessment_harness/cli.py:1018`
  - `src/assessment_harness/cli.py:1021`
  - `src/assessment_harness/cli.py:1026`
  - `src/assessment_harness/cli.py:1050`
  - `src/assessment_harness/cli.py:1066`
  - `src/assessment_harness/cli.py:1073`
  - `src/assessment_harness/cli.py:1092`
- Read compacting trace-link canonical ID materialization:
  - `src/assessment_harness/compacting.py:189`
  - `src/assessment_harness/compacting.py:252`
  - `src/assessment_harness/compacting.py:269`
- Read the current verify tests:
  - `tests/test_cli_output_contract.py:1856`
  - `tests/test_cli_output_contract.py:1918`
  - `tests/test_cli_output_contract.py:1926`
  - `tests/test_cli_output_contract.py:1936`

## Findings

### F1 — Confirmed

The finding is valid. `verify` loads `spec_items.yaml`, `rubric_items.yaml`, and `trace_links.yaml`, but does not load `id_map.yaml` (`src/assessment_harness/cli.py:944-949`). It emits `trace_link_id` via `_trace_link_id`, which falls back to `T{trace_index}` when the trace link has no explicit `id` (`src/assessment_harness/cli.py:1092-1096`).

Compacting assigns trace-link canonical IDs as `T{len(groups)+1}` (`src/assessment_harness/compacting.py:189`), but materialized trace link items do not receive that ID field; trace-link materialization adds support, identity basis, variants, sources, and review metadata only (`src/assessment_harness/compacting.py:252-272`). The current test asserts `T2` after a real compact-to-verify handoff (`tests/test_cli_output_contract.py:1856-1918`), but it does not cross-check that `T2` came from `id_map.yaml`.

Verdict for F1: **real medium risk**. The current behavior is correct only while compacted trace-link order and id_map trace-link canonical order remain coupled. Because `trace_link_id` is the downstream join key for semantic verification, this should be locked before the slice is treated as fully closed.

### F2 — Confirmed

The finding is valid. `evidence_quote.source_ref` is optional in the trace-link schema, while `_ai_judgement_source_refs` only returns refs when `source_ref` is a mapping (`src/assessment_harness/cli.py:1043-1056`). `_mock_semantic_verifications` skips a trace link entirely when `source_refs` is empty (`src/assessment_harness/cli.py:1021-1023`). The queue path does not require `source_ref`; it only checks `verification_mode == "ai_judgement"` and then appends `ai_judgement_pending` (`src/assessment_harness/cli.py:1066-1088`).

Verdict for F2: **real low-risk contract gap**. It is not necessarily a bug, but the behavior is currently undocumented and untested: semantic proposals and review queue entries can diverge.

### F3 — Confirmed As Clarity Issue

The finding is accurate. `verify --runner mock_fixture` does not replay a fixture directory. It synthesizes proposals from compacted trace links (`src/assessment_harness/cli.py:1012-1040`). `--source-manifest` and `--policy` are loaded/validated (`src/assessment_harness/cli.py:948-949`) but not otherwise used by the mock proposal synthesis. `--runs` controls generated verifier run IDs and support counts (`src/assessment_harness/cli.py:943`, `src/assessment_harness/cli.py:1016`, `src/assessment_harness/cli.py:1033-1036`).

Verdict for F3: **real low-risk naming/documentation issue**. It is acceptable for a mock slice if documented; the risk is caller expectation, not current output correctness.

## Issues / Risks

- **Blocking before closing this slice**: F1 needs either a code/test lock against `id_map.yaml` or an explicit Owner decision accepting order-coupled `T{index}` as canonical for the initial mock slice.
- **Non-blocking but should be decided**: F2 needs a contract choice for `ai_judgement` evidence without `source_ref`.
- **Non-blocking documentation cleanup**: F3 can be handled by wording if the Owner accepts the synthetic mock verifier behavior.

## Verdict

**Conditional pass.** I agree with the external AI's verdict. The happy path and public-surface tests are real, but F1 is a load-bearing identity gap. F2 and F3 are lower-risk clarity/contract issues.

## Outstanding Items

Owner should decide:

1. For F1, should I implement `verify` so it loads `id_map.yaml` and derives `trace_link_id` from canonical trace-link lineage, with a regression that fails if order and id_map diverge?
2. For F2, should missing `source_ref` on `ai_judgement` evidence emit an `agent_uncertain` proposal with empty `source_refs`, or should it intentionally emit only a review queue entry?
3. For F3, is the name `mock_fixture` acceptable for this synthetic verifier path if README/HANDOFF clarify that verify does not replay fixture files?

## Reproduction

No new full-suite run was needed for this feedback check. The verification was by scoped source/spec/test inspection, using:

```bash
sed -n '930,1128p' src/assessment_harness/cli.py
sed -n '180,275p' src/assessment_harness/compacting.py
sed -n '1850,2005p' tests/test_cli_output_contract.py
sed -n '330,365p' docs/implementation_plan_assessment_harness_poc_v1.md
sed -n '586,642p' docs/implementation_plan_assessment_harness_poc_v1.md
```

## Follow-up Status

After this feedback check, the Owner selected F2 option A and authorized the F1/F2 follow-up implementation. The follow-up changed `verify` so official compact output resolves `trace_link_id` through `id_map.yaml` lineage when present, while manual/no-id-map inputs retain the existing fallback. It also changed missing quote-level `source_ref` on `ai_judgement` evidence to emit an explicit `agent_uncertain` proposal with `source_refs: []`.

Follow-up regression coverage:

- `test_verify_uses_id_map_trace_link_canonical_id_when_trace_order_changes`
- `test_verify_ai_judgement_without_source_ref_still_records_uncertain_proposal`
- `test_verify_token_sequence_only_links_do_not_create_semantic_proposals`

Follow-up verification:

```bash
python3 -m pytest tests/test_cli_output_contract.py::test_verify_mock_fixture_writes_semantic_verifications_and_queue tests/test_cli_output_contract.py::test_verify_uses_id_map_trace_link_canonical_id_when_trace_order_changes tests/test_cli_output_contract.py::test_verify_ai_judgement_without_source_ref_still_records_uncertain_proposal tests/test_cli_output_contract.py::test_verify_token_sequence_only_links_do_not_create_semantic_proposals tests/test_cli_output_contract.py::test_verify_preserves_existing_queue_and_does_not_duplicate_pending_entry -q
python3 -m py_compile src/assessment_harness/cli.py
python3 -m pytest tests/test_cli_output_contract.py tests/test_compacting.py tests/test_models.py -q
python3 -m pytest -q
python3 -m pytest --collect-only -q
```

Follow-up result: full suite passed; 228 tests collected (agent-runner 27, CLI 69, compacting 7, fixtures 8, models 22, rules 95).
