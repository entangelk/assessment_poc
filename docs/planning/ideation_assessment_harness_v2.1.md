<p align="right">
  <a href="./ideation_assessment_harness_v2.1.md"><img src="https://img.shields.io/badge/Language-EN-111111?style=for-the-badge" alt="English"></a>
  <a href="./ideation_assessment_harness_v2.1.ko.md"><img src="https://img.shields.io/badge/Language-KO-6B7280?style=for-the-badge" alt="한국어"></a>
</p>

# Ideation v2.1 — Hiring Assignment Evaluation Design Harness

## 0. Re-review Summary

The core problem statement from v1 is valid. Hiring assignment evaluation needs a safety net similar to code tests. However, v1's scope was broad. By including automated scoring, statistical verification, post-hoc reports, and VectorDB-based pattern mining, the initial product hypothesis became blurred.

This v2 narrows the focus.

> A harness that detects mismatches between a hiring assignment's public specification and private evaluation rubric before the assessment runs.

In other words, this tool does not evaluate candidates. It **evaluates the evaluation design**.

---

## 1. Problem Definition

Hiring assignments are usually split into two document worlds.

* **Candidate-facing spec**: the README, assignment description, requirements, constraints, and submission guide visible to candidates
* **Evaluator-facing rubric**: the scoring criteria, weights, internal judgment rules, penalty rules, and excellent-answer examples visible to evaluators

The problem is that these two document worlds are often maintained separately. That creates the following structural issues.

### 1.1 Hidden Criterion

A criterion that was not disclosed to candidates carries meaningful weight in the actual evaluation.

For example, the README may not mention it, while the internal rubric gives high points for “independently discovering a specific edge case.” In that situation, candidates are doing the same assignment, but in practice they have received different exam papers.

### 1.2 Misleading Optionality

Something that looks optional in the README is used as a strong differentiating signal in the actual evaluation.

If a feature labeled “Optional” is actually a top-tier selection criterion, candidates will misallocate their time. The problem is not the candidate's judgment, but the way the evaluation design communicates information.

### 1.3 Time Budget Mismatch

The recommended completion time does not match the depth of work demanded by the rubric.

For example, the README may recommend 10 to 18 hours, while the rubric effectively requires several days of exploration, experimentation, and documentation to earn a high score. In that case, the evaluation result depends heavily not only on skill, but also on available time, capacity for over-investment, and luck around prior knowledge.

### 1.4 Post-hoc Rubric Drift

New criteria start to matter during evaluation or retrospective review.

After seeing a good submission, it is a natural human reaction to say “this approach was important” and turn it into a criterion after the fact. But if that criterion affects scores in the same round, the standard was created after candidates had already submitted.

### 1.5 Feedback Non-debuggability

Candidates receive a result but cannot tell what they should improve.

Feedback such as “it was lacking,” “it lacked depth,” or “there was a gap from the top tier” may be qualitatively accurate. But if candidates cannot trace which public requirement and which evaluation criterion drove the score difference, its learning value is low.

---

## 2. Core Hypothesis

Hiring assignment evaluation should satisfy the following invariant.

> Every rubric item must be traceable to one or more candidate-facing spec items.

A rubric item that does not satisfy this invariant should be handled in one of three ways.

1. Add it to the spec.
2. Remove it from the rubric.
3. Downgrade it to a bonus or qualitative note rather than a formal scoring item.

If this invariant is enforced like CI, much of hidden criterion, misleading optionality, and post-hoc rubric drift can be structurally reduced.

---

## 3. Product Definition

### Name

**Assessment Spec Harness**

### One-line Description

A tool that compares a hiring assignment README and internal evaluation rubric, then verifies scoring-criterion traceability, time-budget fit, and weight consistency.

### Shorter Form

> CI for hiring assessments.

### Precise Positioning

This product is not an automated grader. It does not evaluate candidate skill; it checks whether the evaluation design is fair, explainable, and reproducible.

---

## 4. Target Users

