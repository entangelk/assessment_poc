# Work Log - 2026-05-27

## User Decision Rationale Recording Guidance

### Goals

- Make contributor guidance preserve user decisions that explain project direction without retaining conversation transcripts.
- Keep `HANDOFF.md` focused on current development state rather than decision history.

### Completed Work

- Updated `CLAUDE.md` and `AGENTS.md` with a `User Decisions and Rationale` section.
  - Files changed: `CLAUDE.md`, `AGENTS.md`.
  - Key changes: required work-log summaries for user decisions that affect requirements, scope, architecture, design, behavior, or implementation direction; required concise rationale in changelog entries when such a decision directly drives a major recorded change; required confirmation before implementing a later conflicting request.
  - Effect: future workers can recover why important project directions were chosen without storing full conversations.
- Added this contributor-policy change to `CHANGELOG.md`.
  - Files changed: `CHANGELOG.md`.
  - Key change: recorded the new rationale-preservation policy and the deliberate exclusion of conversational history from handoff.
  - Effect: the project history exposes why its documentation discipline changed.
- Extended `CLAUDE.md` and `AGENTS.md` with artifact-specific minimum verification.
  - Files changed: `CLAUDE.md`, `AGENTS.md`.
  - Key changes: documented minimum checks for documentation-only changes, behavioral code changes, and public interfaces or structured contracts; required use of the closest available verification when an example surface such as schema or introspection output is absent.
  - Effect: the general-purpose TDD guidance now defines a completion floor without assuming every repository has the same contract artifacts.

### Issues Found

- Problem: existing guidance required a `Decisions` section in each work log, but did not explicitly say to retain user-provided rationale or how to handle a later request that conflicts with it.
  Cause: the log policy described general engineering decisions rather than user-informed product and design direction.
  Resolution: added targeted guidance for decision summaries, major-change changelog notes, handoff exclusion, and conflict confirmation.
  Outcome: the documentation policy now distinguishes durable rationale from transient conversation.
- Problem: the verification guidance established TDD and regression guards, but did not specify the minimum verification expected for documentation or public-contract changes.
  Cause: the guidance focused on behavioral defects and tests rather than varying artifact types across projects.
  Resolution: added artifact-type verification rules while making schema, examples, and introspection checks conditional on those surfaces existing in the repository.
  Outcome: the guidance remains portable across projects without weakening the test-first expectation for behavioral code.

### Decisions

- The owner wants the substance of user decisions retained because it explains why project and design choices were made; full conversation transcripts are unnecessary.
- User rationale belongs in `work_log.md` whenever it affects project direction, and in `CHANGELOG.md` only when it directly drives a major design or feature change.
- `HANDOFF.md` remains an operational development handoff and must not become a conversational decision-history record.
- A later request that conflicts with a recorded user decision or established direction must be surfaced to the user for canonical-direction confirmation before implementation.
- The owner chose a general-purpose minimum verification rule rather than project-specific onboarding or instruction-maintenance guidance; structured-contract checks must apply to available project artifacts instead of assuming a `schemas/` directory exists.

### Next Steps

- Apply the new recording and conflict-confirmation guidance during future design or feature work.

---

## Ideation v2.2 Draft — Rubric Lint Rules (역방향 검증 가족)

### Goals

- 채점 구조에 lint 사고방식(있어서는 안 되는 것 검출)을 도입할 수 있는지 검토하고, 구체 룰 후보를 ideation 단계 문서로 남긴다.
- plan은 건드리지 않고 ideation에 머무름으로써 HANDOFF가 사실상 spec이 되는 안티패턴을 회피한다.

### Completed Work

- 신규 문서 `docs/ideation_assessment_harness_v2.2.md` 작성 (약 250줄, 11개 절).
  - Files changed: `docs/ideation_assessment_harness_v2.2.md` (신규).
  - Key changes:
    - inverse invariant 정의 — v2.1 coverage 가족의 거울 ("있으면 안 되는 것이 있는가").
    - Lint Rule 가족 9개 후보 정의 (L1~L9). L-DET 6개(L1~L6), L-SEM 3개(L7~L9).
    - 각 결정론적 룰은 plan v1.10 §6 Rule 1 스타일(조건/결과/의도/한계/two-directional 가드)로 작성하여 plan 승격 시 그대로 복사 가능.
    - 스키마 확장 후보 정리: C1(`requirement_level: forbidden`) 채택 권장, C2(`exclusion_links`) 보류, C3(`section`) 불필요(`evaluation_role`로 충분).
    - 정책 파라미터 신설 후보: `policy.lint.bonus_ratio_threshold` (PoC 기본 0.25), `policy.lint.spec_trace_fanout_threshold` (PoC 기본 4).
    - 승격 우선순위표: 1순위 L1+L5 묶음(둘 다 L-DET, fixture 공유 가능), 2순위 L6, 3순위 C1+L7-DET.
    - Owner 결정 사항 8개를 §9에 미해결 결정으로 명시(v2.2 spec-precedence 위치, 룰 가족 명명, finding type 규약, L4의 Rule 0 흡수 여부, plan 승격 범위, semantic lint 우선순위, L9 PoC 포함 여부, 정책 임계값 초기값).
  - Effect: v2.1까지의 coverage 일변도 룰 가족에 exclusion 축을 도입할 수 있는 설계 공간이 문서로 잡혔고, 다음 단계(owner 결정 → plan v1.11 승격 PR 초안)가 명시되었다.

### Issues Found

- Problem: v2.2의 spec-precedence tree 위치가 자명하지 않음. v2.1과 동순위로 둘지, v2.2가 §7 영역에서 우선할지 모호.
  Cause: 본 가족이 v2.1의 §7을 확장/대체하지 않고 *추가*하는 성격이므로 기존 tree에 단순 삽입이 안 됨.
  Resolution: 문서 §0.1에 두 옵션을 명시하고, 잠정적으로 (b)안(v2.2가 §7 영역에서 우선)을 가정해 작성한 뒤 owner 결정 사항으로 남김.
  Outcome: 코드/plan 변경 없이도 정합성 결정이 미루어졌고, 다음 worker가 무엇을 결정해야 하는지가 명시됨.
