# Ideation v2.2 — Rubric Lint Rules (역방향 검증 가족)

> **Revised 2026-05-27** (final 잠금과 동일 날짜): §9.2 잔여 1번(L6 안전장치 구체 형태)과 잔여 3번(L8 trace_drift 처리)을 Owner가 즉시 결정해 해소. 그 결과 L6를 §7의 v1.12+ 슬라이스에서 **v1.11 슬라이스로 승격**(L1+L5+L6 한 묶음). 구현 진입 중 Owner가 L6의 `bonus-only` 명칭/payload와 `qualitative` 포함 문구의 모순을 해소하여, L6는 bonus trace만 대상으로 확정하고 qualitative 정합성은 Rule 2 계열 후속 규칙으로 분리했다. 자세한 결정 근거는 `docs/daily_logs/2026-05-27/work_log.md`의 "Ideation v2.2 Revision" 및 "Phase 0 Rule L6 Implementation" 절 참조. 본 in-place 개정으로 v2.3 별도 문서는 만들지 않는다(plan v1.10 → v1.13 버전 갱신과 짝).

## 0. 문서 목적과 위치

v2.2는 v2.1을 대체하지 않는다. v2.1의 핵심 invariant("모든 scored rubric item은 candidate-facing spec의 항목으로 trace 가능해야 한다")는 그대로 유효하며, v2.2는 그 **역방향 가족(inverse rule family)**을 신설하자는 제안이다.

본 문서는 ideation 단계이며 plan v1.11로의 승격은 별도 검토 후 진행한다. 즉 본 문서가 곧 구현 지시는 아니다 (HANDOFF가 사실상 spec이 되는 안티패턴 회피).

### 0.1 Spec-precedence 위치 (확정)

Owner 결정: 최신 ideation 문서가 ideation 계층 내에서 가장 앞에 온다.

```text
plan v1.10  >  ideation v2.2  >  ideation v2.1  >  ideation v2  >  ideation v1
```

영역 한정 없음. v2.1과 v2.2가 같은 영역을 다루면 v2.2가 우선한다. v2.2가 다루지 않는 모든 영역(v2.1 §1.1~§1.5 문제 정의, §2 invariant, §5 MVP 범위, §6 데이터 모델 초안, §10 LLM 역할 등)에서 v2.1은 여전히 canonical이다. plan v1.10은 구현된 모든 영역(Rule 0~3)에서 가장 위에 있다.

---

## 1. 동기

### 1.1 v2.1까지의 룰은 모두 coverage 방향이다

plan v1.10 §6에 구현된 Rule 0~3는 모두 같은 질문을 던진다.

> "있어야 할 것이 있는가?"

- Rule 0: 참조가 깨졌는가 (없는 ID, 누락된 evidence, snapshot 불일치)
- Rule 1: scored rubric에 trace가 있는가
- Rule 2: must spec에 scored 채점이 있는가
- Rule 3: optional spec에만 trace된 scored rubric의 가중치가 임계 미만인가

이 네 룰은 **누락/불충분**을 본다.

### 1.2 거울 문제 — 안 다루는 영역

채점 설계에는 그 거울 문제가 있다.

> "있으면 안 되는 것이 들어와 있는가?"

- 같은 명세를 본채점과 가산에서 동시에 채점하는가
- 가산이 본채점만큼 변별력을 갖는가 (= 사실상 본채점인데 가산이라고 표기되어 있는가)
- 명세에 명시되지 않은 평가축이 채점에 스며들어 있는가
- 명세가 금지한 행동을 채점에서 보상하는가
- 두 채점 기준이 서로 모순되는가

이 질문들은 현재 Rule 0~3에서 어디에도 잡히지 않는다. Rule 1이 일부 인접하지만(scored rubric에 trace가 없으면 잡힘) "trace는 있으나 잘못 걸려있는" 경우와 "명세에서 금지한 것을 채점하는" 경우는 통과한다.