### 4.1 Primary User: Technical Assessment Owner

An engineer, team lead, or hiring manager who designs and maintains hiring assignments.

This user needs to answer the following questions.

* Are the abilities we want to evaluate sufficiently visible in the README?
* Does the internal rubric connect to the requirements disclosed to candidates?
* Does a particular evaluation item exceed the assignment scope?
* Is the assignment structured so that a high score is achievable within the recommended time?

### 4.2 Secondary User: Recruiting Ops / HR Ops

The person who manages hiring-process consistency, records, and auditability.

This user wants the following.

* Rubric change history by round
* Confirmation that evaluation criteria were finalized before the round
* Candidate feedback templates
* Source and anonymization checklists for externally shared material

### 4.3 Future User: Assessment Platform Vendor

Platforms such as Codility, HackerRank, and Coderbyte, or internal assessment platforms.

For these users, the added value may be less “creating problems” and more “verifying that problems can be evaluated fairly.”

---

## 5. MVP Scope

The MVP should be small. It includes only Layer 0 from v1 and part of Pre-flight.

### 5.1 Inputs

* `spec.md`: candidate-facing document
* `rubric.yaml`: internal evaluation criteria
* Optional inputs

  * `time_budget.yaml`
  * `evaluator_notes.md`
  * `sample_submission/`

### 5.2 Outputs

* Traceability Report
* List of Orphan Rubric Items
* List of Ambiguous Spec Items
* Optionality Mismatch warnings
* Time Budget Risk warnings
* Draft Candidate-facing Disclosure

### 5.3 What the MVP Does Not Do

* Automatically grade submissions
* Decide pass/fail
* Replace evaluators
* Make legal judgments
* Mine large-scale candidate patterns
* Run VectorDB-based similarity analysis

---

## 6. Draft Data Model

### 6.1 Spec Item

```yaml
spec_items:
  - id: S1
    source: README.md
    section: "Requirements > Refund Policy"
    text: "Implement refund handling for cancelled orders."
    visibility: candidate_facing
    requirement_level: must
    estimated_effort_hours: 1.5
```

### 6.2 Rubric Item

```yaml
rubric_items:
  - id: R1
    title: "Refund policy conflict handling"
    description: "Detects and resolves conflicting refund rules across cancellation states."
    weight: 12
    type: functional_correctness
    trace_to:
      - S1
    evidence_required:
      - code
      - test
    scoring:
      full: "Handles all documented cancellation/refund states."
      partial: "Handles basic cancellation but misses conflict cases."
      zero: "No refund handling."
```

### 6.3 Verification Result

```yaml
findings:
  - type: orphan_rubric_item
    severity: high
    rubric_item: R7
    message: "This rubric item has no candidate-facing spec trace."
    recommended_action:
      - "Add corresponding spec item"
      - "Downgrade to bonus"
      - "Remove from scoring rubric"
```

---

## 7. Core Verification Rules

### Rule 1. Rubric Coverage

Every rubric item must be connected to at least one spec item.

* Failure example: “independently discovering a specific edge case” exists only in the internal criteria
* Recommended action: state it in the README as an evaluation axis, or downgrade it to a bonus

### Rule 2. Spec Coverage

Important spec items should be reflected in the rubric.

* Failure example: the README describes something as a core requirement, but the scoring table does not include it
* Recommended action: add a rubric item or adjust the importance level in the README

### Rule 3. Optionality Consistency

Items marked optional in the spec should also be low weight or bonus items in the rubric.

* Failure example: the README says optional, but the rubric weight is 20%
* Recommended action: remove the optional wording or lower the evaluation weight

### Rule 4. Time Budget Consistency

Warn when the rubric's expected full-score path conflicts too strongly with the recommended time.

* Failure example: recommended time 10 to 18 hours, estimated full-score effort 35 hours
* Recommended action: reduce requirements, revise the recommended time, or separate bonus items

### Rule 5. Rubric Version Lock

