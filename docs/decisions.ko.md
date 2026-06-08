<p align="center">
  <a href="./decisions.md"><img src="https://img.shields.io/badge/Language-EN-6B7280?style=for-the-badge" alt="English"></a>
  <a href="./decisions.ko.md"><img src="https://img.shields.io/badge/Language-KO-111111?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# 설계 결정

이 프로젝트의 가치는 코드 줄 수가 아니라 **왜 지금의 모습으로 형성되었는가**다. 나는 이
결정들을 *일어난 그 순간에* 기록했다. 구현 계획서의 변경 이력(v1.0 → v1.30), 일일 작업
로그, ideation 문서, 그리고 독립 검증 기록 속에. 여기 어떤 것도 발표용으로 사후에 재구성한
것이 아니다. 모든 항목은 당대의, 타임스탬프가 찍힌 출처로 링크된다.

**내가 일한 방식에 대하여:** 나는 이것을 AI 에이전트와 함께 만들었다 — 초안 작성을 위해,
candidate 생성을 위해, 그리고 (의도적으로) 내 작업에 대한 *독립 감사*를 위해. 나는 이를
숨기지 않는다. 2026년에 보여줄 가치가 있는 기술은 코드를 타이핑하는 것이 아니라 **문제를
프레이밍하고, 에이전트를 지휘하며, 어떤 결정이 옳은지에 대한 판단을 행사하는 것**이다.
그래서 이 항목들은 1인칭으로 쓰였다. 에이전트는 실행하고 찔러봤으며, 결정은 내 것이었다.

각 결정은 같은 형식을 따른다: **무엇이 걸려 있었나 → 결정과 그 이유 → 트레이드오프 →
어떻게 검증되었나 → 어디서 확인하나.**

---

## Part A — 이 도구는 무엇이며, 무엇을 만들기를 거부했나

### A1. 1차 사용자는 사람이 아니라 AI 에이전트다

**걸려 있던 것.** 초기 초안은 이것을 "LLM 어댑터"를 덧붙인 평범한 CLI로 다뤘다. 그러나
assessment-validation 도구의 현실적 호출자는, 명령을 타이핑하는 사람이 아니라 파이프라인
안의 AI 에이전트 자체다.

**결정 (v1.2).** 나는 *agent-as-user*를 제1원칙으로 삼았다. LLM 통합은 **framework-agnostic한
`AgentRunner` 프로토콜** 뒤에 자리 잡고(Claude Agent SDK가 기본값, 한 모듈로 교체 가능),
CLI는 **에이전트가 소비할 수 있는 계약**이다. 안정적인 출력 core(`status`, `exit_code`,
`command`, `next_actions`), `--output json`, 분리된 stdout/stderr, 실행 가능한 에러,
그리고 호출자가 인터페이스를 스스로 발견할 수 있는 `schema --command <name>` introspection 명령.

**트레이드오프.** 이것은 사람을 향한 CLI에 필요한 것보다 더 많은 초반 계약 설계이고, 이후
모든 기능이 envelope를 안정적으로 유지하도록 제약한다. 나는 그것을 받아들였다. 안정적인
계약이 편의 기능이 아니라 제품이다.

**확인.** Plan 변경 이력 v1.2; `tests/test_cli_output_contract.py`.

### A2. 거부한 것으로 그려진 범위 경계

도구는 하지 않기로 한 것만큼이나 그 정체성이 정의된다. 세 가지 규칙이 제안되었고, 나는 각
각을 노력이 아니라 원칙에 따라 거부했다.

- **L3 — fan-out / 가중치 분포 lint → 거부.** 모든 요구사항이 공개라면, 평가자가 가중치를
  어떻게 분배하는가는 숨겨진 함정이 아니라 정당한 **설계 재량**이다. 이 도구는 응시자가 볼
  수 있는 선택이 아니라 *공개되지 않은* 기준으로부터 응시자를 보호한다. 응시자 보호 가치
  없음 → 제외.
- **L8 — 자동 scoring-drift 탐지 → 거부 (수동 유지).** 에이전트 기반 탐지기는 여기서 그
  값어치보다 비용이 크고, 그것이 쫓는 불변식("명세에 없는 채점 기준은 없다")은 이미 Rule 1이
  일부 잡는다. *기존* link에서의 진짜 drift는 사람의 최종 검토 책임이며,
  `final_review_record.drift_observations[]`에 기록된다.