- Problem: Rule L4(`duplicate_trace_link`)가 lint 가족과 Rule 0(reference integrity) 둘 다에 속할 수 있음.
  Cause: 데이터 품질 결함은 lint 성격이지만 schema 무결성 위반 성격도 강함(input error 등급 격상 여지).
  Resolution: 본 문서에서는 lint 가족에 둠과 동시에 Rule 0 흡수 후보임을 명시하고 §9의 미해결 결정으로 올림.
  Outcome: 두 선택지가 모두 추적 가능 상태로 남았다.

### Decisions

- **Owner 결정 (B안 채택, 본 세션)**: lint 사고방식을 별도 ideation 문서(v2.2)로 정리하기로 함. 대안은 (A) plan v1.11에 새 §6 항목으로 직접 추가하는 것이었으나, owner는 "버전 업데이트이므로 큰 커밋 자체는 상관없을 것"이라는 인식 아래 별도 문서 작성을 선택했다.
  - 채택 이유: 새 룰 가족 전체 설계 공간을 ideation 단계에서 먼저 펼친 뒤 일부만 plan으로 승격하는 편이 (a) HANDOFF가 spec이 되는 안티패턴을 회피하고, (b) 룰 간 상호 의존(L1↔L5, L7↔C1)을 한 자리에서 보이게 한다.
  - Tradeoff: plan v1.11 작성이 한 단계 더 필요하다(즉시 코딩 시작 안 됨). 다만 owner가 큰 커밋 자체를 허용했으므로 분리 단계가 부담은 아니다.
- **Owner 결정 (lint 적용 방향 재정의)**: 처음 owner가 lint를 언급했을 때 가정은 "프로젝트의 Python 코드에 lint 도입"이었으나, owner가 직접 방향을 바꿔 "lint의 사고방식을 채점 구조 검증에 적용"으로 재정의했다.
  - 채택 이유: 본 프로젝트의 본질이 *명세-루브릭 정합성 검증 하네스*이므로, 자체 코드 lint보다 채점 구조에 lint 패턴을 적용하는 것이 프로젝트 가치 축과 직결된다. 또한 사용자가 식별한 구체적 통점("기입 채점 영역과 창의 채점 영역이 분리되어 있어, 명시된 것에 기반해 있어서는 안 되는 것이 들어올 수 있다")이 본 가족이 직접 해결하는 문제다.
  - Tradeoff: 프로젝트 자체 코드의 일관성 검증은 별도 결정으로 남는다. 본 가족이 채택/구현되더라도 자체 코드 lint(ruff 등) 결정은 여전히 미정.
- **본 세션이 결정하지 않은 것** (모두 owner 결정 사항으로 §9에 남김): Rule 가족 명명(`Rule L*` vs `Rule 4~` vs `Lint Rule*`), finding type 명명 규약, L4의 Rule 0 흡수 여부, plan v1.11 승격 범위(L1만 / L1+L5 / L1+L5+L6 / +C1+L7-DET), L9의 PoC 포함 여부, 정책 임계값 초기값.
- **v2.1과의 관계**: v2.2는 v2.1을 어떤 절도 *수정*하지 않는다. 추가만 한다. plan v1.10의 Rule 0~3도 변경 없음. 본 결정은 향후 worker가 v2.2 도입을 v2.1/plan v1.10 무효화로 오해하지 않게 하기 위함.

### Next Steps

1. Owner가 `docs/ideation_assessment_harness_v2.2.md` §9의 미해결 결정 8개를 답한다. 특히 5번(plan v1.11 승격 범위)이 다음 단계 트리거.
2. 결정 결과를 v2.2 본문에 반영하고 final로 잠근다.
3. 승격 범위만 plan v1.11의 §6에 추가하는 PR 초안 작성(plan만 변경, 코드 변경 없음).
4. plan v1.11이 잠긴 후 슬라이스 단위 구현(Rule 1 슬라이스 1/2/3 패턴 따름).

---

## Ideation v2.2 Finalization — Owner 결정 반영 및 잠금

### Goals

- Owner가 위 Drafting 절의 §9 미해결 결정 8개에 답한 결과를 v2.2 본문에 반영하고 문서를 final 상태로 잠근다.
- 채택/기각 룰을 명확히 표시해 다음 worker가 어떤 룰을 plan v1.11/v1.12+에 올려야 하는지 헷갈리지 않게 한다.

### Completed Work