If the scoring rubric changes after the round starts, that change must be explicitly recorded.

* Allowed changes: typo fixes, explanatory clarification, future-round changes
* Risky changes: adding, removing, or reweighting criteria that affect current-round scores

### Rule 6. Disclosure Readiness

After evaluation ends, it should be possible to generate a minimal score breakdown that can be shared with candidates.

* Each score item must connect to a spec item.
* Feedback should be phrased not as “good/bad,” but as “which requirement lacked which evidence.”

---

## 8. Example Report

```text
Assessment Spec Harness Report

Overall status: FAIL

High severity findings: 3
Medium severity findings: 4
Low severity findings: 2

[HIGH] R7 has no traceable spec item
- Rubric: "Detects undocumented library workaround"
- Problem: Candidate-facing README does not mention library-level investigation as an evaluation axis.
- Suggested action: Add explicit advanced evaluation criterion or downgrade to bonus.

[HIGH] Optionality mismatch
- Spec: "Chatbot integration is optional"
- Rubric: Chatbot-related items account for 18% of total score.
- Suggested action: Reclassify as recommended/advanced or reduce weight.

[MEDIUM] Time budget risk
- Recommended time: 10~18h
- Estimated full-score path: 27~34h
- Suggested action: Separate baseline pass criteria from distinction criteria.
```

---

## 9. User Flow

### 9.1 Local CLI

```bash
assessment-harness check \
  --spec README.md \
  --rubric rubric.yaml \
  --time-budget time_budget.yaml
```

Output:

```bash
status: fail
report: reports/assessment_harness_report.md
machine_readable: reports/assessment_harness_report.json
```

### 9.2 GitHub PR Check

CI runs whenever the rubric or README changes.

* An orphan rubric item blocks merge
* Optionality mismatch becomes a warning or block
* Time budget risk becomes a warning
* Rubric changes after a round starts require approval

### 9.3 After the Round Ends

Generate candidate-facing feedback by connecting evaluation results to the rubric.

```text
You received partial credit on R3.
This maps to README requirement S4: "Handle refund states."
Evidence found: basic refund flow implemented.
Missing evidence: conflict handling between cancellation and refund policy.
```

---

## 10. Role of the LLM

The LLM is not the core judge; it is an analysis assistant.

### Suitable Roles

* Extract requirement candidates from the README
* Suggest semantic match candidates between rubric items and spec items
* Detect ambiguous wording
* Draft candidate-facing feedback sentences

### Unsuitable Roles

* Make the final pass/fail decision
* Calculate scores on its own
* Decide legal risk
* Replace evaluator responsibility

### Operating Principle

LLM output must always be stored as a structured finding and approved by a human.

```yaml
llm_suggestion:
  type: possible_orphan_rubric_item
  confidence: 0.78
  reason: "No candidate-facing requirement appears to mention this criterion."
  human_status: pending_review
```

---

## 11. Why This Approach Is Good Now

### 11.1 It Can Start Small

The MVP can start as a YAML schema and validation script, not a complex platform.

### 11.2 The Pain Point Is Clear

Teams that have run hiring assignments intuitively understand the problem of the README and internal rubric drifting apart.

### 11.3 It Is More Defensible Than Automated Grading

Automated grading is contentious. In contrast, “evaluation criteria should connect to the public specification” is an organizationally easy principle to accept.

### 11.4 It Improves Candidate Experience and Company Risk at the Same Time

Candidates understand the criteria better, while companies gain evaluation consistency, auditability, and external trust.

---

## 12. Competitive / Alternative Landscape

Existing hiring assessment platforms mainly focus on the following.

* Problem authoring
* Coding-test execution
* Automated grading
* Plagiarism detection
* Candidate management

By contrast, the differentiator of Assessment Spec Harness is this:

> It verifies not how well someone solves the problem, but how fairly evaluable the problem design is.

It is therefore less a replacement for existing platforms than an upper design-verification layer.

---

## 13. Phased Roadmap

