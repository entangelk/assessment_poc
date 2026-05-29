# Verification: Candidate Artifact Schema Foundation (plan v1.24)

## Subject metadata

- **Date**: 2026-05-29
- **Requester**: Owner (kdtyohan@gmail.com) — "검증하고 의심해줄래?"
- **Verifier**: Claude (independent audit)
- **Target slice**: candidate artifact schema foundation — `schemas/candidates.schema.json` 신설, `schemas.py` 등록, `test_models.py` 회귀 추가, plan v1.24 승격 + 문서 갱신.
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.24, §5.4 Candidate Artifact (lines 377–411), §5.4.1 cross-ref, 보강 A enum (line 1522), v1.24 변경 이력 (lines 1324–1330).
- **Source of work verified**: working tree, uncommitted (모든 변경이 staged/untracked 상태, `git status` clean 아님).

## Scope

1. 정본 계약 (plan §5.4 + 보강 A) 내부 일관성.
2. 스키마 ↔ 계약 literal 일치 (`candidates.schema.json`).
3. 스키마 등록 표면 (`SCHEMA_FILES`).
4. 회귀 테스트가 boundary matrix를 실제로 잠그는지.
5. 임베드된 `proposed_item` 정의 ↔ 정본 스키마(`spec_items`/`rubric_items`/`trace_links`) 일치 및 drift 위험.
6. 문서(HANDOFF/README/CHANGELOG/work_log)의 정량 주장 재계산.

## Methodology

- 스키마/계약 정독: `candidates.schema.json` 전체, plan §5.4 (lines 377–411), 정본 `spec_items`/`rubric_items`/`trace_links` schema 전체.
- 동작 탐침: `python3 -c` 로 `validate("candidates", ...)` 직접 호출하여 발화/미발화 분기 6종(P1–P6) 측정.
- 테스트: `python3 -m pytest tests/test_models.py -q`, 전체 `python3 -m pytest -q`.
- 카운트 재계산: `grep -c "^def test"`, `ls schemas/*.json | wc -l`.

## Findings

### F1. 정본 계약 내부 일관성 — 일치

§5.4 prose enum (lines 402–407) 와 보강 A (line 1522) 가 `integrity_status` 6값(`pending_check`/`validated`/`invalid_reference`/`quote_mismatch`/`schema_violation`/`blocked_by_runner_error`)을 동일하게 명시. 모순 없음.

### F2. 스키마 ↔ 계약 literal 일치 — 일치

- `integrity_status` enum 6값이 §5.4 와 byte-for-byte 일치 (`candidates.schema.json:41-48`).
- 공통 provenance 필수 필드 `candidate_id`/`proposed_item`/`agent_runner`/`agent_run_id`/`integrity_status` (lines 26-32) 가 §5.4 예시 및 line 398 prose와 일치. `source_excerpt`/`confidence` optional 처리는 prose가 필수로 못박지 않으므로 타당.
- 임베드 `spec_item`/`rubric_item`/`trace_link`/`evidence_quote`/`source_ref` 의 required·enum 이 정본 `spec_items.schema.json`/`rubric_items.schema.json`/`trace_links.schema.json` 의 해당 `$defs` 와 일치 (compacting 전용 필드 `support`/`identity_basis`/`variants` 만 제외 — candidate는 pre-compacting이므로 정당).

### F3. 스키마 동작 — 정확 (경험적 확인)

`validate("candidates", ...)` 직접 호출 결과:
- P1 spec_item `id` 누락 → 거부 ✓
- P2 `requirement_level: mandatory` (enum 위반) → 거부 ✓
- P3 `proposed_item` = 문자열 → 거부 ✓
- P4 `proposed_item` 누락 → 거부 ✓
- P5 최상위 배열 1개 누락 → 거부 ✓
- P6 spec 슬롯에 trace_link 투입 → 거부 ✓

`allOf` + `$ref` + `additionalProperties: true` 조합이 `proposed_item` 구조 제약을 **실제로 발화**한다. 스키마 자체는 기능적으로 정확.

### F4. 등록 표면 — 일치

`schemas.py:24` 에 `"candidates": "candidates.schema.json"` 등록. `SCHEMA_FILES` 14개. 테스트가 `"candidates" in SCHEMA_FILES` 단언. CLI `schema --command` 은 review action 노출 전용이라 JSON 스키마 목록과 무관 — 대상 introspection 표면은 `SCHEMA_FILES` 가 맞음.

### F5. 회귀 테스트 — boundary matrix에 빈 칸 존재 (조건부 합격 사유)

잠긴 분기:
- 정상 full 문서 validate → `test_phase_two_contract_schemas_are_registered_and_validate_plan_examples` ✓
- `agent_run_id` 누락(역추적 불가) 거부 → `test_phase_two_contract_schemas_reject_untraceable_entries` ✓
- `integrity_status` enum 위반 거부 → `test_candidates_schema_rejects_invalid_integrity_status` ✓

**빈 칸 (untraced branch):**
- 스키마의 핵심 가치인 **`proposed_item` 임베드 구조 검증**(F3의 P1/P2/P3/P6)이 **어떤 회귀 테스트로도 잠겨 있지 않음.** 경험적으로는 발화하지만(F3), 향후 `allOf`/`$ref` 배선이 깨지면 `proposed_item` 이 임의 garbage를 통과시켜도 green bar는 유지된다. 이는 CLAUDE.md가 "future risk"로 재명명하는 것을 금지한 전형적 under-strict guard 누락.
- `proposed_item` 누락(P4), 최상위 배열 누락(P5) 거부도 미잠금 (경미).