### 1.3 lint 비유

이 패턴은 소프트웨어 lint와 같다. lint는 컴파일러가 통과시키는 코드 중 "구문은 맞지만 안 좋은" 것을 자동 검출한다. v2.2의 lint rule family는 **trace_links schema는 통과하지만 채점 설계상 안 좋은** 패턴을 검출한다.

### 1.4 사용자가 식별한 1차 동기

기획안에는 **기입 채점 영역(명시된 요구사항을 평가)**과 **창의 채점 영역(명시되지 않은 잘함을 평가)**이 분리되어 있다. 두 영역이 분리된 채로 관리되면, 창의 영역이 기입 영역을 잠식하거나 명세에 없는 — 또는 명세가 금지한 — 기준이 창의 영역으로 스며들 수 있다. v2.2의 1차 목표는 이 잠식을 시스템적으로 잡는 것이다.

---

## 2. 핵심 가설 — Inverse Invariant

v2.1의 invariant를 다음과 같이 확장한다.

> (v2.1) 모든 scored rubric은 spec에 trace 가능해야 한다.
> (v2.2) 모든 rubric은 spec과 모순되지 않아야 하며, 같은 spec을 중복 채점해서는 안 된다.

이 두 invariant는 독립적으로 검증 가능하다. v2.1이 *coverage*를, v2.2가 *exclusion*을 잠근다. 두 축 모두 잠겨야 채점 설계의 정합성이 시스템적으로 보장된다.

---

## 3. 분류 체계

본 가족(이하 "Lint Rules")의 모든 룰은 다음 세 계층 중 하나에 속한다.

- **L-DET (deterministic)**: 현재 schema와 deterministic core만으로 즉시 구현 가능. Phase 0 범위.
- **L-SEM (semantic)**: verifier-agent (`ai_judgement` 경로) 필요. Phase 2 이후.
- **L-SCH (schema-dependent)**: 스키마 확장이 전제. 확장 후 L-DET 또는 L-SEM로 흡수.

**Owner 확정 (본 문서)**:

- Rule 가족 명명은 `Rule L1, L2, ...` 사용. coverage 가족(`Rule 0~3`)과 시각적으로 구별되고 lint 가족임을 명시.
- Finding type 명명은 §4~§5에서 제시한 후보(`double_scored_spec`, `bonus_weight_encroachment`, ...) 그대로 사용. 가독성을 최우선 기준으로 채택.

---

## 4. Lint Rules — L-DET (deterministic, Phase 0 가능)

### Rule L1. Cross-role Double Scoring

- **상태**: 채택 (Owner 확정, v1.11 승격).
- **조건**: 동일 `spec_id`가 `evaluation_role == scored` rubric의 `trace_links`와 `evaluation_role == bonus` rubric의 `trace_links` 양쪽에서 참조됨.
- **결과**: `medium`, `provisional`.
- **Finding type**: `double_scored_spec`.
- **의도**: 같은 명세가 본채점과 가산 양쪽에서 점수화되어 실질 가중치가 부풀려지는 것을 검출. 사용자가 §1.4에서 식별한 잠식 케이스의 가장 직접적인 형태.
- **한계**: 정당한 경우 존재 — scored가 기본 동작, bonus가 같은 명세의 심화/edge case 처리인 경우. 그래서 high가 아닌 medium으로 둠.
- **심화 확인 장치 (Owner 확정)**: medium finding을 단순 발화로 끝내지 않고 다음 두 경로로 사람 검토를 보장한다.
  - (a) **Finding payload 확장**: `double_scored_spec` finding은 한 payload에 `scored_rubric_id`, `bonus_rubric_id`, `spec_id`, 양쪽 rubric의 `title` / `description` 또는 `text`, 양쪽 link의 `semantic_status`를 동봉한다. 리뷰어가 한 화면에서 정당/부당을 구별할 수 있어야 한다.
  - (b) **Review queue 별도 entry**: 같은 발화에 대해 `review_queue.yaml`에 `type: double_scoring_review` entry를 추가한다. semantic verifier가 "정당한 심화"로 판정하면 `human_overridden`으로 통과, 부당으로 판정하면 finding이 final review에서 confirmed로 승급.
  - 비용 측면: payload 확장은 무료, review queue entry는 verifier 호출 1건 추가. owner 결정으로 둘 다 도입.