### Phase 0 — Schema & Manual Review

* Define YAML schemas for spec items and rubric items
* Have a human manually author the trace mapping
* Simple orphan detection

Success criteria:

* A traceability matrix can be generated for one assignment
* At least one real orphan rubric item is detected

### Phase 1 — CI Check

* Automate verification through a GitHub Action
* Generate reports on rubric-change PRs
* Block merges on high-severity findings

Success criteria:

* Reports are generated automatically when README/rubric changes
* Evaluation-criteria change history can be tracked

### Phase 2 — LLM-assisted Mapping

* The LLM extracts spec item candidates
* The LLM suggests rubric-to-spec mapping candidates
* Humans only approve/reject

Success criteria:

* Manual mapping time decreases by at least 50%
* Humans can easily correct false positives and false negatives

### Phase 3 — Feedback Generator

* Generate candidate feedback from the score table and trace matrix
* Separate candidate-shareable level from internal level

Success criteria:

* A draft score breakdown can be generated for candidates
* It can be sent after evaluator review

### Phase 4 — Analytics & Round Drift

* Track rubric changes across rounds
* Analyze changes in difficulty and discriminative power for specific items
* Calibrate time-budget estimates

Success criteria:

* Results connect to an assignment-improvement PR for the next round

### Phase 5 — Pattern Provenance

Only consider this after large-scale candidate data has accumulated.

* Similar-approach clustering
* Outlier detection
* Pattern provenance
* Support for reviewing IP/source issues

Caution:

This stage depends on the embedding model, thresholds, and clustering parameters. Therefore, it is not part of the MVP.

---

## 14. Risks and Objections

### Objection 1. “Good evaluation naturally includes tacit knowledge.”

Correct. Not every evaluation criterion can be fully formalized. However, criteria that significantly affect scores should at least disclose their direction to candidates. Tacit knowledge can remain as a qualitative note, but it should not become a core scoring axis.

### Objection 2. “If we are too transparent, candidates will game it.”

Preventing gaming by hiding evaluation criteria is weak design. A good rubric should still distinguish skill even when disclosed. For example, “write good tests” can be public, but actually writing good tests remains difficult.

### Objection 3. “Time estimates are inaccurate.”

Correct. Therefore, the time-budget check should be a risk signal, not a hard fail. The goal is not exact time prediction; it is to detect obviously overlarge assignment designs in advance.

### Objection 4. “The LLM may map things incorrectly.”

Correct. That is why the LLM is a reviewer assistant, not the final judge. The final SoT is human-approved YAML and the audit log.

### Objection 5. “This is too much for a small company.”

Phase 0 is not excessive. Small teams are especially likely to depend on one or two evaluators' intuition, so even a minimal trace matrix can have a large effect.

---

## 15. Success Metrics

### Product Usage Metrics

* Number of spec items generated per assignment
* Trace coverage ratio among rubric items
* Number of orphan rubric items detected
* Number of rubric changes blocked by CI

### Quality Metrics

* Number of evaluation-criteria mismatches found before a round starts
* Reduced scoring disagreement among evaluators
* Candidate feedback satisfaction
* Reduced objections/confusion after evaluation

### Operational Metrics

* Time required to update a rubric
* Time required to write candidate feedback
* Number of improvement PRs for the next round

---

## 16. Smallest PoC

The goal is not to build a platform. It is to create a traceability matrix for one real or sample assignment.

### Inputs

* One README
* One rubric YAML
* One recommended time budget

### Implementation

* Python script
* YAML parser
* Markdown heading parser
* Simple validation rules
* Markdown report generator

### Outputs

* `traceability_matrix.md`
* `findings.md`
* `rubric.schema.yaml`
* `spec.schema.yaml`

### PoC Success Criteria

It is a success if any one of the following is achieved.

* It finds a rubric item that does not exist in the README.
* It finds high weight on an item described as optional.
* It explains a mismatch between recommended time and rubric depth.
* It creates the skeleton of a score breakdown that could be given to candidates after evaluation.

