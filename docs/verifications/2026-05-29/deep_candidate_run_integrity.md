# Verification: Deep Candidate Run Integrity Classifier (plan v1.29)

## Subject metadata

- **Date**: 2026-05-29
- **Requester**: Owner — "다음작업 검증해줘"
- **Verifier**: Claude (independent audit)
- **Target slice**: `classify_deep_candidate_run_integrity` (`integrity.py`) 신설 + 회귀 4종, plan v1.29 승격, 문서 갱신. structurally_validated → validated/invalid_reference/quote_mismatch 승격·격리 단계(직전 라운드에서 후속으로 scope된 것).
- **Canonical spec reference**: plan v1.29 — §5.4 integrity_status enum (lines 405-415, 특히 412 quote_mismatch / 411 invalid_reference 정의), §6 Rule 0 (`run_rule_zero` diagnostic 코드), §5.3 verification_mode(ai_judgement vs token_sequence, line 923), v1.29 changelog (1329-1347).
- **Source of work verified**: working tree, uncommitted.

## Scope

1. deep classifier 분기 정확성 + structural 단계 short-circuit.
2. `_QUOTE_MISMATCH_CODES` 분류표가 Rule 0 19개 코드를 정확/완전하게 partition하는지.
3. §5.4 enum 정의 ↔ 코드 routing 일치.
4. ai_judgement over-strict guard.
5. mutation 비파괴.
6. boundary matrix 완전성.
7. 문서 정량 주장.

## Methodology

- 코드 정독: `integrity.py` 전체, `rules.py` 의 `run_rule_zero` diagnostic 코드 enumerate(19종).
- 동작 탐침: `PYTHONPATH=src python3 -c` 로 deep classifier 직접 호출 — clean/A(spec_id mismatch)/B(spec grounding)/C(mixed) 케이스.
- 테스트: `pytest`, `--collect-only`, `git diff --check`.

## Findings

### F1. 분기 로직 + short-circuit — 정확

- structural 단계 미통과(schema_violation/trace_attribution_error)면 Rule 0 미실행, structural 결과 그대로 반환(`integrity.py:61-63`). malformed 입력에 Rule 0 안 돌림.
- diagnostics 없음 → `validated` 승격(테스트 `..._promotes_clean_run_to_validated`, `==` exact). mutation 비파괴(원본 pending_check 유지 단언) + 출력 schema-valid.
- 분류: quote 집합 외 코드가 하나라도 있으면 `invalid_reference`, 전부 quote 집합이면 `quote_mismatch`(`integrity.py:82-86`). precedence(reference 우선) 탐침 C에서 확인.

### F2. ai_judgement over-strict guard — 정확 (중요)

`..._does_not_over_reject_ai_judgement_quote`: ai_judgement quote가 spec text substring이 아니어도 `validated`, token mismatch diagnostic 미발생. §5.3:923(token_sequence만 결정적 검사) 계약을 `run_rule_zero` 통해 정확히 상속. 가장 중요한 over-strict 방향 잠김.

### F3. **[조건] §5.4 quote_mismatch 정의 ↔ 코드 routing 불일치 (spec-silent-but-code-enforced)**

§5.4:412 는 `quote_mismatch` 를 **"evidence_quote가 spec_item.text의 substring이 아님"** 으로 좁게 정의한다(`invalid_reference` 줄과 달리 "등" 없음 → 망라적/특정적으로 읽힘). 그러나 `_QUOTE_MISMATCH_CODES`(`integrity.py:94-102`)는 evidence_quote 와 무관한 **spec/rubric source grounding** 코드까지 포함한다:
- `spec_text_not_in_snapshot_span`, `spec_quote_not_in_snapshot_span`, `rubric_quote_not_in_snapshot_span` — spec/rubric 텍스트가 cited source span에 grounding 안 됨(evidence_quote substring 문제 아님).

**탐침 B로 입증**: spec text를 source 미grounding 상태로 만들면 → `quote_mismatch` 로 분류됨. §5.4 정의상 quote_mismatch 는 evidence_quote에 한정되는데, 코드는 spec grounding 실패를 여기로 보낸다. v1.29 changelog(1338-1342)는 이 broadening("spec/rubric source quote mismatch … quote_mismatch")을 기술했으나, **정본 §5.4 enum 줄(412)은 amend되지 않아** changelog와 §5.4가 quote_mismatch 범위에 대해 불일치한다.

