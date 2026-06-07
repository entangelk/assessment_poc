# Work Log - 2026-06-07

## Extract Source Snapshot and Runner Decisions

### Goals

- Read `HANDOFF.md` and the latest daily logs to identify the next safe task.
- Record the owner decisions needed before real SDK runner work.
- Adopt the tool side-effect policy without adding write/propose tools prematurely.
- Implement `extract` source snapshot auto-generation without changing the existing explicit `--source-manifest` path.

### Completed work

- Reviewed `HANDOFF.md`, `docs/daily_logs/2026-06-04/work_log.md`, and the latest verification records.
  - Key finding: the `materialize-review` and read-only framework tool residuals from 2026-06-04 were closed by follow-up work and independent re-verification.
  - Effect: there was no remaining verification-blocking defect from those slices.
- Added `docs/sdk_runner_decisions.md`.
  - Key change: records the pending real SDK runner decisions: first SDK surface, credential delivery, sample assignment, raw trace retention/redaction, runner limits, SDK tool registration, and live-output contract.
  - Effect: real SDK runner work can start later from a checklist instead of reopening the whole design space.
- Updated `docs/implementation_plan_assessment_harness_poc_v1.md` to v1.32.
  - Key change: records the owner decision to keep framework tools read-only and have runners collect proposed outputs before emitting candidate artifacts.
  - Key change: records the owner decision to defer publication mirrors until all work reaches publication freeze.
  - Key change: defines the `extract` source snapshot auto-generation contract.
  - Effect: the code change has a canonical contract instead of an implicit path convention.
- Implemented `extract` source snapshot auto-generation in `src/assessment_harness/cli.py`.
  - Key change: when `--source-manifest` is omitted, `extract` writes `source_snapshot/spec.md`, `source_snapshot/rubric.md`, and `source_snapshot/manifest.yaml` beside `--out-dir`.
  - Key change: the generated manifest uses `DOC_SPEC` and `DOC_RUBRIC`, includes sha256 hashes, and is validated before use.
  - Key change: explicit `--source-manifest` still takes precedence and suppresses auto-generation.
  - Effect: `extract --out-dir work/runs` now produces the source snapshot expected by later `verify --source-manifest work/source_snapshot/manifest.yaml`.
- Added focused CLI regressions in `tests/test_cli_output_contract.py`.
  - Key change: locks generated snapshot path, manifest schema validity, sha256 values, copied source contents, and explicit-manifest precedence.
  - Effect: future changes cannot silently fall back to fixture manifests or overwrite explicit manifest intent.
- Updated `HANDOFF.md`, `README.md`, `docs/evaluation.md`, and `CHANGELOG.md`.
  - Effect: project status, plan version, document map, changelog, and measured test counts reflect v1.32 and the 279-test suite.

### Issues found

- Problem: `extract` source snapshot generation was an intended direction but did not have a concrete path/output contract.
  Cause: previous plan text established that source manifests are mandatory for downstream grounding, but left production snapshot placement implicit.
  Resolution: defined the sibling `source_snapshot/` convention in plan v1.32 and implemented it.
  Outcome: the CLI now produces the manifest path later stages already expect.
- Problem: real SDK runner implementation still depends on owner decisions.
  Cause: credentials, sample assignment permission, raw trace retention/redaction, and runner limits affect security and publication scope.
  Resolution: documented the decision checklist in `docs/sdk_runner_decisions.md`.
  Outcome: no SDK credential or live-run behavior was guessed.

### Decisions

- **Tool side-effect policy:** keep framework tools read-only. Propose/write behavior must be runner-collected and emitted as candidate artifacts at run end, not written directly to candidate files.
- **Publication freeze:** bilingual mirrors and README EN/KO flip stay deferred until all planned development work reaches publication freeze.
- **Extract source snapshot:** path convention is implementation-owned, not a separate owner decision. Use sibling `source_snapshot/` beside `--out-dir`; explicit `--source-manifest` remains authoritative.
- **SDK runner:** defer implementation until credential delivery, runnable sample assignment, raw trace retention/redaction, and runner limits are decided.

### Next steps

1. Decide the real SDK runner checklist in `docs/sdk_runner_decisions.md`.
2. Implement the first live SDK runner only after sample assignment and credential delivery are available.
3. Implement runner-collected propose behavior only when the runner output shape is specified.
4. At publication freeze, recompute `docs/evaluation.md` again and perform the deferred bilingual mirrors.

### Verification

- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q -k "extract"` -> 8 passed.
- `python3 -m py_compile src/assessment_harness/cli.py` -> passed.
- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q` -> 110 passed.
- `PYTHONPATH=src python3 -m pytest --collect-only -q` -> 279 tests collected: agent-runner 27, CLI 110, compacting 7, fixtures 8, models 22, rules 95, tools 10.
- `PYTHONPATH=src python3 -m pytest -q` -> 279 passed.
- Fixture smoke runs for `docs/evaluation.md` were re-run and still match the table:
  - `clean_assignment` -> `provisional_findings`, exit `0`, `(high=0, medium=2, informational=0)`, `review_queue_count=0`.
  - `orphan_scored_rubric` -> `provisional_findings`, exit `0`, `(high=1, medium=1, informational=1)`, `review_queue_count=0`.
  - `uncovered_must_spec` -> `provisional_findings`, exit `0`, `(high=1, medium=5, informational=0)`, `review_queue_count=1`.
  - `optionality_mismatch` -> `provisional_findings`, exit `0`, `(high=2, medium=1, informational=0)`, `review_queue_count=0`.
  - `bonus_misuse` -> `provisional_findings`, exit `0`, `(high=1, medium=5, informational=1)`, `review_queue_count=2`.
  - `reference_integrity` -> `invalid_input`, exit `2`, `high_integrity_count=9`.
- Input guard smoke runs still match `docs/evaluation.md`: no `--source-manifest` -> `provide_source_manifest`; no `--policy` -> `provide_policy`; both omitted -> `provide_source_manifest`.

## Extract Source Snapshot Recheck

### Goals

- Re-check the independent verification record for `extract` source snapshot auto-generation.
- Confirm whether the four recorded issues are blocking defects or non-blocking observations.

### Completed work

- Added `docs/verifications/2026-06-07/extract_source_snapshot_auto_generation_recheck.md`.
  - Key change: independently re-read the prior verification record, plan v1.32, implementation, tests, and schema.
  - Key change: re-ran the reported test commands and additional smoke probes for relative `--out-dir` and mismatched `--spec` vs `--fixture-dir`.
  - Effect: the prior verification's pass verdict is independently confirmed.

### Issues found

- Problem: the generated `project_id` is weak metadata (`source` for fixture-style paths).
  Cause: `extract` derives it from `Path(args.spec).parent.name`.
  Resolution: left unchanged because current code does not consume `SourceSnapshot.project_id`.
  Outcome: recorded as a non-blocking future improvement candidate.

### Decisions

- No production code change was made during the recheck. The four recorded observations remain non-blocking.

### Next steps

1. Commit/publish only when the owner asks.
2. Consider improving generated `project_id` only if it becomes user-facing or semantically consumed.

### Verification

- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q -k "extract"` -> 8 passed.
- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q` -> 110 passed.
- `PYTHONPATH=src python3 -m pytest --collect-only -q` -> 279 tests collected.
- `PYTHONPATH=src python3 -m pytest -q` -> 279 passed.
- Independent smokes confirmed generated snapshot sha256 values, relative `--out-dir runs` behavior, and mismatched `--spec` vs `--fixture-dir` invalid-run isolation.
- `git diff --check` -> clean.

## Sample Assignment Creation Guide

### Goals

- Add a document that an AI agent can read to create a PoC test assignment sample.
- Keep the immediate goal focused on making the PoC run.
- Defer permission/anonymization/publication review until later.

### Completed work

- Added `docs/sample_assignment_guidelines.md`.
  - Key change: defines the expected `spec.md` / `rubric.md` outputs, recommended size, subject-matter constraints, spec/rubric structure, harness-friendly design mix, and a reusable prompt for sample generation.
  - Key change: states that permission, anonymization, and publication readiness are deferred until publication freeze.
  - Effect: a caller AI can create a synthetic/local sample without needing the owner to hand-author the first assignment.
- Updated `docs/sdk_runner_decisions.md`.
  - Key change: records that sample assignment creation can proceed from the new guide.
  - Key change: moves permission/anonymization review out of the immediate PoC execution gate and into the later publication-freeze gate.
  - Effect: the remaining live-run blockers are narrower: SDK surface, credential delivery, raw trace retention, runner limits, and output contract.
- Updated `README.md`.
  - Key change: added the sample assignment guide to the documentation map.
  - Effect: the next worker can discover the guide from the top-level docs map.

### Issues found

- Problem: "bring a sample assignment" was underspecified for an AI agent.
  Cause: the repo had an SDK runner decision checklist but no concrete guidance for producing a small harness-friendly assignment/rubric pair.
  Resolution: added a sample authoring guide with file outputs, content shape, and a prompt.
  Outcome: sample creation can proceed without blocking on publication-safe data selection.

### Decisions

- **PoC-first sample policy:** a synthetic/local sample is enough for the next PoC run.
- **Permission/anonymization deferred:** permission, anonymization, and publication review are intentionally deferred until publication freeze rather than blocking the first live-run sample.

### Next steps

1. Generate or bring a sample `spec.md` / `rubric.md` pair using `docs/sample_assignment_guidelines.md`.
2. Decide the first live SDK runner surface and credential delivery.
3. Keep generated samples private/local until publication review happens.

### Verification

- Documentation-only change.
- `git diff --check` -> clean.

## Deterministic Extraction Runner + First Full-Workflow Sample Run

### Goals

- Run the full harness workflow on the real sample under
  `/workspace/assessment_spec_harness_sample` instead of replaying fixtures.
