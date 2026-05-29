# Verification: Normalized Candidate Run Integrity Classifier (plan v1.27)

## Subject metadata

- **Date**: 2026-05-29
- **Requester**: Owner (kdtyohan@gmail.com) — "검증 진행해줘"
- **Verifier**: Claude (independent audit)
- **Target slice**: `classify_candidate_run_integrity` / `CandidateRunIntegrityResult` (`integrity.py`) 신설 + 회귀, plan v1.27 승격, 문서 갱신.
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.27 — §5.4 integrity_status enum (lines 400-411, 특히 403 `validated` 정의, 404 `invalid_reference`, 405 `quote_mismatch`, 411 run-integrity→compacting 흐름), §10.2 (line 1194 attribution), line 1168 (invalid candidate가 deterministic assessment로 유입 금지), v1.27 §15 changelog (lines 1322-1334).
- **Source of work verified**: working tree, uncommitted.

## Scope

1. §5.4 integrity_status enum 정의 ↔ 분류기가 emit하는 status 의미 일치.
2. 분류 분기 정확성 (`integrity.py`) — 탐침.
3. mutation 비파괴 / 복사본 정확성.
4. 회귀 테스트 boundary matrix 완전성.
5. 문서 정량/서술 주장 재계산.

## Methodology

- 계약 정독: §5.4 enum 전문(400-411), §10.2 attribution, line 1168, v1.27 changelog.
- 코드 정독: `integrity.py`(73 lines), `validation.py` 오류 prefix 규약 대조.
- 동작 탐침: `PYTHONPATH=src python3 -c` 로 분류기 직접 호출 — clean run, 내부 dangling reference run.
- 테스트: `pytest`, `--collect-only`, `git diff --check`.

## Findings

### F1. 구현된 분기 — 정확

- clean run(오류 없음) → `validated`, 모든 candidate 복사본 `validated` (탐침 ✓, 테스트 `..._marks_valid_run_candidates_validated`).
- schema 오류(candidate/audit) → `schema_violation`. prefix 판정 `_is_schema_error`(`integrity.py:53-54`)가 `candidates:` / `audit_trace/` 로 정확히 식별. attribution 오류 prefix(`spec_item_candidates/0/agent_run_id:`)와 충돌 없음 → precedence(schema 우선) 정확.
- attribution 누락 → `invalid_reference` (탐침 ✓).
- **mutation 비파괴**: `_with_integrity_status` 가 `copy.deepcopy` 로 새 dict 생성, 원본 미변경. 테스트가 원본 `pending_check` 유지 단언 ✓.
- invalid_reference 출력이 여전히 candidates schema-valid (테스트 ✓; enum에 포함되므로).

### F2. **[블로킹] `validated` 리터럴 과대부여 — §5.4 정의와 불일치**

§5.4:403 은 `validated` = **"모든 Rule 0 항목 통과. compacting 대상이 됨"** 으로 정의하고, §5.4:411 은 "run integrity check를 통과(`validated`)하고 compacting을 거쳐 rule engine에 입력" 으로 못박는다. 즉 canonical 계약에서 **run integrity check 통과 = validated = 모든 Rule 0 통과**.

그러나 분류기는 `validate_candidate_audit_trace`(candidate schema + audit schema + run attribution)만 통과하면 `validated` 를 부여한다. §5.4:404 `invalid_reference`(dangling rubric/spec id, evidence_quote spec_id 불일치)와 §5.4:405 `quote_mismatch`(evidence_quote가 spec_item.text substring 아님)는 **검출하지 않으면서** `validated` 를 emit한다.

**탐침으로 입증** — 다음 run이 오류 0개로 `validated` 분류됨:
```
trace_link.rubric_id = 'R_DOES_NOT_EXIST'   (dangling)
trace_link.spec_ids  = ['S_DOES_NOT_EXIST'] (dangling)
evidence_quote.spec_id = 'S_MISMATCH', quote = 'totally unrelated quote' (불일치 + non-substring)
→ STATUS: validated, ERRORS: ()
```
§5.4 기준 이 run은 `invalid_reference`(+`quote_mismatch`)여야 한다. 그런데 `validated` 로 표시된다.

이것은 **계약 내부 불일치**다: §5.4 enum 정의(validated = 모든 Rule 0)와 v1.27 §15 changelog 동작(schema+attribution만으로 validated, deep Rule 0 deferred)이 `validated` 의 보장 수준에 대해 서로 다르게 말한다. CLAUDE.md "Cross-check the contract against itself … Internal contract inconsistency is a blocking finding" 에 해당. 또한 work_log 가 "compacting can later consume only `validated` candidate runs" 라 적었듯, dangling-reference candidate가 `validated` 로 승격되면 §5.4:411 흐름상 compacting/assessment로 유입될 자격을 얻어 line 1168("invalid candidate가 deterministic assessment 판정으로 유입되지 않음")을 위반하게 된다. (오늘은 compacting 미구현이라 live 손상은 없으나, 부여되는 상태 리터럴의 전제가 spec보다 약하다.)

