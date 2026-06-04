# Verification — `materialize-review` slice (plan v1.31 §5.6.1)

## Subject metadata

- **Date**: 2026-06-04
- **Requester**: Owner (kdtyohan@gmail.com) — "작업 AI가 작업한 내용을 검증하고 의심해줘"
- **Verifier**: Claude (independent audit)
- **Target slice**: `materialize-review` contract + CLI implementation
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.31 §5.6.1 (Review Materialization), with cross-references to §5.6 (gate verdict-only), §5.7 (review queue entry), §8 (CLI usage), §9 Phase 3, §12.4 (override scope), §15 v1.31 change log.
- **Source of work**: committed — `667b7d4` (contract) + `97d371c` (CLI). Working tree clean at `97d371c`.

## Scope

1. Contract self-consistency (plan v1.31 §5.6.1 vs the rest of the plan).
2. Spec ↔ implementation literal consistency (`_cmd_materialize_review` and helpers in `src/assessment_harness/cli.py`).
3. Downstream schema validity of the materialized artifacts (`schemas/review_queue.schema.json`, `schemas/trace_links.schema.json`, `schemas/final_review.schema.json`).
4. Regression test coverage vs the contract boundary matrix (`tests/test_cli_output_contract.py`).
5. Schema self-discovery (`schema --command materialize-review`).
6. Independent green-bar + smoke reproduction.

## Methodology

- Read §5.6.1 end-to-end from the v1.31 contract diff (`git show 667b7d4 -- docs/implementation_plan_assessment_harness_poc_v1.md`).
- Read the implementation and reused helpers directly (`cli.py:2204-2515` for `_cmd_materialize_review` and friends; `cli.py:1241-1296` for `_trace_link_id` lineage resolution).
- Grepped the three downstream schemas for every literal the materializer emits.
- Ran the full suite (`PYTHONPATH=src python3 -m pytest`) and the materialize subset (`-k materialize`).
- Ran independent CLI smokes against a hand-built compacted dir for **untested** branches (non-minimal key, spec_item + finding decisions), not just the tested happy paths.

## Findings

### 1. Contract self-consistency — mostly consistent, one internal ambiguity

- §5.6.1 cleanly separates `gate` (verdict-only) from `materialize-review` (artifact writer); §5.6, §8, §9 Phase 3, §11 deliverables, §12.4, and §15 all updated in lockstep. No cross-section literal disagreement on key shape, action mapping, or status mapping.
- **Internal ambiguity (contract gap)**: §5.6.1 says spec_item/rubric_item decisions are "입력 artifact를 그대로 보존하고, **지원하지 않는 materialization으로 판정하지 않는다**", yet the same section *requires* `materialization_summary.json` to carry `unsupported_decision_count`. The contract never defines what that field counts. The implementation counts spec_item/rubric_item decisions as `unsupported_decision_count` (`cli.py:2376`, `cli.py:2497`). That is a defensible reading ("판정" = *fail/verdict*, not *tally*), and behaviorally the command does **not** error on them — but the literal wording and the field name pull in opposite directions. This should be reconciled by the owner (clarify that `unsupported_decision_count` = deferred-scope spec/rubric decisions preserved as-is, OR redefine the field). Surfacing per the contract-ambiguity rule; not silently accepted.

### 2. Spec ↔ implementation — faithful on every checked literal

- Trace-link key is `{trace_link_id}` only; `_trace_link_decision_key_errors` (`cli.py:2225-2235`) rejects missing **and** extra fields, so `{rubric_id, spec_ids}` is refused as non-minimal. Confirmed by smoke (CASE 1 → `invalid_input` / exit 2 / "target_key ... is not minimal").
- `trace_link_id` resolves through `id_map.yaml` `entity_type: trace_link` run_refs via the same `_trace_link_id` lineage resolver that `verify`/`check` use (`cli.py:1241-1280`), not trace-file order. `_trace_links_by_canonical_id` (`cli.py:2237-2253`) raises on two links resolving to one id (the "한 link로 매칭되지 않으면" guard).
- Trace action mapping (`_apply_trace_link_decision`, `cli.py:2274-2308`): `accept → human_accepted`, `override → human_overridden` + shallow top-level merge of `override_payload` + `sources[] {kind: human_override, review_id, reviewer, reviewed_at, note}`, `hold → early return / no change`, `rerun_requested → rerun_requested`. `reviewed_by`/`reviewed_at` set from `review_doc.reviewer`/`reviewed_at` for all non-hold actions. Matches §5.6.1 verbatim.
- Queue action mapping (`_materialized_queue_status`, `cli.py:2310-2315`): `accept`/`override → resolved`, `rerun_requested → rerun_pending`, else (`hold`) → `held`. Entries are never deleted; `review_decision` metadata (`review_id`, `reviewer`, `reviewed_at`, `action`, `note`) is attached. Matches §5.6.1.
- Output/default resolution: `--id-map` defaults to `<compacted-dir>/id_map.yaml` and is only required when trace decisions exist (`cli.py:2381-2389`); `--review-queue` defaults to `inputs.review_queue_path` then `<compacted-dir>/review_queue.json` if it exists (`_load_materialize_review_queue`, `cli.py:2317-2340`). Outputs (spec/rubric/trace YAML, optional queue JSON, summary JSON) and summary keys match the contract.
- **No in-place mutation**: `trace_doc`/`queue_doc` are `copy.deepcopy`-ed before edit; all writes target `out_dir` (`cli.py:2358-2407`). spec/rubric docs pass through untouched. Confirmed by the override test asserting source `trace_links.yaml` text is byte-unchanged.