- **L9 — 모순 기준 탐지 → 거부.** 두 채점 기준이 서로 모순되는 것은 채점 검증이 아니라
  *설계*의 실패다. 그것은 미래의 "design validation" 계열에 속한다. 이를 거부함으로써 이
  PoC의 책임 경계를 날카롭게 유지했다. **설계 비평이 아니라 채점 일관성.**

**왜 중요한가.** Scope creep은 PoC의 기본 실패 모드다. 각 거부는 시스템을 한 문장으로
설명 가능하게 유지하는 의도적인 선이다.

**확인.** Ideation v2.2 §4–§5 (L3/L8/L9 거부 근거, Owner 결정).

### A3. `check`는 결코 차단하지 않는다. 오직 `gate`만

**걸려 있던 것.** deterministic checker가 pass/fail을 반환하게 두고 싶은 유혹이 있다.
그것은 *평가 설계의 linter*를 조용히 *자동 심판자*로 바꾼다 — 그리고 틀릴 수 있는 자동
심판자는 없느니만 못하다.

**결정 (v1.3, v1.6).** `check`는 오직 **provisional** finding만 낸다. 확정된 외부 verdict를
반환할 수 있는 유일한 명령은 `gate`이고, `gate`는 오직 **사람의 최종 검토 기록**만 읽는다.
`ai_judgement` trace link는 사람이 수락하거나 override하기 전까지는 최종 커버리지로 치지
않는다. 기계는 분석하고, 사람이 판단한다.

**트레이드오프.** fire-and-forget 한 번 호출 대신 두 개의 명령과 필수 사람 단계. 그 마찰이
핵심이다. 그리고 `gate`에서조차 모든 확정 finding이 차단하지는 않는다. 차단 verdict(exit `1`)는
설계를 무효화하는 세 가지 유형(`orphan_scored_rubric_item`, `optionality_mismatch`,
`mandatory_spec_bonus_only_traced`)으로 한정된다. 확정된 커버리지-갭 및 lint finding은
검토 결과이지 실격 사유가 아니다 — severity와 blocking은 인접하지만 동일하지 않다.

**확인.** Plan 변경 이력 v1.3/v1.6; plan §5.6 (gate 차단 범위); 검증 기록
[gate_initial_slice.md](verifications/2026-05-28/gate_initial_slice.md).

### A4. "Lint"는 내 코드가 아니라 채점 구조를 위한 것이었다

**걸려 있던 것.** "lint"가 처음 등장했을 때, 기본 해석은 뻔한 것이었다. *이 프로젝트의*
Python에 linter를 추가하기. 평범한 정리 작업.

**결정.** 나는 lint의 *사고방식* — "있어선 안 될 것을 탐지한다" — 을 도구가 실제로 검증하는
artifact인 과제의 채점 구조로 돌렸다. 커버리지 규칙(Rule 1–3)은 *"여기 있어야 할 모든 것이
여기 있는가?"*를 묻는다. lint 계열(Rule L\*)은 **역(inverse) 불변식**을 묻는다:
*"여기 있어선 안 될 무언가가 있는가?"* 그 재프레이밍이 Rule L 계열 전체와, 그것이 겨냥하는
구체적 고통 — 공개된 명세가 이미 요구하는 것을 창의성 채점 영역이 조용히 잠식하는 것 — 을
낳았다.

**트레이드오프.** 그 결과 프로젝트 자체의 코드 스타일 linting은 미결로 남았다(여전히
그렇다). 나는 내 소스 트리를 정돈하는 것보다 이 패턴을 제품의 가치 축에 적용하는 것이 더
중요하다고 판단했다.

**확인.** 작업 로그 2026-05-27 (ideation v2.2 초안, "lint 적용 방향 재정의");
ideation v2.2 §1 (inverse invariant).

---

## Part B — 시스템을 정직하게 유지한 방법

### B1. 조용히 거짓말하던 `validated` 라벨 → 단계화된 무결성 모델

**걸려 있던 것.** 모든 candidate run은 `integrity_status`를 갖는다. 계약은 `validated`를
*"모든 Rule 0 검사 통과; compacting 자격 있고, downstream에서 deterministic assessment
자격 있음"*으로 정의했다. `validated`는 실제 verdict를 만들어내는 시스템 부분으로 들어가는
관문이다.