- `docs/ideation_assessment_harness_v2.2.md` 본문 13개 절 갱신.
  - Files changed: `docs/ideation_assessment_harness_v2.2.md`.
  - Key changes:
    - §0.1 spec-precedence를 "미정"에서 "확정"으로 변경. 결과: `plan v1.10 > v2.2 > v2.1 > v2 > v1` (영역 한정 없음).
    - §3 룰 명명 규약 확정 — `Rule L1, L2, ...` + finding type은 문서 §4~§5 후보 그대로 사용 (가독성 최우선).
    - §4 Rule L1에 심화 확인 장치 절 추가: payload 확장 (양쪽 rubric_id/title/semantic_status 동봉) + review queue `double_scoring_review` entry 양쪽 도입.
    - §4 Rule L3에 `[기각 — Owner 결정]` 표시 + 기각 사유 ("정보 비대칭이 아니면 가중치 분배는 평가자 재량") + 잔여 위험 기록.
    - §4 Rule L4에 위치 확정 — lint 가족 독립 유지, Rule 0 흡수 안 함. 사유 명시 (실수/의도/분리 link 가능성).
    - §4 Rule L6에 채택 정정 경위 명시 — 초안에서 기각 검토되었으나 owner가 안전장치 필요로 판단해 채택 정정.
    - §5 Rule L8 / L9에 `[기각 — Owner 결정]` 표시 + 각각의 기각 사유 (L8: verifier 비용 vs 가치 + 수동 review 책임 / L9: 설계 검증 영역, PoC 책임 경계 밖).
    - §6 C1 채택 확정 — L7 동반, plan v1.12+로 분리.
    - §7 우선순위표를 "후보"에서 "Plan 승격 계획 (Owner 확정)"으로 재작성. v1.11=L1+L5, v1.12+=L2/L4/L6/L7+C1.
    - §8 정책 파라미터에서 `spec_trace_fanout_threshold` 제거 (L3 기각으로 무관). `bonus_ratio_threshold=0.25`만 유지.
    - §9를 "미해결 결정 8개"에서 "확정 결정 10개 (§9.1) + 잔여 결정 3개 (§9.2)"로 재작성.
    - §10에 채택 경위 메모 추가 (L6 기각→채택 정정).
    - §11 다음 단계를 owner 결정 풀어주는 흐름에서 plan 승격 흐름으로 교체. 문서가 final 잠금 상태임을 명시.
  - Effect: v2.2가 ideation final 상태가 됨. 다음 worker가 plan v1.11에 L1+L5만 추가하면 코드 구현 진입 가능.
- `CHANGELOG.md`에 v2.2 finalized 행 추가 (drafted 행 위).
  - Files changed: `CHANGELOG.md`.
  - Key change: 동일 날짜의 두 상태(drafted → finalized)를 분리 기록.

### Issues Found

- Problem: Owner가 L6 기각 사유로 제시한 예시("필요하지 않은 라이브러리 사용시 감점")가 L6(must spec이 bonus rubric으로만 채점)와 무관하고 L7(forbidden clause)의 사례에 더 가까웠다.
  Cause: L6와 L7이 모두 "must/금지 명세 처리"라는 점에서 인접해 헷갈리기 쉬움.
  Resolution: 확인 질문에서 owner가 직접 "L3와 같은 논리로 기각이지만 안전장치가 필요하므로 채택으로 정정"하여 해소. 결과 채택 룰에 L6 추가.
  Outcome: L6 채택 경위가 명시적으로 기록되어 향후 worker가 "왜 안전장치가 필요한가"를 §9.2 잔여 결정 1번에서 추적 가능.
- Problem: L1/L5/L6는 같은 bonus 영역 fixture를 공유할 수 있어 한 plan에 묶는 쪽이 fixture 재사용 측면에서 효율적인데, owner가 v1.11에서 L6를 분리하기로 결정.
  Cause: L6의 안전장치 구체 형태가 v1.11 시점에 미확정이라 함께 묶기 어려움.
  Resolution: 트레이드오프를 §7 표 하단에 명시 — v1.12에서 L6 진입 시 v1.11 fixture를 확장 재사용한다.
  Outcome: 분리 결정의 비용(fixture 일부 중복 작성)이 문서에 추적 가능 상태로 남았다.

### Decisions

- **Owner 결정 (Lint Rule 채택/기각 일괄)**: 채택 6개 (L1, L2, L4, L5, L6, L7), 기각 3개 (L3, L8, L9), 스키마 확장 채택 1개 (C1). 기각 사유의 골격은 두 갈래로 정리됨.
  - L3/L6 같은 "응시자 정보 비대칭이 아니면 평가자 재량" 논리. (L6는 안전장치 필요로 채택 정정)
  - L8/L9 같은 "PoC 책임 경계 외 / 비용 대비 가치 부족" 논리.
- **Owner 결정 (plan v1.11 승격 범위 축소)**: 채택 룰 5개 중 L1+L5만 v1.11에 진입. 사유: L1+L5가 사용자 §1.4에서 식별한 "창의 영역의 명세 잠식"의 가장 직접적 검출이고, L6는 안전장치 구체 형태 결정이 선행되어야 함. 나머지(L2, L4, L7+C1)는 단독 슬라이스 또는 별도 진입이 자연스러움.
- **Owner 결정 (spec-precedence 단순화)**: 영역 한정 없이 "최신 ideation이 ideation 계층에서 앞". 이전 (b)안(§7 영역에서만 우선)보다 단순. 결과: v2.2가 v2.1과 같은 영역을 다루면 v2.2가 우선, 다른 모든 영역은 v2.1 그대로.
- **Owner 결정 (L1 심화 확인 장치 — 양쪽 모두)**: payload 확장(무료) + review queue entry(verifier 호출 1건) 둘 다 도입. "비용보다 추적성 강화" 우선. L1 발화의 정당/부당 구별을 사람이 한 화면에서 + verifier 흐름으로 이중 보장.
- **Owner 결정 (정책 임계값 권위 없음)**: `bonus_ratio_threshold=0.25`는 PoC 기본값일 뿐 권위값 아님. "기업/팀마다 정책이 다르므로 사용자가 자기 기준으로 조정". 본 프로젝트는 임계값 자체에 의견을 갖지 않는다.

### Next Steps

1. plan v1.11 §6에 L1 + L5 구현 명세 추가 (plan만 변경, 코드 변경 없음). 슬라이스 단위 명세는 Rule 1 슬라이스 1/2/3 패턴 따름.
2. plan v1.11이 잠긴 후 코드 슬라이스 진입 (L1 → L5 순).
3. v1.12+에서 L6 진입 시 §9.2 잔여 1번(L6 안전장치 구체 형태)을 owner와 먼저 결정.
4. v1.12+에서 L7 진입 시 §9.2 잔여 2번(L7-DET vs L7-SEM 우선순위) 결정.

---

## Ideation v2.2 Revision + Plan v1.10 → v1.11 Bump

### Goals

