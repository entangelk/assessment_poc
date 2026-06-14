# Pulse — reference solution

A small Go CLI that reads service request events and prints a per-service metrics
summary. This is the **reference solution** for the Pulse assignment: a working
implementation of the required behavior with tests, so a reviewer can confirm the
assignment is buildable and that the rubric is gradeable against real output.

> This is a fully synthetic example for the Assessment Spec Harness PoC, not a
> real submission.

## Build and run

```bash
go build -o pulse .

./pulse testdata/events.csv          # text table
./pulse --json testdata/events.csv   # JSON (matches testdata/expected.json)
cat testdata/events.csv | ./pulse    # stdin also works
```

Expected text table for `testdata/events.csv`:

```text
SERVICE       COUNT ERROR_RATE   P95_MS
checkout          2       0.50      510
search            2       0.00       27
```

with `skipped 1 malformed line(s)` on standard error (the `,,,` line).

## Test

```bash
go test ./...
```

Covers parsing (valid + five malformed shapes), aggregation (count, error rate,
nearest-rank p95, sort order), and the empty-input boundary.

## What is implemented

- Required: file/stdin input, per-service count and error rate, p95 latency,
  malformed-line skip-and-count (no crash), sorted text table, tests, design note
  (`docs/design.md`).
- Bonus (spec `may`): JSON output via `--json`.
- Optional, intentionally not implemented: time-window rollups — see
  [`docs/design.md`](docs/design.md) for the rationale.

## Layout

```text
main.go                       CLI: args, IO, table/JSON output
internal/event/event.go       line -> Event parsing
internal/rollup/rollup.go     per-service aggregation + percentile
testdata/                     sample input + expected JSON
docs/design.md                design tradeoffs note
```
