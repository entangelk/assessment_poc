# Pulse Assignment Rubric

Total score: 100 points, plus up to 10 bonus points. This rubric is for
evaluators only and is not shared with candidates.

## R1. Input handling (15 points)

Evidence expectations:

- The tool accepts a file path argument and also reads from standard input.
- Both paths produce the same aggregation for the same events.

Traceable spec quote: "The tool must read events from a file path or from standard input."

## R2. Count and error rate (15 points)

Evidence expectations:

- Per-service event counts are correct.
- Error rate counts status >= 500 and divides by that service's events.

Traceable spec quote: "The tool must report, per service, the event count and the error rate."

## R3. p95 latency (15 points)

Evidence expectations:

- A p95 latency is reported per service.
- The chosen percentile method is documented and applied consistently.

Traceable spec quote: "The tool must report the p95 latency for each service."

## R4. Malformed-line handling (15 points)

Evidence expectations:

- Malformed lines do not stop processing.
- The skipped-line count is surfaced to the operator.

Traceable spec quote: "The tool must reject malformed lines and exit with a nonzero status."

## R5. Time-window rollups (15 points)

Evidence expectations:

- Results can be grouped into fixed time windows.
- Window boundaries are applied consistently across services.

Traceable spec quote: "The tool may group results into fixed time windows when a window size is given."

## R6. Tests (15 points)

Evidence expectations:

- Automated tests cover parsing, aggregation, and malformed input.
- The suite runs locally with no network access.

Traceable spec quote: "The tool must ship automated tests that run without a network connection."

## R7. Design note (10 points)

Evidence expectations:

- A written note explains the main design tradeoffs (percentile method,
  windowing, memory).
- The note is specific to this submission, not generic.

Traceable spec quote: "The submission must include a short written explanation of the main design tradeoffs."

## RB1. Bonus: metrics exposition (+5 points)

Award up to 5 bonus points when the tool can expose its summary in a scrape-ready
metrics format for monitoring systems.

Traceable spec quote: "The tool must support Prometheus exposition format."

## RB2. Bonus: JSON output (+5 points)

Award up to 5 bonus points when the tool can emit the summary as JSON in addition
to the text table.

Traceable spec quote: "The tool may emit the summary as JSON in addition to the text table."

## Q1. Qualitative note: malformed-input robustness

This note is not scored directly. Review whether the tool degrades gracefully on
junk input rather than failing hard. Use it to guide written feedback, not to add
or remove points.

Traceable spec quote: "The tool must not crash when a line is malformed."
