# Verification: Candidate Audit-Trace Attribution Helper (plan v1.25)

## Subject metadata

- **Date**: 2026-05-29
- **Requester**: Owner — "다음 작업물 검증해줘"
- **Verifier**: Claude (independent audit)
- **Target slice**: `validate_candidate_audit_trace` 헬퍼 신설 + 회귀 테스트, plan v1.25 승격, 문서 갱신.
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.25, §10.2 (line 1194: "audit trace는 schema validation을 통과하고, 모든 candidate의 `agent_run_id`가 audit trace에 존재해야 한다"), v1.25 변경 이력 (lines 1322-1331). 연계 스키마: `candidates.schema.json`, `agent_trace.schema.json`.
- **Source of work verified**: working tree, uncommitted.

## Scope

1. 정본 계약(§10.2 해당 1문장) ↔ 헬퍼 동작 일치.
2. 헬퍼 구현 정확성(`validation.py`) — false-pass / 누락 분기 탐침.
3. 회귀 테스트가 boundary matrix를 비공허하게 잠그는지.
4. export 표면(`__init__.py`).
5. 문서(HANDOFF/README/CHANGELOG/work_log) 정량/내용 주장 재계산.

## Methodology

- 계약 정독: plan §10.2 (line 1188-1200), v1.25 changelog, `agent_trace.schema.json` 전체.
- 코드 정독: `validation.py` 전체 (45 lines).
- 동작 탐침: `PYTHONPATH=src python3 -c` 로 `validate_candidate_audit_trace` 직접 호출 — 정상/run_id 불일치/빈 trace/무효 trace 이벤트.
- 테스트: `pytest tests/test_agent_runner_contract.py -q`, 전체 `pytest`, `--collect-only` 카운트, `git diff --check`.

## Findings

### F1. 계약 ↔ 구현 일치 — 일치

§10.2 line 1194 의 두 요구:
- "audit trace는 schema validation을 통과" → `validation.py:21` 각 이벤트를 `validate("agent_trace", event)` 로 검증, 오류를 `audit_trace/{index}:` prefix 로 노출.
- "모든 candidate의 `agent_run_id`가 audit trace에 존재" → `validation.py:27-43` spec/rubric/trace 세 배열을 순회하며 `agent_run_id ∉ trace_run_ids` 면 오류 추가.
- candidate schema 검증도 `validation.py:17` 에서 함께 수행(계약이 명시하는 "candidate schema로 normalize" 전제와 정합).

### F2. 구현 정확성 — 정확 (탐침 확인)

직접 호출 결과:
- 정상(run_id 일치) → `[]` ✓
- run_id 불일치 → `spec_item_candidates/0/agent_run_id: 'runX' has no matching audit_trace run_id` ✓
- 빈 trace → 모든 candidate가 미매칭 오류 ✓
- 무효 trace 이벤트(system role에 content_ref 누락) → `audit_trace/0: <root>: 'content_ref' is a required property` ✓

**False-pass 점검**: run_id를 가진 무효 trace 이벤트도 `trace_run_ids` 에 수집되므로(`validation.py:23-25`) 그 run_id에 대한 attribution 자체는 통과한다. 그러나 동일 이벤트의 스키마 오류가 결과 리스트에 남아 전체 검증은 비어있지 않게 되어 **실패 처리됨**. 즉 무효 trace를 두고 통과로 오인할 위험 없음. (설계 노트: attribution이 스키마 무효 이벤트의 run_id에도 근거할 수 있으나, 결과가 flat error list이고 어떤 오류든 실패이므로 계약상 무해.)

### F3. 회귀 테스트 — boundary matrix 완전, 빈 칸 없음

| 분기 | 계약 | 테스트 | 상태 |
|---|---|---|---|
| 정상 매칭 → `[]` | should NOT fire | `..._accepts_matching_run_ids` (`== []`) | ✓ over-strict guard |
| candidate run_id ∉ trace | should fire | `..._rejects_missing_trace_run_id` | ✓ |
| candidate schema 오류 노출 | should fire | `..._keeps_schema_errors_visible` | ✓ |
| spec/rubric/trace 세 섹션 각각 검사 | should fire (각) | `..._checks_each_candidate_section` parametrize×3 | ✓ |
| audit trace 이벤트 스키마 오류 노출 | should fire | `..._rejects_invalid_trace_event` (`audit_trace/0`+`content_ref` 핀) | ✓ |

