# Verification — Initial `verify` CLI orchestration (`mock_fixture`)

## Subject metadata

- **Date**: 2026-06-02
- **Requester**: Owner (kdtyohan@gmail.com)
- **Verifier**: Claude (independent audit)
- **Target slice**: `verify` subcommand — mock-only CLI orchestration that writes
  `semantic_verifications.yaml` + `review_queue.json` for compacted trace links.
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md`
  v1.30 — §5.3.1 (semantic verification states/flow), §5.7 (review queue entry),
  §8 (CLI flow). Schemas: `schemas/semantic_verifications.schema.json`,
  `schemas/review_queue.schema.json`, `schemas/trace_links.schema.json`.
- **Source of work**: working tree, uncommitted (`git status`: `M src/assessment_harness/cli.py`,
  `M tests/test_cli_output_contract.py`, `M README.md`, `M HANDOFF.md`, `M CHANGELOG.md`,
  `M docs/case_study.md`, `M src/assessment_harness/__init__.py`,
  `?? docs/daily_logs/2026-06-02/`). HEAD = `c11eed9`.

## Scope

1. Spec contract (§5.3.1 / §5.7 / §8) ↔ implementation literals.
2. `_cmd_verify` orchestration in `src/assessment_harness/cli.py`.
3. Schema self-discovery (`schema --command verify`) and `COMMAND_CONTRACTS["verify"]`.
4. Regression tests added in `tests/test_cli_output_contract.py`.
5. Generated-artifact schema validity (semantic_verifications, review_queue).
6. Full test suite + smoke run vs. reported envelope counts.

## Methodology

- Read §5.3.1 / §5.7 / §8 end-to-end and the three governing schemas.
- Read `_cmd_verify` and helpers (`cli.py:941-1125`) and the argparse wiring (`cli.py:1925-1945`).
- Read the four added tests (`test_cli_output_contract.py:480, 1856, 1936, 2003`).
- Re-derived the trace-link-id coincidence by reading `compacting.py:168-284`.
- Reproduced every reported number:
  - `PYTHONPATH=src python3 -m pytest -q` → `225 passed`.
  - `--collect-only` → agent 27 / cli 66 / compacting 7 / fixtures 8 / models 22 / rules 95 = 225.
  - `schema --command verify` → `status=success`, contract exposes `verify`, `next_actions=[fix_input]`.
  - Independent `verify` smoke on compacted `clean_assignment`-shaped artifacts (`--runs 3`).

## Findings

### Spec ↔ implementation literals (all match)
- `status_proposal: agent_uncertain` — §5.3.1 enum + schema enum; `cli.py:1029`. ✓
- Queue `type: ai_judgement_pending` — §5.7 L634 + schema enum; `cli.py:1074`. ✓
- Queue `reason` string is **verbatim** to §5.7 example L603
  (`"verification_mode=ai_judgement; semantic disclosure check required."`); `cli.py:1081-1084`. ✓
- semantic_verification required fields (`trace_link_id`, `status_proposal`, `rationale`,
  `source_refs`, `support`, `variants`) all emitted; `cli.py:1024-1039`. ✓
- "does not rewrite compacted artifacts" — verify writes only under `--out-dir`; smoke
  `sha256 -c` on the compacted `trace_links.yaml` = OK (unchanged). §5.3.1 L344. ✓

### Behavioral boundaries
- Only `ai_judgement` evidence drives proposals/queue; the two `token_sequence` links in
  `clean_assignment` are correctly suppressed (smoke + test: 3 links → `count == 1`,
  proposal `trace_link_id == T2`). Over-strict guard present, if implicit. ✓
- Incoming queue metadata + entries preserved; duplicate `entry_id` suppressed
  (`test_verify_preserves...`: top-level `source: preexisting` survives, count stays 1). ✓
- Real SDK runner rejected with `invalid_input`/exit 2 and the deferred message on both
  envelope and stderr (`test_verify_rejects_unknown_runner`). ✓
- Generated `semantic_verifications.yaml` and `review_queue.json` both pass their schemas
  (asserted in test + re-validated in smoke). ✓

### Tests are honest
The four tests pin the **public** surface (envelope counts, on-disk artifact shape,
schema validity), not internal helpers. `test_verify_mock_fixture_...` runs a real
`compact` first, so the `T2` assertion exercises the actual compact→verify handoff, not a
hand-built fixture. No green-bar-without-assertion padding observed.

## Issues / Risks

- **F1 (medium, conditional) — `trace_link_id` ↔ `id_map` canonical id is correct only
  by construction and is unguarded.** Compacted `trace_links.yaml` carries **no `id`
  field** (`compacting.py:252-273` materializes the remapped trace-link primary without an
  id; the canonical `T{n}` lives only in `id_map.yaml`, `compacting.py:189,276-284`).
  `verify` therefore always uses the `T{index}` fallback (`cli.py:1092-1096`). This equals
  the id_map canonical id **only because** the compacted file order equals group-creation
  order today. No regression cross-checks the proposal/queue `trace_link_id` against
  `id_map.yaml`. If compacting ever reorders its output independently of the id_map,
  `verify` would silently mislabel proposals and queue entries — and `trace_link_id` is the
  load-bearing key the downstream review/gate consumption will join on. The work log lists
  this as a known "Issue found" but shipped no lock for it.
  *Recommendation*: add a regression that loads `id_map.yaml` and asserts the ai_judgement
  proposal's `trace_link_id` matches the id_map `canonical_id` of the corresponding
  `trace_link` entry — or have the owner explicitly accept the order-coupling.

- **F2 (low) — `ai_judgement` evidence without `source_ref` diverges between the two
  outputs, undocumented and untested.** `source_ref` is **optional** on `evidence_quote`
  (`trace_links.schema.json`: required = `spec_id`, `quote`, `verification_mode`). For such
  an evidence, `_ai_judgement_source_refs` returns `[]`, so `_mock_semantic_verifications`
  `continue`s and emits **no proposal** (`cli.py:1022-1023`), while
  `_ai_judgement_pending_entries` still emits a **queue entry** (`cli.py:1066-1069` does not
  consult `source_ref`). The schema allows an empty `source_refs` array, so the skip is a
  silent design choice, not a schema constraint. *Recommendation*: either emit a proposal
  with empty `source_refs`, or document the skip and add an over-strict guard.

- **F3 (low, clarity) — `mock_fixture` runner token is overloaded and verify's mock ignores
  several declared inputs.** In `extract`, `--runner mock_fixture` replays `--fixture-dir`;
  in `verify` there is no `--fixture-dir` and the mock synthesizes proposals purely from the
  compacted trace links. `--source-manifest` and `--policy` are required and validated but
  otherwise **unused** by the mock verifier, and `--runs` only sets cosmetic
  `support.total_valid_runs` / fabricated `verify_00N` run ids. Acceptable for a mock slice,
  but a caller agent could reasonably expect fixture replay. Recommend a one-line doc note.

- **R1 (note) — `--runs 1..7` bound** is enforced via the shared `_extract_run_count`
  (`cli.py:943`); the only regression for it targets `extract`, not `verify`. Low risk
  (shared helper), but the verify branch is unguarded.

## Verdict

**조건부 합격 (conditional pass).** The slice is behaviorally correct for the happy path,
matches every checked spec literal exactly, does not rewrite compacted artifacts, and its
tests honestly pin the public envelope/artifact contract. All reported numbers reproduced
(225 passed; smoke identical to HANDOFF claim). The condition is **F1**: the
`trace_link_id` ↔ `id_map` identity is currently true only by ordering coincidence and is
neither locked by a regression nor carried as an explicit field — this is the downstream
join key, so it should be locked or explicitly owner-accepted before the slice closes.
F2/F3/R1 are minor.

## Outstanding items

- Work is uncommitted (working tree). No publication authorization implied by this record.
- F1 lock (or owner acceptance) is the gating follow-up; F2/F3/R1 are optional hardening.

## Re-verification 2026-06-02 (after owner fix) — verdict upgraded to 합격

Owner reworked the slice; re-audited from primary sources. Source: working tree,
uncommitted (`228 passed`; cli contract 66 → 69).

- **F1 — CLOSED.** `verify` now joins each compacted trace link back to `id_map.yaml` by
  **lineage**, not file order: `_trace_variant_refs` collects `(run_id, candidate_id)` from
  the trace link's `variants`, and `_trace_link_id_from_id_map` matches them against id_map
  `run_refs` `(run_id, local_id)` (`cli.py:1159-1190`). This is sound because `compacting.py`
  writes the same `(run_id, candidate_id)` into both `variants` and `run_refs`
  (`compacting.py:242-249`). A compacted link with variants but no id_map match now **fails
  loud** (`cli.py:1148-1152`) instead of silently mislabeling. Regression
  `test_verify_uses_id_map_trace_link_canonical_id_when_trace_order_changes`
  (`test_cli_output_contract.py:1936`) reorders the compacted trace links to `[R2,R1,R3]` and
  asserts the ai_judgement proposal/queue still carry `T2` — a two-directional guard
  (positional `T{index}` would yield `T1`).
  *Independent discriminating proof (re-derived, not trusted):* built a compacted dir via the
  real `extract → compact` pipeline, reordered trace links so R2 sits at position 0, then ran
  `verify` twice — **with `id_map.yaml` → `T2`**, **with `id_map.yaml` deleted → `T1`**. The
  T2/T1 contrast proves the id_map is genuinely load-bearing, not an ordering coincidence.

- **F2 — CLOSED (option A, owner-chosen).** ai_judgement evidence with no quote-level
  `source_ref` now still emits an `agent_uncertain` proposal with `source_refs: []` and a
  **branched rationale** ("No quote-level source_ref was available …") so the two artifacts no
  longer diverge (`cli.py:1035-1051, 1061-1070`). The over-strict risk I flagged for option A
  is locked: `test_verify_token_sequence_only_links_do_not_create_semantic_proposals`
  (`:2065`) forces all evidence to `token_sequence` and asserts `count == 0`, so a future
  over-correction that proposes for every link re-fails. `test_verify_ai_judgement_without_
  source_ref_still_records_uncertain_proposal` (`:2009`) locks the empty-`source_refs` +
  rationale behavior.

- **F3 — addressed.** README:211 and HANDOFF:32/136 now state the mock verify path is a
  conservative `agent_uncertain` proposal over compacted links (with `source_refs: []` when
  the quote-level ref is absent), not fixture replay or a real SDK judgment.

- **Residual (non-blocking) — `_resolve_verify_trace_link_ids` index alignment.** The resolver
  filters non-`Mapping` trace links via a list comprehension (`cli.py:1132-1136`) while the two
  consumers index a 0-based `enumerate` over the original list and `continue` past
  non-Mappings (`cli.py:1032,1094`). These align only because `trace_links.schema.json`
  requires every item to be an object, so post-`load_validated` the list is all-Mappings and
  no filtering occurs. Unreachable today; recommend aligning the iteration style to avoid a
  future foot-gun if the helpers are ever called without schema validation. R1 (verify-side
  `--runs` bound) and the fail-loud branch remain untested but defensive.

**Upgraded verdict: 합격 (pass).** The F1 condition is closed by implementation + a
two-directional regression + an independent discriminating smoke; F2 is locked per the
owner-chosen option A with its over-strict guard. Remaining items are non-blocking robustness
notes.

## Reproduction

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 -m pytest --collect-only -q
PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command verify

rm -rf /tmp/vsmoke && mkdir -p /tmp/vsmoke/compacted
cp fixtures/clean_assignment/{spec_items,rubric_items,trace_links}.yaml /tmp/vsmoke/compacted/
sha256sum /tmp/vsmoke/compacted/trace_links.yaml > /tmp/vsmoke/before.sha
PYTHONPATH=src python3 -m assessment_harness.cli --output json verify \
  --compacted-dir /tmp/vsmoke/compacted \
  --source-manifest fixtures/clean_assignment/source_manifest.yaml \
  --runner mock_fixture --runs 3 \
  --policy fixtures/clean_assignment/policy.yaml \
  --out-dir /tmp/vsmoke/out
sha256sum -c /tmp/vsmoke/before.sha   # expect: OK (compacted unchanged)
```
