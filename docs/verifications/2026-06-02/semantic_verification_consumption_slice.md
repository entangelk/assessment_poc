# Verification — Semantic verification consumption path (`check` / `report` / `review`)

## Subject metadata

- **Date**: 2026-06-02
- **Requester**: Owner (kdtyohan@gmail.com)
- **Verifier**: Claude (independent audit)
- **Target slice**: consume `semantic_verifications.yaml`:
  - `check --semantic-verifications` applies proposals as effective Rule 1 `semantic_status`
    without rewriting `trace_links.yaml`.
  - `report --semantic-verifications --review-queue` validates + renders both as sections.
  - `review --semantic-verifications --review-queue` schema-validates before recording.
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.30 —
  §5.3.1 (effective semantic status, status table), §6 Rule 1 (final-coverage boundary).
  Schemas: `semantic_verifications.schema.json`, `review_queue.schema.json`. Locked decision:
  HANDOFF "Rule 1 final-coverage boundary" — only `human_accepted` / `human_overridden` count.
- **Source of work**: working tree, uncommitted (HEAD `7a21f9d`). `M cli.py`, `M report.py`,
  `M tests/test_cli_output_contract.py`, `M README/CHANGELOG/HANDOFF`, `?? docs/daily_logs/2026-06-02`.

## Scope

1. §5.3.1 / §6 Rule 1 ↔ `_trace_doc_with_semantic_verifications` and `run_rule_one`.
2. `check` envelope/finding payload effect and the trace-links non-rewrite lock.
3. `report` rendering + input validation; `review` pre-write validation.
4. Regression tests added in `test_cli_output_contract.py`.
5. Cross-command `trace_link_id` keying consistency vs. the F1 lineage fix.
6. Full suite + independent smokes.

## Methodology

- Read the full `cli.py` diff, `report.py` diff, and `rules.py:580-694` (Rule 1).
- Read the new tests (`test_cli_output_contract.py:373, 440, 1784, 1877, 931, 1007`).
- Reproduced `235 passed`; collection cli 76 / agent 27 / compacting 7 / fixtures 8 /
  models 22 / rules 95 = 235 (matches report).
- Independent smoke A (happy path) and smoke B (reorder) via the real
  `extract → compact → verify → check` pipeline.

## Findings

### Correct & honest (happy path)
- `check` applies the proposal's `status_proposal` as the link's effective `semantic_status`
  on a **deep copy** (`cli.py:_trace_doc_with_semantic_verifications`), runs Rule 1 on the
  copy, and runs Rules 2/3/L* on the original. The on-disk `trace_links.yaml` is never
  written by `check`; `test_check_applies_..._without_rewriting_trace_links` asserts byte
  equality before/after. ✓
- **Rule 1 boundary preserved.** `status_proposal` enum is only `agent_*`
  (`semantic_verifications.schema.json`); `HUMAN_ACCEPTED_SEMANTIC_STATUSES =
  {human_accepted, human_overridden}` (`rules.py:580`). So overwriting
  `pending_verification → agent_supported` does **not** change the finding type — R2 stays
  `unconfirmed_trace_coverage`; only `evidence.semantic_statuses` updates. The test asserts
  exactly this (R2 → `["agent_supported"]`, R1 → `["pending_verification"]`) and does **not**
  wrongly assert suppression. This is the correct, honest behavior. ✓
- Unrelated/non-matching proposal (`T_NOT_PRESENT`) changes nothing
  (`test_check_token_sequence_links_not_changed...`). Over-strict guard present. ✓
- Duplicate `trace_link_id` in the proposals → fail-loud `HarnessInputError`
  (`_semantic_status_by_trace_link_id`). Defensive; untested.
- `report` renders `## Semantic Verifications` / `## Review Queue`, schema-validates both, and
  rejects a malformed proposal with exit 2 (`test_report_command_includes...`,
  `..._rejects_invalid_semantic_verifications`). ✓
