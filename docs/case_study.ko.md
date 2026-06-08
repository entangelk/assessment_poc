<p align="center">
  <a href="./case_study.md"><img src="https://img.shields.io/badge/Language-EN-6B7280?style=for-the-badge" alt="English"></a>
  <a href="./case_study.ko.md"><img src="https://img.shields.io/badge/Language-KO-111111?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# 케이스 스터디 — Assessment Spec Harness

응시자가 채점되기 전에 채용 과제의 *설계* 자체를 검증하기 위해 내가 (AI 에이전트와 함께)
설계하고 구현한 proof-of-concept다. 이 문서는 결정을 중심으로 풀어낸 서사 버전이며,
1차 출처 인용까지 갖춘 독립형 결정 기록은 [decisions.md](decisions.ko.md)에 있다.

## 문제

채용 과제는 서로 어긋나기 쉬운 두 부분으로 이루어진다. 응시자가 읽는 **공개 명세(spec)**와,
평가자가 채점 기준으로 삼는 **비공개 평가 rubric**이다. 이 둘이 소리 없이 벌어질 때 —
어떤 scored 기준도 다루지 않는 *must* 요구사항, 명세가 한 번도 요구하지 않은 것을
조용히 채점하는 창의성 평가 기준, 보너스 점수만 받는 필수 요구사항 — 응시자는 공개되지
않은 조건으로 평가받는다. 불공정해지고 나서야 누군가 알아챈다.

이 도구는 **응시자를 평가하지 않는다. 평가 설계 자체를 평가한다** — spec과 rubric 사이의
내부 일관성을 본다 — 그리고 누구도 채점되기 전에 그 간극을 검토 가능한 finding으로 드러낸다.

## 목표

freeze된 spec + rubric + 그 trace link가 주어지면 *설계*의 구조적 결함을 표시하는,
deterministic하고 감사(audit) 가능한 하네스. 그리고 **절대 자동 pass/fail을 내지 않는다.**
1차 호출 주체는 파이프라인 안의 **AI 에이전트**이고, 사람은 최종 검토자다 — 기계가 사람을
대체하지 않는다.

범위에 대한 정직함을 먼저 밝힌다. 이것은 **proof-of-concept**다. deterministic validation
core와 review/verdict 흐름은 구현·테스트되어 있지만, 그것들에 입력을 공급할 multi-run
agent extraction 파이프라인은 계약/기반(foundation)만 잡혀 있다. 그 경계는
[아키텍처 다이어그램](../README.md)과 [구현 현황](../README.md) 표에 정직하게 그려져 있다.

## 핵심 결정 (이 프로젝트의 심장)

여기서의 가치는 코드 줄 수가 아니라 판단이다. 시스템을 형성한 다섯 가지 결정을 아래에 하나씩
담았으며, 각 결정의 전체 논의·트레이드오프·당대 인용은 [decisions.md](decisions.ko.md)에 있다.

### 1. 1차 사용자는 사람이 아니라 AI 에이전트 — `decisions.md` §A1

초기 초안은 이것을 LLM을 덧붙인 평범한 CLI로 다뤘다. 대신 나는 *agent-as-user*를
제1원칙으로 삼았다. 안정적인 출력 계약(`status`, `exit_code`, `command`, `next_actions`),
`--output json`, 에이전트가 스스로 발견할 수 있는 `schema --command` introspection 명령,
그리고 framework-agnostic한 `AgentRunner` 프로토콜. 그 비용 — 초반의 더 많은 계약 설계,
이후 모든 기능이 envelope를 안정적으로 유지하도록 제약받는 것 — 이 바로 핵심이다.
안정적인 계약 *그 자체가* 제품이다.

### 2. 만들기를 거부한 것으로 그려진 범위 — `decisions.md` §A2 / §A4

도구는 하지 않기로 한 것만큼이나 그 정체성이 정의된다. 나는 제안된 세 가지 규칙(가중치
분포 lint, 자동 scoring-drift 탐지, 모순 기준 탐지)을 원칙적으로 거부했다. 그것들은
응시자가 볼 수 있는 평가자의 *재량*을 막을 뿐, 이 도구가 잡으려는 *공개되지 않은* 기준을
막지 않기 때문이다. 같은 절제가 "lint" 규칙 계열 전체를 낳은 프레이밍 전환을 만들었다.
여기서 "lint"는 내 Python 코드를 위한 것이 아니다 — 채점 구조에 적용된 **역(inverse)
불변식**이다 ("여기 *있어선 안 될* 무언가가 있는가?").

### 3. `check`는 결코 차단하지 않는다. 오직 `gate`만 — `decisions.md` §A3

deterministic checker가 pass/fail을 반환하게 두면, *평가 설계의 linter*가 조용히
*자동 심판자*로 변한다 — 그리고 틀릴 수 있는 자동 심판자는 없느니만 못하다. 그래서
`check`는 오직 **provisional** finding만 낸다. 확정된 외부 verdict를 반환할 수 있는
유일한 명령은 `gate`이고, `gate`는 오직 **사람의** 최종 검토 기록만 읽는다. 그마저도
모든 확정 finding이 차단하는 것은 아니다 — 차단 verdict는 설계를 무효화하는 세 가지
유형으로 한정된다. 기계는 분석하고, 사람이 판단한다.

### 4. 조용히 거짓말하던 `validated` 라벨 → 단계화된 무결성 모델 — `decisions.md` §B1 (대표 사례)