- **two-directional regression 가드**:
  - under-strict: 같은 spec_id가 scored+bonus 양쪽 trace → 발화 + payload에 양쪽 rubric_id 포함.
  - over-strict A: spec_id가 scored에만 trace → 미발화.
  - over-strict B: 다른 spec_id끼리 (한쪽은 scored, 다른쪽은 bonus) → 미발화.

### Rule L2. Bonus Weight Encroachment

- **상태**: 채택 (Owner 확정, v1.12+ 분리 슬라이스).
- **조건**: `sum(weight of role==bonus rubrics) / sum(weight of role==scored rubrics) >= policy.lint.bonus_ratio_threshold` (PoC 기본값: `0.25`)
- **결과**: `medium`, `provisional`.
- **Finding type**: `bonus_weight_encroachment`.
- **의도**: 가산이 본채점만큼 변별력을 갖는다면 사실상 scored임에도 응시자에게 "bonus"로 표기된다 — 정보 공개와 채점 위상의 불일치.
- **정책 파라미터**: `policy.lint.bonus_ratio_threshold`. §8에 정의. Owner 결정: "기업마다 정책이 다르므로 본 프로젝트가 임계값을 고정할 이유 없음 — 정책 파일로 노출하고 사용자가 자기 팀 기준으로 조정".
- **한계**: 비율은 절대 기준이 없다. 0.25는 PoC 기본값일 뿐 권위값이 아님.

### Rule L3. Spec Over-trace

- **상태**: **기각 (Owner 결정)**.
- **기각 사유**: 응시자가 명세 한 줄의 실질 가중치를 모르더라도 명세를 따르는 것이 원칙. 비대칭 정보 제공이 아니라 모든 정보가 공개된 상태라면 평가자의 가중치 분배는 설계 재량에 속한다. 따라서 본 룰은 응시자 보호 차원에서 추가 가치 없음.
- **잔여 위험 (기록용)**: 평가자가 같은 spec에 여러 채점을 걸어두고 본인이 실질 가중치를 의식 못 하는 경우는 본 룰로 잡히지 않는다. 이는 응시자 보호가 아닌 평가 설계 품질 영역이며, 향후 "설계 검증" 확장(§5 Rule L9 참고)에서 다룬다.
- (원안 — 미적용) 조건: 단일 `spec_id`가 `evaluation_role == scored` rubric trace에서 `>= policy.lint.spec_trace_fanout_threshold`회 참조 (PoC 기본값 후보: `4`). 결과: `informational`, `provisional`. Finding type 후보: `spec_overtraced`.

### Rule L4. Duplicate Trace Link

- **상태**: 채택 (Owner 확정, v1.12+ 분리 슬라이스, lint 가족 독립 유지).
- **조건**: 동일 `(rubric_id, spec_id)` 쌍이 `trace_links`에 둘 이상.
- **결과**: `medium`, `provisional`.
- **Finding type**: `duplicate_trace_link`.
- **의도**: 데이터 품질 결함. 후속 단계(semantic verification, gate 승격, scoring 계산)에서 중복 가중되거나 양쪽 link의 `semantic_status`가 충돌할 수 있음.
- **위치 결정 (Owner 확정)**: Rule 0(reference integrity)에 흡수하지 않고 lint 가족 독립. 사유: input error로 차단(exit 2, 작업 중단)하면 일률적이지만, 실제 duplicate는 (a) 실수 (b) 의도(가중치 강조) (c) 다른 evidence/rationale을 다는 목적의 분리 link 중 하나일 수 있다. 사람이 보고 판단(통과/감점/수정)하도록 lint finding으로 띄우는 것이 적절. 감점 요소로의 사용 여지도 열어둠.

