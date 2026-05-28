# Work Log - 2026-05-28

## Initial Gate / Final Review Finding Mapping

### Goals

- Start the next contracted area after Rule 0-3 and lint L1/L5/L6: `gate`.
- Resolve the final-review-to-finding mapping before implementation so review records do not copy excessive finding payload data.
- Add the smallest useful vertical slice: final review schema, `gate` command, public CLI contract tests, and fixture-level gate regression.

### Completed Work

- Promoted the canonical plan to v1.16.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: added `target_type: finding`; defined per-finding minimal `target_key` fields; excluded `message`, `evidence`, title/description/text, and other explanatory payload from matching keys; documented missing/stale/duplicate decision behavior; documented Rule 1 promotion and confirmed blocking scope.
  - Effect: `gate` can match final review decisions to findings without bloating review records or depending on unstable explanatory text.
- Added the final review schema and initial `gate` command.
  - Files changed: `schemas/final_review.schema.json`, `src/assessment_harness/schemas.py`, `src/assessment_harness/cli.py`.
  - Key changes: registered `final_review`; added `gate --final-review`; loaded the referenced `findings.json`; matched `target_type: finding` decisions by canonical minimal keys; returned `pending_review`, `success`, `fail`, or `invalid_input`; exposed `schema --command gate`.
  - Effect: caller agents now have a machine-readable external verdict stage after human final review.
- Added contract and fixture regressions.
  - Files changed: `tests/test_cli_output_contract.py`, `tests/test_fixtures.py`.
  - Key changes: locked `gate` schema introspection, pending behavior, Rule 1 promotion to confirmed blocking, override dismissal, nonblocking confirmed Rule 2 behavior, stale decision rejection, strict rejection of non-minimal finding `target_key` payload copies, and an end-to-end `orphan_scored_rubric` check → final review → gate path.
  - Effect: both under-strict and over-strict directions are covered for the new gate slice, including the "minimal key, no copied evidence" concern.
- Updated current-state documentation.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: documented plan v1.16, initial `gate`, `final_review.schema.json`, gate output fields, and next work after this slice.
  - Effect: handoff now points to `review`/runner/queue composition work rather than treating all of `gate` as unimplemented.

### Issues Found

- Problem: final review examples previously showed `trace_link`, `spec_item`, and `review_queue_entry`, but did not define how a human review closes a provisional finding.
  Cause: `gate` had been deferred until after the final review contract existed, so finding-level mapping had not yet been specified.
  Resolution: added `target_type: finding` and a canonical key table in plan v1.16 before implementing code.
  Outcome: implementation follows a documented contract rather than inventing an implicit matching rule.
- Problem: a naive final review record could copy full finding payloads (`message`, `evidence`, rubric text, spec text) just to identify a finding.
  Cause: without a key table, the safest apparent matching input would be "copy everything".
  Resolution: limited `target_key` to generated identifiers only: `type` plus `rubric_id`, `spec_id`, or L1 paired rubric IDs as needed; `gate` now rejects non-identity fields such as copied `message`.
  Outcome: review records stay compact and robust against explanatory payload changes, and the code enforces the minimal-key contract rather than merely documenting it.
- Problem: accepted findings are not all blocking in the plan. Rule 2/L1/L5 can be confirmed as review outcomes but are not v0 external blocking verdicts.
  Cause: severity and blocking status are adjacent but not identical in the canonical plan.
  Resolution: limited `gate` exit `1` to confirmed `orphan_scored_rubric_item`, `optionality_mismatch`, and `mandatory_spec_bonus_only_traced`.
  Outcome: `gate` does not over-block medium confirmed Rule 2/L1/L5 findings.

### Decisions

- **Owner decision (proceed with mapping-first gate work)**: implement the final-review finding mapping after explicitly checking that keys do not carry excessive data.
- `target_type: finding` keys are matching keys only, not payload snapshots. Explanatory fields remain in `findings.json` and reports.
- Missing decisions and `hold`/`rerun_requested` return `pending_review`/exit `0`; stale or duplicate finding decisions return `invalid_input`/exit `2`.
- `accept` confirms a finding. For Rule 1 `possible_orphan_scored_rubric_item` and `unconfirmed_trace_coverage`, `accept` promotes to `orphan_scored_rubric_item` (`high`, `confirmed`). `override` dismisses the finding.

### Next Steps

1. Implement the `review` command that helps produce final review records rather than hand-authoring `final_review.yaml`.
2. Materialize trace-link override provenance (`sources.kind: human_override`) when review/gate work reaches trace artifact rewriting.
3. When Phase 2 compact/verifier queues land, implement queue composition before pointing `--review-queue-out` at a unified queue path.
4. Independently verify the v1.16 `gate` slice before publication.

### Verification