**감사가 발견한 것.** 나는 AI 에이전트에게 각 slice를 독립적으로 검증시켰다. run-integrity
classifier에서 에이전트는 `trace_link`가 존재하지 않는 rubric과 spec을 가리키고 evidence
quote가 날조된 run을 찔러봤다 — 그리고 classifier는 **에러 0개**로 `validated`를 반환했다.
deep reference 및 quote 검사가 아직 보류된 상태에서, 값싼 두 검사(schema + audit-trace
attribution)만 거친 뒤 `validated`를 찍고 있었던 것이다. **손상된 데이터는 없었다 —
downstream 소비자(compacting, assessment)가 아직 존재하지 않는다.** 이것은 무언가가 그
거짓에 의존하기 전에, *계약* 차원에서 잡혔다. 잠복한 함정을 선제적으로 잡는 것이 독립
감사가 존재하는 이유 전부다.

**결정.** 나는 classifier를 조용히 패치하지 않았다 — *라벨*이 코드가 지키지 않는 약속을
하고 있었다. 대신 계약을 화해시켰다. **모델을 단계화**함으로써: 값싼 검사만 통과한 run은
이제 `structurally_validated`(실제 상태, deep correctness 주장 없음, compacting 자격
**없음**)이고, `validated`는 전체 Rule 0를 통과한 run에 예약된다.

**뒤따른 원칙.** deep 검사가 도착했을 때, failure를 버킷으로 나눠야 했다. 첫 시도는
*source-grounding* 실패를 `quote_mismatch`로 접어 넣었다 — 그러나 그 라벨은 "evidence
quote가 spec 텍스트의 substring이 아니다"를 뜻하고, grounding되지 않은 spec은 다른 실패다.
라벨이 또 거짓말을 하게 된다. 그래서 나는 실패를 세 갈래(`invalid_reference` /
`source_grounding_mismatch` / `quote_mismatch`)로 나눴다. 내가 분명히 말할 규칙 아래:

> **downstream 소비자가 그 차이로 실제로 분기하는 만큼만, 그리고 이름이 그렇지 않으면
> 오도(mislead)할 만큼만 상태를 쪼갠다. 그 이상은 아니다.**

여럿이 동시에 발생할 때는 precedence 순서가 대표 상태를 고르고, 알 수 없는 미래의 진단은
가장 보수적인 버킷으로 떨어진다.

**트레이드오프.** 더 많은 상태 + precedence 규칙 = 유지할 표면이 더 많아진다. 나는 그것을
받아들였다. **거짓말하는 라벨이 라벨 하나 더 있는 것보다 나쁘다.** 세밀한 이유는 결코
사라지지 않는다 — 모든 진단은 coarse status와 무관하게 에러 리스트에 보존된다.

**확인.** 검증 기록
[candidate_run_integrity_classifier.md](verifications/2026-05-29/candidate_run_integrity_classifier.md)
와 [deep_candidate_run_integrity.md](verifications/2026-05-29/deep_candidate_run_integrity.md);
plan §5.4; 변경 이력 v1.27 → v1.28 → v1.30.

### B2. Compacting은 union이지, 자동 병합이 아니다

**걸려 있던 것.** 여러 독립 agent run은 겹치는 candidate를 생성한다. 쉬운 수는
"통합(consolidate)"이다 — 승자를 고르고 나머지를 버린다.

**결정 (v1.4).** 나는 이 단계를 "분류된 집계"에서 **감사 가능한 compacting**으로 재정의했다.
quorum 없음, 자동 수락 없음, 자동 분류 없음. 모든 유효한 candidate는 entry로 보존된다 —
*단일 run에서만 발견된 것까지 포함해* — 그리고 같은 entity로 판단된 entry는 `support`(어느
run이 그것을 발견했나), `identity_basis`(왜 동일하다고 판단했나), `variants`(약간 다른
표현들)를 지닌다. 따라서 compacting 자체가 검토 가능하다.

**이유.** run 간의 불일치를 숨기는 것은 불확실성을 거짓 확신으로 세탁하는 일이다.
determinism은 정직하게 한정된다. 나는 오직 *"동일한 compacted artifact + 동일한
semantic-verification artifact → 동일한 finding"*만 보장하지, 한 에이전트의 두 run이 같은
candidate를 만든다고 보장하지 않는다.