또한 source_ref-family 진단 7종(`*_source_ref_unknown_document`, `*_source_ref_span_invalid`, `evidence_source_ref_*`, `source_document_missing/hash_mismatch`)이 invalid_reference로 가는데, §5.4 invalid_reference 정의("dangling rubric/spec id, evidence_quote spec_id 불일치 등")는 source_ref grounding/document 오류를 명시하지 않는다. enum 설명이 19개 코드 중 source-grounding 계열 routing을 규범적으로 정의하지 않음 → **계약 amendment 필요**.

**비-safety**: invalid_reference 와 quote_mismatch 모두 비-validated·비-compacting-eligible(§5.4: validated만 compacting 대상)이므로, 어느 버킷이든 run은 compacting/assessment에서 제외됨 — line 1168 안전 불변식은 유지된다. 즉 이번 gap은 직전 라운드의 validated 과대부여(safety hole)와 달리 **triage 라벨 정밀도/계약 일관성** 문제다.

### F4. **[조건] 분류표 boundary matrix 빈 칸**

Rule 0 19개 코드 routing 중 테스트된 cell은 2개뿐: `dangling_rubric_reference`→invalid_reference, `evidence_quote_token_sequence_mismatch`→quote_mismatch (+ ai_judgement 비발화). 미테스트:
- `evidence_quote_spec_id_mismatch`→invalid_reference — **§5.4가 직접 든 invalid_reference 예시**인데 회귀 없음(탐침 A로 동작은 확인).
- snapshot-span grounding 코드(`spec_text/spec_quote/rubric_quote_not_in_snapshot_span`)→quote_mismatch — 미테스트(그리고 F3의 계약 모호 대상).
- 혼합(reference+quote 동시)→invalid_reference precedence 분기 — 미테스트(탐침 C로 확인).

분류표의 set membership은 §5.4가 정의하는 계약 경계인데 대부분 untraced. CLAUDE.md "every enumerated boundary value … not just one sample", "untraced branch is a blocking finding" 대상.

### F5. 문서 정량 — 재계산 일치

- "196 tests pass" → `pytest`: **196 passed** ✓; agent-runner `--collect-only` = **24** ✓ (합 196); `git diff --check` clean.
- HANDOFF/README/CHANGELOG/work_log v1.29 일관(확인). deep slice의 후속 범위(extract/compact/review_queue/recovery) 솔직히 기재.

## Issues / Risks

- **[조건] F3**: §5.4 quote_mismatch(및 invalid_reference) 정의가 코드의 source-grounding routing과 불일치 — spec-silent-but-code-enforced. (비-safety, but 계약 일관성/triage 정밀도.)
- **[조건] F4**: 분류표 대부분 untested — 특히 §5.4 자신의 invalid_reference 예시(evidence_quote_spec_id_mismatch)와 precedence 분기, snapshot-span quote 코드.
- **[비블로킹]** `_QUOTE_MISMATCH_CODES` 는 하드코딩 집합 — 향후 Rule 0 코드 추가 시 기본 invalid_reference로 빠짐(유지보수 fragility). 동기화 가드 없음.

## Verdict

**조건부 합격 (conditional pass).**

분기 로직·structural short-circuit·ai_judgement over-strict guard·mutation 비파괴는 정확하고 비공허 회귀로 잠겼으며(F1/F2), 안전 불변식(invalid run은 compacting 제외)은 유지된다(F3). 그러나 §5.4 enum 정의가 코드의 source-grounding 진단 routing과 불일치하고(F3), diagnostic→status 분류표가 대부분 untested(F4)다.

**합격 조건:**
1. **§5.4 enum reconciliation**: quote_mismatch 줄(412)을 코드 동작에 맞게 amend(예: "evidence_quote substring 불일치 **및 spec/rubric source span grounding 불일치**") 하거나, 코드에서 spec/rubric grounding 코드를 다른 버킷으로 재routing. source_ref-family 19개 코드의 버킷을 §5.4에 규범적으로 명시(changelog만으로 부족). — 어느 방향이 canonical인지 결정 필요(broaden quote_mismatch vs 재routing).
2. **분류표 cell 회귀 추가**: 최소 (a) `evidence_quote_spec_id_mismatch`→invalid_reference(§5.4 예시), (b) snapshot-span grounding 코드 1종→quote_mismatch, (c) 혼합 reference+quote→invalid_reference precedence. reconciliation 후 source-grounding 버킷도 그에 맞춰 잠금.

## Outstanding items

- 모든 변경 uncommitted. 커밋 권한 Owner 결정.
- F3/F4 는 검증자가 임의 수정하지 않음 — reconciliation 방향(조건 1)은 Owner/개발측 결정.

