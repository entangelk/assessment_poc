<p align="right">
  <a href="./ideation_assessment_harness_v2.md"><img src="https://img.shields.io/badge/Language-EN-6B7280?style=for-the-badge" alt="English"></a>
  <a href="./ideation_assessment_harness_v2.ko.md"><img src="https://img.shields.io/badge/Language-KO-111111?style=for-the-badge" alt="한국어"></a>
</p>

# Ideation v2 — 채용 과제 평가 설계 하네스

## 0. 재검토 요약

v1의 핵심 문제의식은 유효하다. 채용 과제 평가에는 코드 테스트와 비슷한 안전망이 필요하다. 다만 v1은 범위가 넓었다. 자동 채점, 통계 검증, 사후 리포트, VectorDB 기반 패턴 마이닝까지 포함하면서 초기 제품 가설이 흐려졌다.

이번 v2에서는 초점을 좁힌다.

> 채용 과제의 공개 명세와 비공개 평가 rubric 사이의 불일치를 사전에 검출하는 하네스.

즉, 이 도구는 응시자를 평가하는 도구가 아니라 **평가 설계를 평가하는 도구**다.

---

## 1. 문제 정의

채용 과제는 보통 두 개의 문서 세계로 나뉜다.

* **Candidate-facing spec**: 응시자가 보는 README, 과제 설명, 요구사항, 제약 조건, 제출 가이드
* **Evaluator-facing rubric**: 평가자가 보는 채점 기준, 가중치, 내부 판단 기준, 감점 규칙, 우수 답안 예시

문제는 두 문서 세계가 자주 분리되어 관리된다는 점이다. 이때 다음과 같은 구조적 문제가 발생한다.

### 1.1 Hidden Criterion

응시자에게 공개되지 않은 기준이 실제 평가에서 중요한 가중치를 갖는다.

예를 들어 README에는 명시되지 않았지만, 내부 rubric에서는 “자율적으로 특정 edge case를 발견했는가”가 높은 점수를 갖는 경우다. 이 경우 응시자는 같은 과제를 수행하지만, 실제로는 서로 다른 시험지를 받은 것과 비슷한 상태가 된다.

### 1.2 Misleading Optionality

README에서는 선택 항목처럼 보이지만, 실제 평가에서는 강한 차별 시그널로 쓰인다.

“Optional”이라고 쓰인 기능이 실제로는 상위권 선별 기준이라면, 응시자는 시간 배분을 잘못하게 된다. 문제는 그 응시자의 판단력이 아니라, 평가 설계의 정보 제공 방식에 있다.

### 1.3 Time Budget Mismatch

권장 수행 시간과 rubric이 요구하는 작업 깊이가 맞지 않는다.

예를 들어 README는 10~18시간을 권장하지만, rubric은 실질적으로 며칠 단위의 탐색·실험·문서화가 있어야 높은 점수를 받는 구조일 수 있다. 이 경우 평가 결과는 실력뿐 아니라 가용 시간, 과몰입 가능성, 사전 정보 운에 크게 좌우된다.

### 1.4 Post-hoc Rubric Drift

평가 과정이나 회고 과정에서 새로운 기준이 뒤늦게 의미를 갖기 시작한다.

좋은 제출물을 본 뒤 “이런 접근이 중요했다”고 사후적으로 기준화하는 것은 자연스러운 인간 반응이다. 그러나 그것이 해당 라운드의 평가 점수에 반영되면, 기준이 응시 이후에 생긴 셈이 된다.

### 1.5 Feedback Non-debuggability

응시자는 결과를 받아도 무엇을 개선해야 하는지 알기 어렵다.

“아쉬웠다”, “깊이가 부족했다”, “상위권과 차이가 있었다” 같은 피드백은 정성적으로는 맞을 수 있지만, 어떤 공개 요구사항과 어떤 평가 기준 사이에서 점수가 갈렸는지 추적할 수 없다면 학습 가치가 낮다.

---

## 2. 핵심 가설

채용 과제 평가는 다음 invariant를 만족해야 한다.

> 모든 rubric item은 candidate-facing spec의 하나 이상의 항목으로 trace 가능해야 한다.

이를 만족하지 못하는 rubric item은 세 가지 중 하나로 처리되어야 한다.

1. spec에 명시한다.
2. rubric에서 제거한다.
3. 정식 평가 항목이 아니라 bonus / qualitative note로 격하한다.

이 invariant를 CI처럼 강제하면, hidden criterion, misleading optionality, post-hoc rubric drift의 상당 부분을 구조적으로 줄일 수 있다.

---

## 3. 제품 정의

### 이름

**Assessment Spec Harness**

