# DeskHive 샘플 — 작성 노트 (사람용)

이 샘플은 Assessment Spec Harness PoC를 **복잡한 과제 형식**에서도 검증하기 위해
만든 합성(synthetic) 과제다. 실제 회사/지원자 데이터는 전혀 포함하지 않는다.

## 복잡도 의도

기존 간단 샘플(단일 CLI 도구, 평탄한 요구사항 8개)과 달리, 실제 인수인계형
디버깅 과제처럼 구성했다:

- 다단계(Phase 0~4): 환경 / 결함 진단·수정 / 검증 설계 / 선택 개선 / 보고서
- 구체적 결함 5개(B1~B5)와 증상·확인 위치 표
- 필수/선택/가산점 산출물 혼재 + 정성 평가
- 여러 산출물(코드 / diagnosis_log / verification_design / tests / report)

## 의도적으로 심은 spec↔rubric 신호 (하네스 룰 발화용)

| 위치 | 의도한 finding |
|---|---|
| R5 (호스트 추천) | `possible_orphan_scored_rubric_item` — rubric 인용문이 spec에 verbatim으로 없음 (paraphrase) |
| R8 (대시보드 패널) | `optionality_mismatch` — spec은 "may"(선택)인데 rubric은 10점 배점 |
| RB1 (AI 로그 가산점) | `uncovered_must_spec_item` + `mandatory_spec_bonus_only_traced` + `bonus_grades_mandatory_only` — "must"인 AI 로그 제출을 scored가 아닌 bonus로만 평가 |
| R7 + RB2 (보고서) | `double_scored_spec` — 같은 spec(CTO 보고서)을 scored와 bonus가 동시에 채점 |
| R1~R4, R6, R7, R8 | Phase 0에서 의미 검증 전이라 `unconfirmed_trace_coverage` |

가이드라인(`docs/guidelines/sample_assignment_guidelines.md`)의 "함정 퍼즐을
만들지 말 것" 원칙에 맞춰, 핵심 신호 위주로 현실적인 수준만 심었다.

## 형식 제약 (deterministic_extraction 러너)

- rubric 헤더는 `## R1. 제목 (12 points)` 형식이어야 파싱된다.
- 각 채점 항목의 `Traceable spec quote: "..."` 가 spec.md에 그대로 등장해야
  trace link가 생성된다 (공백만 정규화됨, 백틱 등은 그대로 매칭).
- 러너 리터럴(`Traceable spec quote:`, `(N points)`, `Bonus`, `Qualitative`)이
  영문이라 spec/rubric 본문도 영문으로 작성했다. 한국어 맥락은 이 파일에만 둔다.