- `review` schema-validates `--semantic-verifications` / `--review-queue` **before** writing
  the draft, and records their resolved paths in `review.yaml inputs`
  (`test_review_command_validates_and_records...`, `..._rejects_invalid_review_queue_input`). ✓

## Issues / Risks

- **F1' (medium) — `check`'s semantic-application keying is positional (`T{index}`) and
  inconsistent with `verify`'s lineage-based keying; silent misattribution under reorder.**
  `verify` resolves `trace_link_id` from `id_map.yaml` lineage (the prior F1 fix, order-robust).
  But `check` has no `id_map` / `--compacted-dir` input, so
  `_trace_link_id_for_semantic_application` (`cli.py`) falls to `T{index}` by file position
  (compacted trace links carry no `id`). The two halves of the same feature therefore compute
  the join key by different methods, coinciding only when `trace_links.yaml` is in canonical
  compact order.
  *Independent proof (re-derived):* `extract → compact → verify` keyed the ai_judgement
  proposal to **T2 = R2** (lineage). After reordering the compacted `trace_links.yaml` to
  `[R2,R1,R3]` and running `check` with that proposal, the verifier's judgment landed on the
  **wrong rubric**: `R1 → ['agent_uncertain']`, `R2 → ['pending_verification']`.
  *Impact*: no verdict change (agent_* never alters Rule 1 coverage), but the
  `semantic_statuses` audit data — the entire point of the consumption feature for the human
  reviewer — is silently attached to the wrong rubric. This re-introduces, asymmetrically, the
  exact fragility F1 closed. Unguarded: both `check` tests use canonical-order fixtures.
  Spec-silent on the resolution method (§5.3.1 only shows `trace_link_id: T1`).
  *Recommendation*: give `check` `id_map`/`--compacted-dir` access and reuse the lineage
  resolver (symmetry with `verify`), or document + guard the ordering coupling. Per the F1
  precedent and the project's fail-loud principle, lineage symmetry is the consistent fix.

- **F2' (low) — proposals blindly override any existing `semantic_status`, including
  `human_accepted` / `human_overridden`.** `_trace_doc_with_semantic_verifications` overwrites
  unconditionally. Because proposals are only `agent_*`, this can never falsely *add* coverage,
  but it can *strip* coverage from an already human-finalized link
  (`human_accepted → agent_rejected ⇒ unconfirmed_trace_coverage reappears`). Not reachable in
  the documented `compact → verify → check` order (links are `pending` then), but it is a
  spec-silent precedence boundary. *Recommendation*: skip application when the current status
  is in `HUMAN_ACCEPTED_SEMANTIC_STATUSES`, or document that `semantic_verifications` is a
  pre-human-review input only.

## Verdict

**조건부 합격 (conditional pass).** The consumption path is correct and honest for the
documented pipeline: the trace-links non-rewrite lock holds, the Rule 1 final-coverage
boundary is preserved exactly (agent_* never suppresses/promotes), and `report`/`review` input
validation is properly tested. The condition is **F1'**: the positional-vs-lineage keying
mismatch is a demonstrated silent misattribution that undercuts the F1 guarantee and the
feature's audit purpose — it should be fixed (lineage symmetry) or explicitly documented and
guarded before the slice closes. **F2'** is a minor precedence boundary to resolve. Reported
numbers reproduced (235 passed; counts match).

## Outstanding items

- Work is uncommitted (working tree). No publication authorization implied.
- F1' is the gating follow-up; F2' is optional hardening.

## Re-verification 2026-06-02 (after owner fix) — verdict upgraded to 합격

Owner fixed both findings; re-audited from primary sources. Source: working tree, uncommitted.
`237 passed`; cli contract 76 → 78.