- Owner가 ideation v2.2 §9.2 잔여 결정 1번(L6 안전장치)과 3번(L8 trace_drift 수동 발견 기록)을 즉시 결정.
- 결정 결과를 ideation v2.2 본문에 in-place 반영하고 L6를 v1.11 슬라이스로 승격.
- plan v1.10 → v1.11로 버전 갱신하며 L1 + L5 + L6 명세, §5.6 `drift_observations[]` field, §5.7 review_queue entry type 2개 신설을 한 plan 갱신으로 묶어 처리. 코드 변경 없음 (spec-only).

### Completed Work

- `docs/ideation_assessment_harness_v2.2.md` in-place 개정 (v2.3 별도 문서 안 만듦).
  - Files changed: `docs/ideation_assessment_harness_v2.2.md`.
  - Key changes:
    - 문서 최상단에 "Revised 2026-05-27" 메모 추가 — final 잠금과 동일 날짜 개정임을 명시하고 v2.3 분리하지 않은 사유 기록.
    - §4 Rule L6: 상태를 "v1.12+ 분리 슬라이스" → "v1.11 승격". 안전장치 절 신설 — L1과 동일 mechanism (payload 확장 + review_queue `mandatory_spec_bonus_review` entry). two-directional 가드의 under-strict 항목에 payload/review_queue 생성 명시.
    - §5 Rule L8: 상태를 "기각" → "자동 검출 기각, 수동 발견은 final_review_record에 기록"으로 변경. 수동 발견 기록 절 신설 — `drift_observations[]` field 5개 (rubric_id / linked_spec_ids / observed_drift_summary / severity / recommended_action).
    - §7 Plan 승격 계획표: v1.11 행을 "L1 + L5"에서 "L1 + L5 + **L6**"로 변경. v1.12+ 행에서 L6 제거. 표 하단 트레이드오프 메모를 "개정 메모"로 교체 — L6 안전장치가 L1과 동일 패턴으로 결정되면서 mechanism 일관성 + fixture 공유 이득이 분리 비용을 넘었음을 명시.
    - §9.1 확정 결정: 9번(plan v1.11 승격 범위)에 L6 추가, 5번(기각 룰)에 L8을 "자동 검출 기각"으로 세분화, 11번(L6 안전장치)/12번(L8 수동 기록) 신규 추가.
    - §9.2 잔여 결정: 1번(L6 안전장치)/3번(L8 잔여 위험) 해소되어 제거. 2번(L7-DET vs L7-SEM 우선순위)만 단일 잔여로 남김.
    - §10 채택 경위 메모: "2026-05-27 동일 날짜 개정" 항목 추가.
    - §11 다음 단계: plan v1.11 갱신 범위(§6 Rule L1/L5/L6 + §5.6 drift_observations + §5.7 review_queue type + §15 changelog) 명시. 구현 슬라이스 순서를 L1 → L5 → L6로 갱신.
  - Effect: ideation v2.2가 plan v1.11과 1:1 정합 상태가 됨. 잔여 결정은 L7 승격 시점까지 단 1개로 축소.
- `docs/implementation_plan_assessment_harness_poc_v1.md`를 v1.10 → v1.11로 갱신 (spec-only).
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes:
    - §5.6 Final Review Record: `drift_observations[]` field 예시와 5개 sub-field 정의 추가. `check`/`gate` 결과 코드와 무관함을 명시.
    - §5.7 Review Queue Entry: `type` enum에 `double_scoring_review` (Rule L1 짝)와 `mandatory_spec_bonus_review` (Rule L6 짝) 추가. 기존 5개 type과 같은 schema/lifecycle 따름.
    - §6 신규 항목 3개 (Rule L1 / L5 / L6): 각각 조건/결과/판정 상태/차단 대상/의도/심화 확인 장치/two-directional 가드/fixture를 Rule 1 v1.10 패턴과 같은 형식으로 작성. ideation v2.2 §4 본문과 정합.
    - §6 "Lint 가족 공통 메모" 신설: Rule 0 선행 의존, semantic_status 비참조(L-DET), check의 blocking_count 미가산, next_actions 명명(`review_double_scoring` / `review_bonus_mandatory_only` / `review_mandatory_spec_bonus_only`)을 한 자리에 정리.
    - §6 후속 규칙: L2 / L4 / L7+C1을 v1.12+ 항목으로 명시.
    - §15 v1.11 changelog 항목 추가: 변경 6건과 owner 결정 근거(명명, 안전장치 mechanism, L8 처리 방식)를 압축 기록.
  - Effect: plan이 ideation v2.2 v1.11 승격분과 1:1 정합. 다음 worker는 plan v1.11 §6 Rule L1부터 슬라이스 단위로 구현 진입 가능.
- `HANDOFF.md` 갱신.
  - Files changed: `HANDOFF.md`.
  - Key changes: plan version 참조 v1.10 → v1.11 일괄 교체. Active Decisions에 lint 가족 명명/안전장치 규약 추가. Next Tasks에 Rule 2/3 이후 lint 가족 슬라이스 진입 트랙 추가. Project Structure에 ideation v2.2 항목 추가.
  - Effect: 다음 worker가 HANDOFF만 읽고도 현재 spec 상태(plan v1.11, ideation v2.2 final + revised)와 다음 진입 트랙을 파악 가능.
- `CHANGELOG.md`에 plan v1.11 행 추가.

### Issues Found

- Problem: HANDOFF.md가 plan version을 9곳에서 참조하고 있어 한 곳 누락 시 inconsistency가 즉시 발생.
  Cause: 기존 HANDOFF 패턴이 plan version을 인용해 결정 출처를 명시하는 방식이라 plan 버전 갱신마다 그 횟수만큼의 동기화가 필요함.
  Resolution: 갱신 전 grep으로 9개 위치를 모두 식별한 뒤 일괄 교체. 새 plan v1.11에만 있는 항목은 별도 추가.
  Outcome: HANDOFF가 plan v1.11과 동기화. 향후 plan 버전 갱신 시 같은 패턴(grep → 일괄 교체)을 따른다.