### Rule L5. Bonus Traces Only Mandatory

- **상태**: 채택 (Owner 확정, v1.11 승격).
- **조건**: `evaluation_role == bonus`인 rubric item의 **모든** trace 대상의 `requirement_level == must`.
- **결과**: `medium`, `provisional`.
- **Finding type**: `bonus_grades_mandatory_only`.
- **의도**: 가산은 "명세를 넘어선 행동"을 보상해야 한다는 v2.1 §2의 조치 (3)("bonus / qualitative note로 격하")의 거울. 모든 trace가 must로만 향한다면 사실상 must 명세를 가산 점수로 다시 매기는 셈 — bonus의 정체성 붕괴.
- **L1과의 차이**:
  - L1: 같은 spec_id가 scored와 bonus 양쪽에 등장 — **직접적 double-counting**.
  - L5: bonus가 must spec만 본다 — scored와 겹치지 않더라도 **bonus 영역의 의미가 잘못 설계됨**.
- **two-directional regression 가드**:
  - under-strict: bonus의 모든 trace가 must spec → 발화.
  - over-strict A: bonus의 trace에 optional/informational spec이 하나라도 있음 → 미발화.
  - over-strict B: trace가 아예 없는 bonus → 미발화 (이는 Rule 1의 `orphan_bonus_rubric_item` 책임).

### Rule L6. Mandatory Spec Bonus-only Coverage

- **상태**: 채택 (Owner 확정, **v1.11 승격** — 2026-05-27 개정으로 v1.12+에서 이동).
- **채택 경위**: 초안 §9에서 기각 검토(L3와 같은 정보 비대칭 논리 — must spec이 명세에 있으면 응시자는 그것이 must인 줄 인지)되었으나, Owner가 "must spec이 bonus로만 채점되는 케이스에 대한 안전장치가 있으면 좋겠다"고 판단해 채택 정정. 안전장치 구체 형태가 결정되면서(아래) v1.11로 승격, L1+L5와 fixture 공유 가능.
- **조건**: `requirement_level == must`인 spec_item을 참조하는 trace가 존재하지만, 그 trace의 모든 rubric이 `evaluation_role == bonus`.
- **결과**: `high`, `provisional`.
- **Finding type**: `mandatory_spec_bonus_only_traced`.
- **의도**: must 명세인데 본채점이 아예 없고 가산만 걸려있는 경우. Rule 2가 "must spec에 scored trace 없음"을 medium으로 잡지만, 본 룰은 한 단계 더 구체적이다 — "없을 뿐 아니라 *가산으로만* 평가되도록 설계됨". 응시자가 핵심 요구사항을 가산처럼 인식할 위험.
- **Rule 2와의 관계**: Rule 2의 특수 케이스. 동시 발화 가능. Rule 2가 medium이라 한 단계 상위(high)로 잡는 가치가 있음.
- **qualitative 경계 (Owner 확정, 구현 진입 시 정합화)**: qualitative는 점수화/가산 역할이 아니므로 L6 발화 조건에서 제외한다. qualitative-only 또는 bonus+qualitative trace인데 scored가 없는 must spec은 Rule 2 영역의 별도 후속 규칙으로 다룬다.
- **안전장치 (Owner 확정)**: L1과 동일 패턴 채택. 사유: L6도 정당/부당 구별이 필요한 의미적 판단이고(예: 의도적으로 가산 영역에 둔 경우 vs 설계 실수) L1과 같은 mechanism이면 review 인터페이스도 통일됨.
  - (a) **Finding payload 확장**: `mandatory_spec_bonus_only_traced` finding은 한 payload에 `spec_id` (must spec), 그 spec을 trace하는 모든 `bonus_rubric_ids[]`, 각 bonus rubric의 `title` / `description` 또는 `text`, 각 link의 `semantic_status`, `spec_item.text` 또는 `source_ref`를 동봉.
  - (b) **Review queue 별도 entry**: `review_queue.yaml`에 `type: mandatory_spec_bonus_review` entry. semantic verifier 또는 final reviewer가 "의도적 가산 배치"로 판정하면 `human_overridden`, 부당 판정이면 finding이 confirmed로 승급(Rule 2 confirmed orphan_must_spec과는 별도 type).