- Focused CLI + fixture suite: `python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed (27 tests).
- Full suite: `python3 -m pytest -q` passed (134 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 20 CLI contract, 7 fixture, 12 model, and 95 rule tests.
- Gate schema smoke: `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command gate` returns `status=success` and exposes `complete_final_review`, `fix_final_review`, and `revise_assessment`.
- Diff hygiene: `git diff --check` passed.

## Gate Conditional-Pass Follow-Up

### Goals

- Address the independent verification record `docs/verifications/2026-05-28_gate_initial_slice.md`.
- Convert the reported boundary-matrix empty cells into named regressions.
- Resolve the two minor design findings: unused `gate --policy` and spec-silent duplicate finding-key rejection.

### Completed Work

- Promoted the plan to v1.17.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: explicitly made duplicate canonical finding keys in `findings.json` an `invalid_input`/exit `2` condition; added v1.17 changelog text for the verification follow-up; removed `--policy` from `gate` examples.
  - Effect: the code's duplicate-key guard is no longer a spec-silent behavior, and `gate` no longer advertises an unused policy input.
- Expanded `gate` regression coverage.
  - Files changed: `tests/test_cli_output_contract.py`.
  - Key changes: added named tests for direct blocking accepts (`optionality_mismatch`, `mandatory_spec_bonus_only_traced`), nonblocking L1/L5 accepts, `hold`/`rerun_requested`, duplicate decisions, missing key fields, unknown finding type, invalid final-review schema, missing findings file, invalid findings schema, and duplicate finding keys.
  - Effect: the independent verification's boundary-matrix empty cells are now locked by tests rather than only by manual smoke execution.
- Removed the unused `gate --policy` CLI argument.
  - Files changed: `src/assessment_harness/cli.py`, `README.md`, `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: `gate` now accepts only `--final-review` plus output formatting; examples match the actual parser.
  - Effect: the CLI no longer carries speculative policy plumbing.
- Updated current-state records.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: marked current plan as v1.17 and documented that this slice closes the conditional-pass regression gaps.
  - Effect: next workers see the verification follow-up as completed rather than as a lingering caveat.

### Issues Found

- Problem: the initial `gate` implementation behaved correctly on branches the tests did not name.
  Cause: implementation smoke covered more branches than the committed regression matrix.
  Resolution: added explicit tests for each contract branch called out by the verification record.
  Outcome: removing `optionality_mismatch` or `mandatory_spec_bonus_only_traced` from the blocking set, or adding L1/L5 to it, now fails tests.
- Problem: `gate --policy` existed but `_cmd_gate` never read policy.
  Cause: the final workflow had historically shown `--policy` on gate before gate's actual responsibilities were narrowed to final-review consumption.
  Resolution: removed the argument and updated command examples.
  Outcome: no speculative CLI surface remains for policy in `gate`.
- Problem: duplicate canonical finding keys in `findings.json` were rejected by code but not named in the plan.
  Cause: the duplicate-key guard was added as defensive input validation during implementation.
  Resolution: documented duplicate finding keys as invalid gate input in plan v1.17.
  Outcome: spec and implementation now agree.

### Decisions

- The owner accepted the verification finding and directed reinforcement rather than treating the conditional pass as sufficient.
- Duplicate canonical finding keys are invalid gate input, because gate cannot map one review decision to two indistinguishable findings safely.
- `gate` remains policy-free for now. Policy belongs to earlier rule evaluation; `gate` consumes final review records and findings.

### Next Steps

1. Ask for or perform independent re-verification of the v1.17 gate follow-up before publication.
2. Continue with the `review` command after the gate slice is accepted.

### Verification