---

## 17. Changes from v1

### Kept

* The core analogy that evaluation also needs a test harness
* Separation between Spec SoT and Rubric SoT
* The invariant that rubric items must trace to the spec
* The importance of post-hoc transparency and audit trails

### Reduced

* Centrality of automated grading
* VectorDB / pattern miner / RAG grader
* Large-scale evaluation platform architecture
* Early emphasis on statistical visualization layers

### Strengthened

* MVP definition
* Target user
* Non-goals
* Verification rules
* Data model
* CI workflow
* Responses to objections

---

## 18. Final Summary

The core of Assessment Spec Harness is simple.

> Do not evaluate candidates by criteria they could not see.

It turns this from an emotional principle into a system invariant.

* Rubric items must trace to spec items.
* Optional items must actually be optional.
* Recommended time should roughly match evaluation depth.
* Mid-round criteria changes must be audited.
* Feedback must be debuggable.

Even implementing only this much can significantly improve the fairness, reproducibility, and explainability of hiring assignment evaluation.

If v1 was closer to a “hiring-evaluation operations platform,” v2 is “evaluation design CI.” This axis is smaller, more persuasive, and easier to move into a real PoC.

---

## 19. PoC Implementation Principles — LLM-agnostic Loose Harness

The goal of the PoC is not to trust a specific LLM. It is to build a loose harness that converges toward a similar verification flow regardless of which LLM is used.

The core principle is:

> The LLM is not the judge; it is a candidate generator. Final verification is done by schema, rules, evidence, and human approval.

### 19.1 Architecture Principles

LLM output never becomes truth directly.

What the LLM does:

* Extract spec item candidates
* Normalize rubric item candidates
* Suggest spec ↔ rubric mapping candidates
* Detect ambiguous wording candidates
* Suggest optionality mismatch candidates

What the harness does:

* YAML/JSON schema validation
* ID consistency check
* Rubric item trace coverage check
* Weight / optionality rule check
* Time budget rule check
* Finding severity calculation
* Report generation

What humans do:

* Approve/reject/edit LLM suggestions
* Handle false positives
* Give final approval for rubric changes

### 19.2 Deterministic Core

The parts that must behave the same regardless of LLM are fixed as deterministic code.

```text
input documents
  ↓
LLM-assisted extraction candidates
  ↓
human-approved structured YAML
  ↓
deterministic validation rules
  ↓
report.md + report.json
```

The core PoC artifact is not the LLM prompt, but the structured intermediate representation.

* `spec_items.yaml`
* `rubric_items.yaml`
* `trace_matrix.yaml`
* `findings.json`
* `report.md`

### 19.3 LLM Adapter Interface

The LLM provider should be replaceable.

```python
class LLMAdapter:
    def extract_spec_items(self, spec_markdown: str) -> list[SpecItemCandidate]:
        ...

    def suggest_trace_links(
        self,
        spec_items: list[SpecItem],
        rubric_items: list[RubricItem],
    ) -> list[TraceLinkCandidate]:
        ...

    def detect_ambiguities(self, spec_markdown: str) -> list[AmbiguityCandidate]:
        ...
```

Initial adapters:

* `ManualAdapter`: use only human-authored YAML, without an LLM
* `OpenAIAdapter`: use structured output
* `AnthropicAdapter`: use JSON mode or XML-ish response parsing
* `LocalAdapter`: parse Ollama/local model responses

The PoC must make `ManualAdapter` work first. That proves the harness value even without an LLM.

### 19.4 Loose Consensus Strategy

Multiple LLM outputs do not need to be identical. Instead, only the following must hold.

* All outputs are normalized to the same schema.
* Confidence is only a reference value and does not directly enter rule outcomes.
* High-severity findings are produced only by deterministic rules.
* Disagreement between LLMs goes to the review queue, not to findings.

Example:

