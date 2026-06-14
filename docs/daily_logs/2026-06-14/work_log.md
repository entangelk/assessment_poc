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

## Runnable assignment codebase for the DeskHive example

### Goals

- Make the example verifiable, not just prose: a reviewer should be able to
  confirm that `spec.md`'s B1–B5 defect claims map to real code, the way a real
  assignment repo would let them.

### Completed work

- Added `examples/deskhive_assignment/codebase/` — a small runnable FastAPI
  back-office repo with the five defects actually present in code:
  - B1 `app/services/membership.py`: zero usage rate → previous dev "handled" it
    by returning `Infinity`.
  - B2 `app/services/membership.py`: frozen days computed (`_frozen_days`) but a
    handover TODO never adds them to the expiry.
  - B3 `app/services/passes.py`: free + paid passes summed into one `remaining`,
    losing the breakdown.
  - B4 `app/services/analytics.py`: counts by raw UTC month, no KST (+9)
    conversion.
  - B5 `app/services/matching.py`: always returns the lowest-id eligible host.
  - Support files: `app/models.py`, `app/seed.py` (pinned clock 2026-02-10,
    in-memory data, no DB/network), `app/main.py` (FastAPI endpoints),
    `scripts/show_symptoms.py` (stdlib-only reproduction), `docs/business_rules.md`,
    `docs/data_model.md`, `README.md` (candidate-facing, Korean), `requirements.txt`,
    `Dockerfile`, `docker-compose.yml`.
- Updated example `README.md` and `notes.md` to describe the two layers (harness
  input vs runnable codebase) and the defect→file map; the harness still consumes
  only `spec.md` + `rubric.md`.

### Issues found

- B1 first raised `ZeroDivisionError` (Python `float / 0.0` raises, unlike JS).
  Changed the seeded bug to the realistic "previous dev returned `float('inf')`",
  which matches the spec symptom "shows infinity" and the fix target "return a
  finite number".
- Over the HTTP layer, FastAPI's `jsonable_encoder` coerced `inf` → `null`. Added
  a plain-`json.dumps` response (`_json`) on the detail endpoint only so the wire
  shows `Infinity`, matching the reported symptom without changing the value.

### Verification (this run)

- `python3 codebase/scripts/show_symptoms.py` reproduces all five: B1 `inf`
  (Alice) vs `56.0` (Bob); B2 frozen=6 but expiry `2026-02-09` (un-extended);
  B3 `{remaining: 5}` (mixed); B4 reported `1` vs actual KST Feb joiners `2`;
  B5 5 calls → only `{H1}`.
- `fastapi.testclient` smoke on `app.main`: health ok; `GET /api/members/M1/detail`
  wire shows `"estimated_exhaustion_days": Infinity`; other endpoints match the
  script.
- `python3 -m py_compile` passes for all app/script files. `__pycache__` is
  gitignored.

## Third example: Pulse (Go greenfield build)

### Goals

- Cover a **different direction** of assignment than the prior two (both Python,
  both build-or-fix-a-service): a different language (Go) and a different
  archetype (greenfield build with design emphasis, not a debugging hand-off), to
  confirm the harness reviews assessment design regardless of tech/archetype.

### Completed work

- Added `examples/pulse_assignment/` — a synthetic greenfield Go CLI assignment
  (`pulse`: read service events → per-service count, error rate, p95 latency;
  malformed-line resilience; optional windowing; JSON bonus).
  - Harness input: `spec.md` (7 requirement groups) + `rubric.md` (7 scored +
    2 bonus + 1 qualitative) + `notes.md` + `README.md`.
  - `codebase/`: a working Go reference solution (`main.go`,
    `internal/event/`, `internal/rollup/`, table+JSON output, nearest-rank p95),
    `*_test.go` for parse/aggregate/malformed, `testdata/events.csv` +
    `testdata/expected.json`, `docs/design.md`, `go.mod`. Unlike DeskHive (seeded
    bugs), this is a *correct* reference build that demonstrates the assignment is
    buildable and the rubric gradeable.
- Seeded a deliberately **different finding mix** from DeskHive to widen rule
  coverage:
  - R4 → `possible_orphan_scored_rubric_item` (high): rubric quote
    ("reject … exit nonzero") contradicts the spec's skip-and-continue.
  - R5 → `optionality_mismatch` (high): optional "may" windowing scored at 15.
  - RB1 → `orphan_bonus_rubric_item` (**informational**): bonus rewards
    Prometheus output the spec never asks for. (New branch vs DeskHive.)
  - Q1 → `uncovered_must_spec_item` (medium) on S8 "must not crash": traced only
    by a *qualitative* note, no scored coverage. (Qualitative-only variant, new.)
  - RB2 → no finding: a correctly-traced "may emit JSON" bonus (over-fire guard).

### Issues found

- RB2's quote first failed to trace: it ended with a period while the spec
  sentence continued with a comma ("… text table, selected by a flag."). The
  whitespace-only normalizer treats `.` vs `,` as a real mismatch, so the bonus
  fell through to `orphan_bonus`. Split the spec sentence so the quote matches
  verbatim; RB2 now traces cleanly (intended over-fire guard restored).
- **Go toolchain is not installed in this environment**, so `go test` / `go run`
  could not be executed here. The Go reference solution was authored and reviewed
  but not run; `testdata/expected.json` and the tests are committed for a reviewer
  with Go. This limitation is stated in the example `README.md` and `notes.md`.

### Verification (this run)