### F6. 부수 관찰

- `test_phase_two_contract_schemas_reject_untraceable_entries` 는 `assert candidate_errors`(truthy)만 단언하고 *어느* 오류인지 고정하지 않음. 입력이 그 외 정상이라 현재는 `agent_run_id`를 핀하지만 느슨함.
- 임베드 `$defs` 는 정본 스키마의 **수기 복사본**. 동기화를 보장하는 테스트가 없어 정본 스키마 진화 시 조용히 drift 가능. (plan이 `$ref` 재사용을 강제하지 않으므로 blocking은 아니나 contract-integrity 위험.)
- 긍정 테스트는 `integrity_status: pending_check` 만 실행. 나머지 5개 유효값은 긍정 검증 안 됨 (저위험).
- work_log line 23 "under-strict candidate provenance acceptance ... locked" 는 provenance 일부(agent_run_id)만 잠겼고 `proposed_item` 구조는 미잠금이므로 과대 주장.

### F7. 문서 정량 주장 — 재계산 일치

- "170 tests pass" → `pytest -q`: **170 passed** ✓
- "15 model tests" → `grep -c "^def test" tests/test_models.py`: **15** ✓
- "fourteen JSON Schemas" → `ls schemas/*.json | wc -l`: **14** ✓
- plan/HANDOFF/README/CHANGELOG v1.24 버전 참조 일관 ✓

## Issues / Risks

- **[조건]** F5: `proposed_item` 임베드 검증의 under-strict guard 부재 — 스키마의 일차 목적이 무회귀 상태.
- **[위험]** F6: 임베드 $defs drift (동기화 테스트 없음); 부정 테스트 단언 느슨; 5개 enum 유효값 긍정 미검증; work_log 과대 주장.

## Verdict

**조건부 합격 (conditional pass).**

근거:
- 스키마는 계약과 literal 일치하고 모든 제약이 실제로 발화함(F2/F3). 등록·문서 정량 주장 전부 재계산 일치(F4/F7). 정본 계약 내부 모순 없음(F1). → 불합격 아님.
- 그러나 스키마의 핵심 기능인 `proposed_item` 구조 검증이 회귀 테스트로 잠기지 않아 boundary matrix에 빈 칸이 존재(F5). CLAUDE.md "빈 칸은 blocking finding" 규율상 무조건 합격 불가.

**합격 조건 (잠금 추가):**
1. 임베드 `proposed_item` 가 무효일 때 거부됨을 잠그는 회귀 — 최소 (a) spec_item `id` 누락 또는 `requirement_level` enum 위반, (b) `proposed_item` 잘못된 타입(문자열). rubric/trace 슬롯도 1건씩 권장.
2. (권장) `test_..._reject_untraceable_entries` 단언을 `agent_run_id` 오류 메시지로 핀.

## Outstanding items

- 모든 변경이 uncommitted (working tree). 커밋 권한은 Owner 결정.
- 위 합격 조건 잠금은 본 slice의 마무리 작업이며, 검증자는 임의 수정하지 않고 Owner 결정 대기.

## Follow-up verification — condition resolved (2026-05-29, same day)

Owner가 조건을 처리한 뒤 재검증함. 독립적으로 재확인한 결과:

- **F5 빈 칸 잠김**: `test_candidates_schema_rejects_invalid_proposed_item_shape` parametrized 6 케이스 추가 — spec_item `id` 누락 / `requirement_level` enum 위반 / `proposed_item`=문자열 / rubric_item `title` 누락 / trace_link `verification_mode` enum 위반 / spec 슬롯에 trace-link payload(→ `text` 누락). 각 케이스가 **주장한 오류 메시지를 정확한 경로에서** 발생시킴을 직접 탐침으로 확인(공허 통과 아님): 예) `trace_link_candidates/0/proposed_item/evidence_quotes/0/verification_mode: 'exact' is not one of [...]`, `rubric_item_candidates/0/proposed_item: 'title' is a required property`. 6 케이스 모두 PASSED.
- **F6 단언 핀 강화**: `test_phase_two_contract_schemas_reject_untraceable_entries` 가 `assert any("agent_run_id" in error ...)` 로 변경 — 더 이상 단순 truthy 아님.
- **과대 주장 정정**: work_log line 23/35, HANDOFF line 171 이 `proposed_item` 구조 잠금을 정확히 기술하도록 수정됨.
- **정량 재계산 일치**: `pytest -q` → **176 passed**; model collection → **21**; `git diff --check` clean.
- 미해소(non-blocking, 추적만): 임베드 `$defs` 가 정본 스키마 수기 복사본이라는 drift 위험은 동기화 테스트 없이 그대로. 향후 정본 진화 시 별도 슬라이스로 다룰 것.

**갱신 판정: 합격 (pass).** 조건부 합격의 차단 사유였던 boundary matrix 빈 칸이 비공허(non-vacuous) 회귀로 잠김. drift 위험은 blocking 아닌 추적 항목으로 남김.

## Reproduction

```bash
cd "/workspace/assessment_poc"
# 동작 탐침
python3 -c "from src.assessment_harness.schemas import validate; \
print(validate('candidates', {'spec_item_candidates':[{'candidate_id':'X','agent_runner':'r','agent_run_id':'r1','integrity_status':'pending_check','proposed_item':'garbage'}],'rubric_item_candidates':[],'trace_link_candidates':[]}))"
# 테스트 + 카운트
python3 -m pytest tests/test_models.py -q
python3 -m pytest -q
grep -c "^def test" tests/test_models.py
ls schemas/*.json | wc -l
```
