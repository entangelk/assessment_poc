<p align="center">
  <a href="./audit_index.md"><img src="https://img.shields.io/badge/Language-EN-6B7280?style=for-the-badge" alt="English"></a>
  <a href="./audit_index.ko.md"><img src="https://img.shields.io/badge/Language-KO-111111?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# 감사 인덱스 — 작업 로그 & 독립 검증

프로젝트의 당대 기록에 대한 큐레이션된 안내이지, raw 덤프가 아니다. 코드와 나란히 두 개의
기록이 흐른다.

- **작업 로그** (`docs/daily_logs/`) — 매일 무엇을 만들었고, 왜, 그리고 어떤 결정을
  내렸는지를, 작업이 일어난 그대로 기록.
- **독립 검증 기록** (`docs/verifications/`) — 구현된 각 slice는 (엄격하고 차단하는 규율을
  지키는 AI 에이전트에 의해) 독립적으로 감사받았다. 이것들은 1급 자산이다. 작업이 단지
  green 테스트 bar가 아니라 명세 대비 검증되었음을 보여준다. 이 규율이 존재하는 이유는
  결정 [C1](decisions.ko.md)을 참조.

결정 서사 자체는 [decisions.md](decisions.ko.md)에 있고, 측정된 테스트/smoke 증거는
[evaluation.md](evaluation.md)에 있다.

## 작업 로그 (날짜별)

| 날짜 | 초점 |
|---|---|
| [2026-05-25](daily_logs/2026-05-25/work_log.md) | Ideation 리뷰; plan v1.0→v1.7 (agent-harness 전환, compacting, gate, source grounding); Phase 0 스캐폴드 + Rule 0 + audit-blocker 수리 |
| [2026-05-26](daily_logs/2026-05-26/work_log.md) | Rule 1 slice 1/2/3 (orphan scored / unconfirmed coverage / orphan bonus); slice-2.5 plan 화해; CLI envelope 계약 lock |
| [2026-05-27](daily_logs/2026-05-27/work_log.md) | Ideation v2.2 lint 계열 (초안→최종→개정); lint Rule L1/L5/L6; Rule 2 + Rule 3 |
| [2026-05-28](daily_logs/2026-05-28/work_log.md) | 초기 `gate` + `review` draft writer + safety guard; policy completeness; Phase 2 스키마 기반; AgentRunner 프로토콜; audit-trace 스키마 |
| [2026-05-29](daily_logs/2026-05-29/work_log.md) | Candidate 스키마 / attribution / normalization; 단계화된 candidate 무결성; deep candidate Rule 0 (3-way 격리); 검증 기록 레이아웃 |
| [2026-05-31](daily_logs/2026-05-31/work_log.md) | 공개 작업: 결정 수확 + 큐레이션; 케이스 스터디; evaluation; LICENSE + secret scan + audit index |

## 독립 검증 기록 (주제별)

주목할 것 먼저 — 화해나 수정 사연을 담은 기록들:

- [rule_3_boundary_tightening](verifications/2026-05-27/rule_3_boundary_tightening.md)
  — 감사가 불완전한 경계 검사를 발견한 뒤 **철회되고 재발행된 verdict**(최초 Rule 3 pass를
  대체). 규율에 이빨이 있다는 가장 분명한 예.
- [gate_initial_slice](verifications/2026-05-28/gate_initial_slice.md)
  — **조건부 합격**: 코드는 named regression이 없던 분기에서 올바르게 동작했지만, 비어 있는
  boundary-matrix 칸들은 lock될 때까지 차단으로 취급되었고, 이후 합격으로 재검증되었다.
- [candidate_run_integrity_classifier](verifications/2026-05-29/candidate_run_integrity_classifier.md)
  + [deep_candidate_run_integrity](verifications/2026-05-29/deep_candidate_run_integrity.md)
  — **`validated` 라벨이 코드가 전달하는 것보다 더 많이 약속**한 것을 잡은 감사
  (결정 [B1](decisions.ko.md)).

전체 목록, 날짜별:

**2026-05-27** — [rule_2_implementation](verifications/2026-05-27/rule_2_implementation.md) ·
[rule_3_implementation](verifications/2026-05-27/rule_3_implementation.md) ·
[rule_3_boundary_tightening](verifications/2026-05-27/rule_3_boundary_tightening.md)

**2026-05-28** — [gate_initial_slice](verifications/2026-05-28/gate_initial_slice.md) ·
[review_draft_writer](verifications/2026-05-28/review_draft_writer.md) ·
[review_safety_guards](verifications/2026-05-28/review_safety_guards.md) ·
[policy_completeness](verifications/2026-05-28/policy_completeness.md) ·
[agent_runner_protocol_foundation](verifications/2026-05-28/agent_runner_protocol_foundation.md) ·
[audit_trace_schema](verifications/2026-05-28/audit_trace_schema.md) ·
[phase_two_schema_foundation](verifications/2026-05-28/phase_two_schema_foundation.md)

**2026-05-29** — [candidate_schema_foundation](verifications/2026-05-29/candidate_schema_foundation.md) ·
[candidate_audit_trace_attribution](verifications/2026-05-29/candidate_audit_trace_attribution.md) ·
[runner_candidate_normalization](verifications/2026-05-29/runner_candidate_normalization.md) ·
[candidate_run_integrity_classifier](verifications/2026-05-29/candidate_run_integrity_classifier.md) ·
[deep_candidate_run_integrity](verifications/2026-05-29/deep_candidate_run_integrity.md)