### F3. **[블로킹] boundary matrix 빈 칸 — invalid_reference(내부) / quote_mismatch 미검출·미테스트**

§5.4:404 `invalid_reference` 의 **문자 그대로의 예시**(dangling rubric/spec id, evidence_quote spec_id 불일치)는 분류기가 검출하지 않는다. 분류기는 `invalid_reference` 를 **trace run attribution 누락**이라는 다른 조건에 재할당했고, §5.4가 열거한 내부 dangling 조건에는 어떤 status도 부여하지 않는다(`validated` 로 흡수됨, F2). `quote_mismatch` 는 분류기가 **결코 생성하지 않는다**. 두 조건 모두 회귀 테스트 없음.

work_log Next steps #1 "Add deeper candidate Rule 0 integrity checks for candidate-internal references" 는 이 누락을 후속 작업으로 미루고 있다. CLAUDE.md 는 누락된 over-strict guard를 "future enhancement / 후속 보강"으로 재명명하는 것을 명시적으로 금지한다 — 빈 칸은 차단 사유다.

### F4. invalid_reference 매핑 — 계약 명시 필요 (F2/F3와 연동)

attribution 누락 → `invalid_reference` 매핑 자체는 "candidate가 존재하지 않는 run_id를 참조"라는 점에서 dangling reference로 해석 가능하나, §5.4:404 의 예시는 candidate-내부 참조였다. 어느 reconciliation 경로를 택하든 `invalid_reference` 가 (a) 내부 dangling, (b) trace attribution 중 무엇을 덮는지 계약에 명시해야 literal이 코드와 일치한다.

### F5. 문서 정량 — 재계산 일치

- "191 tests pass" → `pytest`: **191 passed** ✓
- "19 agent-runner / 48 / 8 / 21 / 95" → agent-runner = **19** ✓ (합 191)
- v1.27 참조 일관, `integrity.py` 구조 기재, `git diff --check` clean ✓
- HANDOFF/work_log 는 deep Rule 0 deferral 을 솔직히 기재(과대 주장 아님). 단 F2의 계약 불일치는 문서가 §5.4 정의를 amend하지 않은 채 남겨둔 것이 문제.

## Issues / Risks

- **[블로킹] F2**: `validated` 가 §5.4 정의("모든 Rule 0 통과")보다 약한 전제(schema+attribution)로 부여됨 — 계약 내부 불일치 + 상태 과대부여.
- **[블로킹] F3**: §5.4 정의상의 `invalid_reference`(내부 dangling)와 `quote_mismatch` 가 미검출·미테스트 — boundary matrix 빈 칸.
- **[비블로킹] F4**: `invalid_reference` 의미 범위가 계약에 미명시.

## Verdict

**조건부 합격 (conditional pass).**

구현된 분기(validated/schema_violation/invalid_reference-attribution, mutation 비파괴, precedence)는 기계적으로 정확하고 비공허 회귀로 잠겨 있다(F1/F5). 그러나 분류기가 §5.4 가 "모든 Rule 0 통과"로 정의한 `validated` 를 schema+attribution만으로 부여하여 **계약 내부 불일치**를 만들고, §5.4가 열거한 `invalid_reference`(내부 dangling)·`quote_mismatch` 조건을 검출/테스트하지 않는다(F2/F3, 블로킹).

**합격 조건 (Owner 결정 필요 — 어느 쪽이 canonical인지):**
1. **계약 reconciliation 중 택1**
   - (a) §5.4를 **staged integrity 모델**로 개정: 본 분류기의 `validated` 는 "구조적 검증(candidate/audit schema + run attribution) 통과"를 의미하고, candidate-내부 reference·quote 검사는 별도 후속 단계로 명시하여 그 단계의 status(invalid_reference/quote_mismatch)와 "compacting 자격 status"를 분리. → `validated` 가 "모든 Rule 0"로 오독되지 않게.
   - (b) deep Rule 0 구현 전까지 분류기가 **terminal `validated` 를 emit하지 않도록** 변경(중간 status 유지). 어떤 run도 실제 모든 Rule 0를 통과하기 전에 `validated` 로 라벨되지 않게.
2. reconciliation 후, §5.4 정의상의 `invalid_reference`(내부 dangling rubric/spec id, evidence_quote spec_id 불일치)와 `quote_mismatch`(non-substring)에 대한 **검출 + 비공허 회귀**를 추가하여 빈 칸을 잠근다.
3. `invalid_reference` 가 내부 dangling / trace attribution 중 무엇을 덮는지 계약에 명시(F4).

## Outstanding items

- 모든 변경 uncommitted. 커밋 권한 Owner 결정.
- F2/F3 는 검증자가 임의 수정하지 않음 — Owner가 reconciliation 방향(1a vs 1b)을 결정해야 진행 가능.