### Decisions

- **Owner 결정 (L6 안전장치 = L1과 동일 mechanism)**: payload 확장 + review_queue entry 양쪽 도입. 근거: L6도 정당/부당 구별이 필요한 의미적 판단이고(예: 의도적으로 가산 영역에 둔 경우 vs 설계 실수), L1과 같은 mechanism이면 리뷰 인터페이스가 통일되어 reviewer cognitive load가 줄어든다. 비용 측면(verifier 호출 1건 추가)도 L1과 같아 일관성 우선.
- **Owner 결정 (L8 수동 발견은 `drift_observations[]`)**: 자동 검출은 비용 대비 가치 부족으로 PoC 비범위로 두지만, trace_link 통과 + criterion drift 케이스를 final reviewer가 발견했을 때의 audit log 채널은 필요. final_review_record schema 확장이 review_queue entry type 신설보다 적절 — drift는 trigger-on-detection 이벤트가 아니라 review 산출물의 일부이기 때문.
- **Owner 결정 (버전 갱신 = plan v1.10 → v1.11, ideation v2.2 in-place)**: plan은 §6 신규 항목 3개 + §5.6/§5.7 schema 확장이라 명확한 minor bump 자격. ideation은 final 잠금과 동일 날짜 개정이라 v2.3 분리 시 noise 큼 — in-place revision으로 처리하되 문서 최상단 revision note로 추적성 보장.
- **L6 v1.11 승격 결정 근거 (재정정)**: 같은 날 final 잠금 시 owner가 "L6는 v1.12+ 분리"로 결정했으나, 안전장치 구체 형태가 L1과 동일 mechanism으로 결정되는 순간 분리 사유가 사라짐(L1 mechanism이 이미 v1.11에 들어가므로 L6 추가는 신규 mechanism 도입 비용 없음). fixture 공유 + 슬라이스 패턴 일관성 이득까지 더해져 v1.11 승격이 자연스러운 선택이 됨.

### Next Steps

1. plan v1.11이 잠겼으니 코드 슬라이스 진입 가능. 순서는 L1 → L5 → L6 (Rule 1 슬라이스 1/2/3 패턴).
2. 각 슬라이스는 (a) finding payload schema 확장 (`findings.schema.json`), (b) review_queue.json 갱신, (c) fixture 추가 (`fixtures/bonus_misuse/` 등), (d) two-directional 가드 테스트 추가, (e) CLI envelope `next_actions` 갱신을 동반.
3. Rule 2/3가 lint 슬라이스보다 먼저 끝나야 할지 owner와 우선순위 협의 필요 — 현재 HANDOFF Next Tasks는 Rule 2/3 우선으로 적혀 있음.
4. v1.12+ 승격 시 §9.2 잔여 1번(L7-DET vs L7-SEM 우선순위) 결정.

---

## Sequencing 결정 + Rule 2 Literal 추천 (2026-05-27 추가 결정)

### Goals

- 다음 슬라이스 진입 전 owner 결정 필요한 항목 두 개(트랙 순서 + Rule 2 literal)를 정리해 HANDOFF에 박는다. 미해결로 남기면 다음 worker가 헷갈리거나, 슬라이스 직전에 다시 owner 차임을 깨워야 함.

### Completed Work

- `HANDOFF.md`에 sequencing 결정 + Rule 2 literal 추천 박음.
  - Files changed: `HANDOFF.md`.
  - Key changes:
    - Next Tasks 섹션 맨 위에 `### Sequencing Decision (Owner, 2026-05-27)` 신설. lint family를 다음 트랙으로 잠그고 그 사유(schema 인프라 선구축, 동기화)를 명시.
    - `### Lint family ... — NEXT TRACK`으로 헤더 갱신. L1을 "heavy 슬라이스"로 표시하고 슬라이스 1.5 분할 옵션을 명시. Rule 1/L5/L6의 mutual-exclusion 시각화 의무를 fixture 항목에 박음. `drift_observations[]`는 paper spec ahead임을 다시 못박음.
    - Rule 2 섹션의 "Output contract decision required" 항목을 owner 추천(`uncovered_must_spec_item` / `review_uncovered_must_spec`)과 실행 AI 개입 규칙(동일 컨벤션 family 내 미세 조정 가능, 가족 외 변경은 owner 재승인)으로 교체. lock point는 슬라이스 merge 시점으로 명시.
    - fixture 이름을 `fixtures/uncovered_must_spec/`로 갱신 (literal 변경 시 실행 AI가 함께 갱신).
  - Effect: 다음 worker가 HANDOFF만 읽고 (a) lint family를 먼저 들어가야 함, (b) Rule 2 literal은 owner 추천 + 개입 규칙 내에서 선택, (c) plan 본문 업데이트 의무가 슬라이스 직전 단계라는 것을 한 자리에서 파악 가능.

### Issues Found

- Problem: lint 선 작업으로 sequencing이 정해지면서, Rule 2 literal 결정의 긴급도가 떨어졌지만 **잊혀질 위험은 오히려 커짐** (Rule 2가 한 트랙 뒤로 밀려서).
  Cause: 일정상 거리가 멀면 인지적으로 덜 부각됨. HANDOFF가 안 적어두면 Rule 2 슬라이스 진입 시점에 "왜 literal이 plan에 없지?"부터 다시 시작.
  Resolution: Rule 2 entry에 owner 추천 + 개입 규칙을 박아둠. 실행 AI가 슬라이스 진입 시점에 owner 차임 없이도 작업 시작 가능 (단 plan 본문 업데이트는 슬라이스 일부로 의무화).
  Outcome: literal 결정이 "사라지는 게 아니라 미뤄지는" 위험이 운영적으로 잠겼다.

### Decisions