- **two-directional regression 가드**:
  - under-strict: must spec에 trace는 있지만 모두 bonus → 발화 + payload에 모든 bonus_rubric_ids 포함 + review_queue entry 생성.
  - over-strict A: must spec에 scored trace가 하나라도 있음 → 미발화.
  - over-strict B: must spec에 trace 자체가 없음 → 미발화 (Rule 2 책임).
  - over-strict C: must spec trace에 qualitative가 하나라도 있음 → 미발화 (Rule 2 계열 후속 규칙 책임).

---

## 5. Lint Rules — L-SEM (semantic, Phase 2+)

본 가족은 verifier-agent의 `ai_judgement` 경로를 통해 검증된다. 결정론적 발화가 아니므로 모두 `human_overridden` 경로를 통해 최종 확정한다.

### Rule L7. Forbidden-clause Violation

- **상태**: 채택 (Owner 확정, plan 버전 v1.12+ 별도 — C1 스키마 확장 동반).
- **조건**: `requirement_level == forbidden` (C1로 신설)인 spec_item에 trace된 rubric이 존재 (= 응시자에게 금지된 행동을 채점이 보상).
- **전제**: §6의 C1 채택 (Owner 확정). L7-DET 구현이 가능해짐.
- **결과**: `high`, `provisional` → final review 또는 verifier 승인 시 `confirmed`.
- **Finding type**: `forbidden_clause_rewarded`.
- **의도**: 응시자에게 "하지 말라"고 한 것을 채점에서 보상하는, 가장 큰 종류의 모순. 응시자 신뢰의 직접 침해.
- **구현 계층**:
  - L7-DET: C1 채택으로 즉시 가능 — `forbidden` spec에 trace된 rubric을 schema 비교만으로 검출.
  - L7-SEM: spec 본문에 자연어 금지절이 있지만 `forbidden`으로 마킹 안 된 경우를 verifier로 검출. Phase 2+. L8 기각 사유(비용)와 비슷한 부담이 있어 우선순위 낮음.

### Rule L8. Criterion Drift in Scored Rubric

- **상태**: **자동 검출 기각 (Owner 결정). 수동 발견은 final_review_record에 기록.**
- **기각 사유**: verifier-agent 호출 비용 부담이 본 룰의 자동 검출 가치를 넘는다. 또한 "명세에 없는 채점 기준이 있어서는 안 된다"는 invariant는 Rule 1(trace_link 부재 검출)이 부분적으로 잡으며, trace_link가 *있으면서도* 실제 채점 기준이 drift된 경우는 수동 final review가 책임진다.
- **수동 발견 기록 방식 (Owner 확정, 2026-05-27 개정)**: final review 중 리뷰어가 drift를 발견하면 `final_review_record.drift_observations[]` field에 기록한다. 각 observation은 `rubric_id`, `linked_spec_ids[]`, `observed_drift_summary` (자유 텍스트), `severity` (`informational` / `medium` / `high`), `recommended_action` (`revise_rubric` / `revise_spec` / `accept_with_note`)을 포함. 자동 finding은 발생하지 않으며 final review의 일부로 audit log에 남는다.
- (원안 — 자동 검출 미적용) 조건: rubric trace_link가 spec_id를 가리키지만, 그 rubric의 실제 채점 기준이 해당 spec_item 본문에 등장하지 않는 평가축임 (semantic mismatch). 결과 후보: `medium`, `provisional`. Finding type 후보: `criterion_drift`. v2.1 §1.1의 "Hidden Criterion" 패턴이 rubric 수준에서 재발하는 케이스. 본 자동 검출은 비용 대비 가치 부족으로 PoC 비범위지만, 영역 자체는 위 수동 기록으로 추적 가능.

