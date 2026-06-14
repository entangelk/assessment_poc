# Pulse — Service Metrics Rollup CLI

## Overview

Build a small command-line tool named `pulse` that reads a stream of service
request events and prints a per-service metrics summary. This is a greenfield
build: there is no starter code. The task is deliberately open about *how* you
structure the aggregation — we care about your design choices and how you justify
them as much as about the output.

Each input event is one line with four comma-separated fields:

```text
timestamp,service,latency_ms,status
```

Example input:

```text
2026-03-01T10:00:00Z,checkout,42,200
2026-03-01T10:00:01Z,checkout,510,500
2026-03-01T10:00:02Z,search,18,200
2026-03-01T10:00:02Z,,,
2026-03-01T10:00:03Z,search,27,200
```

A `status` of 500 or above counts as an error.

## Deliverables

Submit your source code, automated tests, and a short design note. The tool must
run locally without any network connection or paid service. Use Go.

## Requirements

### 1. Input

The tool must read events from a file path or from standard input. A reviewer
should be able to pass a file as the first argument, or pipe events on stdin.

### 2. Core aggregation

The tool must report, per service, the event count and the error rate. The error
rate is the fraction of that service's events whose status is 500 or above.

The tool must report the p95 latency for each service. You may choose how to
compute the percentile (nearest-rank, interpolation, etc.); document the method
you chose in the design note.

### 3. Malformed input

Real logs contain junk. The tool must not crash when a line is malformed. A
malformed line is one that does not have four fields, or whose latency or status
is not an integer. The tool should skip malformed lines, continue processing, and
report the number of skipped lines on standard error.

### 4. Output

The tool should print a readable text table with one row per service, sorted by
service name. The tool may emit the summary as JSON in addition to the text
table. The output format is selected by a flag.

### 5. Optional windowing

The tool may group results into fixed time windows when a window size is given.
This is an optional enhancement; a submission that always aggregates over the
whole input is complete.

### 6. Tests and design note

The tool must ship automated tests that run without a network connection. The
submission must include a short written explanation of the main design tradeoffs.

### 7. Boundaries

The tool must not modify its input. The tool must not require a network
connection or a paid service. The tool does not need to support streaming input
larger than memory, multiple input files, or live tailing.

## Acceptance criteria

A reviewer should be able to build the tool, run it against the example input
above, and see per-service rows for `checkout` and `search` with a count, an
error rate, and a p95 latency, while the malformed blank line is skipped and
counted on standard error. The test suite should run to green offline.