### 한 줄 설명

채용 과제의 README와 내부 평가 rubric을 비교하여, 평가 기준의 명세 추적성·시간 예산·가중치 정합성을 검증하는 도구.

### 더 짧은 표현

> CI for hiring assessments.

### 정확한 포지셔닝

이 제품은 자동 채점기가 아니다. 응시자의 실력을 평가하는 것이 아니라, 평가 설계가 공정하고 설명 가능하며 재현 가능한지 검사한다.

---

## 4. 대상 사용자

### 4.1 Primary User: Technical Assessment Owner

채용 과제를 설계하고 유지보수하는 엔지니어, 팀 리드, hiring manager.

이 사용자는 다음 질문에 답해야 한다.

* 우리가 평가하려는 능력이 README에 충분히 드러나 있는가?
* 내부 rubric이 응시자에게 공개된 요구사항과 연결되는가?
* 특정 평가 항목이 과제 범위를 넘어서는가?
* 권장 시간 안에서 상위 점수를 받을 수 있는 구조인가?

### 4.2 Secondary User: Recruiting Ops / HR Ops

채용 프로세스의 일관성, 기록, 감사 가능성을 관리하는 사람.

이 사용자는 다음을 원한다.

* 라운드별 rubric 변경 이력
* 평가 기준의 사전 확정 여부
* 응시자 피드백 템플릿
* 외부 공유 자료 작성 시 출처·익명화 체크리스트

### 4.3 Future User: Assessment Platform Vendor

Codility, HackerRank, Coderbyte류 플랫폼 또는 사내 평가 플랫폼.

이들에게는 “문제를 출제하는 기능”보다 “문제가 공정하게 평가 가능한지 검증하는 기능”이 부가가치가 될 수 있다.

---

## 5. MVP 범위

MVP는 작아야 한다. v1의 Layer 0과 일부 Pre-flight만 포함한다.

### 5.1 입력

* `spec.md`: 응시자 공개 문서
* `rubric.yaml`: 내부 평가 기준
* 선택 입력

  * `time_budget.yaml`
  * `evaluator_notes.md`
  * `sample_submission/`

### 5.2 출력

* Traceability Report
* Orphan Rubric Item 목록
* Ambiguous Spec Item 목록
* Optionality Mismatch 경고
* Time Budget Risk 경고
* Candidate-facing Disclosure 초안

### 5.3 MVP가 하지 않는 것

* 제출물 자동 채점
* 합격/불합격 판단
* 평가자 대체
* 법적 판단
* 대규모 응시자 패턴 마이닝
* VectorDB 기반 유사도 분석

---

## 6. 데이터 모델 초안

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

### 6.3 검증 결과

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

## 7. 핵심 검증 규칙

### Rule 1. Rubric Coverage

모든 rubric item은 하나 이상의 spec item에 연결되어야 한다.

* 실패 예: 내부 기준에만 존재하는 “특정 edge case 자율 발견”
* 권장 조치: README에 평가축으로 명시하거나 bonus로 격하

### Rule 2. Spec Coverage

중요한 spec item은 rubric에 반영되어야 한다.

* 실패 예: README에는 핵심 요구사항으로 쓰였지만 평가표에는 없음
* 권장 조치: rubric 항목 추가 또는 README에서 중요도 조정

### Rule 3. Optionality Consistency

spec에서 optional로 표시된 항목은 rubric에서도 낮은 가중치이거나 bonus여야 한다.

* 실패 예: README에는 optional, rubric weight는 20%
* 권장 조치: optional 문구 제거 또는 평가 가중치 하향

### Rule 4. Time Budget Consistency

rubric의 expected full-score path가 권장 시간과 과도하게 충돌하면 경고한다.

* 실패 예: 권장 시간 10~18h, full-score 예상 effort 35h
* 권장 조치: 요구사항 축소, 권장 시간 수정, bonus 항목 분리

### Rule 5. Rubric Version Lock

라운드 시작 이후 scoring rubric이 변경되면 해당 변경은 명시적으로 기록되어야 한다.

* 변경 허용: 오탈자 수정, 설명 보강, 미래 라운드용 변경
* 변경 위험: 현재 라운드 점수에 영향을 주는 기준 추가·삭제·가중치 변경

### Rule 6. Disclosure Readiness

평가 종료 후 응시자에게 제공할 수 있는 최소한의 score breakdown이 생성 가능해야 한다.

* 각 점수 항목은 spec item과 연결되어야 한다.
* 피드백은 “좋음/나쁨”이 아니라 “어느 요구사항에서 어떤 증거가 부족했는가”로 표현되어야 한다.

---

## 8. 리포트 예시

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