### Rule L9. Mutually Contradictory Rubrics

- **상태**: **기각 (Owner 결정)**.
- **기각 사유**: 두 채점 기준이 서로 모순된다는 것은 명세-루브릭 *설계 단계*의 실패이지 채점 검증 단계의 책임이 아니다. 본 프로젝트가 향후 "설계 검증" 가족으로 확장될 때 그 가족이 다룬다. 본 결정은 PoC의 책임 경계를 "채점 정합성" 영역으로 명확히 한정한다.
- (원안 — 미적용) 조건: 두 rubric의 채점 기준이 상반된 행동을 보상 (semantic pair check). 결과: `medium`, `provisional`. Finding type 후보: `rubric_self_contradiction`. pairwise 검사이므로 N개 rubric에서 N(N-1)/2 verifier 호출 — 비용 부담도 큼.

---

## 6. 스키마 확장 후보 — L-SCH

### C1. `requirement_level: forbidden`

- **상태**: 채택 (Owner 확정). L7 채택과 동반.
- **변경**: `schemas/spec_items.schema.json`의 `requirement_level` enum에 `forbidden` 추가.
- **의미**: 이 spec_item은 응시자가 **해서는 안 되는** 행동을 정의한다.
- **영향**:
  - Rule L7의 deterministic 측면이 가능해진다 (`forbidden` spec에 trace된 rubric은 즉시 high finding).
  - Rule 2 (must spec coverage)는 영향 없음. Rule 2는 `must`만 검사하므로.
  - Rule 3 (optional weight)는 영향 없음.
  - `models.py`의 `RequirementLevel` enum 확장.
  - 기존 fixture는 영향 없음 (값이 추가되는 것이지 변하는 것이 아님).
- **plan 승격 시점**: v1.11에는 포함되지 않음 (v1.11은 L1+L5만). L7과 함께 v1.12+에 묶어 별도 plan 버전에서 진입.
- **비용**: 작음. plan 갱신 + 슬라이스 한 개로 가능.

### C2. `exclusion_links` (대칭 trace 테이블)

- **변경**: `trace_links`와 평행한 새 테이블 `exclusion_links`. 각 항목은 `(rubric_id, spec_id, reason)`.
- **의미**: "이 rubric은 이 spec을 채점하면 안 됨" 명시.
- **평가**: **권장 안 함**. C1이 있으면 대부분의 사용처가 흡수된다 (forbidden spec에 trace된 rubric → L7로 잡힘). 별도 테이블 유지 비용(스키마, 무결성 검사, fixture, CLI 인자) 대비 이득이 작음.
- **재검토 조건**: 실제 과제 적용 후 C1만으로 표현되지 않는 케이스가 반복 발견되면 그때 다시 검토.

### C3. (검토 후 보류) `rubric_items.section`

- 사용자가 §1.4에서 식별한 "기입 채점 영역" vs "창의 채점 영역" 구분은 이미 `evaluation_role: {scored, bonus, qualitative}`로 충분히 표현된다.
- 별도 `section` 필드를 추가하면 두 분류가 충돌할 위험이 있음 (`role: scored, section: 창의`가 가능해짐).
- **결론**: 새 필드 도입하지 않고 `evaluation_role` 사용 유지.

---

## 7. Plan 승격 계획 (Owner 확정, 2026-05-27 개정)