- `check` envelope: `status=provisional_findings`, high=2 / medium=7 /
  informational=1, `blocking_count=0` (10 findings).
- Full chain exercised: `extract` (valid_run_count=1) → `compact` → `verify` →
  `check` → `report` → `review` → `gate` (`pending_review`, exit 0, 10 pending) →
  `materialize-review` (success). Artifacts under `work/pulse_run/` (gitignored).

### Next steps

- When a live SDK runner lands, re-run all three samples to compare deterministic
  vs real extraction on the same inputs.
- If a Go toolchain becomes available, run `go test ./...` on the Pulse reference
  solution to close the one unverified surface.

## PoC report: repeated verification of in-repo examples

### Goals

- Respond to the owner request to check whether the in-repo `examples/` samples
  are set up correctly and whether the project's own verification workflow
  produces correct, stable results.
- Run the official harness workflow three times and leave a durable Markdown
  result report at `report.md`.

### Completed work

- Added `report.md` at the repository root.
  - Summarizes the verification scope, exact workflow, three repeated runs,
    finding distributions, interpretation, and risks.
  - Records artifacts under `work/poc_report_runs/run{1,2,3}/...` (gitignored).
- Re-ran the full workflow three times for both in-repo examples:
  `extract --runner deterministic_extraction --runs 3` → `compact` → `verify`
  (`mock_fixture`, `--runs 3`) → `check` → `report` → `review` → `gate` →
  `materialize-review`.
  - DeskHive reproduced the same result all three times: `check`
    `provisional_findings`, high=3 / medium=11 / informational=0, 14 findings,
    Rule 0 diagnostics=0, `gate` `pending_review` with 14 pending decisions.
  - Pulse reproduced the same result all three times: `check`
    `provisional_findings`, high=2 / medium=7 / informational=1, 10 findings,
    Rule 0 diagnostics=0, `gate` `pending_review` with 10 pending decisions.
- Checked sample setup with two parallel read-only explorer agents:
  - DeskHive: confirmed B1-B5 map to real seeded defects and the seeded
    spec/rubric signals are coherent.
  - Pulse: confirmed the harness signals and Go reference solution mostly map to
    the spec, while flagging the existing Go-toolchain limitation and some public
    CLI test-surface gaps.

### Issues found

- This verification is still an offline wiring/grounding proof, not live LLM
  extraction. `deterministic_extraction` and `mock_fixture` are stand-ins; real
  SDK runners remain deferred.
- The semantic verifier produced no semantic proposals in this path, so
  `unconfirmed_trace_coverage` findings are expected and should not be read as
  final orphan decisions.
- DeskHive has a small documentation-alignment risk: the candidate spec asks for
  a finite B1 result, while codebase business rules mention `null` as an allowed
  no-usage representation. Treat `spec.md` as canonical unless the example docs
  are tightened later.
- Pulse cannot be executed end-to-end in this environment because `go` is not
  installed. `go version` failed with `command not found`, matching the caveat
  already stated in the sample docs.
- Pulse's reference tests do not fully lock public CLI surfaces such as
  file-vs-stdin equivalence, stderr skipped-count output, JSON expected-output
  matching, and text output shape.

### Verification (this run)

- `PYTHONPATH=src python3 -m assessment_harness.cli schema --command check --output json`
  returned the expected stable core and `check` informational fields.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider`
  passed.
- `python3 scripts/show_symptoms.py` from
  `examples/deskhive_assignment/codebase` reproduced all five intended symptoms:
  B1 `inf`, B2 unextended expiry, B3 combined pass balance, B4 UTC/KST count
  mismatch, B5 repeated `H1`.
- `go version` from `examples/pulse_assignment/codebase` failed because the Go
  toolchain is unavailable.

### Decisions

- The report frames the examples as validating the deterministic harness
  workflow across two assignment archetypes, not as validating live LLM
  extraction quality.
- The repeated run uses `--runs 3` inside each workflow repetition and repeats
  the whole workflow three times, so the result checks both multi-run artifact
  handling and repeatability of the generated findings.

### Next steps

- Before public release, decide whether to tighten the DeskHive B1 finite/null
  wording.
- When Go is available, run `go test ./...`, `go run . testdata/events.csv`, and
  `go run . --json testdata/events.csv` for the Pulse reference solution.
- When a real SDK runner lands, re-run `report.md`'s scenario to compare
  deterministic extraction against live LLM extraction.

## README cleanup for PoC report

### Goals

- Make the root README reflect the latest example verification result.
- Link the new `report.md` from the first-read path so readers can see the
  current PoC evidence without digging through logs.

### Completed work

- Updated `README.md` with a new "지금 무엇을 증명했나" section.
  - Summarizes DeskHive/Pulse example purpose and the stable 3-run result.
  - Links directly to `report.md`.
  - States the key limitation: deterministic extraction + mock semantic
    verification is not live LLM SDK runner validation.
- Added a quick-start subsection for the example PoC report and one concrete
  `deterministic_extraction` command.
- Updated the implementation-status table to distinguish completed in-repo
  deterministic example validation from the still-unimplemented live LLM SDK
  workflow.
- Added `report.md` to the documentation map and changed the Phase 0 report
  sample output path to `work/report.md` so it does not imply overwriting the root
  PoC report.

### Verification (this run)

- Re-read the changed README sections for link/flow consistency.
- `git diff --check` passed after the README edit.

### Next steps

- If the publication copy is later flipped to English-primary README, mirror this
  new PoC-report framing into the English canonical version and Korean mirror.
