# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Scope:** This file is intended for Codex-based contributors working in this repository.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.
- If you detect a contradiction within a spec doc, or across spec docs, surface the contradiction to the user and ask which side is canonical. Never silently pick a side.
- At the start of a project (or when entering an unfamiliar repo), check whether a spec-precedence tree for conflicting sources exists. If it's absent, recommend defining one before deeper work — without it, future spec conflicts collapse into ad-hoc judgment calls.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

### Pattern sweep before declaring fix complete

When fixing a defect, spend ~30 seconds grepping for the same root-cause pattern in adjacent functions / files before marking the fix done. Bugs are rarely solo — the same misunderstanding tends to repeat in places nobody reported yet.

- After fixing `f()`, grep for the symptom signature (function call, magic value, naive UTC, etc.) repo-wide.
- If the pattern is found elsewhere: either fix it inline (if scope-trivial) or document it as a tracked debt with file:line. Never silently skip.
- For each discovered location, run `git blame` on that line for one-line context — knowing *why* the pattern was placed there often changes the fix decision (intentional vs accidental).
- The 30-second budget is on purpose — this is a sanity sweep, not a refactor. Anything deeper goes to a separate task.

### Two-directional regression guards

A regression test should fail in *both* directions, not just one.

- **Under-strict guard**: if the pre-fix bug is reintroduced, the test must re-fail.
- **Over-strict guard**: if an over-correction breaks a normal case (e.g. someone applies `+1` where the original cancelation was intentional), the test must also fail.
- State both directions in the test docstring or assertion names so future readers (and future-you) can see what's being locked.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## 5. Work Logs & Handoff

**Always update these files after completing tasks. No exceptions.**

### Work Log
- Path: `docs/daily_logs/YYYY-MM-DD/work_log.md`
- Follow the style of existing logs in `docs/daily_logs/`

**Required sections:**
- Goals — specific objectives for the day
- Completed work — for each task: description, files changed, key changes, effect
- Issues found — problem / cause / resolution / outcome
- Decisions — what was decided / why / tradeoffs
- Next steps

**Writing principles:**
- Be specific: not "fixed it" but "what was changed and how"
- Include reasoning: why this approach was chosen
- State the outcome: what effect the change had
- Write immediately after completing work, while details are fresh

### HANDOFF.md
- Purpose: current-state snapshot for the next worker, not a changelog or running diary
- Keep only information that is still true, actionable, or blocking right now
- If a newer note replaces an older one, rewrite the section instead of appending history
- Remove completed tasks, stale hypotheses, one-off experiments, and outdated verification notes
- Keep "Current Status" focused on today's system state and active drafts, not past milestones
- Keep "Next Tasks" short and prioritized so someone can pick up work immediately
- Keep "Verification" limited to the latest checks that still describe the current system
- Put detailed implementation history in `work_log.md`, and major milestones in `CHANGELOG.md`
- Update project structure if files are added/removed/moved
- Update MCP interface table if tools/resources change

### CHANGELOG.md
- Update on major design or feature changes (not every small edit)
- Top table links to daily_logs for detail