| Plan 버전 | 포함 룰 | 비고 |
|---|---|---|
| **v1.11** | **L1 + L5 + L6** | bonus 영역 핵심 3개. 모두 L-DET. fixture 공유. 슬라이스 단위 분할 (L1 → L5 → L6 순, Rule 1 슬라이스 1/2/3 패턴). L6 안전장치(payload+review_queue)가 확정되면서 L1과 같은 mechanism으로 통일됨. |
| v1.12+ (분리) | L2 | 정책 임계값 노출 슬라이스. 단독 가능. |
| v1.12+ (분리) | L4 | duplicate trace link 감지. 단독 가능. Rule 0 흡수 안 함. |
| v1.12+ 또는 별도 | L7 + C1 | spec 스키마 확장(C1) 동반. L7-DET 가능. L7-SEM은 Phase 2 verifier-agent 이후. |

**기각** (재논의 없음): L3 (정보 비대칭이 아니면 가중치 분배는 평가자 재량), L8 자동 검출 (verifier 비용 대비 가치 부족 — 수동 발견은 `final_review_record.drift_observations[]`로 기록), L9 (설계 검증 영역, PoC 책임 경계 밖).

**개정 메모 (2026-05-27)**: 초안에서 L6는 v1.12+로 분리되었지만, 안전장치 구체 형태가 L1과 동일 패턴으로 결정되면서 mechanism 일관성 + fixture 공유 이득이 분리 비용을 넘었다. v1.11에 L6 포함.

---

## 8. 정책 파라미터 신설 (Owner 확정)

`config/policy.yaml`에 lint 섹션을 추가한다.

```yaml
lint:
  bonus_ratio_threshold: 0.25          # Rule L2
```

`spec_trace_fanout_threshold`는 Rule L3 기각으로 제거. 초기값 `0.25`는 PoC 기본일 뿐 권위값이 아님 — Owner 결정에 따라 "기업/팀마다 정책이 다르므로 사용자가 자기 기준으로 조정". 이 값은 plan v1.10의 `optionality_mismatch.weight_threshold: 10`과 같은 위상에 둔다.

---

## 9. 결정 기록과 잔여 사항

### 9.1 확정 결정 (Owner, 2026-05-27)

1. **Spec-precedence**: 최신 ideation이 앞 → `plan v1.10 > v2.2 > v2.1 > v2 > v1`. 영역 한정 없음 (§0.1).
2. **Rule 가족 명명**: `Rule L1, L2, ...` (§3).
3. **Finding type 명명**: 본 문서 §4~§5의 후보 그대로 (`double_scored_spec`, `bonus_weight_encroachment`, `duplicate_trace_link`, `bonus_grades_mandatory_only`, `mandatory_spec_bonus_only_traced`, `forbidden_clause_rewarded`) 사용. 가독성 최우선 (§3).
4. **채택 룰**: L1, L2, L4, L5, L6, L7 (6개).
5. **기각 룰**: L3, L8 자동 검출, L9 (3개) — 재논의 없음. L8은 자동 검출 기각이며 수동 발견 기록은 보존(아래 11번).
6. **스키마 확장**: C1 (`requirement_level: forbidden`) 채택. C2 보류, C3 불필요.
7. **L4의 위치**: lint 가족 독립 유지 (Rule 0 흡수 안 함). 감점 요소로 활용 가능하도록 열어둠.
8. **L1 심화 확인 장치**: finding payload 확장 + review queue 별도 entry 양쪽 도입.
9. **Plan v1.11 승격 범위**: L1 + L5 + **L6** (2026-05-27 개정으로 L6 추가). 나머지 채택 룰(L2, L4, L7+C1)은 v1.12+로 분리.
10. **정책 임계값**: `bonus_ratio_threshold = 0.25` 유지. 기업별 자유 조정 — 본 프로젝트는 기본값만 제공.
11. **L6 안전장치 (2026-05-27 개정)**: L1과 동일 패턴 채택 — payload 확장 + review_queue `mandatory_spec_bonus_review` entry. §4 Rule L6 본문 참고.
12. **L8 수동 발견 기록 (2026-05-27 개정)**: `final_review_record.drift_observations[]` field 신설. 자동 검출은 없고 final review의 일부로 수동 기록. plan §5.6 갱신 필요.
13. **L6 qualitative 경계 (2026-05-27 구현 진입 시 정합화)**: L6는 모든 trace rubric이 `bonus`일 때만 발화한다. `qualitative`가 포함된 must-spec 무본채점 문제는 Rule 2 계열의 별도 후속 규칙으로 분리한다. 이유는 qualitative가 점수화/가산 역할이 아니며 기존 finding/queue payload가 명시적으로 bonus만 표현하기 때문이다.

