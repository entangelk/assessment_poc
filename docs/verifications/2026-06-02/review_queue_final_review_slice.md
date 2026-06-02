# Verification — review_queue final-review processing (`review` / `gate`)

## Subject metadata

- **Date**: 2026-06-02
- **Requester**: Owner (kdtyohan@gmail.com)
- **Verifier**: Claude (independent audit)
- **Target slice**: final-review handling of `review_queue` entries.
  - `review --review-queue` drafts `target_type: review_queue_entry` /
    `target_key: {entry_id}` decisions for unresolved entries (open/held → `hold`,
    rerun_pending → `rerun_requested`, resolved → skipped).
  - `gate` reads `inputs.review_queue_path`, matches queue decisions, and treats a
    non-resolved entry with no decision or `hold`/`rerun_requested` as `pending_review`;
    `accept`/`override` close the work item without a blocking verdict.
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md`
  §5.6 (final review / gate), §5.7 (review queue). Schema: `final_review.schema.json`
  (`decision.target_type` enum includes `review_queue_entry`), `review_queue.schema.json`
  (`status` enum open/held/rerun_pending/resolved).
- **Source of work**: working tree, uncommitted. HEAD `7a21f9d`. `M cli.py`,
  `M tests/test_cli_output_contract.py`, `M plan/HANDOFF/CHANGELOG`, `?? docs/daily_logs`.

## Scope

1. Spec §5.6/§5.7 deltas ↔ `review`/`gate` implementation.
2. `final_review.schema.json` allows the new target_type + minimal `{entry_id}` key.
3. `review` draft generation (status → action mapping; resolved skip; key minimalism).
4. `gate` queue decision matching, pending/closed semantics, and interplay with the
   existing finding-decision and blocking paths.
5. Regression tests + independent smokes + full suite.

## Methodology

- Read the full `cli.py` diff (`_review_queue_decision_action`,
  `_review_target_key_for_queue_entry`, `_review_queue_entry_key`,
  `_review_queue_decision_key_errors`, `_load_gate_review_queue`, and the `_cmd_gate`
  queue block) and the plan diff (§5.6/§5.7).
- Read the new tests (`test_cli_output_contract.py:1241, 1322, 1900, 1941`).
- Reproduced `244 passed`; cli 85 / agent 27 / compacting 7 / fixtures 8 / models 22 /
  rules 95 = 244 (matches report).
- Independent gate smokes for the untested finding×queue interplay.

## Findings

### Spec ↔ implementation (matches)
- `review` status→action: `_review_queue_decision_action` returns `None` for `resolved`,
  `rerun_requested` for `rerun_pending`, else `hold` (covers open/held). Exactly the plan
  §5.6 wording ("open/held → hold, rerun_pending → rerun_requested, resolved 제외"). ✓
- Queue `target_key` is `{entry_id}` only (`_review_target_key_for_queue_entry`), matching
  the plan key-minimalism rule and the schema's `minProperties: 1`. ✓
- `gate` loads the queue when `queue_decisions` exist **or** `inputs.review_queue_path` is
  present (`_cmd_gate`), so a referenced-but-undecided queue cannot be silently ignored —
  matches "inputs에 review_queue_path가 있으면 gate는 … 매칭한다". ✓
- Queue decision key uses `_decision_key({entry_id})` = `(("entry_id", v),)`, identical to
  `_review_queue_entry_key(entry)`, so decisions join entries correctly. Finding and queue
  decisions are partitioned by `target_type` into separate key maps — no cross-collision. ✓

### Behavior (correct)
- `review` with an open + a rerun_pending entry → two decisions (`hold`, `rerun_requested`)
  with exact target_keys; piping to `gate` → `pending_review`, `pending_decision_count=2`
  (`test_review_command_writes...review_queue...` at `:1241`). ✓
- `resolved` entry → `decision_count=0`, `gate` → `success`
  (`test_review_command_skips_resolved_review_queue_entries`). Over-strict guard. ✓
- `gate` missing queue decision (open entry, empty decisions, path present) → `pending_review`,
  count 1 (`:1900`); queue `accept` → `success`, count 0, no blocking
  (`:1941`). Two-directional. ✓
- Fail-loud branches present (untested but defensive): duplicate queue `entry_id`,
  decision matching no entry, non-minimal `{entry_id}` key, and queue decisions present
  without a `review_queue_path` → all `invalid_input`/exit 2.

### Independent smokes (finding × queue interplay — not covered by tests)
- finding `accept` (confirmed blocking `optionality_mismatch`) **+** queue `accept` →
  `status=fail`, exit 1, `blocking_count=1`, `pending=0`. Queue closure does **not** mask the
  blocking finding verdict. ✓
- same, but queue decision `hold` → `status=pending_review`, exit 0, `blocking_count=0`,
  `pending=1`. Pending (finding **or** queue) dominates blocking — consistent with the
  established finding-pending precedence; a final fail is not issued while review work
  remains. ✓

## Issues / Risks

- **Low / non-blocking — defensive queue branches lack regressions.** Duplicate `entry_id`,
  decision-matches-no-entry, non-minimal key, and decisions-without-path all fail loud in code
  but have no dedicated tests, unlike their finding-decision counterparts. The happy / missing /
  accept / resolved-skip paths are locked; these guards are parallel to already-tested finding
  logic, so risk is low. Recommend mirroring the finding-decision negative tests for the queue
  path when convenient.
- **Note (not a defect)** — the pending_review/fail envelopes expose `confirmed_finding_count`
  / `dismissed_finding_count` but no analogous count for closed queue work items; queue
  `accept`/`override` are traceable only via the review.yaml input. Acceptable for this slice;
  flagging for future observability if queue closure needs to be summarized in the envelope.

## Verdict

**합격 (pass).** The slice matches the amended §5.6/§5.7 contract and the schema, the
status→action mapping and key-minimalism are exact, and `gate` integrates queue decisions
without disturbing the finding/blocking path — confirmed by an independent finding×queue smoke
(blocking preserved under queue-accept; pending dominates under queue-hold). Reported numbers
reproduced (244 passed; counts match). The only items are low-severity, non-blocking test-
coverage and observability notes.

## Outstanding items

- Work is uncommitted (working tree). No publication authorization implied.

## Follow-up 2026-06-02 — residual closed (at owner request)

The low/non-blocking test-coverage residual was closed by the verifier at the owner's request.
Four mirror regressions were added in `tests/test_cli_output_contract.py` for the previously
untested defensive `gate` queue branches:

- `test_gate_rejects_duplicate_review_queue_entry_ids` — "duplicate entry_id".
- `test_gate_rejects_review_queue_decision_matching_no_entry` — "matches no queue entry".
- `test_gate_rejects_non_minimal_review_queue_target_key` — "not minimal".
- `test_gate_rejects_review_queue_decision_without_review_queue_path` — "no review_queue_path".

Each asserts `exit 2` / `invalid_input` **and the branch-specific message**, which is what makes
them two-directional: removing the minimality or no-path guard would otherwise fall through to
the adjacent "matches no queue entry" path and still exit 2 — the message assertion catches
that. No production code changed. Suite: `248 passed` (CLI 85 → 89); `git diff --check` clean.

The observability note (no closed-queue-item count in the gate envelope) was deliberately **not**
actioned: it is a public-contract addition, not a defect, and out of scope without an explicit
request. The slice verdict (합격) is unchanged.

## Reproduction

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 -m pytest --collect-only -q

# finding × queue interplay
rm -rf /tmp/vq && mkdir -p /tmp/vq
python3 - <<'PY'
import json, yaml
json.dump({'status':'provisional_findings','findings':[
  {'type':'optionality_mismatch','severity':'high','decision_status':'provisional','rubric_id':'R_HIGH','message':'x'}],
  'diagnostics_ref':'d.json','blocking_count':0,'generated_at':'2026-06-02T00:00:00Z'}, open('/tmp/vq/findings.json','w'))
json.dump({'review_queue':[{'entry_id':'q1','type':'low_support','target':{'k':'v'},'reason':'r',
  'related_runs':['run_1'],'status':'open'}]}, open('/tmp/vq/rq.json','w'))
yaml.safe_dump({'review_id':'rv1','reviewer':'t','reviewed_at':'2026-06-02T00:00:00Z',
  'inputs':{'findings_path':'/tmp/vq/findings.json','review_queue_path':'/tmp/vq/rq.json'},
  'decisions':[{'target_type':'finding','target_key':{'type':'optionality_mismatch','rubric_id':'R_HIGH'},'action':'accept'},
               {'target_type':'review_queue_entry','target_key':{'entry_id':'q1'},'action':'accept'}]},
  open('/tmp/vq/review.yaml','w'), sort_keys=False)
PY
PYTHONPATH=src python3 -m assessment_harness.cli --output json gate --final-review /tmp/vq/review.yaml
# expect: status=fail, exit 1, blocking_count=1  (queue accept does not mask the block)
```