## Follow-up verification — staged model 채택(옵션 A), v1.28 재검증

Owner가 옵션 A(계약을 staged 모델로 개정)를 선택해 개발측에서 반영. 독립 재확인 결과:

- **계약 §5.4 개정 정합**: enum이 8값으로 확장됨 — `pending_check` / `structurally_validated` / `validated` / `trace_attribution_error` / `invalid_reference` / `quote_mismatch` / `schema_violation` / `blocked_by_runner_error` (plan:408-413). `structurally_validated` = "schema+attribution 통과, deep Rule 0 미통과, **compacting 대상 아님**", `validated` = "내부 reference + quote/source grounding 포함 모든 candidate Rule 0 통과, compacting 대상"으로 명시. `trace_attribution_error`(귀속 누락)를 `invalid_reference`(내부 dangling)와 분리. F4 매핑 모호성 해소.
- **스키마 self-discovery 일치**: `candidates.schema.json` integrity_status enum에 `structurally_validated` / `trace_attribution_error` 추가됨(8값). 분류기가 찍는 상태가 schema-valid임을 탐침으로 확인(`validate("candidates", result.candidates) == []`).
- **F2(과대부여) 해소**: `integrity.py` 가 더 이상 `validated`를 emit하지 않음. 분류기 3분기 = `structurally_validated` / `schema_violation` / `trace_attribution_error`. **이전 재현 케이스(내부 참조 전부 깨짐)를 직접 재탐침 → `structurally_validated`**(NOT validated), §5.4상 compacting 비대상이므로 평가 유입 자격 없음. over-claim 사라짐.
- **F3(빈 칸) 해소**: 개정 계약에서 `invalid_reference` / `quote_mismatch` 는 구조 분류기가 아니라 **명시적으로 후속 deep Rule 0 슬라이스**의 책임(plan:1340-1342). 구조 분류기 자신의 boundary matrix는 완전 — 5개 회귀로 잠김: clean→structurally_validated, **dangling-internal→structurally_validated(over-promote 차단, `..._does_not_claim_deep_rule_zero_validation`)**, candidate schema→schema_violation, audit schema→schema_violation, attribution→trace_attribution_error. 모두 `==` exact-equality 단언이라 `validated` 회귀 시 재실패(under-strict guard). mutation 비파괴 + 원본 pending_check 유지도 유지.
- **재계산 일치**: `pytest` → **192 passed**; agent-runner `--collect-only` = **20**; `git diff --check` clean; HANDOFF/README/CHANGELOG/work_log v1.28 staged-model 서술로 갱신, "validated = 유일한 compacting-eligible status" 일관.

### 비블로킹 관찰
- plan:1584 (v1.4 **변경 이력** 항목, 보강 A)은 여전히 옛 6값 enum을 나열한다. 이는 **정본 규범이 아니라 v1.4 시점의 dated changelog 기록**이며 §5.4가 단일 정본 — 블로킹 아님(오히려 과거 항목을 현재 enum으로 고치면 history 왜곡). 다만 그 줄 끝 `(§5.4)` 교차참조가 변경된 섹션을 가리켜 독자 혼동 소지는 있음(선택적 정리 대상).

### 갱신 판정: **합격 (pass).** 직전 조건부 합격의 블로킹 2건(F2 over-claim, F3 빈 칸)이 옵션 A staged 모델로 §5.4·schema·코드·테스트 전반에서 일관 해소됨. `validated`/`invalid_reference`/`quote_mismatch`는 계약에 명시적으로 후속 단계로 scope되어, 다음 deep Rule 0 슬라이스의 lock list가 분명함.

## Reproduction

```bash
cd "/workspace/assessment_poc"
PYTHONPATH=src python3 -c "
from assessment_harness.agent_runners import classify_candidate_run_integrity as cls
c={'spec_item_candidates':[{'candidate_id':'SC1','agent_runner':'m','agent_run_id':'run_1','integrity_status':'pending_check','proposed_item':{'id':'S1','text':'Refund handling required.','requirement_level':'must','source_ref':{'document_id':'D','start_line':1,'end_line':1}}}],'rubric_item_candidates':[],'trace_link_candidates':[{'candidate_id':'TC1','agent_runner':'m','agent_run_id':'run_1','integrity_status':'pending_check','proposed_item':{'rubric_id':'R_X','spec_ids':['S_X'],'evidence_quotes':[{'spec_id':'S_MISMATCH','quote':'unrelated','verification_mode':'token_sequence'}]}}]}
r=cls(c,[{'run_id':'run_1','turn':0,'role':'system','content_ref':'x'}])
print(r.integrity_status, r.errors)  # -> validated ()  (should be invalid_reference/quote_mismatch per 5.4)"
python3 -m pytest tests/test_agent_runner_contract.py -q
python3 -m pytest
git diff --check
```