- **F1' — CLOSED.** `check` gained `--id-map` (`cli.py` argparse + `_load_optional_validated`),
  and `_trace_doc_with_semantic_verifications` now resolves each trace link's id via the
  **same lineage resolver `_trace_link_id(trace_link, index, id_map_doc)` that `verify` uses**
  (the F1 fix), instead of the positional-only helper, which is gone (no dead code:
  `_trace_link_id_for_semantic_application` not found in `src/` or `tests/`). Schema
  self-discovery now exposes `id_map_path` (+ `semantic_verifications_path`).
  Regression `test_check_uses_id_map_for_semantic_verification_when_trace_order_changes`
  (`:440`) reorders the compacted trace to `[R2,R1,R3]`, runs `verify → check --id-map`, and
  asserts `R2 → ['agent_uncertain']` / `R1 → ['pending_verification']` — a two-directional
  guard (positional keying would invert these).
  *Independent discriminating proof (re-ran my prior break case):* same reorder, `check`
  **with `--id-map` → `R2=['agent_uncertain']`, `R1=['pending_verification']` (correct)**;
  **without `--id-map` → `R1=['agent_uncertain']`, `R2=['pending_verification']` (old
  misattribution)**. The contrast proves the lineage resolver is load-bearing and the fix
  works.

- **F2' — CLOSED.** `_trace_doc_with_semantic_verifications` now skips application when the
  link's current status `_is_human_finalized_status` (∈ `HUMAN_ACCEPTED_SEMANTIC_STATUSES`).
  Regression `test_check_semantic_verification_does_not_downgrade_human_final_status` (`:543`)
  sets R2 = `human_accepted`, feeds an `agent_rejected` proposal for it, and asserts `R2` is
  **absent** from findings (still covered) while R1 is unaffected — two-directional (removing
  the guard makes R2 reappear as `unconfirmed_trace_coverage`).

- **Residual (low, non-blocking) — `--id-map` is optional and not auto-derived.** Without it,
  a reordered trace still misattributes silently (correct only in canonical order). Unlike
  `verify`, which auto-discovers `id_map.yaml` from `--compacted-dir`, `check` requires the
  explicit flag, and the plan §8 `check` example does not show it — a caller could omit it.
  The default (canonical order, no flag) is correct, so this is a usability/doc note, not a
  regression. Recommend documenting "pass `--id-map` whenever `--semantic-verifications` is
  passed."

- **Residual (low, non-blocking) — downgrade guard covers only the two coverage-granting
  human states.** `_is_human_finalized_status` protects `human_accepted` / `human_overridden`
  but not `human_rejected` / `rerun_requested`, which an agent proposal can still overwrite.
  No verdict harm (both are non-coverage → finding type unchanged) and only reachable out of
  the canonical pre-review ordering, but the helper name reads broader than its check.
  Consider widening the guard to all human-decided states or renaming it.

**Upgraded verdict: 합격 (pass).** Both conditions are closed by implementation + a
two-directional regression each + an independent discriminating smoke. Residuals are
low-severity, non-blocking usability/hardening notes. Reported numbers reproduced (237 passed;
counts match; schema exposes `id_map_path`).

## Re-verification 2026-06-02 (second pass) — both residuals also closed

Owner closed the two low residuals too. `241 passed`; cli contract 78 → 82. Re-audited:

- **Residual 1 (optional/unenforced `--id-map`) — CLOSED, now spec-mandated.** `check` now
  fails loud: `semantic_doc present + id_map_doc None + _trace_doc_has_compacting_variants` →
  `invalid_input` / exit 2 / `fix_input` (`cli.py`). The plan was amended to match — §8 example
  now passes `--id-map work/compacted/id_map.yaml` (plan:1046) and §section 936 explicitly
  requires the fail-loud ("구현은 fail-loud해야 한다"), so this is no longer a spec-silent
  boundary. Regression `test_check_rejects_semantic_verifications_for_lineage_trace_without_id_map`
  (`:543`) asserts exit 2 + "requires --id-map".
  *Independent smokes:* (A) compacted lineage trace + semantic + no `--id-map` → `invalid_input`
  / exit 2 with the exact message; (B) non-lineage fixture (`variants: []`) + semantic + no
  `--id-map` → still `provisional_findings` / exit 0 — confirming the guard does **not**
  over-fire and the documented fallback is preserved.