- Add the smallest runner slice that makes that possible without faking a live
  SDK.

### Context / constraint

- The current environment has no `ANTHROPIC_API_KEY`, no `anthropic` /
  `claude_agent_sdk` install, and no egress to `api.anthropic.com`, so a real
  Claude Agent SDK runner cannot execute here.
- Owner decision (2026-06-07): prioritize executing the workflow now; make
  pragmatic placeholder choices and record them for later. Do the SDK work as a
  minimal slice and add a plan doc.

### Completed work

- Added `docs/sdk_runner_minimal_slice_plan.md`.
  - Records the environment constraint, the deterministic-runner design, and the
    placeholder decisions (runner identity, rubric-quote-derived spec items,
    `should`→`optional` mapping, `token_sequence`-only evidence, untouched
    runner limits/credentials) that must be revisited before a real SDK runner.
- Added `src/assessment_harness/agent_runners/deterministic.py`
  (`DeterministicExtractionRunner`, `name = "deterministic_extraction"`).
  - Parses the sample `rubric.md` headings and `Traceable spec quote: "..."`
    hints, locates each quote inside `spec.md` (whitespace-normalized minimal
    span), and emits fixture-shaped spec/rubric/trace candidate artifacts that
    are grounding-correct against the auto-generated source snapshot.
  - No LLM call, no network, no credentials. Same `AgentRunner` protocol as the
    future SDK runner.
- Wired `extract --runner deterministic_extraction` in `cli.py`
  (`_extract_runner` branch; per-pass run-id rewrite extended to the new
  runner). `--fixture-dir` is not required for this runner.
- Added a CLI regression in `tests/test_cli_output_contract.py`
  (`test_extract_deterministic_runner_generates_grounded_validated_candidates`):
  locks grounded→`validated` promotion (under-strict), scored/bonus/qualitative
  role classification, and that the no-quote qualitative item is NOT traced
  while scored/bonus items are (over-strict).

### Full-workflow run (sample)

Ran the whole pipeline on the sample (artifacts under `work/sample_run/`):

- `extract --runner deterministic_extraction` → `valid_run_count=1`,
  `invalid_run_count=0`; snapshot auto-generated at
  `work/sample_run/source_snapshot/manifest.yaml`.
- `compact` / `verify` (mock_fixture, no AI-judgement evidence) → exit 0.
- `check` → `provisional_findings`, 7 findings, `blocking_count=0`
  (5× `unconfirmed_trace_coverage` medium, 1× `possible_orphan_scored_rubric_item`
  high, 1× `optionality_mismatch` high).
- `report` / `review` / `materialize-review` → exit 0; `gate` →
  `pending_review` (all findings still held in the draft).

### Issues found

- Problem: `mock_fixture` cannot run the sample meaningfully — it replays the
  fixture's fixed candidates, which are not grounded in the sample spec, so every
  candidate isolates as `source_grounding_mismatch` (`valid_run_count=0`).
  Cause: `mock_fixture` is a wiring smoke, not a candidate generator (documented
  in `sample_assignment_guidelines.md`).
  Resolution: added the deterministic offline runner that derives grounded
  candidates from the sample itself.
  Outcome: the full workflow now completes on the sample.
- Observation: the `optionality_mismatch` high finding is partly an artifact of
  the runner's placeholder `should`→`optional` mapping (R5/R6 scored items trace
  `should`/deliverable quotes classified as `optional`), not purely the sample's
  design. Flagged in the plan doc as a revisit item.

### Decisions

- **Offline deterministic runner as the execution vehicle:** since a live SDK
  runner cannot run in this environment, execution-first is satisfied by a
  deterministic, grounding-correct runner behind the same `AgentRunner`
  protocol. Placeholder choices are recorded in
  `docs/sdk_runner_minimal_slice_plan.md` for later owner discussion.
- **Not presented as live extraction:** `deterministic_extraction` must not be
  described as live agent extraction in public/portfolio copy.
- **Runner testing via agentic environments (owner, 2026-06-07):** end-to-end
  runner testing is delegated to agentic environments (Claude Code / Codex acting
  as the runner over the harness CLI) instead of embedding a live SDK runner. So
  self-hosted SDK credentials / network integration are not pursued now, and the
  embedded-SDK decision items in `docs/sdk_runner_decisions.md` are
  de-prioritized. `deterministic_extraction` stays the offline/CI default.

### Next steps

1. Review the placeholder decisions in `docs/sdk_runner_minimal_slice_plan.md`
   (especially `requirement_level` mapping and spec-item provenance).
2. Run more sample assignments through the workflow and add more test samples.

### Verification

- `PYTHONPATH=src python3 -m pytest` → `280 passed`.
- `python3 -m py_compile src/assessment_harness/cli.py src/assessment_harness/agent_runners/deterministic.py` → OK.
- Full sample pipeline re-run end-to-end (artifacts under `work/sample_run/`).
