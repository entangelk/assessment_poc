# Example: Pulse — service-metrics CLI (Go, greenfield build)

A fully synthetic **greenfield build** assignment in **Go**, deliberately a
different shape from the other examples: not a flat single-tool CLI
([`assessment_spec_harness_sample`](../../../assessment_spec_harness_sample)) and
not a debugging hand-off ([`deskhive_assignment`](../deskhive_assignment)). It
exists to show the harness reviews assessment design regardless of language,
tech, or assignment archetype — the harness only ever reads `spec.md` + `rubric.md`.

This directory carries two layers:

1. The harness **input** — `spec.md` (candidate-facing) + `rubric.md`
   (evaluator-only). These two files are all the harness reads.
2. The **reference solution** under [`codebase/`](codebase) — a working Go module
   that implements the required behavior with tests, so a reviewer can confirm the
   assignment is buildable and the rubric is gradeable against real output. Unlike
   the DeskHive codebase (seeded bugs to find), this is a *correct* reference
   build. The harness does **not** consume it.

## Files

```text
spec.md      # candidate-facing assignment (greenfield Go build, 7 requirement groups)
rubric.md    # evaluator-only rubric (7 scored + 2 bonus + 1 qualitative)
notes.md     # human context (Korean): intent + seeded signals
codebase/    # Go reference solution (pulse CLI) with tests and sample I/O
```

## Seeded spec↔rubric signals

A deliberately **different finding mix** from DeskHive, to exercise branches the
other example does not:

| Rubric | Intended finding |
|---|---|
| R4 | `possible_orphan_scored_rubric_item` (Rule 1, high) — quote ("reject … exit nonzero") contradicts the spec, which says skip-and-continue |
| R5 | `optionality_mismatch` (Rule 3, high) — optional "may" windowing scored at weight 15 |
| RB1 | `orphan_bonus_rubric_item` (Rule 1, **informational**) — bonus rewards Prometheus output the spec never asks for |
| Q1 → S8 | `uncovered_must_spec_item` (Rule 2, medium) — "must not crash" is traced only by a *qualitative* note, no scored item |
| RB2 | *no finding* — a correctly-traced bonus ("may emit JSON"); shows the harness does not over-fire |
| scored items | `unconfirmed_trace_coverage` (Rule 1) — Phase 0 semantic still pending |

Latest run: 10 findings (high 2 / medium 7 / informational 1), `blocking_count=0`.

## The reference solution

```bash
cd codebase
go test ./...                        # parsing, aggregation, malformed input
go run . testdata/events.csv         # text table
go run . --json testdata/events.csv  # JSON == testdata/expected.json
```

> Note: this Go module was authored and reviewed but **not executed in the
> environment that produced this example** (no Go toolchain was available there).
> The harness signals above were verified by running the harness; the Go code
> ships with tests and committed expected output (`testdata/expected.json`) for a
> reviewer with Go to run. See [`codebase/README.md`](codebase/README.md).
