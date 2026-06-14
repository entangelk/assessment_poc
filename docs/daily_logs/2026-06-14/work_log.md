# Work Log - 2026-06-14

## Complex sample: DeskHive maintenance assignment

### Goals

- Exercise the full harness workflow on a **complex** assignment format, not just
  the flat single-tool sample under `/workspace/assessment_spec_harness_sample`.
- Use the real maintenance/hand-off assignment at
  `/workspace/reference_assignment` (the reference assignment) as the complexity
  reference, but produce a fully synthetic assignment — no real company/applicant
  data (per `docs/guidelines/sample_assignment_guidelines.md`).
- Confirm the `deterministic_extraction` runner and every downstream stage still
  behave when the assignment is multi-phase with required/optional/bonus mixing.

### Completed work

- Created a new sample repo `/workspace/deskhive_assessment_sample` (git
  initialized, one commit).
  - Files: `sample_assignment/spec.md`, `sample_assignment/rubric.md`,
    `sample_assignment/notes.md` (Korean human context), `README.md`,
    `.gitignore`.
  - Domain (owner decision): synthetic DeskHive co-working membership PoC, chosen
    to mirror the reference assignment's membership/freeze/pass/matching/analytics mechanics
    without copying the real assignment.
  - Structure: Phase 0–4 (environment / 5-defect diagnosis B1–B5 / verification /
    optional dashboard / CTO report), boundaries, acceptance criteria.
  - English body so the runner literals (`Traceable spec quote:`, `(N points)`,
    `Bonus`, `Qualitative`) parse; Korean rationale kept in `notes.md` only.
- Seeded realistic spec↔rubric signals (owner decision: "현실적 + 핵심 신호",
  not an exhaustive trap puzzle):
  - R5 host recommendation → `possible_orphan_scored_rubric_item` (quote not
    verbatim in spec).
  - R8 dashboard panel → `optionality_mismatch` (optional "may" spec scored at
    weight 10 = threshold).
  - RB1 AI usage log → `uncovered_must_spec_item` + `mandatory_spec_bonus_only_traced`
    + `bonus_grades_mandatory_only` (a required `must` spec graded as bonus only).
  - R7 + RB2 CTO report → `double_scored_spec` (same spec scored and bonus-traced).
- Ran the full workflow from the `assessment_poc` checkout against the new sample
  (artifacts under `work/deskhive_run/`, which is gitignored):
  `extract` (`deterministic_extraction`, valid_run_count=1) → `compact` →
  `verify` (mock_fixture, semantic pending) → `check` → `report` → `review` →
  `gate` → `materialize-review`.
  - Effect: end-to-end success on a complex format, parallel to the prior
    simple-sample proof but with a much richer finding set.

### Issues found

- `verify` does not accept `--fixture-dir` (only `extract` does). Re-ran `verify`
  without it; semantic stays pending in Phase 0, which is the expected behavior.
  No code change.
- Extra `bonus_grades_mandatory_only` on R10 (RB2): RB2 traces only the `must`
  CTO-report spec, so the rule firing is logically correct, not a defect — RB2 is
  a bonus grading already-required work. Recorded here so it is not mistaken for a
  miscount.

### Verification (this run)

- `check` envelope: `status=provisional_findings`, `blocking_count=0`,
  `provisional_high_count=3`, `provisional_medium_count=11` (14 findings total).
- Finding types observed: 7× `unconfirmed_trace_coverage`, 1×
  `possible_orphan_scored_rubric_item`, 1× `uncovered_must_spec_item`, 1×
  `optionality_mismatch`, 1× `double_scored_spec`, 2× `bonus_grades_mandatory_only`,
  1× `mandatory_spec_bonus_only_traced` — exercises Rules 1, 2, 3, L1, L5, L6.
- `gate` on the unedited hold draft: `status=pending_review`, exit 0,
  `pending_decision_count=16` (expected; a human edits the draft before a verdict).

### Decisions

- This sample is a wiring/grounding proof on a complex synthetic assignment, the
  same as the prior simple-sample run — it is NOT live-LLM extraction. The
  `deterministic_extraction` runner derives candidates from the rubric's declared
  `Traceable spec quote` hints; real SDK runners remain deferred.
- **Sample location (owner decision, 2026-06-14):** manage the complex sample
  **inside the repo** so the published portfolio is self-contained (clone one
  repo → run one command → see a realistic review). Initially created as a
  sibling repo `/workspace/deskhive_assessment_sample`; relocated to
  `examples/deskhive_assignment/` (`spec.md`, `rubric.md`, `notes.md`, `README.md`)
  and the sibling repo was deleted (single source of truth — no duplicate copy).
  - `examples/` is distinct from `fixtures/` by purpose: `fixtures/` holds
    pre-extracted per-rule YAML for unit tests; `examples/` holds a raw assignment
    a reader runs end-to-end. Only `deskhive` was brought in;
    `assessment_spec_harness_sample` stays external as the wiring smoke.
  - Still subject to the existing deferred publication-review decision
    (2026-06-07): in-repo co-location is not publication; freeze-time review still
    applies before public release. Both samples are fully synthetic, so risk is low.
- Re-ran the full workflow from the new in-repo path (`examples/deskhive_assignment`);
  `check` reproduced `provisional_findings`, high=3 / medium=11, blocking=0 —
  identical to the pre-move run, confirming the path change broke nothing.

### Next steps

- When a live SDK runner lands, re-run this sample to compare deterministic vs
  real extraction on the same complex input.