### 3. Downstream schema validity — passes

Materialized artifacts are written **without** re-validation, so their downstream validity was checked directly:
- `review_queue.schema.json`: `status` enum already includes `held`/`rerun_pending`/`resolved`; entry `additionalProperties: true` admits `review_decision`. ✓
- `trace_links.schema.json`: `semantic_status` enum includes `human_accepted`/`human_overridden`/`rerun_requested`; `sources[].kind` enum includes `human_override`; `reviewed_by`/`reviewed_at` accept string|null; entity `additionalProperties: true` admits override_payload keys. ✓
- `final_review.schema.json`: `target_type` enum includes `trace_link`/`review_queue_entry`/`spec_item`/`rubric_item`/`finding`; `target_key` is a free object; `override_payload` allowed. ✓

### 4. Regression coverage — boundary matrix has empty cells (load-bearing)

Tested (traced to contract): trace accept/override/hold/rerun (`test_materialize_review_trace_status_mapping`, `..._applies_trace_override_and_queue_status`, `..._hold_preserves_trace_link`); queue accept/override/hold/rerun (`..._queue_status_mapping` + combined test); trace non-mutation; missing id_map (`..._rejects_trace_decision_without_id_map`); unknown trace_link_id (`..._rejects_unknown_trace_link_id`); schema self-discovery (`test_schema_command_returns_materialize_review_contract`). 10 tests, all green.

**Untested contract branches (no regression pins them):**