- **Residual 2 (narrow downgrade guard) — CLOSED.** Helper renamed to
  `_is_post_review_semantic_status` and widened to `human_accepted` / `human_overridden` /
  `human_rejected` / `rerun_requested`, so an agent proposal never overwrites any post-review
  human decision. Regression `test_check_semantic_verification_does_not_downgrade_post_review_status`
  (`:631`) is **parametrized across all four** states (two-directional: coverage-granting
  states ⇒ R2 absent; non-coverage human states ⇒ R2 retains the human status, not the agent
  proposal).

**Final verdict: 합격 (pass), no open items.** Both conditions and both residuals are closed
with two-directional regressions and reproduced independently; the spec was amended so the
fail-loud is contractual, not implicit.

## Reproduction

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 -m pytest --collect-only -q

# End-to-end lineage guard smoke
rm -rf /tmp/vck && mkdir -p /tmp/vck
PYTHONPATH=src python3 -m assessment_harness.cli --output json extract \
  --spec fixtures/clean_assignment/source/spec.md --rubric fixtures/clean_assignment/source/rubric.md \
  --source-manifest fixtures/clean_assignment/source_manifest.yaml \
  --runner mock_fixture --fixture-dir fixtures/clean_assignment --runs 1 --out-dir /tmp/vck/runs
PYTHONPATH=src python3 -m assessment_harness.cli --output json compact \
  --runs-dir /tmp/vck/runs --policy fixtures/clean_assignment/policy.yaml --out-dir /tmp/vck/comp
PYTHONPATH=src python3 -m assessment_harness.cli --output json verify \
  --compacted-dir /tmp/vck/comp --source-manifest fixtures/clean_assignment/source_manifest.yaml \
  --runner mock_fixture --runs 1 --policy fixtures/clean_assignment/policy.yaml --out-dir /tmp/vck/ver
python3 - <<'PY'
import yaml; p='/tmp/vck/comp/trace_links.yaml'; d=yaml.safe_load(open(p))
tl=d['trace_links']; d['trace_links']=[tl[1],tl[0],tl[2]]; yaml.safe_dump(d,open(p,'w'),sort_keys=False)
PY
PYTHONPATH=src python3 -m assessment_harness.cli --output json check \
  --spec-items /tmp/vck/comp/spec_items.yaml --rubric-items /tmp/vck/comp/rubric_items.yaml \
  --trace-links /tmp/vck/comp/trace_links.yaml --source-manifest fixtures/clean_assignment/source_manifest.yaml \
  --semantic-verifications /tmp/vck/ver/semantic_verifications.yaml \
  --id-map /tmp/vck/comp/id_map.yaml \
  --policy fixtures/clean_assignment/policy.yaml --out /tmp/vck/find.json --diagnostics-out /tmp/vck/diag.json
# observe: R2 carries agent_uncertain; R1 remains pending_verification

PYTHONPATH=src python3 -m assessment_harness.cli --output json check \
  --spec-items /tmp/vck/comp/spec_items.yaml --rubric-items /tmp/vck/comp/rubric_items.yaml \
  --trace-links /tmp/vck/comp/trace_links.yaml --source-manifest fixtures/clean_assignment/source_manifest.yaml \
  --semantic-verifications /tmp/vck/ver/semantic_verifications.yaml \
  --policy fixtures/clean_assignment/policy.yaml --out /tmp/vck/find_no_id_map.json --diagnostics-out /tmp/vck/diag_no_id_map.json
# observe: invalid_input / exit 2 because lineage trace links require --id-map
```