모든 candidate run은 `integrity_status`를 갖는다. 계약은 `validated`를 "모든 무결성
검사 통과; downstream assessment 자격 있음"으로 정의했다. 내 작업을 **독립적으로 감사**하라고
맡긴 AI 에이전트가, reference가 dangling이고 evidence quote가 날조된 run을 찔러봤는데 —
classifier는 에러 0개로 `validated`를 반환했다. 가장 값싼 두 검사만 거친 뒤 gate-status를
찍고 있었던 것이다. 손상된 데이터는 없었다(downstream 소비자가 아직 존재하지 않는다) —
*계약* 차원에서 잡혔고, 이것이 바로 독립 감사가 존재하는 이유다. 나는 조용히 패치하지
않았다. *라벨*이 코드가 지키지 않는 약속을 하고 있었으므로 **모델을 단계화했다**
(`structurally_validated` vs `validated`). 이후 failure state를 내가 분명히 말할 규칙
아래 세 갈래로 나눴다 — *downstream 소비자가 실제로 분기하는 만큼만, 그리고 이름이 그렇지
않으면 거짓이 될 만큼만 상태를 쪼갠다.*

### 5. AI에게 내 작업을 감사시키고 — verdict 철회까지 허용했다 — `decisions.md` §C1

green 테스트 스위트는 코드가 테스트가 말하는 대로 작동함을 증명할 뿐, 명세가 요구하는 대로
작동함을 증명하지 않는다. 나는 독립 검증을 1급 산출물([docs/verifications/](verifications/))로
삼고, 이빨 있는 규칙을 적용했다. 모든 명세 분기는 regression에 매핑되어야 하고, guard는
*양방향*으로 실패해야 하며, 누락된 경계 lock은 **차단(blocking)** finding이다 — 절대
"향후 과제"로 재포장하지 않는다. 이 규율은 실제로 작동한다. 최초의 Rule 3 verdict는 감사가
불완전한 경계 검사를 발견한 뒤 **철회**되고 재발행되었다. 거짓말하는 green bar를 내보내느니
철회된 verdict를 기록하는 쪽을 택하겠다.

## 무엇을 만들었나 (현재)

구현·테스트 완료:

- **Rule 0** reference-integrity 엔진(source-snapshot grounding, evidence
  completeness, 필수 `--source-manifest`).
- **Rule 1–3**(scored-rubric 커버리지, required-spec 커버리지, optionality 일관성)과
  **lint 규칙 L1 / L5 / L6**(이중 채점, 필수 작업의 보너스 재채점, 필수의 보너스-전용 처리).
- 안정적인 agent-consumable envelope와 `schema` introspection 명령을 갖춘
  **`check` / `report` / `review` / `gate` / `materialize-review`**.
- **Agent-runner 프로토콜 + deterministic mock**, candidate artifact 스키마,
  audit-trace attribution, runner normalization, 그리고 deep Rule 0 분류를 갖춘
  **단계화된 candidate 무결성 모델**.

계약 / 기반만 (의도적으로 보류): 실제 SDK runner, Phase 1 수동 실행, 전체 end-to-end
워크플로. 초기 `extract` / `compact` / `verify` 오케스트레이션은 deterministic
`mock_fixture` 경로에 한해 존재한다. mock verifier는 실제 모델 판단을 주장하지 않고
보수적인 semantic proposal만 기록한다. 영역별 정직한 상태는
[구현 현황 표](../README.md)를 참조.

## 어떻게 검증되었나

- **양방향 regression guard**를 갖춘 **통과하는 regression 스위트**(각 규칙 분기마다
  under-strict guard — 원래 버그가 다시 실패할 수 있음 — 와 over-strict guard —
  정상 케이스가 잘못 표시되지 않음 — 를 모두 가진다).
- 위의 "누락 lock은 차단" 규율을 따르는 에이전트가 생성한,
  [docs/verifications/](verifications/) 아래의 **독립 AI 검증 기록**.
- Fixture는 테스트에서 manifest 대비 source hash를 재계산하므로, 모든 주장이 원본
  freeze 텍스트에 grounding된다.

(측정된 테스트 + smoke 증거 표는 날짜가 박힌 moving snapshot으로 `docs/evaluation.md`에
있으며, 공개 전 재계산되어야 한다.)

## 한계 / 의도적 보류

- 실제 runner를 갖춘 전체 agent extraction 파이프라인은 구현되지 않았다. 초기
  `extract` / `compact` / `verify`는 `mock_fixture` 경로를 실행할 수 있지만, 아직
  실제 SDK runner가 그 artifact를 생성하지 않는다.
- 이 도구는 **threshold 값에 대해 어떤 의견도 갖지 않는다**. 그것들은 호출자가 조정하는
  policy이지 권위 있는 기본값이 아니다.
- Raw-trace 보존/편집(redaction) policy는 보류 상태다. 오늘 스키마로 검증되는 것은
  audit trace뿐이다.
- 이것은 single-run-quality PoC다. determinism은 "동일한 compacted + verified
  artifact → 동일한 finding"으로 정직하게 한정되며, agent 재현성으로 한정되지 않는다.

## 다음 단계

1. 공개 freeze 시점에 실제 테스트/smoke 출력으로부터 `docs/evaluation.md`를 한 번 더 재계산.
2. 기존 runner-protocol, candidate-integrity, compacting, mock verifier 기반 위에서
   실제 SDK runner 지원.
3. 첫 실제 과제 수동 실행(Phase 1).

---

*AI 에이전트와 함께 만들었다 — 초안 작성, candidate 생성, 그리고 (의도적으로) 내 작업에
대한 독립 감사를 위해. 결정은 내 것이었고, 에이전트는 실행하고 찔러봤다. 이에 대한 더 많은
이야기는 [decisions.md](decisions.ko.md)에.*
