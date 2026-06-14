# Pulse — design note

A short record of the main design tradeoffs, as the assignment asks for.

## Percentile method

p95 latency uses the **nearest-rank** method: sort the latencies, take
`rank = ceil(0.95 * n)` (1-indexed, clamped), and return that element. Nearest
rank was chosen over linear interpolation because it always returns an observed
latency value, which is easier to explain to operators and has no ambiguity at
small sample sizes. The tradeoff is coarser resolution when `n` is small (with
two samples, p95 is just the larger one). The method lives in one place
(`internal/rollup.percentile`) so it can be swapped without touching callers.

## In-memory aggregation

All events are read into memory before aggregation. The spec explicitly states
the tool does not need to support input larger than memory, so a streaming
aggregator would be premature. Keeping everything in a slice keeps the parse and
rollup stages independent and trivially testable.

## Malformed input

`event.ParseLine` returns `(Event, ok bool)` instead of an error, because the
caller's policy is uniform: skip and count. A line is malformed when it does not
have four fields, has an empty service, or carries a non-integer latency/status.
The tool never aborts on bad input; the skipped count is reported on stderr so it
stays out of the machine-readable stdout.

## Intentionally not implemented (optional/out of scope)

- **Time-window rollups** are optional in the spec. The reference solution
  aggregates over the whole input; windowing is left as a candidate enhancement.
  If added, window boundaries should be derived by truncating each event's
  timestamp to the window size and bucketing per `(service, window)`.
- **Prometheus exposition format** is not part of the spec, so it is not
  implemented here. (The evaluator rubric mentions it as a bonus, but the spec
  never asks for it — see the parent `notes.md`.)