- **Owner 결정 (sequencing — lint family 우선)**: Rule 2/3보다 lint family(L1 → L5 → L6)를 먼저 진입. 근거: lint가 도입하는 schema 인프라(findings payload 확장, review_queue 첫 등장 가능성, cli_output next_actions 확장)를 먼저 세우면 Rule 2/3가 그 위에 자연스럽게 동기화됨. 병렬 트랙으로 두기보다 lint를 "기존 룰 파이프라인으로 동기화하는 뼈대 작업"으로 frame.
- **Owner 결정 (Rule 2 literal — Option C 추천 + 실행 AI 개입 여지)**: finding_type=`uncovered_must_spec_item`, next_action=`review_uncovered_must_spec`. 근거: Rule 2는 coverage-gap이지 no-trace orphan이 아니므로 Rule 1의 `orphan_*` 패턴이 의미상 안 맞음. `uncovered_*`는 Rule 1의 `_rubric_item` suffix와 대칭(`_spec_item`)이고 lint 가족의 descriptor 스타일과 안 겹침.
- **Owner 결정 (실행 AI 개입 규칙)**: 실행 AI는 동일 컨벤션 family(`uncovered_*` / `missing_*` 스타일, `_spec_item` suffix, `review_` prefix) 내에서 미세 조정 가능. family 밖 변경(예: `_rubric_item` suffix로 전환, `double_*` descriptor로 전환)은 owner 재승인 필요. Lock point는 슬라이스 merge 시점 — 그 이전은 자유, 이후는 breaking change.
- **Owner 결정 (literal 잠금 범위 — Option A: HANDOFF에만)**: plan v1.11 §6 Rule 2 본문은 그대로 두고 HANDOFF Rule 2 brief에만 추천 + 규칙 박음. plan 본문 갱신은 Rule 2 슬라이스 진입 직전(plan v1.12 §6)에 함께 함. 근거: lint가 한참 앞에 있어 Rule 2가 immediate next가 아니고, 지금 plan 본문에 박으면 v1.11이 spec-only를 넘는 변경이 됨(불필요한 plan revision 회피).
- **harness scoring 영향 평가**: literal 후기 결정 자체는 채점 정확성에 영향 없음 (literal은 결과 식별자일 뿐 평가 로직에 내용으로 들어가지 않음). 5-surface 동기화(rules.py / findings.schema / cli_output.schema / contract test / plan)만 슬라이스 내에서 함께 처리되면 안전. cross-slice 회귀는 lock point(merge) 규칙으로 차단.

### Next Steps

1. 이번 결정까지 한 묶음으로 커밋 + 푸시.
2. 다음 슬라이스 진입은 lint L1 (heavy 슬라이스 — schema 뼈대 도입). 실행 AI는 슬라이스 크기가 리뷰 가능 범위를 넘으면 슬라이스 1.5 분할 옵션 보유.
3. lint family 끝나면 Rule 2 슬라이스 — plan v1.12 §6 Rule 2 본문에 literal 박는 단계가 슬라이스 시작 직후 첫 commit.

---

## Phase 0 Rule L1 Implementation + Review Queue Contract Resolution

### Goals

- Resolve the canonical-plan contradiction about when paired lint review queue entries are persisted.
- Implement Rule L1 (`double_scored_spec`) with its required human-review context and public CLI contract.
- Preserve the L1 boundary with under-strict and over-strict regressions and a grounded shared lint fixture.

### Completed Work

- Updated `docs/implementation_plan_assessment_harness_poc_v1.md` from v1.11 to v1.12.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: clarified that general compacting/verifier queues remain Phase 2 scope while deterministic lint safeguard queue artifacts are a Phase 0 `check` exception; specified `--review-queue-out`, default sibling `review_queue.json`, envelope queue fields, and empty-queue overwrite behavior; inserted v2.2 in the documented ideation precedence order.
  - Effect: Rule L1/L6's required review mechanism no longer conflicts with the Phase 0 scope boundary.
- Implemented Rule L1 and queue artifact output.
  - Files changed: `src/assessment_harness/rules.py`, `src/assessment_harness/cli.py`, `src/assessment_harness/schemas.py`, `schemas/findings.schema.json`, `schemas/review_queue.schema.json`.
  - Key changes: added structural `run_rule_l1`; emitted `double_scored_spec` with scored/bonus rubric IDs and paired context including semantic statuses as evidence only; generated `double_scoring_review`; added `review_double_scoring`, `review_queue_path`, and `review_queue_count`; created the review queue schema and registered it.
  - Effect: `check` now detects same-spec scored/bonus overlap without consulting semantic status, and retains the human-review safeguard required by the plan.
- Added regression coverage and a grounded shared lint fixture.
  - Files changed: `tests/test_rules.py`, `tests/test_cli_output_contract.py`, `tests/test_fixtures.py`, `fixtures/bonus_misuse/*`.
  - Key changes: added L1 under-strict guard and two non-overlap over-strict guards; locked the public schema contract and default queue artifact path; introduced `bonus_misuse` with an L1 overlap plus a different-spec bonus control.
  - Effect: future L5/L6 slices can extend one grounded lint scenario while L1's structural boundary and output contract stay protected.