```yaml
trace_link_candidates:
  - rubric_id: R7
    suggested_spec_ids: []
    source_model: gpt-x
    confidence: 0.71

  - rubric_id: R7
    suggested_spec_ids: [S12]
    source_model: claude-y
    confidence: 0.54
```

Harness judgment:

```yaml
review_queue:
  - type: llm_disagreement
    rubric_id: R7
    message: "Models disagree on whether R7 is traceable. Human review required."
```

In other words, LLM disagreement is not evaluation failure; it is a review target.

### 19.5 Severity Is Not Decided by the LLM

Severity is decided by the rule engine.

Example rules:

```yaml
rules:
  orphan_rubric_item:
    if: "rubric.trace_to is empty and rubric.weight > 0"
    severity: high

  optionality_mismatch:
    if: "linked_spec.requirement_level == optional and rubric.weight >= 10"
    severity: high

  high_weight_low_visibility:
    if: "rubric.weight >= 15 and linked_spec.visibility != candidate_facing"
    severity: critical
```

The LLM can only say “this item may be orphaned.” The actual high/medium/low judgment is made by deterministic rules.

### 19.6 Golden Fixture-based Regression Tests

The PoC should have a small fixture set.

```text
fixtures/
  clean_assignment/
    spec.md
    rubric.yaml
    expected_findings.yaml

  orphan_rubric/
    spec.md
    rubric.yaml
    expected_findings.yaml

  optionality_mismatch/
    spec.md
    rubric.yaml
    expected_findings.yaml

  time_budget_mismatch/
    spec.md
    rubric.yaml
    time_budget.yaml
    expected_findings.yaml
```

Each fixture must be testable deterministically without an LLM.

```bash
pytest tests/test_fixtures.py
```

Success criteria:

* The rule engine reproduces expected findings for every fixture.
* If the approved YAML is the same, the report is the same even when the LLM adapter changes.
* Even when LLM extraction results differ, the deterministic validation stage does not break.

### 19.7 PoC CLI

The initial CLI should be simple.

```bash
assessment-harness init
assessment-harness extract --spec README.md --out spec_items.yaml
assessment-harness check --spec-items spec_items.yaml --rubric rubric.yaml
assessment-harness report --findings findings.json --out report.md
```

LLM usage is kept behind an optional flag.

```bash
assessment-harness extract \
  --spec README.md \
  --provider openai \
  --out spec_items.candidates.yaml
```

Then a human approves it.

```bash
assessment-harness approve \
  --candidates spec_items.candidates.yaml \
  --out spec_items.yaml
```

### 19.8 Minimal Repo Structure

```text
assessment-spec-harness/
  pyproject.toml
  README.md
  assessment_harness/
    __init__.py
    cli.py
    models.py
    parser.py
    rules.py
    report.py
    adapters/
      __init__.py
      base.py
      manual.py
      openai_adapter.py
  schemas/
    spec_items.schema.json
    rubric.schema.json
    findings.schema.json
  fixtures/
    clean_assignment/
    orphan_rubric/
    optionality_mismatch/
    time_budget_mismatch/
  tests/
    test_rules.py
    test_fixtures.py
    test_report.py
```

### 19.9 First PoC Goal

The first goal is not impressive AI analysis.

The first goal is to make the following command run reliably.

```bash
assessment-harness check \
  --spec-items fixtures/orphan_rubric/spec_items.yaml \
  --rubric fixtures/orphan_rubric/rubric.yaml \
  --out findings.json
```

And to produce the following in `findings.json`.

```json
{
  "type": "orphan_rubric_item",
  "severity": "high",
  "rubric_id": "R2",
  "message": "Rubric item R2 has positive weight but no candidate-facing spec trace."
}
```

### 19.10 Judgment

This PoC is possible. And the smaller it starts, the stronger it is.

The rule engine runs even without an LLM. With an LLM, extraction and mapping become faster. Even when the LLM changes, the final judgment is fixed by schema and rules.

Therefore, the identity of this harness is:

> LLM-assisted, human-approved, deterministic assessment design validator.
