# Sample Assignment Guidelines

This guide is for an AI agent that needs to create a small test assignment sample
for the Assessment Spec Harness PoC.

The immediate goal is not publication readiness. The goal is to produce a
synthetic or local sample that lets the full harness workflow run:

```text
extract -> compact -> verify -> check -> report -> review -> gate -> materialize-review
```

Permission, anonymization, and publication review are intentionally deferred until
the publication freeze. Do not treat a sample created from this guide as public
release material without a later review.

## Output Files

Create a directory with at least:

```text
sample_assignment/
  spec.md
  rubric.md
```

The harness can generate `source_snapshot/manifest.yaml` during `extract`, so the
sample author does not need to write a manifest by hand.

Optional but useful:

```text
sample_assignment/
  notes.md
```

Use `notes.md` only for human context. The harness input should be `spec.md` and
`rubric.md`.

## Size

Keep the sample small enough for repeated agent runs:

- `spec.md`: 500-1,200 words.
- `rubric.md`: 400-1,000 words.
- 4-8 candidate-facing requirements.
- 4-8 evaluator-facing rubric items.
- 1-2 optional or bonus requirements.

## Subject Matter

Use a safe, synthetic task that does not depend on external private context.

Good examples:

- Build a small command-line inventory tool.
- Design a short data-cleaning script.
- Write a simple API endpoint with validation.
- Implement a toy scheduling or grading utility.
- Analyze a small provided CSV-like text block.

Avoid:

- Real student submissions.
- Real company, school, customer, or internal data.
- Personal data.
- Security-sensitive or credential-bearing scenarios.
- Domain knowledge that requires current web facts.

## `spec.md` Requirements

The spec is candidate-facing. It should describe what the student or implementer
is asked to build.

Include:

- A short task overview.
- Clear deliverables.
- Numbered or headed requirements.
- At least three mandatory requirements.
- At least one optional requirement.
- At least one explicit non-requirement or boundary.
- Acceptance criteria that can be quoted by a rubric item.

Use direct language such as:

```text
The solution must ...
The solution should ...
The solution may ...
The solution must not ...
```

This helps the harness classify `must`, `should`, `optional`, and future
`forbidden`-style boundaries.

## `rubric.md` Requirements

The rubric is evaluator-facing. It should describe how the assignment is scored.

Include:

- A total score, preferably 100 points.
- 4-8 scored rubric items.
- At least one qualitative or non-scored review note.
- At least one bonus item.
- Evidence expectations for each scored item.
- At least one item that traces cleanly to a mandatory spec requirement.
- At least one item that traces to an optional requirement.

Use stable item labels when possible:

```text
R1. Input validation (20 points)
R2. Core transformation behavior (25 points)
R3. Error reporting (15 points)
RB1. Bonus: helpful summary output (+5 points)
Q1. Qualitative note: code readability
```

## Harness-Friendly Design

The sample should contain enough structure for the harness to find useful
trace links, but not be so perfect that no review signals appear.

Recommended mix:

- 3-5 clear spec-to-rubric matches.
- 1 optional requirement with a high-weight scored rubric item.
- 1 bonus item that may be mistaken for mandatory coverage.
- 1 qualitative note that should not count as scored coverage.
- 1 requirement that is intentionally not scored, if you want Rule 2 to fire.

Do not overdo contradictions. The sample should be realistic, not a trap puzzle.

## Evidence Text

Write spec and rubric text so exact quotes are useful.

Good:

```text
The program must reject records with missing item IDs and report the line number.
```

Less useful:

```text
Handle bad stuff well.
```

The harness works best when source spans are concrete and quoteable.

## Verification Modes

For the PoC, the runner can leave semantic status as pending or use
`ai_judgement`-style evidence that later verification reviews.

If writing hand-authored fixture-like candidates later, use:

- `token_sequence` only for evidence that should be checked by exact source quote.
- `ai_judgement` for semantic claims that need verifier/human review.

The sample assignment itself does not need to mention these modes.

## Suggested Prompt For Creating A Sample

An AI agent can use this prompt:

```text
Create a synthetic assessment sample for the Assessment Spec Harness PoC.
Write two files: spec.md and rubric.md.

The task should be small, realistic, and fully synthetic.
The spec must include 4-8 requirements, including mandatory, optional, and boundary language.
The rubric must include 4-8 scored items, one bonus item, and one qualitative note.
Use stable labels and concrete quoteable wording.
Include at least one optional requirement that a rubric might overweight, and one mandatory requirement that might be under-covered.
Do not include real people, real institutions, private data, credentials, or current-events facts.
```

## Quick Manual Check

Before using the sample with a live runner:

- Confirm `spec.md` and `rubric.md` are plain UTF-8 Markdown.
- Confirm labels are easy to reference.
- Confirm the assignment has both mandatory and optional language.
- Confirm the rubric has scored, bonus, and qualitative items.
- Confirm no real private data was accidentally included.

Then run `extract` with the sample paths. The source snapshot manifest can be
auto-generated:

```bash
assessment-harness extract \
  --spec sample_assignment/spec.md \
  --rubric sample_assignment/rubric.md \
  --runner mock_fixture \
  --fixture-dir fixtures/clean_assignment \
  --runs 1 \
  --out-dir work/runs
```

The `mock_fixture` command above is only a wiring smoke; a real sample requires a
live SDK runner to generate candidates from the new spec and rubric.
