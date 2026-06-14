# Pulse 샘플 — 작성 노트 (사람용)

Assessment Spec Harness PoC를 **완전히 다른 방향의 과제**에서도 검증하기 위해
만든 세 번째 합성 샘플이다. 실제 회사/지원자 데이터는 없다.

## 왜 이 샘플인가 (기존 둘과의 차이)

| 샘플 | 언어 | 아키타입 |
|---|---|---|
| inventory (간단) | Python | 맨바닥 CLI 빌드, 단일 산출물 |
| deskhive | Python/FastAPI | 인수인계 디버깅 (버그 찾기) |
| **pulse (이 샘플)** | **Go** | **그린필드 빌드 + 설계 판단** |

언어(Go)와 과제 형태(디버깅이 아니라 맨바닥 설계·구현)를 동시에 바꿔서, 하네스가
기술/언어/과제 종류와 무관하게 **평가 설계만** 검토한다는 점을 보이려는 의도다.
하네스 입력은 여전히 spec.md + rubric.md 둘뿐이다.

## 의도적으로 심은 spec↔rubric 신호 (DeskHive와 다른 조합)

| 위치 | 의도한 finding |
|---|---|
| R4 | `possible_orphan_scored_rubric_item` — 인용문("reject/exit nonzero")이 spec("skip-and-continue, must not crash")과 모순이라 verbatim 부재 |
| R5 | `optionality_mismatch` — spec은 "may"(선택)인 윈도잉을 15점 배점 |
| RB1 | `orphan_bonus_rubric_item` (**informational**) — spec에 없는 Prometheus 출력을 보너스로 평가 |
| Q1 → S8 | `uncovered_must_spec_item` — "must not crash"를 **정성(qualitative) 노트만** 추적, scored 미커버 |
| RB2 | **무발화** — "may emit JSON"을 올바르게 추적하는 보너스 (과발화 안 함 시연) |
| R1~R3, R5~R7 | Phase 0 의미검증 전이라 `unconfirmed_trace_coverage` |

DeskHive에 없던 분기(`orphan_bonus` informational, qualitative-only
`uncovered_must`)를 일부러 넣어 룰 커버리지를 넓혔다. 가이드라인의 "함정 퍼즐
금지"에 맞춰 현실적인 수준만 심었다.

## 형식 제약 (deterministic_extraction 러너)

- rubric 헤더는 `## R1. 제목 (15 points)` 형식이어야 파싱된다.
- 각 채점 항목의 `Traceable spec quote: "..."` 가 spec.md에 그대로 등장해야
  trace link가 생성된다 (공백만 정규화됨; 마침표/쉼표 차이도 매칭을 깨뜨린다 —
  RB2 인용문은 spec 문장을 분리해 정확히 맞췄다).
- 러너 리터럴이 영문이라 spec/rubric은 영문, 한국어 맥락은 이 파일에만 둔다.

## 코드베이스(`codebase/`)와의 관계

`codebase/`는 spec/rubric이 묘사하는 과제의 **reference solution**(정답 예시)을
실제 동작하는 Go 모듈로 구현한 것이다. DeskHive(버그를 심은 코드)와 달리 이건
**올바르게 동작하는 빌드**라, 리뷰어가 "이 과제가 실제로 빌드 가능하고 rubric으로
채점 가능한가"를 확인할 수 있다.

- 하네스는 `codebase/`를 **소비하지 않는다.** 입력은 spec.md + rubric.md뿐.
- **주의:** 이 Go 코드는 작성·검토했지만, 이 샘플을 만든 환경에는 Go 툴체인이
  없어 `go test`/`go run`을 **직접 실행하지는 못했다.** 하네스 신호는 실제로
  하네스를 돌려 검증했고, Go 코드는 테스트와 기대 출력(`testdata/expected.json`)을
  동봉해 Go가 있는 리뷰어가 실행 검증할 수 있게 했다.
- RB1(Prometheus)이 spec에 없다는 점은 reference solution이 Prometheus를 구현하지
  않는 것과 자연스럽게 맞물린다(= orphan_bonus 신호의 실제 근거).