- Focused gate contract suite: `python3 -m pytest tests/test_cli_output_contract.py -q` passed (33 tests).
- Full suite: `python3 -m pytest -q` passed (147 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 33 CLI contract, 7 fixture, 12 model, and 95 rule tests.

---

## Initial Review Draft Writer

### Goals

- Continue from the accepted `gate` slice into the next workflow step: `review`.
- Keep scope narrow and safe: generate a final-review draft, but do not make final human decisions automatically.
- Reuse the v1.17 minimal finding-key contract so review records do not copy finding payloads.

### Completed Work

- Promoted the plan to v1.18.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: defined Phase 0 `review` as a draft writer; required `--findings`, `--out-dir`, and `--reviewer`; documented that every generated finding decision starts as `hold`; documented that draft records gate to `pending_review` when findings exist.
  - Effect: the review command has a canonical contract before being used as part of the workflow.
- Implemented `assessment-harness review`.
  - Files changed: `src/assessment_harness/cli.py`.
  - Key changes: reads and validates `findings.json`; converts each known finding to a minimal canonical `target_key`; writes `<out-dir>/review.yaml`; records optional input paths; exposes `schema --command review`.
  - Effect: users no longer need to hand-author the initial final review record just to begin review.
- Added regression coverage.
  - Files changed: `tests/test_cli_output_contract.py`, `tests/test_fixtures.py`.
  - Key changes: locked `schema --command review`, synthetic review draft generation, empty-findings success through gate, unknown finding rejection, and an end-to-end `orphan_scored_rubric` check → review draft → gate pending path.
  - Effect: review draft behavior is tied to both the public CLI envelope and grounded fixture outputs.
- Updated current-state docs.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: documented `--reviewer`, review draft semantics, and the current package surface including `review`.
  - Effect: handoff now points to richer human decision input / trace override materialization rather than the basic review draft writer.

### Issues Found

- Problem: auto-generating `accept` decisions would make the tool a judge rather than a review recorder.
  Cause: `review` sits between provisional findings and external `gate`, so the temptation is to "complete" decisions automatically.
  Resolution: generated decisions are always `hold`; humans must edit the draft to `accept`, `override`, or `rerun_requested`.
  Outcome: the first review slice is useful without collapsing the human-review boundary.
- Problem: relative `findings_path` inside `review.yaml` could break when `gate` resolves paths relative to the review file.
  Cause: `gate` deliberately resolves relative paths from the final-review file's directory.
  Resolution: `review` writes absolute input paths.
  Outcome: a generated review draft can be passed to `gate` from any working directory.

### Decisions

- `review` is a draft writer, not an interactive or automatic final-review UI.
- `--reviewer` is required so the generated record has explicit audit metadata.
- Unknown finding types are invalid for review draft generation because `gate` would not know a canonical minimal key for them.

### Next Steps

1. Run focused/full/Docker verification for the v1.18 review slice.
2. Independently verify review draft generation before publication.
3. Later review work can add richer human decision input or trace-link override materialization.

### Verification

- Focused review/gate contract suite: `python3 -m pytest tests/test_cli_output_contract.py -q` passed (37 tests).
- Focused review/gate + fixture suite: `python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed (45 tests).
- Full suite: `python3 -m pytest -q` passed (152 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 37 CLI contract, 8 fixture, 12 model, and 95 rule tests.
- Review schema smoke: `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command review` returns `status=success` and exposes `review_path`, `decision_count`, and `input_error`.

---

## Review Draft Safety Guard Follow-Up

### Goals

- Address the independent review of the v1.18 `review` draft writer without weakening the human-review boundary.
- Add the missing regression for known finding types with absent canonical key fields.
- Decide and implement the safest default for invalid findings status and existing draft overwrites.

### Completed Work

- Promoted the plan to v1.19.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: documented that `review` accepts only `findings.status=success` or `provisional_findings`; documented that `gate` remains status-agnostic; documented that existing `<out-dir>/review.yaml` is not overwritten unless `--force` is passed; recorded that timestamped/versioned draft management is deferred.
  - Effect: the status/overwrite behavior is now a contract, not an implementation guess.
- Hardened the `review` command.
  - Files changed: `src/assessment_harness/cli.py`.
  - Key changes: added a findings status guard before draft generation; added overwrite refusal with explicit `--force`; kept generated decisions at `hold` and target keys minimal.
  - Effect: Rule 0 invalid outputs with empty findings cannot be converted into a draft that later gates as success, and human-edited drafts are not silently erased.
- Expanded review regressions.
  - Files changed: `tests/test_cli_output_contract.py`.
  - Key changes: added the missing known-type/missing-key-field invalid-input regression; added status-guard regression; expanded the status guard to reject `invalid_input`, `internal_error`, and missing status inputs; added no-overwrite and force-overwrite regressions.
  - Effect: under-strict status acceptance and accidental overwrite are now locked, while explicit regeneration remains possible.
- Updated current-state docs.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: documented plan v1.19, review status guard, overwrite guard, and the deferred timestamp/versioning boundary.
  - Effect: next workers can continue with richer review/version management without rediscovering this policy.

### Issues Found

- Problem: the v1.18 review test matrix did not lock the known finding type + missing canonical key field branch.
  Cause: unknown finding type was covered, but optional schema fields made the missing-key path separately reachable.
  Resolution: added a regression using `optionality_mismatch` without `rubric_id`; `review` returns `invalid_input`/exit `2` with `missing gate key field`.
  Outcome: the branch named in the final-review mapping contract is now protected.
- Problem: `review` previously accepted `findings.status=invalid_input` if the file matched schema shape and had an empty findings list.
  Cause: the first draft writer focused on findings array conversion and did not gate the producing command status.
  Resolution: `review` now rejects any findings status except `success` and `provisional_findings`.
  Outcome: invalid Rule 0 input cannot be laundered through an empty draft into a successful gate result.
- Problem: the first status-guard regression only sampled `invalid_input`, so a future blocklist-style refactor could still let `internal_error` through.
  Cause: the implementation was a whitelist, but the regression did not prove that shape.
  Resolution: parametrized the status rejection test over `invalid_input`, `internal_error`, and status omission. The omission case is rejected by schema before the whitelist guard, while `internal_error` directly locks the whitelist behavior.
  Outcome: changing the guard to reject only `invalid_input` now fails the CLI contract suite.
- Problem: re-running `review` over the same output directory silently replaced `review.yaml`.
  Cause: the initial implementation treated draft generation as reproducible output, but final review drafts may be hand-edited artifacts.
  Resolution: default overwrite is forbidden; `--force` is required for intentional regeneration.
  Outcome: human edits are preserved by default.

### Decisions

- **Owner-guided decision (2026-05-28)**: put the findings-status safety guard in `review`, not `gate`. This prevents accidental invalid-input laundering at draft creation while preserving `gate` as a consumer of explicit final-review records for manual recovery and audit workflows.
- **Owner-guided decision (2026-05-28)**: default behavior is no overwrite for `review.yaml`. `--force` is the explicit escape hatch.
- Timestamped/versioned draft management is useful but deferred. For now, callers that need draft history should use distinct `--out-dir` values; adding automatic version files belongs in a separate policy slice.

### Next Steps

1. Ask for independent re-verification before publication.
2. Later review work can add richer human decision input and a deliberate draft-versioning policy.

### Verification

- Focused review/gate + fixture suite: `python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed (51 tests).
- Full suite: `python3 -m pytest -q` passed (158 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 43 CLI contract, 8 fixture, 12 model, and 95 rule tests.
- Review schema smoke: `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command review` returns `status=success` and exposes `review_path`, `decision_count`, and `input_error`.
- Gate schema smoke: `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command gate` returns `status=success` and exposes `complete_final_review`, `fix_final_review`, and `revise_assessment`.
- Diff hygiene: `git diff --check` passed.

---

## Phase 0 Policy Completeness Follow-Up

### Goals

- Continue Phase 0 cleanup before moving into real-assignment/manual flow.
- Remove the remaining silent Rule 3 suppression path where missing policy made `optionality_mismatch` impossible to emit.
- Keep caller-agent recovery structured rather than relying on argparse usage errors.

### Completed Work

- Promoted the plan to v1.20.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: made `--policy` a Phase 0 `check` input requirement; made `rules.optionality_mismatch.weight_threshold` required for `check`; documented `provide_policy` and `fix_input` recovery behavior.
  - Effect: Rule 3 cannot be accidentally disabled by omitting policy.
- Hardened `assessment-harness check` policy validation.
  - Files changed: `src/assessment_harness/cli.py`.
  - Key changes: `check` now returns `invalid_input`/exit `2` with next_action `provide_policy` when `--policy` is absent; schema-valid policies missing `rules.optionality_mismatch.weight_threshold` return `invalid_input`/exit `2` with `fix_input`.
  - Effect: caller agents get a structured recovery path and no longer receive a green run with Rule 3 silently skipped.
- Expanded CLI contract regressions.
  - Files changed: `tests/test_cli_output_contract.py`.
  - Key changes: added missing-policy and incomplete-policy tests; added `provide_policy` to `schema --command check`; updated isolated fixture helper/tests to pass the required policy.
  - Effect: both under-strict directions are locked: omitting policy and omitting Rule 3 threshold now fail.
- Updated current-state docs.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: documented plan v1.20 and removed the HANDOFF open decision for Rule 3 policy completeness.
  - Effect: Phase 0 no longer has an active policy-completeness caveat.

### Issues Found

- Problem: `--policy` was optional and `load_policy(None)` returned `{}`.
  Cause: early Phase 0 kept policy optional while Rule 3 was still being introduced.
  Resolution: added an explicit structured missing-policy guard before loading YAML inputs.
  Outcome: caller agents now receive `provide_policy` instead of a misleading run with Rule 3 suppressed.
- Problem: a policy file could pass schema validation while omitting `rules.optionality_mismatch.weight_threshold`.
  Cause: the unified policy schema permits later-phase sections and did not require the Rule 3 threshold.
  Resolution: added `check`-level policy completeness validation for the required Rule 3 path.
  Outcome: policy files that cannot support Rule 3 produce `invalid_input`.

### Decisions

- **Owner-guided decision (2026-05-28)**: because generated YAML will usually be prepared by a caller AI, Phase 0 should fail loudly and structurally when required policy is absent rather than letting a rule disappear.
- Keep argparse permissive for `--policy` so missing input still returns the JSON envelope (`invalid_input`/exit `2`) that caller agents can parse and repair.

### Next Steps

1. Move toward Phase 1 manual real-assignment smoke once this Phase 0 cleanup is accepted.
2. Independently verify v1.20 policy completeness before publication if needed.

### Verification

- Focused CLI + fixture suite: `python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed (53 tests).
- Full suite: `python3 -m pytest -q` passed (160 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 45 CLI contract, 8 fixture, 12 model, and 95 rule tests.
- Check schema smoke: `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command check` returns `status=success` and exposes `provide_policy` in `next_actions_types`.

## Policy Completeness Verification Follow-up — Strengthening Applied

### Goals

- Close the strengthening recommendation in [2026-05-28_policy_completeness.md](../../verifications/2026-05-28_policy_completeness.md) §Issues 1 at owner request, before pushing the Phase 0 cleanup.

### Completed Work

- Parametrized `test_check_policy_missing_rule_three_threshold_returns_invalid_input` across the validator's reachable defect shapes.
  - Files changed: `tests/test_cli_output_contract.py`.
  - Key changes: replaced the single `{rules: {}}` case with four ids — `empty_doc`, `rules_missing`, `rules_empty`, `threshold_missing` — all asserting the same contract outcome (exit 2 / `fix_input` / `rules.optionality_mismatch.weight_threshold` in `input_error`).
  - Effect: a refactor of `_validate_check_policy` cannot silently let one incomplete shape pass while another fails.
- Discovery during strengthening: the `optionality_mismatch` typed as a non-dict shape never reaches `_validate_check_policy` because the policy schema rejects it first. That shape was removed from the parametrize and the validator's `isinstance(optionality, dict)` branch documented as a defensive guard rather than an actively reached path. The new docstring records this explicitly so future readers do not expect the schema-rejected shape to flow through the validator.
- Updated HANDOFF Verification counts to reflect the +3 parametrized cases (160 → 163; CLI contract 45 → 48).

### Verification

- Focused CLI + fixture suite: `python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed (56 tests).
- Full suite: `python3 -m pytest -q` passed (163 tests).
- Collection check: `python3 -m pytest --collect-only -q` reports 48 CLI contract, 8 fixture, 12 model, and 95 rule tests.
- Parametrize enumeration: `pytest --collect-only -k "policy_missing_rule_three"` confirms 4 test ids.

## Plan v1.21 — Contract Gap Closure & Verifier Discipline Note

### Goals

- Land the two follow-up items the owner accepted after reviewing the policy completeness verification's strengthening report:
  1. Plan §8: name policy schema-validation failure as a `fix_input` recovery source so the v1.20 strengthening's "two paths converge on the same envelope" finding sits inside the contract instead of being a verifier-side observation.
  2. HANDOFF: record the verifier discipline lesson (probes claiming branch coverage must distinguish paths by error message, not only by exit code / `next_action`) so future verifiers do not repeat the imprecise probe attribution.

### Completed Work

- Plan v1.21.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: §8 905-911 policy completeness paragraph gains one sentence specifying that policy schema-validation failures (e.g. `rules.optionality_mismatch` typed as non-dict) are part of the same `fix_input` recovery surface as a missing required field. §15 adds v1.21 changelog entry tagged as no-code-change contract clarification.
  - Effect: caller agents reading the contract see a single recovery instruction ("policy is not in a usable shape → `fix_input`") regardless of which internal validator raised it, matching the actual envelope behaviour.
- HANDOFF verifier discipline note.
  - Files changed: `HANDOFF.md`.
  - Key changes: added a sibling paragraph to the existing "Test-surface lessons" section that records the v1.20→v1.21 finding directly. Names the exact failure mode (probing with only exit code / `next_action` while two code paths converge on the same envelope) and the operating fix (include the rejection message or a path-attributing assertion).
  - Effect: the lesson lives next to the existing envelope-vs-findings.json discipline note, so future verifiers see both at the start of work without having to grep the verification archive.
- CHANGELOG row added for v1.21.

### Decisions

- **Owner decision (2026-05-28)**: keep the verifier discipline note in HANDOFF rather than in personal memory; it should travel with the project, not the verifier instance. `CLAUDE.md` change deferred — the operating rule is small enough that HANDOFF placement is sufficient and avoids over-promoting a single instance lesson into project-wide policy.
- No code change in this slice. The `_validate_check_policy` `isinstance(optionality, dict)` branch is left in place as documented defense-in-depth against a future policy schema relaxation; removing it would discard a guard that costs nothing today.

### Verification

- `python3 -m pytest -q` still passes 163 tests after the documentation-only change (no behavior change expected).
- `git diff --check` clean.

## Current Spec Version Reference Alignment

### Goals

- Start the next handoff-directed work by checking whether the project has a clear spec-precedence tree and whether current-state docs agree on the active implementation plan version.
- Fix only stale "current version" references before deeper Phase 1/2 work, leaving historical v1.20 references intact.

### Completed Work

- Aligned current-state documentation to plan v1.21.
  - Files changed: `HANDOFF.md`, `README.md`, this work log.
  - Key changes: updated the HANDOFF canonical specification line, HANDOFF project-structure entry, HANDOFF sequencing rationale, and README document table from current v1.20 wording to current v1.21 wording.
  - Effect: new workers see a single current implementation source of truth: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.21, followed by ideation v2.2.

### Issues Found

- Problem: `HANDOFF.md` opened by saying the implementation plan is v1.21, but later current-state entries still named v1.20; README also listed the implementation plan as current v1.20.
  Cause: the v1.21 documentation-only clarification updated the plan/changelog/HANDOFF lesson note, but not every current-version reference.
  Resolution: updated only current-version statements to v1.21 and left historical v1.20 changelog, verification, and policy-completeness context untouched.
  Outcome: spec precedence is internally consistent before Phase 1/2 entry.

### Decisions

- No new implementation direction was chosen. Phase 1 still needs authorized real assignment materials before a manual smoke can proceed, and Phase 2 still has unresolved runner/compacting policy decisions.

### Next Steps

1. If authorized real assignment/spec/rubric materials are available, run Phase 1 manual smoke with non-public content kept out of git unless explicitly anonymized.
2. Otherwise, resolve the Phase 2 open decisions before implementing `extract`, `compact`, or `verify`.

### Verification

- Current-version stale-reference grep: `rg -n "현재 v1\\.20|Canonical specification.*v1\\.20|implementation source of truth \\(v1\\.20\\)|Plan v1\\.20 now supplies" README.md HANDOFF.md docs/daily_logs/2026-05-28/work_log.md` returned no matches.
- Diff hygiene: `git diff --check` passed.

## Cross-Project CLI Invocation Check

### Goals

- Confirm whether the harness can be invoked while working from a different project directory, before deciding whether Phase 1 real-assignment smoke must wait for more implementation work.

### Completed Work

- Checked CLI availability from outside the repository.
  - Files changed: `HANDOFF.md`, this work log.
  - Key changes: recorded the two currently working cross-project invocation forms: `docker compose -f /workspace/assessment_poc/docker-compose.yml run --rm harness ...` and `PYTHONPATH=/workspace/assessment_poc/src python3 -m assessment_harness.cli ...`.
  - Effect: the owner can switch to another project and run the Phase 0 CLI during ongoing work without waiting for Phase 2.

### Issues Found

- Problem: the bare `assessment-harness` command is not on PATH, and `python3 -m assessment_harness.cli` from `/tmp` cannot import the package without `PYTHONPATH`.
  Cause: the project has a console-script entry point in `pyproject.toml`, but the package is not installed in the active environment.
  Resolution: verified Docker and explicit `PYTHONPATH` invocation forms instead of assuming the script exists globally.
  Outcome: cross-project invocation is possible today, but not via the bare command unless the package is installed later.

### Decisions

- No Phase 2 implementation is required just to run Phase 0 checks from another project. Use absolute paths for input/output artifacts when invoking from outside this repository.

### Next Steps

1. Continue implementation/documentation work in this repository today.
2. When ready to smoke a real assignment, run the existing Phase 0 CLI from that project via Docker `-f` or explicit `PYTHONPATH`, keeping non-public source files out of this repository unless anonymized.

### Verification

- `command -v assessment-harness` returned no executable.
- From `/tmp`, `python3 -m assessment_harness.cli --output json schema --command check` failed with `ModuleNotFoundError`, confirming no ambient install.
- From `/tmp`, `PYTHONPATH=/workspace/assessment_poc/src python3 -m assessment_harness.cli --output json schema --command check` returned `status=success`.
- From `/tmp`, `docker compose -f /workspace/assessment_poc/docker-compose.yml run --rm harness --output json schema --command check` returned `status=success`.

## Phase 2 Contract Schema Foundation

### Goals

- Continue implementation work without entering unresolved Phase 2 decisions such as runner credentials, identity-basis algorithm policy, run-count behavior, or trace retention.
- Add only the schema surfaces already fixed in the canonical plan: canonical ID lineage (`id_map`) and read-only semantic verifier proposals (`semantic_verifications`).

### Completed Work

- Added and registered the Phase 2 foundation schemas.
  - Files changed: `schemas/id_map.schema.json`, `schemas/semantic_verifications.schema.json`, `src/assessment_harness/schemas.py`.
  - Key changes: `id_map` validates canonical IDs, entity type, and at least one `{run_id, local_id}` reference; `semantic_verifications` validates trace-link proposal entries with verifier-only statuses (`agent_supported`, `agent_rejected`, `agent_uncertain`), source refs, support, and variants.
  - Effect: later `compact` and `verify` implementations have contract validation targets without silently choosing runner or compacting behavior today.
- Added schema regression tests.
  - Files changed: `tests/test_models.py`.
  - Key changes: locked schema registration and plan-example validation for both new schemas; added rejection guards for empty `run_refs` and human final statuses appearing as verifier proposals.
  - Effect: schema drift around ID lineage traceability and verifier/final-review status separation now fails tests.
- Updated current-state docs.
  - Files changed: `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: schema count updated from ten to twelve and the new Phase 2 contract foundation is recorded as a milestone.
  - Effect: handoff no longer understates the public contract surface.

### Issues Found

- Problem: the implementation plan listed `semantic_verifications.schema.json` and `id_map.schema.json` as planned schema files, and §5.0/§5.3.1 already defined their core shape, but the repository schema registry did not expose them.
  Cause: Phase 0 focused on deterministic validation and final-review/gate surfaces; these Phase 2-adjacent schemas had stayed as plan-only contracts.
  Resolution: added schemas for the already-specified structures and registered them in `SCHEMA_FILES`.
  Outcome: future compact/verifier work can validate these artifacts through the same `validate()` helper used by existing contracts.

### Decisions

- This slice deliberately does not implement `compact`, `verify`, runner orchestration, queue composition, or an identity-basis algorithm. It only codifies the existing data contracts.
- `semantic_verifications.status_proposal` is restricted to verifier-agent proposal statuses. Human statuses remain final-review/gate territory and are rejected by the schema.

### Next Steps

1. Add `compact` only after choosing or explicitly adopting the identity-basis algorithm behavior for Phase 2.
2. Add `verify` only after runner credential/tool-side-effect and read-only verifier boundaries are settled.

### Verification

- Focused model/schema tests: `python3 -m pytest tests/test_models.py -q` passed (14 tests).
- Focused existing schema contract smoke: `python3 -m pytest tests/test_cli_output_contract.py::test_schema_command_returns_check_contract -q` passed.
- Full suite: `python3 -m pytest -q` passed (165 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 48 CLI contract, 8 fixture, 14 model, and 95 rule tests.
- Stale schema-count grep: `rg -n "ten JSON Schemas|10 JSON Schemas|ten schemas|10 schemas" README.md HANDOFF.md CHANGELOG.md docs/implementation_plan_assessment_harness_poc_v1.md src tests` returned no matches.
- Diff hygiene: `git diff --check` passed.

## Plan v1.22 — Trace Link ID Lineage Clarification

### Goals

- Resolve the conditional verification finding against the Phase 2 contract schema foundation.
- Make the `id_map.entity_type: trace_link` contract explicit rather than leaving it as schema-permitted but plan-silent behavior.

### Completed Work

- Promoted the plan to v1.22.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: §5.0 now distinguishes dependent trace-link references (`rubric_id` / `spec_ids`, remapped through spec/rubric item `id_map`) from trace link entry identity (the compacted relationship artifact itself, with `support` / `identity_basis` / `variants`). §15 records the v1.22 clarification.
  - Effect: `id_map.entity_type` including `trace_link` is now inside the canonical contract.
- Updated current-state records.
  - Files changed: `HANDOFF.md`, `README.md`, `CHANGELOG.md`, this work log.
  - Key changes: bumped current plan references to v1.22 and recorded the owner decision that trace link entries keep canonical ID lineage separately from their dependent item references.
  - Effect: future workers do not have to infer whether the schema should be narrowed or the plan should be expanded.

### Issues Found

- Problem: `id_map.schema.json` allowed `trace_link`, but plan v1.21 §5.0 only explicitly described spec/rubric item canonical IDs and trace-link reference remapping.
  Cause: the schema treated trace links as compacted entries, matching §5.3/§5.7 review-target language, but §5.0 did not state that lineage boundary directly.
  Resolution: owner chose explicit plan clarification rather than narrowing the enum; v1.22 now states both halves of the model.
  Outcome: spec, schema, and intended compacting model agree.

### Decisions

- **Owner decision (2026-05-28)**: keep `trace_link` in `id_map.entity_type`. Internal trace-link references follow spec/rubric item remapping, while the relationship entry itself also has canonical identity because compacting/review must be able to target the trace link as a first-class artifact.

### Next Steps

1. Commit and push the current documentation/schema/test batch.
2. Defer `compact` implementation until the remaining Phase 2 runner/identity-basis decisions are ready to be encoded.

### Verification

- Focused model/schema tests: `python3 -m pytest tests/test_models.py -q` passed (14 tests).
- Full suite: `python3 -m pytest -q` passed (165 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 48 CLI contract, 8 fixture, 14 model, and 95 rule tests.
- Current-version stale-reference grep: `rg -n "현재 v1\\.21|Implementation plan is at v1\\.21|Canonical specification.*v1\\.21|implementation source of truth \\(v1\\.21\\)" README.md HANDOFF.md docs/daily_logs/2026-05-28/work_log.md` returned no current-state matches.
- Diff hygiene: `git diff --check` passed.

## AgentRunner Protocol Foundation

### Goals

- Start Phase 2 runner work at the smallest already-specified boundary.
- Prove runner portability through a protocol plus deterministic mock runner without choosing SDK credentials, tool side effects, orchestration, compacting, or trace retention policy.

### Completed Work

- Added the framework-neutral runner boundary.
  - Files changed: `src/assessment_harness/agent_runners/__init__.py`, `src/assessment_harness/agent_runners/base.py`.
  - Key changes: introduced `AgentRunResult` and runtime-checkable `AgentRunner` protocol with the plan-specified `run(spec_path, rubric_path, tools, max_turns, policy)` signature.
  - Effect: future Claude/Codex/Gemini or verifier runners can target one local protocol instead of leaking SDK-specific shapes into orchestration code.
- Added deterministic mock fixture replay.
  - Files changed: `src/assessment_harness/agent_runners/mock.py`.
  - Key changes: `MockFixtureRunner` loads fixture `spec_items.yaml`, `rubric_items.yaml`, `trace_links.yaml`, plus optional `source_manifest.yaml` and `policy.yaml`; returns append-only audit/raw trace placeholders through `AgentRunResult`.
  - Effect: protocol contract tests can run without network credentials or a real SDK.
- Added contract tests and current-state docs.
  - Files changed: `tests/test_agent_runner_contract.py`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: tests assert the mock satisfies `AgentRunner`, replays schema-valid fixture artifacts, and returns trace metadata; HANDOFF now separates the live protocol/mock foundation from still-pending real runner/orchestrator work.
  - Effect: the first Phase 2 runner surface is testable while the unresolved implementation decisions remain explicit.

### Issues Found

- Problem: Phase 2 listed a mock runner contract test as a completion criterion, but the repository had no runner protocol surface to test.
  Cause: Phase 0 deliberately held `agent_runners/` out of scope until deterministic validation was stable.
  Resolution: implemented only the protocol and fixture replay mock runner, leaving SDK/tool/orchestrator choices untouched.
  Outcome: runner portability now has a concrete contract test without entering unresolved credential or tool-policy decisions.

### Decisions

- No new owner decision was needed for this slice: plan §7 and §9 already specify the `AgentRunner` protocol role and mock runner purpose. The mock remains test-only and is not a real assessment extraction path.

### Next Steps

1. Decide the remaining Phase 2 runner/tool policies before adding real SDK runners or orchestration.
2. Implement compacting only after identity-basis behavior is ready to encode.

### Verification

- Focused runner contract tests: `python3 -m pytest tests/test_agent_runner_contract.py -q` passed (2 tests).
- Syntax check: `python3 -m py_compile src/assessment_harness/agent_runners/base.py src/assessment_harness/agent_runners/mock.py src/assessment_harness/agent_runners/__init__.py` passed.
- Full suite: `python3 -m pytest -q` passed (167 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 2 agent-runner contract, 48 CLI contract, 8 fixture, 14 model, and 95 rule tests.
- Diff hygiene: `git diff --check` passed.

## AgentRunner Protocol Conditional-Pass Follow-Up

### Goals

- Address the nonblocking verifier finding that `AgentRunResult.status` duplicated `finish_reason` without a canonical plan contract.
- Keep the protocol foundation minimal until candidate shape, recovery behavior, and trace schema are promoted in their own slices.

### Completed Work

- Removed the speculative `status` field from the runner result contract.
  - Files changed: `src/assessment_harness/agent_runners/base.py`, `src/assessment_harness/agent_runners/mock.py`, `tests/test_agent_runner_contract.py`.
  - Key changes: `AgentRunResult` now records `run_id`, `runner_name`, `finish_reason`, artifacts, audit trace, raw trace, and optional error message; tests assert `finish_reason` only.
  - Effect: the protocol matches plan §9's current runner completion vocabulary without inventing a second status channel.

### Issues Found

- Problem: `AgentRunResult.status` was not named in the plan; plan §9 names `finish_reason`, while plan §5.4's `integrity_status` belongs to candidate artifact validation rather than runner result metadata.
  Cause: the first protocol slice overgeneralized the result shape.
  Resolution: removed `status` instead of promoting it into the plan.
  Outcome: no spec-silent runner status field remains.

### Decisions

- Candidate-shaped mock artifacts, recovery-policy simulation, and `agent_trace.schema.json` are still deferred. They need their own contract read because they affect candidate generation and trace retention surfaces, not just the protocol type boundary.

### Next Steps

1. Add candidate artifact schemas or fixtures before requiring mock output to match candidate shape.
2. Add runner failure/recovery tests when `blocked_by_runner_error` and trace finish-reason behavior are implemented.
3. Add `agent_trace.schema.json` in a separate trace-contract slice.

### Verification

- Focused runner contract tests: `python3 -m pytest tests/test_agent_runner_contract.py -q` passed (2 tests).
- Full suite: `python3 -m pytest -q` passed (167 tests).
- Status cleanup grep: `rg -n "result\\.status|status=\\\"complete\\\"|status, and" src tests HANDOFF.md` returned no matches.
- Diff hygiene: `git diff --check` passed.