**트레이드오프.** 검토자는 더 적게가 아니라 더 많이 본다 — 모든 entry가 검토까지 살아남는다.
그것이 불확실성을 숨기지 않기 위한 올바른 비용이다.

**확인.** Plan 변경 이력 v1.4; plan §5 (`support`/`identity_basis`/`variants`).

### B3. Semantic quote를 문자 그대로의 substring으로 강제하지 않는다

**걸려 있던 것.** Rule 0는 evidence quote가 spec에 grounding되었는지 검사한다. 엄격한 형태 —
정확한 substring 일치 — 는 determinism에는 좋지만, 패러프레이즈된 의미 수준의 evidence에는
틀렸다. 유효한 quote를 거부하게 된다.

**결정 (v1.5).** Evidence는 quote마다 **`verification_mode`**를 지닌다:
`token_sequence`(엄격한 substring, 완전히 deterministic) vs `ai_judgement`(reference
integrity만, 검토로 라우팅). PoC 기본값은 `ai_judgement`이고, 엄격한 검사는 진정으로
정량화 가능한 주장에 대해 **opt-in**이다. deep integrity 감사는 이후 명시적인 over-strict
guard를 추가해, `ai_judgement` quote가 문자 그대로의 substring이 아니라는 이유로는 결코
실패하지 않게 했다.

**트레이드오프.** 하나의 보편 규칙 대신 두 모드. 그러나 단일 규칙은 입력의 절반에 대해 이쪽
아니면 저쪽 방향으로 틀렸을 것이다.

**확인.** Plan 변경 이력 v1.5; deep-integrity 검증 기록(over-strict `ai_judgement` guard).

### B4. 모든 것은 불변 source snapshot에 닻을 내린다

**걸려 있던 것.** 모델의 source 기억을 신뢰하는 validator는 그 자신이 신뢰받을 수 없다.

**결정 (v1.1, v1.6).** DB 없음, RAG 없음. spec과 rubric은 `sha256`을 가진 불변 snapshot으로
freeze되고, 모든 item과 quote는 그것을 가리키는 line/span `source_ref`를 지닌다.
`--source-manifest`는 `check`의 **필수** 인자다(v1.8) — manifest 누락은 조용한 pass가
아니라 `invalid_input`이다. Fixture는 테스트에서 manifest 대비 hash를 재계산한다.

**트레이드오프.** 입력마다 더 많은 절차. 그러나 그것은 모든 주장을 원본 텍스트 대비 독립적으로
검증 가능하게 만들며, 그것이 전제 전부다.

**확인.** Plan 변경 이력 v1.1/v1.6/v1.8; `schemas/source_manifest.schema.json`.

### B5. 시끄럽게 실패하라, 규칙을 조용히 비활성화하지 마라

**걸려 있던 것.** 몇몇 입력은 선택적으로 보이지만 하중을 받는다(load-bearing). source
manifest는 모든 주장을 grounding하고, policy는 Rule 3의 threshold를 공급한다. 그것들이
없을 때 쉬운 동작은 영향받는 검사를 건너뛰고 green을 반환하는 것이다 — 그리고 그 green은
거짓이다. 규칙 하나가 통째로 사라졌기 때문이다.

**결정.** 하중을 받는 입력의 누락은 구조화된 typed 복구 action을 동반한 `invalid_input`(exit
`2`)이다 — 결코 조용한 건너뛰기가 아니다. `--source-manifest`가 필수가 되었고(v1.8),
`--policy`와 Rule 3 threshold가 필수가 되었으며(v1.20), 각각 argparse usage 텍스트 대신
`provide_source_manifest` / `provide_policy` / `fix_input`을 반환한다. 원칙:
**조용히 비활성화된 규칙이 하드 에러보다 나쁘다** — 특히 호출자가, 구조화된 피드백은
고칠 수 있지만 green 실행은 기꺼이 신뢰하는 AI 에이전트일 때.

**트레이드오프.** 호출마다 더 많은 필수 절차, 유지할 거부 경로도 더 많아진다. 그럴 가치가
있다. 그것이 제거하는 실패 모드 — "검사가 한 번도 실행되지 않았기 때문에 run이 통과했다" —
는 바로 이 도구가 *남들*에게서 잡으려고 존재하는 종류의 보이지 않는 결함이다.