| # | Contract branch (§5.6.1) | Code site | Verified by me how |
|---|---|---|---|
| A | non-minimal / `{rubric_id, spec_ids}` key → `invalid_input` (explicit bullet) | `cli.py:2225-2235`, `2390-2396` | smoke CASE 1 → exit 2 ✓ |
| B | `trace_link_id` resolving to **multiple** links → `invalid_input` ("한 link로 매칭되지 않으면"; worker's own next-step "ambiguous id_map joins") | `cli.py:2244-2249` | code read only |
| C | duplicate trace decisions for one id | `cli.py:2398-2402` | code read only |
| D | queue decision matching no entry | `cli.py:2459-2463` | code read only |
| E | duplicate queue decision | `cli.py:2453-2458` | code read only |
| F | queue decision with no resolvable queue input → `invalid_input` | `cli.py:2333-2337` | code read only |
| G | spec_item/rubric_item decision preserved + **not failed** (explicit carve-out) | `cli.py:2376`, `2497` | smoke CASE 2 → success, unsupported=1, spec text preserved ✓ |
| H | finding decision ignored (no artifact, not counted) (explicit clause) | filtered out at `cli.py:2362-2376` | smoke CASE 2 → not counted ✓ |

A, G, H are spelled out verbatim in §5.6.1; B is named in the worker's own work-log "Next steps #2". Each is currently correct in code (I confirmed A, G, H by smoke; B–F by reading the guard), but none is locked by a regression — a refactor could silently drop any of them with the green bar intact. Per the project's verification doctrine ("an untraced branch is a blocking finding regardless of the green bar"), these are the load-bearing reason the verdict is conditional, not a clean pass.

### 5. Schema self-discovery — present and correct

`schema --command materialize-review` returns the documented informational set (`reviewed_dir`, `trace_links_path`, `review_queue_path`, `materialization_summary_path`, the three decision counts, `input_error`) and `next_actions_types: [fix_input]`; pinned by `test_schema_command_returns_materialize_review_contract`.

### 6. Reproduction results

- `PYTHONPATH=src python3 -m pytest` → **258 passed** (matches HANDOFF/work_log claim, independently recomputed).
- `-k materialize` → 10 passed.
- Smoke CASE 1 (non-minimal key) → `status=invalid_input`, exit 2.
- Smoke CASE 2 (spec_item override + finding accept, no trace/queue decisions) → `status=success`, exit 0, `trace=0 queue=0 unsupported=1`; spec_item `override_payload` **not** applied (data preserved; output YAML differs only by flow→block reserialization).

## Issues / Risks

1. **(Coverage — conditional-pass driver)** Eight contract branches lack regressions; A/G/H/B are explicit contract or worker-committed items (Findings §4). Implementation is correct today but unlocked.
2. **(Contract ambiguity)** `unsupported_decision_count` semantics vs the "지원하지 않는 materialization으로 판정하지 않는다" clause (Findings §1). Owner reconciliation needed.
3. **(Minor risk, not failing)** No guard against `--out-dir` == `--compacted-dir`; passing the same path would overwrite inputs, defeating the "never mutate inputs" guarantee. Not in contract scope; worth a one-line guard or doc note.
4. **(Minor)** Unknown/typo `target_type` values are silently dropped (not counted anywhere). Contract is silent; acceptable but undefined.

## Verdict

**조건부 합격 (Conditional Pass).** The contract is internally coherent (one ambiguity), the implementation matches every checked literal, the materialized output is downstream schema-valid, and the 258-test green bar reproduces. The condition: the boundary matrix has empty cells — the explicit `invalid_input` key-minimalism branch (A), the multi-match guard (B), the spec/rubric preservation carve-out (G), and the finding-ignore clause (H) are correct in code but pinned by **no** regression. Add those locks (and ideally C–F) before treating the slice as closed; resolve the `unsupported_decision_count` wording so the next reader isn't guessing.

## Outstanding items

- Owner decision on the `unsupported_decision_count` contract wording (Issue 2).
- Coverage additions for branches A–H (Issue 1) — defect-free but unlocked; this is the conditional-pass condition, not a separate defect.
- Working tree is clean at `97d371c`; no uncommitted work. No publication authorization implied by this record.

## Reproduction

```bash
cd /workspace/assessment_poc
PYTHONPATH=src python3 -m pytest -q                 # expect 258 passed
PYTHONPATH=src python3 -m pytest -q -k materialize   # expect 10 passed
PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command materialize-review
# Branch smokes: build a compacted dir (spec_items/rubric_items/trace_links/id_map[/review_queue]) +
# a final_review with (1) target_key {rubric_id,spec_ids} -> invalid_input/exit2,
# (2) spec_item + finding decisions -> success, unsupported_decision_count=1, inputs preserved.
```

---

## Re-verification — follow-up (2026-06-04, commit `874d3b9` "Lock materialize review guard branches")

Owner reports addressing both conditional-pass conditions. Re-audited the new commit independently.

### Contract ambiguity (Issue 2) — RESOLVED

`docs/implementation_plan...v1.md` §5.6.1 now reads: spec_item/rubric_item decisions "이런 decision의 존재만으로 실패 verdict(`invalid_input`)를 내지 않는다. 입력 artifact는 그대로 보존하고, `materialization_summary.json`의 `unsupported_decision_count`에 후속 범위(spec_item/rubric_item) 결정 수로 집계한다." This is exactly the verdict-reading fix recommended (Option 1): the "판정" ambiguity is replaced with an explicit "실패 verdict(invalid_input) 아님", and the field semantics are now defined (= spec/rubric deferred-decision count). Internal contract self-consistency restored; matches the implementation.

### Coverage (Issue 1) — 7 of 8 branches now locked; 1 residual

New regressions in `tests/test_cli_output_contract.py`, each asserting a **distinct** `input_error` substring (so branches are distinguished by message, not just exit code — satisfies the HANDOFF "test-surface lesson"):

| Branch (orig. matrix) | New test | Pins |
|---|---|---|
| A non-minimal key | `..._rejects_non_minimal_trace_key` | exit 2 / "target_key is not minimal" ✓ |
| B multi-match (one id → two links) | `..._rejects_trace_link_id_matching_multiple_links` | exit 2 / "multiple trace links"; two links share canonical T1 via id_map run_refs ✓ |
| G spec/rubric preserve + count | `..._preserves_spec_and_rubric_decisions_as_unsupported` | success / `unsupported_decision_count==2` (envelope + summary) / parsed spec+rubric == original ✓ — also locks the now-explicit §5.6.1 semantics |
| H finding ignored | `..._ignores_finding_decisions` | success / `trace_link_decision_count==0` / `unsupported_decision_count==0` (over-strict guard: finding must not inflate unsupported) ✓ |
| D queue no-match | `..._rejects_queue_decision_matching_no_entry` | exit 2 / "matches no queue entry" ✓ |
| E queue duplicate decision | `..._rejects_duplicate_queue_decisions` | exit 2 / "duplicate decisions" ✓ |
| F queue no-input | `..._rejects_queue_decision_without_queue_input` | exit 2 / "no review_queue input" ✓ |
| (bonus) duplicate entry_id in queue file | `..._rejects_duplicate_queue_entry_ids` | exit 2 / "duplicate entry_id" ✓ |

I re-derived B's construction: both trace links resolve to `T1` through `id_map` run_refs, so `_trace_links_by_canonical_id` (`cli.py:2244-2249`) raises — correct path, not a byproduct. G compares **parsed** YAML (correct given flow→block reserialization) and checks both envelope and summary.

**Residual — Branch C still untraced.** The trace-side duplicate-decision guard ("two `trace_link` decisions for one `trace_link_id`", `cli.py:2398-2402`, raises "duplicate decisions for one trace link") has **no** regression — `grep` over `tests/` finds no reference. The added "duplicate decisions" test exercises the *queue* analog (E, `cli.py:2453-2458`), a different code path. The trace-side guard is correct on read and its queue-side twin is locked, but the trace line itself could be dropped by a refactor with the green bar intact.

### Reproduced numbers (independent)

- `-k materialize` → **18 passed**, 248 deselected.
- `tests/test_cli_output_contract.py` → **107 passed**.
- full suite → **266 passed**.
- `git diff --check` → clean; working tree clean at `874d3b9` (only this verification record is untracked).

All match the owner's reported numbers.

### Updated verdict

**합격 (Pass), with one minor unlocked residual.** Both conditional-pass conditions are cleared: the contract ambiguity is reconciled with a self-consistent, implementation-matching wording, and 7 of the 8 boundary cells (plus a bonus queue-integrity guard) are now pinned by message-distinguishing regressions. The single residual is Branch C (trace-side duplicate-decision guard) — defect-free in code, symmetric guard locked on the queue side, but its own line is untested. Recommend adding the one-line analog test (two trace_link decisions with the same `trace_link_id` → exit 2 / "duplicate decisions for one trace link") to fully close the matrix. This residual is not blocking on its own given the symmetric coverage, but per the project's "no empty cells" doctrine it is the last cell to fill.

---

## Re-verification — residual closed (2026-06-04, working tree, uncommitted)

`tests/test_cli_output_contract.py::test_materialize_review_rejects_duplicate_trace_link_decisions` was added: two `trace_link` decisions with the same `target_key: {trace_link_id: T1}` (both minimal, both matching an existing link), asserting exit 2 / `status=invalid_input` / `input_error` contains "duplicate decisions for one trace link". I confirmed this hits the trace-side guard (`cli.py:2398-2402`) and not the queue analog — the asserted substring is trace-specific ("...one trace link" vs the queue path's "...one review_queue entry"), so the branch is distinguished by message.

Reproduced independently: the new test alone → 1 passed; `-k materialize` → **19 passed**; `tests/test_cli_output_contract.py` → **108 passed**; full suite → **267 passed**; `git diff --check` clean. All match the owner's reported numbers.

**Boundary matrix for this slice now has no empty cells.** Branch C was the last conditional-pass residual and it is now locked.

### Final verdict — 합격 (Pass)

The `materialize-review` slice passes. Contract (plan v1.31 §5.6.1) is internally self-consistent and matches the implementation on every checked literal; materialized artifacts are downstream schema-valid; inputs are never mutated in place; and every "should fire" / "should NOT fire" branch in the boundary matrix is pinned by a message-distinguishing regression. No defects outstanding.

### Outstanding (operational, not defects)

- The branch-C test plus HANDOFF/work_log/evaluation updates are **uncommitted** in the working tree (`git status`: `M tests/test_cli_output_contract.py`, `M HANDOFF.md`, `M docs/daily_logs/2026-06-04/work_log.md`, `M docs/evaluation.md`). This verification record is untracked. Commit when ready.
- No publication authorization is implied by this record.