- Updated user/operator state documents.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`.
  - Key changes: documented Rule L1, Phase 0 lint queue behavior, plan v1.12, new schema/fixture, next slice L5, and the owner rationale for the contract decision.
  - Effect: documentation now describes the implemented surface rather than the pre-L1 state.

### Issues Found

- Problem: plan v1.11 stated that `review_queue.json` files are generated only from Phase 2, while Rule L1/L6 mandated paired queue entries when findings fire.
  Cause: lint safeguards were promoted into the plan after the original Phase 0/Phase 2 artifact boundary had already been written.
  Resolution: surfaced the contradiction before coding; after owner approval, revised the canonical plan to v1.12 and made deterministic lint queue artifacts an explicit Phase 0 exception.
  Outcome: implementation can preserve required reviewer context without implicitly overriding the specification.
- Problem: writing a queue file only when L1 fires would leave stale entries if the same output directory is reused after the assessment is corrected.
  Cause: findings and diagnostics are regenerated per run, but a conditional queue artifact would not be cleared on a subsequent clean lint pass.
  Resolution: on each Rule 0 clean `check`, write the lint review queue artifact, using an empty queue when no lint safeguard entry fires.
  Outcome: queue files reflect the current successful parse/run rather than earlier findings.
- Problem: the future workflow already describes a compact/verifier `review_queue`, while the new Phase 0 lint output writer would overwrite a shared target path rather than compose with upstream entries.
  Cause: Phase 2 queue generation and composition are still unimplemented; L1 is the first implemented producer.
  Resolution: kept `--review-queue-out` explicitly scoped to the Phase 0 lint-safeguard artifact and recorded Phase 2 merge/update behavior as required follow-through before a unified queue path is wired.
  Outcome: the current slice remains minimal and correct without silently defining destructive future composition semantics.
- Problem: adjacent Rule 0 prose still described `ai_judgement_pending` queue insertion as immediate even though Phase 0 has never emitted verifier queue entries.
  Cause: the same pre-lint Phase 0/Phase 2 boundary ambiguity appeared in the semantic-verification description.
  Resolution: qualified both plan locations and HANDOFF: Phase 0 retains pending links; Phase 2 introduces `ai_judgement_pending` entries and verifier routing.
  Outcome: lint safeguard queue output is no longer mistaken for unimplemented semantic-verifier queue output.

### Decisions

- **Owner decision (Phase 0 lint queue exception)**: proceed with Rule L1 by persisting paired lint review entries during Phase 0 `check`, despite the earlier general rule placing review queue generation in Phase 2. Rationale: an L1/L6 finding without its paired human-review context would defeat the documented safeguard mechanism.
- **Implementation boundary**: the exception covers deterministic lint safeguard entries only. `ai_judgement_pending`, compacting identity collisions, low-support handling, and verifier-generated queue behavior remain Phase 2 work.
- **Stale-state prevention**: Rule 0 clean executions emit a queue artifact even when empty; this is a small public-contract extension justified by deterministic rerun correctness.
- **Composition boundary**: the Phase 0 L1 artifact is not yet the future unified compact/verifier/lint queue; Phase 2 must preserve existing upstream entries when that pipeline is implemented.

### Next Steps

1. Implement Rule L5 (`bonus_grades_mandatory_only`) using the existing L1 rule/CLI/schema path and extending `fixtures/bonus_misuse/`.
2. Implement Rule L6 (`mandatory_spec_bonus_only_traced`) using the paired `mandatory_spec_bonus_review` entry already represented in `review_queue.schema.json`.
3. Resume Rule 2/3 after the lint family lands; amend the then-current plan with the final Rule 2 output literal before code emits it.

### Verification

- Red-state confirmation: `docker compose run --rm test tests/test_rules.py tests/test_cli_output_contract.py tests/test_fixtures.py -q` initially failed during collection because `run_rule_l1` did not yet exist.
- Focused suite: `docker compose run --rm test tests/test_rules.py tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed after implementation.
- Full suite: `docker compose run --rm test -q` passed (102 tests).
- Contract smoke: `docker compose run --rm harness --output json schema --command check` exposes `review_double_scoring`, `review_queue_path`, and `review_queue_count`.
- L1 smoke: `check` on `fixtures/bonus_misuse` returns exit `0`, `status=provisional_findings`, two medium findings (`unconfirmed_trace_coverage`, `double_scored_spec`), and one `double_scoring_review` queue entry.
- Publication review: the owner reported that an independent AI verification of this work passed and authorized committing and pushing the Rule L1 batch to `origin/main`.

---

## Phase 0 Rule L5 Implementation

### Goals

- Implement Rule L5 (`bonus_grades_mandatory_only`) on top of the published L1 lint foundation.
- Lock the boundary among L1 double scoring, L5 mandatory-only bonus design, and Rule 1 untraced bonus handling in the shared fixture.

### Completed Work

- Implemented Rule L5 in the deterministic rule pipeline.
  - Files changed: `src/assessment_harness/rules.py`, `src/assessment_harness/cli.py`.
  - Key changes: added structural `run_rule_l5(spec_items, rubric_items, trace_links)`; it emits medium/provisional `bonus_grades_mandatory_only` only for traced bonus rubrics whose referenced spec items are all `must`; wired `review_bonus_mandatory_only` into `check` and schema introspection.
  - Effect: bonus criteria that merely re-grade mandatory work are now surfaced independently of L1 overlap, without consulting semantic status.
- Extended regression and grounded fixture coverage.
  - Files changed: `tests/test_rules.py`, `tests/test_cli_output_contract.py`, `tests/test_fixtures.py`, `fixtures/bonus_misuse/rubric_items.yaml`, `fixtures/bonus_misuse/source/rubric.md`, `fixtures/bonus_misuse/source_manifest.yaml`.
  - Key changes: added L5 under-strict and two over-strict tests; expanded fixture with untraced RB3; asserted RB1 L1+L5 co-firing, RB2 optional trace non-firing, and RB3 Rule 1 informational ownership.
  - Effect: the three nearby bonus behaviors cannot silently collapse into one rule or double-count incorrectly.
- Updated project status documents.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, `docs/daily_logs/2026-05-27/work_log.md`.
  - Key changes: marked L5 complete, documented its no-new-queue surface, updated the next slice to L6, and recorded current test/smoke results.
  - Effect: handoff now directs the next worker to the sole remaining v1.12 lint implementation slice.

### Issues Found

- Problem: iterating over bonus rubric IDs as a set would make multiple future L5 findings appear in non-deterministic order.
  Cause: the initial minimal implementation used membership and iteration through the same set.
  Resolution: retained a list in source rubric order for emission and used a separate set only for membership checks.
  Outcome: CLI findings remain deterministic when more L5-triggering bonus items are introduced.