- role payload 3종(system/agent/tool) 전수 매트릭스는 헬퍼가 아닌 **스키마 레벨** 의 기존 `test_agent_trace_schema_requires_role_payload` 에서 잠김. 헬퍼 테스트는 "스키마 오류가 헬퍼를 통해 노출됨"을 1케이스로 확인하는 것이 올바른 altitude — 빈 칸 아님.
- 정상 케이스 단언이 `== []` 라 over-strict guard 강함(정상 입력 오탐 시 실패).

### F4. export 표면 — 일치

`agent_runners/__init__.py` 가 `validate_candidate_audit_trace` 를 import 하고 `__all__` 에 추가. 테스트가 패키지 최상위 import 로 호출하여 공개 표면을 검증.

### F5. 문서 정량 주장 — 재계산 일치

- "183 tests pass" → `pytest`: **183 passed** ✓
- 컬렉션 "11 agent-runner / 48 CLI / 8 fixture / 21 model / 95 rule" → agent-runner `--collect-only` = **11** ✓ (합 183 정합)
- plan/HANDOFF/README/CHANGELOG v1.25 참조 일관 ✓
- `git diff --check` clean ✓
- work_log Decisions: "finish event를 candidate run마다 요구하지 않음" 은 §10.2 가 run_id 존재만 요구하고 finish-reason 회복은 별도 슬라이스라는 점과 정합 — 과대 주장 아님.

## Issues / Risks

비차단 관찰만:
- **[경미]** `..._keeps_schema_errors_visible` 단언이 `any("agent_run_id" in error)` — schema 오류와 attribution 오류 둘 다 `agent_run_id` 를 포함. 현재는 agent_run_id 삭제로 attribution 분기가 skip 되어 schema 경로만 발화하므로 의도대로 동작하나, `candidates:` prefix 로 핀하면 더 정밀.
- **[설계]** F2 — attribution run_id 수집이 스키마 무효 이벤트도 포함. false-pass 없음(F2 결론)이나 향후 오류 분류 소비 시 유의.
- **[견고성]** `candidates` 가 Mapping이 아니면 `validation.py:32` `.get` 에서 AttributeError 가능. 단 시그니처가 Mapping 이고 호출부는 dict 전달 — 계약 내 비이슈.

## Verdict

**합격 (pass).**

근거:
- 헬퍼가 §10.2 두 요구(스키마 통과 + run_id attribution)를 정확히 구현하고, 탐침상 정상/이상 분기가 모두 올바르게 동작(F1/F2).
- boundary matrix에 빈 칸 없음 — 모든 "should fire"/"should NOT fire" 분기가 비공허 회귀로 잠김. 정상 케이스 `== []` 로 over-strict guard 확보(F3).
- 문서 정량 주장 전부 재계산 일치, 과대 주장 없음(F5).
- 잔여 항목은 모두 비차단(정밀도/설계/견고성 노트).

## Outstanding items

- 모든 변경 uncommitted (working tree). 커밋 권한 Owner 결정.
- F2 설계 노트와 단언 정밀화는 선택적 개선 — 차단 아님.

## Reproduction

```bash
cd "<repo>"
PYTHONPATH=src python3 -c "
from assessment_harness.agent_runners import validate_candidate_audit_trace as v
c={'spec_item_candidates':[{'candidate_id':'SC1','agent_runner':'m','agent_run_id':'rX','integrity_status':'pending_check','proposed_item':{'id':'S1','text':'t','requirement_level':'must','source_ref':{'document_id':'D','start_line':1,'end_line':1}}}],'rubric_item_candidates':[],'trace_link_candidates':[]}
print(v(c,[{'run_id':'run_1','turn':0,'role':'system','content_ref':'x'}]))"
python3 -m pytest tests/test_agent_runner_contract.py -q
python3 -m pytest
python3 -m pytest tests/test_agent_runner_contract.py --collect-only | grep -c test_
git diff --check
```