**확인.** Plan 변경 이력 v1.8 / v1.20; 작업 로그 2026-05-28 (policy completeness,
"fail loudly and structurally"); 검증 기록
[policy_completeness.md](verifications/2026-05-28/policy_completeness.md).

---

## Part C — 프로세스 그 자체

### C1. AI에게 내 작업을 감사시키고 — verdict 철회를 허용했다

**걸려 있던 것.** green 테스트 스위트는 필요하지만 충분하지 않다. 코드가 테스트가 말하는
대로 작동함을 증명할 뿐, 명세가 요구하는 대로 작동함을 증명하지 않는다.

**결정.** 나는 독립 검증을 1급 산출물(`docs/verifications/`)로 삼고, 감사에 적용한 규칙을
지켰다. 모든 명세 분기 — "발생해야 함"과 "발생하면 안 됨" 둘 다 — 는 regression에 매핑되어야
하고, guard는 **양방향**으로 실패해야 하며(원래 버그가 다시 나타날 수 있고 *그리고*
over-correction이 잡힌다), 누락된 guard는 **차단(blocking)** finding이지 결코 "향후
과제"로 재포장되지 않는다. 검증이 계약 갭을 드러냈을 때, slice는 코드만이 아니라 *계약*이
화해될 때까지 닫히지 않았다.

이 규율에는 이빨이 있다. 최초의 Rule 3 verdict는 감사가 경계 검사가 불완전함을 발견한 뒤
**철회**되고 재발행되었다. 거짓말하는 green bar를 내보내느니 철회된 verdict를 기록하는 쪽을
택하겠다.

**트레이드오프.** 더 느리다. 모든 slice가 감사 비용을 진다. 그 일 전체가 *신뢰할 수 있는
검증*인 도구에게, 빠르게 그리고 틀리게 내보내는 것은 목적을 무너뜨린다.

**확인.** `docs/verifications/` 아래의 검증 기록, 예:
[rule_3_boundary_tightening.md](verifications/2026-05-27/rule_3_boundary_tightening.md)
(철회된 최초 verdict를 대체); 검증 규칙은 `CLAUDE.md` / `AGENTS.md`에 있다.

### C2. 계획서가 단일 진실 공급원이다 — handoff는 결코 그림자 명세가 아니다

**걸려 있던 것.** AI 에이전트와 작은 slice로 작업할 때, rule-semantics 결정을 `HANDOFF.md`에
기록하고 넘어가는 것은 빠르다. 그러나 일단 두 작업자가 서로 다른 문서를 권위 있는 것으로
읽으면, 명세는 조용히 갈라진(fork) 것이다.

**결정.** Rule semantics는 **한 곳**에서 바뀐다: 정본 구현 계획서. `HANDOFF.md`는 결정이
사는 곳을 *가리키는* 큐레이션된 인덱스에 운영 노트를 더한 것이지, 결코 계약의 1차 저장소가
아니다. 내가 추출해 이제 선제적으로 적용하는 규칙: **어떤 해결이 다른 작업자가 구현하는
것을 바꾼다면, 그것은 handoff가 아니라 같은 slice에서 계획서 본문에 들어간다.** 나는 한 번
이를 어기는 나 자신을 잡았다 — Rule 1 경계가 HANDOFF에만 기록되고 계획서는 뒤처진 채로 —
그리고 그것을 계획서로 다시 들어 올리는 데 전용 slice(v1.8 → v1.9)를 썼다. 나는 또한 lint
계열 전체를, handoff가 사실상의(de-facto) 명세로 굳어지지 않도록 promote될 때까지 *ideation*
문서에 두었다.

**트레이드오프.** 모든 계약 변경은 작은 것조차 계획서 편집 비용을 진다 — 빠른 handoff 노트보다
느리다. 그러나 그것이 막는 실패(두 문서, 두 진실, 조용한 fork)는 다중 작업자 프로젝트에서
가장 비싼 종류의 drift다.

**확인.** 작업 로그 2026-05-26 (slice 2.5, "Plan is the only mechanism for changing rule
semantics"); `CLAUDE.md` / `AGENTS.md` §5의 문서 규율 규칙.