### Decisions

- Rule L5 adds no paired review queue entry: plan v1.12 assigns paired queue safeguards to L1 and L6, while L5 needs only the finding and `review_bonus_mandatory_only` action.
- `fixtures/bonus_misuse` remains the shared lint fixture: RB1 intentionally co-fires L1 and L5; RB2 and RB3 make the over-strict/mutual-responsibility boundary visible without creating an additional permanent fixture.

### Next Steps

1. Implement Rule L6 (`mandatory_spec_bonus_only_traced`) with paired `mandatory_spec_bonus_review` output and high/provisional severity.
2. Extend `fixtures/bonus_misuse/` with the L6 branch and its scored-trace/no-trace over-strict guards.
3. Resume Rule 2 and Rule 3 only after L6 completes the current lint family.

### Verification

- Red-state confirmation: focused pytest initially failed during collection because `run_rule_l5` did not yet exist.
- Focused suite: `docker compose run --rm test tests/test_rules.py tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed.
- Full suite: `docker compose run --rm test -q` passed (106 tests).
- Contract smoke: `docker compose run --rm harness --output json schema --command check` includes `review_bonus_mandatory_only`.
- L5 smoke: `check` on `fixtures/bonus_misuse` returns `(high=0, medium=3, informational=1)` with RB1 `double_scored_spec` + `bonus_grades_mandatory_only`, RB3 `orphan_bonus_rubric_item`, and one L1 queue entry.
- Publication review: the owner reported that an independent AI verification of Rule L5 passed and authorized committing and pushing this batch to `origin/main`.

---

## Phase 0 Rule L6 Implementation

### Goals

- Implement Rule L6 (`mandatory_spec_bonus_only_traced`) with its paired `mandatory_spec_bonus_review` safeguard.
- Resolve the L6 specification ambiguity discovered at implementation entry and preserve the chosen boundary in canonical documents and regression tests.

### Completed Work

- Implemented the final accepted lint-family rule.
  - Files changed: `src/assessment_harness/rules.py`, `src/assessment_harness/cli.py`, `schemas/findings.schema.json`.
  - Key changes: added `run_rule_l6(spec_items, rubric_items, trace_links)`; emitted high/provisional findings with `bonus_rubric_ids[]` and evidence context; generated paired `mandatory_spec_bonus_review` entries; exposed `review_mandatory_spec_bonus_only` through `check` and schema introspection.
  - Effect: a mandatory requirement evaluated only through bonus credit now appears as a high-priority provisional review target without becoming a blocking verdict before `gate`.
- Extended two-directional regression and grounded fixture coverage.
  - Files changed: `tests/test_rules.py`, `tests/test_cli_output_contract.py`, `tests/test_fixtures.py`, `fixtures/bonus_misuse/*`.
  - Key changes: added L6 under-strict finding/queue guard, scored-coverage and no-trace over-strict guards, qualitative-only and bonus+qualitative suppression guards; expanded the shared fixture with mandatory S3 traced only by bonus RB4.
  - Effect: `bonus_misuse` now demonstrates L1/L5/L6 together while keeping Rule 1 orphan and L6 qualitative boundaries distinct.
- Aligned the specification and project status.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`, `docs/ideation_assessment_harness_v2.2.md`, `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: promoted the canonical plan to v1.13; defined L6 as bonus-only; marked lint Rule L1/L5/L6 complete and Rule 2 as next.
  - Effect: the emitted `bonus_rubric_ids[]`/queue contract and the prose condition no longer disagree about qualitative traces.

### Issues Found

- Problem: plan v1.12 and ideation v2.2 described L6 as firing for all non-scored traces (`bonus` or `qualitative`), while its finding type, payload, and review queue contract represented only bonus rubrics.
  Cause: L6's condition had retained a broad no-scored formulation after its concrete safeguard contract was designed around bonus credit.
  Resolution: surfaced the contradiction before implementation; the owner chose the bonus-only boundary; updated plan v1.13 and ideation; added qualitative suppression regression tests.
  Outcome: L6 cleanly detects mandatory work assigned only to bonus credit, while qualitative/no-scored consistency remains a Rule 2-family follow-up rather than being forced into an incompatible payload.

### Decisions

- **Owner decision (L6 qualitative boundary)**: L6 applies only when every trace for a `must` spec targets a `bonus` rubric. The owner chose this because qualitative content is not itself scored or awarded as bonus; its treatment can be assessed separately under the Rule 2 family without distorting L6's bonus-specific contract.
- Rule L6 preserves L1's paired safeguard pattern: its high/provisional finding is accompanied by a `mandatory_spec_bonus_review` queue item so a reviewer can distinguish intentional bonus treatment from design error before any `gate` confirmation.

### Next Steps

1. Independently verify the Rule L6 implementation batch and publish it after approval.
2. Implement Rule 2 using the recorded `uncovered_must_spec_item` / `review_uncovered_must_spec` recommendation, including the qualitative/no-scored area left outside L6.
3. Implement Rule 3 and then the `gate` promotion flow.

### Verification

- Red-state confirmation: focused pytest initially failed during collection because `run_rule_l6` did not yet exist.
- Focused suite: `docker compose run --rm test tests/test_rules.py tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed.
- Full suite: `docker compose run --rm test -q` passed (111 tests: 13 contract, 4 fixture, 12 model, 82 rule tests).
- Contract smoke: `docker compose run --rm harness --output json schema --command check` includes `review_mandatory_spec_bonus_only`.
- L6 smoke: `check` on `fixtures/bonus_misuse` returns `(high=1, medium=4, informational=1)`; S3/RB4 produces `mandatory_spec_bonus_only_traced`, `review_mandatory_spec_bonus_only`, and the second review queue entry (`review_queue_count=2`).
- Publication review: the owner reported that an independent AI verification of Rule L6 and the plan v1.13 boundary resolution passed and authorized committing and pushing this batch to `origin/main`.