### 9.2 잔여 결정 사항 (향후 plan 승격 시 확정)

1. **L7-DET vs L7-SEM 우선순위**: C1 채택으로 L7-DET 가능. L7-SEM은 Phase 2 verifier-agent 도입 후. 두 계층 모두 진입할지 L7-DET만으로 마감할지 별도 결정.

---

## 10. v2.1 대비 변경점

### 추가 (Owner 확정)

- inverse invariant (§2)
- Lint Rule family 6개 채택 (L1, L2, L4, L5, L6, L7) + 3개 기각 (L3, L8, L9) 기록 보존
- 스키마 확장 1개 채택 (C1: `requirement_level: forbidden`)
- 정책 파라미터 1개 신설 (`policy.lint.bonus_ratio_threshold`)
- Plan 승격 계획표 (§7, 동일 날짜 개정 반영): v1.11 = L1+L5+L6, v1.12+ = L2/L4/L7+C1

### 변경 없음

- v2.1의 모든 invariant (§2)
- v2.1 §1.1~§1.5의 다섯 가지 문제 정의
- v2.1 §7의 Rule 1~6 정의 (plan v1.10이 Rule 0~3를 좁혀 구현했고, Rule 4~6는 plan §6 "후속 규칙"으로 미구현)
- v2.1 §5의 MVP 범위, §6 데이터 모델 초안, §10 LLM 역할
- plan v1.10의 Rule 0~3 구현 — v2.2는 어떤 기존 Rule도 수정하지 않는다

### 채택 경위 메모 (세션 중 결정 변경)

- L6는 본 문서 초안에서 기각 검토되었으나(L3와 같은 정보 비대칭 논리), Owner 검토 중 "must spec이 bonus로만 채점되는 케이스에 대한 안전장치가 필요"로 판단해 채택 정정.
- **2026-05-27 동일 날짜 개정**: L6 안전장치 구체 형태(L1과 동일 mechanism)와 L8 수동 발견 기록 방식(`drift_observations[]`)이 Owner에 의해 결정됨. L6는 v1.12+ 분리에서 v1.11 슬라이스로 승격. v2.3 별도 문서 대신 본 v2.2 in-place 개정.

### 의식적 제외

- 자동 채점, 가중치 자동 조정, 룰 자동 합의 — v2.1 §5.3의 비범위와 동일
- 응시자 행동 분석, 패턴 마이닝 — v2.1 §5.3과 동일

---

## 11. 다음 단계

본 문서는 Owner 결정으로 **final 잠금 상태** (2026-05-27, 동일 날짜 개정 1회). 코드 변경을 요구하지 않으며 plan 승격 전까지 ideation에 머문다.

1. plan v1.10 → v1.11 갱신 — §6에 Rule L1 + L5 + L6 명세 추가, §5.6 Final Review Record에 `drift_observations[]` field 추가, §5.7 Review Queue Entry에 `double_scoring_review` / `mandatory_spec_bonus_review` type 추가, §15에 v1.11 changelog 항목 추가. plan만 변경, 코드 변경 없음.
2. plan v1.11이 잠긴 후 슬라이스 단위 구현 (L1 → L5 → L6 순서, Rule 1 슬라이스 1/2/3 패턴 따름).
3. plan v1.12+에 나머지 채택분(L2, L4, L7+C1) 순차 승격.
4. 본 문서의 잔여 결정(§9.2 1개)은 L7 승격 시점에 해소.