## 9. 사용자 흐름

### 9.1 로컬 CLI

```bash
assessment-harness check \
  --spec README.md \
  --rubric rubric.yaml \
  --time-budget time_budget.yaml
```

출력:

```bash
status: fail
report: reports/assessment_harness_report.md
machine_readable: reports/assessment_harness_report.json
```

### 9.2 GitHub PR Check

rubric이나 README가 변경될 때마다 CI가 실행된다.

* orphan rubric item이 있으면 merge block
* optionality mismatch가 있으면 warning 또는 block
* time budget risk는 warning
* 라운드 시작 이후 rubric 변경은 approval required

### 9.3 라운드 종료 후

평가 결과와 rubric을 연결해 candidate-facing feedback을 생성한다.

```text
You received partial credit on R3.
This maps to README requirement S4: "Handle refund states."
Evidence found: basic refund flow implemented.
Missing evidence: conflict handling between cancellation and refund policy.
```

---

## 10. LLM의 역할

LLM은 핵심 판단자가 아니라 보조 분석기다.

### 적합한 역할

* README에서 요구사항 후보 추출
* rubric item과 spec item의 semantic match 후보 제안
* 모호한 문구 탐지
* candidate-facing feedback 문장 초안 생성

### 부적합한 역할

* 최종 합격/불합격 판단
* 단독 점수 산정
* 법적 리스크 판정
* 평가자의 책임 대체

### 운영 원칙

LLM output은 항상 structured finding으로 저장하고, 사람이 승인해야 한다.

```yaml
llm_suggestion:
  type: possible_orphan_rubric_item
  confidence: 0.78
  reason: "No candidate-facing requirement appears to mention this criterion."
  human_status: pending_review
```

---

## 11. 왜 지금 이 접근이 좋은가

### 11.1 작게 시작할 수 있다

MVP는 복잡한 플랫폼이 아니라 YAML 스키마와 검증 스크립트로 시작할 수 있다.

### 11.2 고통점이 명확하다

채용 과제를 운영해본 팀은 README와 내부 rubric이 어긋나는 문제를 직관적으로 이해한다.

### 11.3 자동 채점보다 방어 가능하다

자동 채점은 논쟁적이다. 반면 “평가 기준이 공개 명세와 연결되어야 한다”는 원칙은 조직적으로 받아들이기 쉽다.

### 11.4 응시자 경험과 회사 리스크를 동시에 개선한다

응시자는 기준을 더 잘 이해하고, 회사는 평가 일관성·감사 가능성·외부 신뢰를 얻는다.

---

## 12. 경쟁/대체재 관점

기존 채용 평가 플랫폼은 주로 다음에 집중한다.

* 문제 출제
* 코딩 테스트 실행
* 자동 채점
* 표절 탐지
* 지원자 관리

반면 Assessment Spec Harness의 차별점은 다음이다.

> 문제를 얼마나 잘 푸는지가 아니라, 문제가 얼마나 공정하게 평가 가능하게 설계되었는지를 검증한다.

즉, 기존 플랫폼의 대체재라기보다 상위 설계 검증 레이어다.

---

## 13. 단계별 로드맵

### Phase 0 — Schema & Manual Review

* spec item / rubric item YAML 스키마 정의
* 사람이 수동으로 trace mapping 작성
* 간단한 orphan detection

성공 기준:

* 한 과제에 대해 traceability matrix 생성 가능
* orphan rubric item을 1개 이상 실제로 검출

### Phase 1 — CI Check

* GitHub Action으로 검증 자동화
* rubric 변경 PR에서 report 생성
* high severity finding은 merge block

성공 기준:

* README/rubric 변경 시 자동 리포트 생성
* 평가 기준 변경 이력 추적 가능

### Phase 2 — LLM-assisted Mapping

* LLM이 spec item 후보 추출
* LLM이 rubric-to-spec mapping 후보 제안
* 사람은 approve/reject만 수행

성공 기준:

* 수동 매핑 시간 50% 이상 감소
* false positive/negative를 사람이 쉽게 수정 가능

### Phase 3 — Feedback Generator

* 점수표와 trace matrix 기반 candidate feedback 생성
* 공개 가능한 수준과 내부용 수준 분리

성공 기준:

* 응시자에게 전달 가능한 score breakdown 초안 생성
* 평가자 리뷰 후 발송 가능

### Phase 4 — Analytics & Round Drift

* 라운드 간 rubric 변경 추적
* 특정 항목의 난이도·변별력 변화 분석
* time budget estimate 보정

성공 기준:

* 다음 라운드의 과제 개선 PR로 연결

### Phase 5 — Pattern Provenance

