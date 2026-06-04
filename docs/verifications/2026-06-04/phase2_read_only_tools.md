# Verification — Phase 2 read-only framework tools

## Subject metadata

- **Date**: 2026-06-04
- **Requester**: Owner (kdtyohan@gmail.com) — "다음작업 검증해줘" (Phase 2 read-only framework tools)
- **Verifier**: Claude (independent audit)
- **Target slice**: `src/assessment_harness/tools/` (`spec_tools.py`, `rubric_tools.py`, `__init__.py`) + `tests/test_tools.py`
- **Canonical spec reference**: `docs/implementation_plan...v1.md` — §7 module map (lines 914–918: `tools/` with `spec_tools` = `read_spec_section`/`list_sections`, `rubric_tools` = `list_rubric_items`/`get_rubric_item`, `propose_tools` = propose/flag, deferred), §7 prose (line 958: framework-agnostic Python functions registered per runner), §9 Phase 2 tool set (line 1226), §12 open decision #8 (line 1393: tool side-effect policy still open).
- **Source of work**: uncommitted working tree; HEAD `dea7adf`. New files untracked.

## Scope

1. Contract alignment (tool names, framework-agnostic shape, read-only scoping vs open decision #8).
2. Read-only / no-side-effect guarantee (no writes; no caller-visible mutation of source data).
3. Reuse vs reinvention (models/schema loader vs hand-rolled logic).
4. Latent-crash safety (direct dict subscripts vs schema guarantees).
5. Test quality (both-direction guards where applicable).
6. Scope-creep check.
7. Independent green-bar + runtime sanity.

## Methodology

- Read the plan tool anchors (§7 map, §9 Phase 2, §12 #8) end-to-end.
- Read all four new files directly.
- Probed `rubric_items.schema.json` (`$defs/rubric_item.required`) to confirm the fields the tools subscript are schema-mandatory.
- Ran `tests/test_tools.py`, the combined runner+tools set, and the full suite.
- Ran a standalone runtime sanity: sha256 of source files before/after tool calls, plus a caller-mutation-leak probe on the returned objects.

## Findings

### 1. Contract alignment — exact

- Tool names match the plan map verbatim: `spec_tools.list_sections` / `read_spec_section`, `rubric_tools.list_rubric_items` / `get_rubric_item` (plan lines 916–917, 1226). `__init__.py` re-exports the four.
- Functions are plain Python taking `Path` and returning `dict`/`list` — framework-neutral, matching plan line 958 ("tool 자체는 Python 함수이며, 각 runner가 … 등록한다"). No SDK coupling.
- **Read-only scoping is correct and contract-justified**: `propose_spec_item` / `propose_trace_link` / `flag_ambiguity` are deliberately absent. Plan open decision #8 (line 1393) leaves the tool side-effect policy (read-only vs propose-writes-to-file vs runner-collect) unresolved, so deferring all write/propose tools is the right call, not an omission.

### 2. Read-only / no-side-effect — confirmed (code + runtime)

- No filesystem writes anywhere; `spec_tools` only `read_text`, `rubric_tools` only `load_validated`.
- `get_rubric_item` and `list_rubric_items` `copy.deepcopy` what they return, so a caller mutating the result cannot corrupt the loaded document on a subsequent call.
- Runtime sanity (standalone script): source `spec.md` / `rubric_items.yaml` sha256 unchanged after calling all four tools; mutating the returned `get_rubric_item` / `list_rubric_items` objects did **not** leak into a re-read (`title != "MUTATED"`, `id != "MUT"`). The slice's defining property (no side effects) holds in practice.

### 3. Reuse vs reinvention — good

- `rubric_tools` reuses `load_validated(path, "rubric_items")` (schema-validated load) and `HarnessInputError` from `models.py` — no reinvention.
- `spec_tools._markdown_sections` is genuinely new logic (Markdown ATX heading → line-span sectioning); `models.py`'s `SourceSnapshot`/`Document` provides line access but no heading-section parsing, so this is new capability, not a duplicate. Acceptable. (It reads the raw spec path directly rather than through a hashed snapshot, which is appropriate for a candidate-generation read tool; source-snapshot grounding is a Rule 0 concern, not the read tool's.)

### 4. Latent-crash safety — cleared

`list_rubric_items` subscripts `item["id"]`, `["title"]`, `["evaluation_role"]`, `["source_ref"]` directly. `rubric_items.schema.json` `$defs/rubric_item.required = ["id","title","evaluation_role","source_ref"]`, confirmed by probe (an item missing `title` → `load_validated` error). So the loader rejects any doc that would KeyError; the direct subscripts are safe. The only optional field, `weight`, is correctly guarded with `if "weight" in item`.

### 5. Test quality — solid on the covered surfaces

- `test_list_sections...` pins the full section list (title/level/start/content_start/end spans) on `clean_assignment/source/spec.md`.
- `test_read_spec_section...` confirms case-insensitive title match and section-boundary correctness ("Optional features" *not* in the Requirements text — over-strict boundary check).
- `test_read_spec_section_rejects_missing_or_ambiguous_section` covers **both** error branches (duplicate heading → "ambiguous"; absent → "not found") on a self-built spec.
- `test_list_rubric_items...` pins ids, the exact R1 summary, and `"weight" not in items[3]` (optional-weight branch).
- `test_get_rubric_item...` confirms the full item (description, evidence_required) is returned, distinct from the summary; missing id → "not found".

### 6. Scope-creep check — none

Only the four intended files are new; `git status --porcelain src/` shows only `src/assessment_harness/tools/`. `cli.py`, `agent_runners/`, `schemas/`, and `config/` are untouched. Doc changes (`CHANGELOG.md`, `HANDOFF.md`, `docs/evaluation.md`, `work_log`) are count/status maintenance required by CLAUDE.md §5. No write/propose tool was slipped in. No unrelated refactor.

### 7. Reproduced numbers (independent)

`tests/test_tools.py` → **6 passed**; `test_agent_runner_contract.py + test_tools.py` → **33 passed**; full suite → **274 passed**; `py_compile src/assessment_harness/tools/*.py` → ok; `git diff --check` → clean. All match the owner's report.

## Issues / Risks (all minor, non-blocking)

1. **Untested symmetric guard**: `get_rubric_item` raises "rubric item id is ambiguous" on duplicate ids, but no test exercises it (the *spec*-side ambiguous branch is tested; the rubric-side twin is not). Not a contract-mandated boundary (the plan only names the tools, not their error taxonomy), so it is a recommended add, not a conditional-pass driver. Rule 0 would normally catch duplicate ids upstream, but the tool guards independently and that line is unprotected.
2. **No-mutation not locked by a test**: the deepcopy isolation is correct (I verified it at runtime) but no regression pins it; a future refactor dropping the `copy.deepcopy` would pass the suite. A one-line "mutate result → re-call → unchanged" test would lock the slice's core property.
3. **Empty-section span cosmetic edge**: a heading with no body produces `content_start_line > end_line` (inverted span) and empty `text`. Harmless for an overview tool, untested. Worth a clamp or a note if these spans are later consumed as ranges.

## Verdict — 합격 (Pass)

Tool names and shape match the plan exactly; read-only scoping is the contract-correct choice given open decision #8; the tools are genuinely side-effect-free (verified in code and at runtime); reuse is appropriate and the one direct-subscript risk is foreclosed by the rubric schema; tests pin the covered surfaces in both directions where errors exist; and there is no scope creep. The three issues are minor coverage/cosmetic items, none contract-mandated. No defects outstanding.

## Outstanding (operational, not defects)

- The slice (`tools/`, `tests/test_tools.py`) and its doc updates are **uncommitted**; `tools/` and `test_tools.py` are untracked. Commit when ready.
- The tools are defined and unit-tested but **not yet wired into any runner** — that registration is later-phase work (plan line 958) and outside this slice's claimed scope.
- No publication authorization implied.

## Reproduction

```bash
cd /workspace/assessment_poc
PYTHONPATH=src python3 -m pytest tests/test_tools.py -q                                   # 6 passed
PYTHONPATH=src python3 -m pytest tests/test_agent_runner_contract.py tests/test_tools.py -q  # 33 passed
PYTHONPATH=src python3 -m pytest -q                                                       # 274 passed
PYTHONPATH=src python3 -c "from assessment_harness.schemas import validate; print(validate('rubric_items', {'rubric_items':[{'id':'X','evaluation_role':'scored','source_ref':{'document_id':'D','start_line':1,'end_line':1}}]}))"  # -> 'title' required
```

---

## Re-verification — minor-fix pass (2026-06-04, working tree, uncommitted)

Re-audited the three minor items I had flagged. Two are cleanly closed; the third's fix introduced a new, more serious defect.

### Issue 1 (ambiguous rubric id) — RESOLVED

`test_get_rubric_item_rejects_ambiguous_id` appends a duplicate of `rubric_items[0]` and asserts `get_rubric_item(..., "R1")` raises `HarnessInputError(match="ambiguous")`. Exercises the previously-untested `"rubric item id is ambiguous"` branch directly. ✓

### Issue 2 (deepcopy / no-mutation) — RESOLVED

`test_rubric_tools_return_deep_copies` mutates `list_rubric_items(...)[0]["source_ref"]["start_line"]` and `get_rubric_item(...,"R3")["evidence_required"]`, then re-reads and asserts the source data is unchanged (`start_line == 3`, `evidence_required == ["code"]`). Locks the `copy.deepcopy` isolation in both functions. ✓

### Issue 3 (empty-section span) — NOT FIXED; the change is a content-correctness REGRESSION

The new branch in `spec_tools._markdown_sections`:
```python
if content_start_line > end_line:
    content_start_line = min(start_line + 1, len(lines) + 1)
    end_line = content_start_line
content_lines = lines[content_start_line - 1 : end_line]
```
sets `end_line = content_start_line = start_line + 1` **without clamping to `raw_end_line`** (the line before the next heading), and then *slices `content_lines` from that span*. When an empty section is immediately followed by another heading with **no blank line between them**, `start_line + 1` points at the next heading, so the slice pulls the next heading's line into this section's text and span.

Proven on ordinary Markdown:
- `# T / ## Overview / ## Details / Real body.` → `read_spec_section("Overview")` returns `text == "## Details"`, `span == (3, 3)` — the empty "Overview" section reports the **next heading** as its body, and its content span (line 3) overlaps "Details"'s heading line (start_line 3).
- `# Spec / ## Empty / ## Next / body` → `read_spec_section("Empty")["text"] == "## Next"`.

This is worse than the original behavior: pre-fix, the same input produced an inverted span (`content_start_line > end_line`) but **correct empty text** (`""`), because the slice `lines[cs-1:end]` with `cs > end` is empty. The fix traded a cosmetic span inversion for a real wrong-content bug in a read tool whose entire purpose is returning the correct section body — and consecutive headings with no blank line (`## A` directly above `## B`) are extremely common.

**Why the suite is still green**: `test_read_spec_section_returns_non_inverted_span_for_empty_section` uses `"# Spec\n\n## Empty\n\n## Next\nText.\n"` — a **blank line** sits between `## Empty` and `## Next`. There, `start_line + 1` lands on the blank line, so `text` is empty *by luck* and the assertions (`content_start_line == end_line`, `text == ""`) pass. The test never exercises the consecutive-heading case that the fix breaks. This is the exact "test pins the benign byproduct, not the adversarial boundary" failure mode — the regression guard is under-strict.

**Required to close**:
1. Fix the span/text computation so an empty section never slices past `raw_end_line` (e.g. derive `content_lines` only when `content_start_line <= end_line`, otherwise force `content_lines = []` / `text = ""`, and report a non-inverted *empty* span without re-slicing a real line). Decide the canonical empty-span representation explicitly.
2. Add a regression on **consecutive headings with no blank line** (`## A\n## B\n…`) asserting the empty section's `text == ""` and that its span does not overlap the next heading's `start_line`. That is the both-direction guard the current test lacks.

### Reproduced numbers (independent)

`tests/test_tools.py` → 9 passed; runner+tools → 36 passed; full → 277 passed; `py_compile` ok; `git diff --check` clean. All match the owner's report — but the green bar does not cover the Issue-3 regression (demonstrated above with a direct call).

### Updated verdict — 조건부 합격 (Conditional Pass) → blocking on Issue 3

Issues 1 and 2 are correctly fixed and locked with both-direction tests. Issue 3's fix is a regression: `read_spec_section` / `list_sections` now return the next heading as an empty section's content/span whenever two headings are adjacent without a blank line, and the accompanying test only covers the blank-line-separated case so it does not catch this. The slice cannot close until the empty-section handling is corrected and guarded by a consecutive-heading regression. I did not modify any code; surfacing per the verification-record discipline.

---

## Re-verification — Issue 3 regression fixed (2026-06-04, working tree, uncommitted)

### The fix is correct

`spec_tools._markdown_sections` now, for an empty section (`content_start_line > end_line` after trimming):
```python
content_start_line = raw_end_line
end_line = raw_end_line
content_lines: list[str] = []
```
It forces `content_lines = []` instead of re-slicing, so no real line (heading or body) is ever pulled into an empty section's text. The span collapses to `(raw_end_line, raw_end_line)`, and because `raw_end_line = next_heading_line - 1`, the empty span is always strictly before the next heading — it cannot overlap or leak it.

### Verified adversarially (the exact case that was broken)

- `# T / ## Overview / ## Details / Real body.` (consecutive headings, no blank line) → `read_spec_section("Overview")` now returns `text == ""`, span `(2,2)`; `read_spec_section("Details")` returns `text == "Real body."`. The leak is gone.
- Edge sweep I ran directly — empty-at-EOF, empty-with-trailing-blanks, nested (`## A / ### A1 / body`), and normal non-empty — all produce correct spans/text. Nesting (an H1/H2 spanning its sub-headings) is correct Markdown containment, not a leak: an *empty same-or-higher-level* section never reaches the following heading.

### The regression is now locked

`test_read_spec_section_empty_section_does_not_include_adjacent_heading` uses `"# Spec\n\n## Overview\n## Details\nText.\n"` (no blank line between the two `##` headings) and asserts `text == ""`, `"## Details" not in text`, `content_start_line == end_line == 3`, and `end_line < 4`. This is the both-direction guard the previous test lacked — it fails if the leak reappears (under-strict direction) and pins the empty span to before the next heading (over-strict direction). The original blank-line test is retained.

### Reproduced numbers (independent)

`tests/test_tools.py` → 10 passed; runner+tools → 37 passed; full suite → 278 passed; `py_compile` ok; `git diff --check` clean. All match the owner's report.

### Final verdict — 합격 (Pass)

All three originally-minor items are now correctly resolved and each is locked by a test that exercises the real boundary (rubric ambiguous-id, deepcopy isolation, empty-section consecutive-heading no-leak). The Issue-3 regression I caught in the prior pass is fixed at the root (no re-slice past `raw_end_line`) and guarded by an adversarial regression; my own edge sweep found no new defect. No defects outstanding for this slice.

### Outstanding (operational, not defects)

- `src/assessment_harness/tools/`, `tests/test_tools.py`, and both verification records remain **uncommitted/untracked**; doc updates (`HANDOFF`, `CHANGELOG`, `evaluation`, `work_log`) are staged in the working tree. Commit when ready.
- Tools remain defined + unit-tested but not yet wired into a runner (later-phase, outside this slice). No publication authorization implied.