## Follow-up verification — 3-way 분리 채택(옵션 C), v1.30 재검증

Owner가 3-way 분리(grounding 전용 상태 신설)를 선택, 개발측 반영. 독립 재확인:

- **계약 §5.4 9-state 개정**: `source_grounding_mismatch` 추가. `quote_mismatch`는 "`token_sequence` evidence_quote substring 실패"로 좁힘. `invalid_reference`는 duplicate id + evidence 누락/공백 포함으로 명시. precedence `invalid_reference > source_grounding_mismatch > quote_mismatch`를 §5.4 본문에 명시. schema enum도 동기 추가(9값).
- **코드 ↔ 계약 정확 일치 (완전 분할 + fail-safe)**: Rule 0 **20개 코드**(`code="..."` 18 + 루프 기반 `duplicate_spec_id`/`duplicate_rubric_id` 2)가 3개 frozenset에 **정확히 1:1 분할**(invalid 7 / grounding 12 / quote 1 = 20, 누락·중복 없음). 각 집합이 §5.4 설명과 byte-수준으로 대응(코드 정독 확인). `_deep_rule_zero_status`(integrity.py:126-135)는 미분류(미지) 코드를 `invalid_reference`로 보내는 fail-safe 포함 → 직전 라운드의 하드코딩 fragility 해소.
- **F3 해소**: 직전 §5.4(quote_mismatch=evidence substring only) ↔ 코드(spec/rubric grounding을 quote로) 불일치가 사라짐. grounding은 전용 상태로 분리, §5.4 설명이 코드 버킷과 일치.
- **F4 해소**: 회귀 추가 — dangling→invalid_reference, evidence_quote_spec_id_mismatch→invalid_reference(§5.4 예시), spec_text_not_in_snapshot_span→source_grounding_mismatch, 혼합(ref+grounding+quote)→invalid_reference precedence, schema가 source_grounding_mismatch 수용(test_models), ai_judgement over-strict guard 유지.
- **탐침으로 분할·precedence 전수 확인**: clean→validated / 순수 quote→quote_mismatch / 순수 rubric grounding(span invalid)→source_grounding_mismatch / grounding+quote→source_grounding_mismatch(grounding>quote) / ref+grounding+quote→invalid_reference(최상위). precedence 체인 검증.
- **재계산 일치**: `pytest` → **200 passed** (27 agent-runner + 48 CLI + 8 fixture + 22 model + 95 rule); `git diff --check` clean; HANDOFF/README/CHANGELOG/work_log v1.30 일관.

### 비블로킹 관찰
- 20개 코드가 각각 개별 회귀를 갖지는 않음(버킷당 대표 + precedence + fail-safe로 커버). 분할이 구성상 망라적이고 fail-safe가 누락을 안전 버킷으로 보내며 §5.4 설명과 집합이 일치함을 정독 확인 → 차단 아님. 코드별 parametrize는 gold-standard 선택지.

### 갱신 판정: **합격 (pass).** 직전 조건부 합격의 F3(계약 gap)·F4(빈 칸)가 옵션 C 3-way 분리로 §5.4·schema·코드·테스트 전반에서 일관 해소. diagnostic→status 매핑이 완전 분할 + fail-safe + 비공허 회귀로 잠김.

## Reproduction

```bash
cd "<repo>"
PYTHONPATH=src python3 -c "
from pathlib import Path
from assessment_harness.agent_runners import MockFixtureRunner, normalize_result_candidates, classify_deep_candidate_run_integrity as deep
from assessment_harness.models import load_source_snapshot
b=Path('fixtures/clean_assignment'); snap=load_source_snapshot(b/'source_manifest.yaml')
def fresh():
    res=MockFixtureRunner(b,run_id='mock_run').run(b/'source/spec.md',b/'source/rubric.md',[],1,{'rules':{}})
    return normalize_result_candidates(res),res.audit_trace
c,t=fresh(); c['spec_item_candidates'][0]['proposed_item']['text']='NOT IN SOURCE SPAN'
print(deep(c,t,snap).integrity_status)  # -> quote_mismatch (spec grounding, 5.4 gap)
c,t=fresh(); c['trace_link_candidates'][0]['proposed_item']['evidence_quotes'][0]['spec_id']='S_X'
print(deep(c,t,snap).integrity_status)  # -> invalid_reference (5.4 example, untested)"
python3 -m pytest
git diff --check
```
