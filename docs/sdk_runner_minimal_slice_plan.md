# SDK Runner Minimal Slice Plan (PoC Execution)

This plan covers the smallest slice that lets the full harness workflow run on a
real sample `spec.md` / `rubric.md` pair, instead of replaying fixture YAML.

It exists because of an owner decision (2026-06-07): **prioritize getting the
workflow to execute end-to-end on the sample now; make pragmatic placeholder
choices where a real decision is still pending, and record those placeholders
here for later discussion.**

## Environment constraint (load-bearing)

A real Claude Agent SDK runner cannot run in the current environment:

- No `ANTHROPIC_API_KEY` (and no other Anthropic/Claude credential) is present.
- `anthropic` / `claude_agent_sdk` / `claude_code_sdk` are not installed.
- Network egress to `api.anthropic.com` is blocked.

So a live-LLM runner would fail before producing a single candidate. To honor the
"execution first" decision without faking credentials, this slice adds a runner
that produces candidates **deterministically and offline**, behind the existing
`AgentRunner` protocol boundary. When credentials / SDK / network become
available, a real SDK runner replaces this one at the same boundary — no
orchestration change.

## What this slice adds

- `agent_runners/deterministic.py` — `DeterministicExtractionRunner`
  (`name = "deterministic_extraction"`).
  - Implements `AgentRunner.run(spec_path, rubric_path, tools, max_turns, policy)`.
  - Parses the sample `rubric.md` headings and their `Traceable spec quote: "..."`
    lines, locates each quote inside `spec.md`, and emits fixture-shaped
    `spec_items` / `rubric_items` / `trace_links` artifacts that are
    **grounding-correct** against the auto-generated source snapshot (so deep
    candidate Rule 0 promotes the run to `validated`).
  - No LLM call, no network, no credentials.
- `extract --runner deterministic_extraction` wiring (no `--fixture-dir` needed).

## Why grounding works deterministically

`rules.run_rule_zero` accepts a quote when, after whitespace normalization
(`" ".join(text.split())`), the quote is a substring of the `source_ref` span
text (`"\n".join(lines[start-1:end])`). The sample `rubric.md` already lists, for
each scored/bonus item, a `Traceable spec quote` copied verbatim from `spec.md`.
The runner finds the minimal `[start_line, end_line]` window in `spec.md` whose
normalized text contains that quote, and uses the same quote as the spec item
`text`, the spec `source_ref.quote`, and the trace-link `evidence_quote`. That
makes every emitted reference provably grounded.

## Placeholder decisions (REVISIT — owner discussion pending)

These were chosen to unblock execution, not as final contract. Each needs a real
decision later.

1. **Runner identity.** `deterministic_extraction` is a stand-in for the real SDK
   runner, not an SDK integration. It must not be presented as live agent
   extraction in any public/portfolio copy.
2. **Spec item provenance.** Spec items are derived from the rubric's
   `Traceable spec quote` hints, not from an independent pass over `spec.md`. A
   real runner would extract spec items independently and then trace. Consequence:
   spec requirements that no rubric item quotes are not materialized as spec
   items in this slice, so some coverage-style signals (e.g. Rule 2 uncovered
   `must`) will not fire from this runner's output.
3. **`requirement_level` mapping.** Schema enum is `must | optional |
   informational`. Mapping applied: `must` (incl. "must not") → `must`;
   `may` / `should` / `optional` / bonus context → `optional`; otherwise
   `informational`. "should" collapsing into `optional` is a simplification.
4. **`verification_mode`.** All evidence quotes use `token_sequence` (exact
   grounded quotes), so no `ai_judgement` items are produced and the `verify`
   step has no AI-judgement evidence to review in this slice.
5. **Runner limits / credentials / raw-trace retention.** `max_turns`, cost
   ceilings, credential delivery, and raw-trace redaction (the open items in
   `docs/sdk_runner_decisions.md`) are not exercised because there is no live
   model. They remain open and must be decided before a real SDK runner.

## Out of scope for this slice

- Real Claude Agent SDK integration and any network/credential handling.
- Runner-collected propose/write tools (still read-only per plan v1.32 §8).
- Multi-run candidate diversity: the deterministic runner emits identical
  candidates per run (only `run_id` differs), so compacting sees one variant.

## Path to the real runner

1. Keep `DeterministicExtractionRunner` as the offline/CI default.
2. Add `SdkExtractionRunner` behind the same protocol once
   `docs/sdk_runner_decisions.md` items 1–7 are decided and credentials/SDK are
   available.
3. Make live SDK tests opt-in; keep the normal suite offline and deterministic.