대규모 응시자 데이터가 쌓였을 때만 검토한다.

* 유사 접근 clustering
* outlier detection
* pattern provenance
* IP/출처 이슈 검토 보조

주의:

이 단계는 임베딩 모델, threshold, clustering parameter에 의존한다. 따라서 MVP에 포함하지 않는다.

---

## 14. 리스크와 반론

### 반론 1. “좋은 평가는 원래 암묵지를 포함한다.”

맞다. 모든 평가 기준을 완전히 명문화할 수는 없다. 그러나 점수에 큰 영향을 주는 기준은 최소한 응시자에게 방향성이라도 공개되어야 한다. 암묵지는 qualitative note로 남길 수 있지만, 핵심 scoring axis가 되어서는 안 된다.

### 반론 2. “너무 투명하면 응시자가 게임한다.”

평가 기준을 숨기는 방식으로 게임을 막는 것은 약한 설계다. 좋은 rubric은 공개되어도 여전히 실력을 변별해야 한다. 예를 들어 “테스트를 잘 작성하라”는 기준은 공개되어도 좋은 테스트를 실제로 작성하는 것은 어렵다.

### 반론 3. “시간 추정은 부정확하다.”

맞다. 따라서 time budget check는 hard fail이 아니라 risk signal이어야 한다. 목적은 정확한 시간 예측이 아니라, 명백히 과도한 과제 설계를 사전에 감지하는 것이다.

### 반론 4. “LLM이 mapping을 틀릴 수 있다.”

맞다. 그래서 LLM은 최종 판단자가 아니라 reviewer assistant다. 최종 SoT는 사람이 승인한 YAML과 audit log다.

### 반론 5. “소규모 회사에는 과하다.”

Phase 0 수준은 과하지 않다. 오히려 작은 팀일수록 한두 명의 평가자 직관에 의존하기 쉬우므로, 최소한의 trace matrix가 큰 효과를 낼 수 있다.

---

## 15. 성공 지표

### 제품 사용 지표

* 과제당 생성된 spec item 수
* rubric item 중 trace coverage 비율
* orphan rubric item 검출 수
* CI에서 차단된 rubric 변경 수

### 품질 지표

* 라운드 시작 전 발견된 평가 기준 불일치 수
* 평가자 간 scoring disagreement 감소
* 응시자 피드백 만족도
* 평가 후 이의제기/혼란 감소

### 운영 지표

* rubric 업데이트에 걸리는 시간
* candidate feedback 작성 시간
* 다음 라운드 개선 PR 수

---

## 16. 가장 작은 PoC

목표는 플랫폼을 만드는 것이 아니다. 하나의 실제 또는 샘플 과제를 대상으로 traceability matrix를 만드는 것이다.

### 입력

* README 1개
* rubric YAML 1개
* 권장 시간 1개

### 구현

* Python script
* YAML parser
* Markdown heading parser
* 간단한 validation rules
* Markdown report generator

### 산출물

* `traceability_matrix.md`
* `findings.md`
* `rubric.schema.yaml`
* `spec.schema.yaml`

### PoC 성공 기준

다음 중 하나라도 달성하면 성공이다.

* README에 없는 rubric item을 찾아낸다.
* optional이라고 쓰인 항목의 높은 가중치를 찾아낸다.
* 권장 시간과 rubric depth 사이의 불일치를 설명한다.
* 평가 후 응시자에게 줄 수 있는 score breakdown의 뼈대를 만든다.

---

## 17. v1 대비 변경점

### 유지한 것

* 평가에도 테스트 하네스가 필요하다는 핵심 비유
* Spec SoT와 Rubric SoT의 분리
* rubric item은 spec에 trace되어야 한다는 invariant
* 사후 투명성과 audit trail의 중요성

### 줄인 것

* 자동 채점 중심성
* VectorDB / pattern miner / RAG grader
* 대규모 평가 플랫폼 아키텍처
* 통계 시각화 레이어의 초기 비중

### 강화한 것

* MVP 정의
* target user
* non-goals
* 검증 규칙
* 데이터 모델
* CI workflow
* 반론 대응

---

## 18. 최종 정리

Assessment Spec Harness의 핵심은 단순하다.

> 응시자가 보지 못한 기준으로 응시자를 평가하지 말라.

이를 감정적 원칙이 아니라 시스템 invariant로 만든다.

* rubric item은 spec item에 trace되어야 한다.
* optional 항목은 실제로 optional이어야 한다.
* 권장 시간은 평가 깊이와 대략 맞아야 한다.
* 라운드 중 기준 변경은 audit되어야 한다.
* 피드백은 디버깅 가능해야 한다.
