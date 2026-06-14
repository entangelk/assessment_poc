<p align="center">
  <a href="./HANDOFF.md"><img src="https://img.shields.io/badge/Language-EN-6B7280?style=for-the-badge" alt="English"></a>
  <a href="./HANDOFF.ko.md"><img src="https://img.shields.io/badge/Language-KO-111111?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Handoff

## 현재 상태

- 구현 계획은 v1.32(`docs/planning/implementation_plan_assessment_harness_poc_v1.md`)이며, `docs/planning/ideation_assessment_harness_v2.2.ko.md`(2026-05-27 제자리 개정, v2.1 대체)보다 우선하는 정식 구현 진실의 원천(source of truth)이다.
- 공개 미러 상태(2026-06-14): 구현 계획은 `docs/planning/implementation_plan_assessment_harness_poc_v1.ko.md` KO-active 미러를 갖고 있으며, 본문은 현재 한국어 원본과 일치한다. 1,825줄 구현 계획의 전체 영어 정본 재작성은 아직 pending이다. README 링크는 이 번역이 완료될 때까지 한국어 원본 anchor를 가리킨다.
- **Rule 0 가동 중**: 소스 스냅샷 그라운딩, 증거 완전성/참조 무결성 검사, 필수 `--source-manifest`, 구조화된 잘못된 입력 복구가 구현되었다.
- **Rule 1 기능 완성**(plan v1.19 §6): `possible_orphan_scored_rubric_item`, `unconfirmed_trace_coverage`, `orphan_bonus_rubric_item`이 모두 구현되었다. CLI는 이들의 검토 액션과 잠정 심각도 카운트를 노출하며, slice 3.1은 보너스 전용 `(high=0, medium=0, informational=1)` 경계를 포함해 공개 envelope/schema 계약을 고정한다.
- **Rule 2 구현 완료**(plan v1.19 §6): 어떤 `scored` 루브릭도 `must` 스펙을 추적하지 않을 때 `uncovered_must_spec_item`이 medium/provisional로 발행되며, `review_uncovered_must_spec`이 `check`를 통해 노출된다. 이는 구조적 검사일 뿐이다: pending 상태의 scored 추적은 커버로 인정되지만, 보너스 전용 또는 정성(qualitative) 전용 추적은 인정되지 않는다.
- **Rule 3 구현 완료**(plan v1.20 §6): scored 루브릭이 `rules.optionality_mismatch.weight_threshold` 이상에서 optional 스펙만 추적할 때 `optionality_mismatch`가 high/provisional로 발행되며, `review_optionality_mismatch`를 노출한다. 이는 구조적 검사일 뿐이다: 의미(semantic) 상태는 참조하지 않으며, Phase 0 `check`는 이제 누락/불완전한 정책을 Rule 3를 조용히 억제하는 대신 거부한다.
- **Rule L1 구현 완료**(plan v1.19 §6): 동일 스펙이 scored 루브릭과 bonus 루브릭에 의해 함께 추적될 때 `double_scored_spec`이 medium/provisional로 발행된다. 이 finding은 짝지어진 루브릭 컨텍스트를 포함하며, `check`는 새 `review_queue` 계약을 통해 짝지어진 `double_scoring_review` 항목을 기록한다.
- **Rule L5 구현 완료**(plan v1.19 §6): 추적된 bonus 루브릭의 대상이 모두 `must`인 경우 `bonus_grades_mandatory_only`가 medium/provisional로 발행되며, `review_bonus_mandatory_only`를 노출하고 큐 항목은 추가하지 않는다.
- **Rule L6 구현 완료**(plan v1.19 §6): `must` 스펙이 bonus 루브릭에 의해서만 추적될 때 `mandatory_spec_bonus_only_traced`가 high/provisional로 발행되며, `bonus_rubric_ids[]`, `review_mandatory_spec_bonus_only`, 짝지어진 `mandatory_spec_bonus_review` 큐 항목을 노출한다.
- **초기 `gate` 가동 중**(plan v1.19 §5.6): 최종 검토 기록은 최소 생성 키를 사용한 `target_type: finding`을 통해 잠정 finding을 종결할 수 있다. `gate`는 누락/보류/재실행 결정에 대해 `pending_review`를 반환하고, 확정된 차단(blocking) finding에 대해 `fail`/종료 코드 `1`을, 모든 finding이 차단 없이 종결되면 `success`를 반환한다. v1.17 후속 작업은 독립 검증에서 도출된 조건부 통과 경계 매트릭스를 고정한다.
- **초기 `review` 초안 작성기 가동 중**(plan v1.19 §5.6): `review --findings ... --out-dir ... --reviewer ...`는 finding마다 최소 키 `hold` 결정 하나를 담은 `review.yaml`을 작성한다. `findings.status=success` 또는 `provisional_findings`만 수용하며, `--force`를 전달하지 않는 한 기존 초안을 덮어쓰지 않고, 산출물을 자동 수락하거나 재작성하지 않는다. 사람이 최종 `gate` 이전에 초안을 편집한다.
- **AgentRunner 프로토콜 기반 가동 중**(plan v1.22 §7 / §9): `agent_runners/base.py`는 프레임워크 중립적인 `AgentRunner` 프로토콜과 `AgentRunResult`를 정의하며, `agent_runners/mock.py`는 프로토콜 계약 테스트 전용으로만 fixture YAML을 결정론적으로 재생한다.
- **후보 산출물 스키마 기반 가동 중**(plan v1.24 §5.4): `candidates.schema.json`은 컴팩팅이나 러너 복구 정책을 선택하기 전에 `candidate_id`, `agent_runner`, `agent_run_id`, `integrity_status`를 갖춘 런 수준의 spec/rubric/trace 후보 배열을 검증한다.
- **후보 audit-trace 귀속 헬퍼 가동 중**(plan v1.25 §10.2): `validate_candidate_audit_trace`는 후보/audit trace 스키마를 검증하고 모든 후보 `agent_run_id`가 audit trace `run_id` 안에 나타나는지 확인하며, `extract`, 컴팩팅, 러너 실패 복구는 구현하지 않는다.
- **러너 산출물 정규화 헬퍼 가동 중**(plan v1.26 §10.2): `normalize_result_candidates`는 fixture 형태의 `AgentRunResult.artifacts`를 후보 산출물로 변환하고, 러너/런 출처를 부착하며, 후보를 `pending_check`로 시작시키고, 검증 전에 컴팩팅 전용 필드를 제거한다.
- **후보 무결성 단계 모델 가동 중**(plan v1.28 §5.4 / §10.2): `classify_candidate_run_integrity`는 이제 구조적으로 깨끗한 런을 `structurally_validated`로, 후보/audit 스키마 오류를 `schema_violation`으로, audit trace 런 귀속 누락을 `trace_attribution_error`로 표시한다. `validated`는 이후 심층 후보 Rule 0 성공을 위해 예약되어 있으며, 여전히 유일한 컴팩팅 적격 상태로 남는다.
- **심층 후보 Rule 0 헬퍼 가동 중**(plan v1.30 §5.4 / §10.2): `classify_deep_candidate_run_integrity`는 구조 검증 이후 정규화된 후보 `proposed_item`에 Rule 0 엔진을 재사용한다. 깨끗한 런은 `validated`로 승격되고, 후보 내부 참조/완전성 실패는 `invalid_reference`로 격리되며, 소스 문서/해시/source_ref/스냅샷 스팬 실패는 `source_grounding_mismatch`로, 토큰 시퀀스 증거 인용 부분문자열 실패는 `quote_mismatch`로 격리된다. 진단이 혼합된 런은 `invalid_reference > source_grounding_mismatch > quote_mismatch` 우선순위를 사용한다.
- **컴팩팅 스키마/헬퍼 기반 가동 중**(plan v1.30 §5.0 / §9): `compacting.schema.json`과 `compact_validated_candidates`는 완전히 `validated`된 런만 컴팩팅하고, 합집합 기반 `support` / `identity_basis` / `variants`를 보존하며, 정식 `id_map`을 작성하고, trace-link 루브릭/스펙 참조를 정식 item ID로 재매핑한다. 상태가 혼합된 런은 단위 전체로 제외된다; `support.total_valid_runs`는 일치하는 후보를 포함하는 런만이 아니라 완전히 검증된 모든 입력 런을 센다. trace-link 재매핑 실패는 후보를 조용히 누락시키는 대신 `CompactingInputError`를 발생시킨다.
- **`mock_fixture` 전용 초기 `extract` CLI 오케스트레이션 가동 중**(plan v1.32 §8 / §9 / §10.2): `extract --runner mock_fixture --fixture-dir ... --runs N --out-dir ...`는 프레임워크 중립 러너 프로토콜을 통해 fixture 산출물을 재생하고, 후보를 정규화하며, 심층 후보 Rule 0을 실행하고, 격리된 `run_###/candidates.yaml`, `agent_trace.audit.jsonl`, `agent_trace.raw.jsonl`을 작성한다. `--source-manifest`가 생략되면 `extract`는 이제 `--out-dir` 옆에 형제 `source_snapshot/manifest.yaml`을 생성한다; 명시적 `--source-manifest`는 여전히 우선한다. 잘못된 런은 런 로컬 스키마 유효 `integrity_diagnostics.json`과 함께 격리된다. 계획상 런 카운트 경계(`1..7`)를 강제하며 `compact --runs-dir`로 공급한다. 두 번째 러너 `--runner deterministic_extraction`은 **오프라인 실행 대역(stand-in)**으로 가동 중이다: 샘플 `spec.md`/`rubric.md`에서 직접 그라운딩이 올바른 후보를 도출해(fixture 없음, LLM 없음, 네트워크 없음) 실제 샘플에서 전체 워크플로를 실행할 수 있게 한다. 이는 실제 라이브 에이전트 추출이 아니다; 자리표시 결정은 `docs/guidelines/sdk_runner_minimal_slice_plan.md`에 기록되어 있다. 실제 LLM 기반 SDK 러너는 자격증명/SDK 경로가 준비될 때까지 보류 상태로 남는다.
- **초기 읽기 전용 프레임워크 도구 가동 중**(plan v1.32 §4 / §9 / §13): `tools.spec_tools`는 Markdown 소스 섹션에 대해 `list_sections`와 `read_spec_section`을 제공하고, `tools.rubric_tools`는 스키마 검증된 컴팩팅 루브릭 YAML에 대해 `list_rubric_items`와 `get_rubric_item`을 제공한다. 소유자 결정(2026-06-07): 프레임워크 도구는 읽기 전용으로 유지한다; 제안/쓰기 동작은 직접 파일 쓰기가 아니라 런 종료 시 러너가 수집해 후보 산출물로 발행해야 한다.
- **초기 `compact` CLI 오케스트레이션 가동 중**(plan v1.30 §5.0 / §8 / §9): `compact --runs-dir ... --policy ... --out-dir ...`는 `candidates.yaml`을 포함하는 계획상 정식 런 디렉터리를 읽는다; `--candidates ...`는 저수준의 명시적 파일 입력으로 여전히 사용 가능하다. 정식 `spec_items.yaml` / `rubric_items.yaml` / `trace_links.yaml` / 래퍼 형태 `id_map.yaml`, 그리고 `review_queue.json`을 작성한다. `--review-queue-in`의 기존 큐 최상위 메타데이터와 항목을 보존하고, 제외된 비검증/혼합 런에 대해 중복되지 않는 `invalid_run` 항목을 추가하며, 동시 `--runs-dir` + `--candidates`는 거부한다.
- **`mock_fixture` 전용 초기 `verify` CLI 오케스트레이션 가동 중**(plan v1.30 §5.3.1 / §5.7 / §8): `verify --compacted-dir ... --source-manifest ... --runner mock_fixture --runs N --policy ... --out-dir ...`는 컴팩팅 산출물을 읽고, 수신 검토 큐 메타데이터/항목을 보존하며, 스키마 유효 `semantic_verifications.yaml`을 작성하고, `verification_mode: ai_judgement` 증거에 대해 중복되지 않는 `ai_judgement_pending` 검토 큐 항목을 추가한다. `id_map.yaml`이 존재하면 `verify`는 trace 파일 순서가 아니라 trace-link 정식 계보에서 `trace_link_id`를 해석한다. mock 검증기는 `agent_uncertain` 제안만 기록하며, 인용 수준 `source_ref`가 없으면 `source_refs: []`를 포함한다; 컴팩팅된 trace link를 재작성하거나 최종 의미 수락 주장을 하지 않는다.
- **초기 의미 검증 소비 가동 중**(plan v1.30 §5.3.1 / §8): `check --semantic-verifications ... --id-map ...`은 컴팩팅된 trace link를 재작성하지 않고 검증기 제안을 Rule 1 증거의 메모리 내 유효 `semantic_status`로 적용한다. 컴팩팅 계보(`variants`)를 가진 trace link의 경우 `check`는 `--id-map`을 요구하고 `verify`와 동일한 trace-link 계보 해석기를 사용한다; 검토 후 상태(`human_accepted`, `human_rejected`, `human_overridden`, `rerun_requested`)는 에이전트 제안에 의해 덮어쓰이지 않는다. `report --semantic-verifications ... --review-queue ...`는 이 산출물을 검증하고 기본적으로 Markdown으로, 또는 `--format html`로 독립 실행형 브라우저 표시용 HTML 보고서로 렌더링한다; 선택적 `report --policy ...`는 구성된 Rule 3 임계값을 보고서의 룰 카탈로그에 추가한다. `review --semantic-verifications ... --review-queue ...`는 최종 검토 초안에 경로를 기록하기 전에 이들을 검증한다.
- **초기 review_queue 최종 검토 처리 가동 중**(plan v1.30 §5.6 / §5.7): `review --review-queue ...`는 최소 `{entry_id}` 키를 사용해 미해결 큐 항목에 대한 `target_type: review_queue_entry` 결정 초안을 작성한다. `gate`는 `inputs.review_queue_path`를 로드하고, 누락/보류/재실행 큐 결정을 `pending_review`로 취급하며, 수락/재정의된 큐 항목이 차단 finding을 만들지 않고 종결되도록 허용한다.
- **초기 `materialize-review` 가동 중**(plan v1.31 §5.6.1 / §8): `materialize-review --final-review ... --compacted-dir ... --out-dir ...`은 검토된 산출물을 새 출력 디렉터리에 작성하고, 컴팩팅 입력을 절대 변형하지 않으며, `id_map.yaml`을 사용해 `target_key: {trace_link_id}`로 trace-link 결정을 구체화하고, review_queue 항목 상태를 구체화하며, finding 결정은 무시하고, spec/rubric 결정은 보존하되 `unsupported_decision_count`로 집계하며, 생성된 `materialization_summary.json`을 `materialization_summary.schema.json`에 대해 검증한다. `gate`는 여전히 판정 전용으로 남는다.
- **샘플에서 전체 워크플로 실행됨(2026-06-07)**: `/workspace/assessment_spec_harness_sample` 아래 샘플이 `deterministic_extraction`을 통해 종단 간 실행되었다(산출물은 `work/sample_run/` 아래): `extract` `valid_run_count=1` → `compact` → `verify` → `check` `provisional_findings`(7 findings, `blocking_count=0`) → `report` → `review` → `gate` `pending_review` → `materialize-review`. 이는 실제 샘플에서의 배선/그라운딩 증명이며, 라이브 LLM 추출이 아니다.
- **PoC 예제 보고서 최신(2026-06-14)**: [`report.md`](report.md)는 두 in-repo 예제(`examples/deskhive_assignment`, `examples/pulse_assignment`)에 대해 반복된 세 차례의 종단 간 harness 런을 요약하며, `deterministic_extraction --runs 3`과 mock 의미 검증을 사용한다. 결과는 세 차례 반복 모두에서 안정적이었다: DeskHive `provisional_findings` high=3 / medium=11 / info=0(14 findings), Pulse high=2 / medium=7 / info=1(10 findings), 두 경우 모두 Rule 0 진단=0, 그리고 안전 보류 초안에 대해 예상대로 `gate`는 `pending_review`로 유지되었다. 이는 여전히 오프라인 결정론적 워크플로 증명이며, 라이브 SDK 러너 검증이 아니다.
- **구현 보류 중**: 실제 LLM 기반 SDK 러너(오프라인 `deterministic_extraction`이 대역으로 가동 중), 러너 수집 제안 동작, 그리고 이후 Phase 2/3 러너 워크플로. SDK 러너 결정은 `docs/guidelines/sdk_runner_decisions.md`에서 추적되며, 실행 우선 최소 슬라이스는 `docs/guidelines/sdk_runner_minimal_slice_plan.md`에 있다.
- **샘플 과제 가이드 가동 중**: `docs/guidelines/sample_assignment_guidelines.md`는 AI 에이전트에게 PoC 실행을 위한 작은 합성/로컬 `spec.md` + `rubric.md` 쌍을 만드는 방법을 알려준다. 소유자 결정(2026-06-07): 권한/익명화/공개 검토는 공개 동결까지 보류되며 첫 PoC 샘플을 막지 않는다.
- 패키지 표면: `check` / `extract` / `compact` / `verify` / `schema` / `report` / `review` / `gate` / `materialize-review` 하위명령, 열여섯 개의 JSON Schema, 그리고 완전히 그라운딩된 여섯 개의 fixture(`clean_assignment`, `reference_integrity`, `orphan_scored_rubric`, `bonus_misuse`, `uncovered_must_spec`, `optionality_mismatch`). Docker가 정식 개발 환경이다.
- 이 PoC는 **에이전트 수준 harness**이다: 1급 호출자는 사람이 아니라 AI 에이전트(Claude Code / Codex / Gemini)이다. 사람은 최종 검토자로서만 참여한다.
- 최종 워크플로는 `extract --runs N -> compact -> verify --runs N -> check -> report -> review -> gate -> materialize-review`이다. 컴팩팅은 **합집합 기반 audit 작업**이다: 모든 유효 후보가 `support` / `identity_basis` / `variants`와 함께 보존되며; 검토된 산출물은 `gate`가 아니라 구체화(materialization)에 의해 생성된다.

## 공개 / 포트폴리오 작업 (진행 중, 2026-05-29)

이 프로젝트는 포트폴리오 작품으로서 공개 릴리스를 준비 중이다.

- **정식 계획:** [`docs/planning/publication_plan_v1.md`](docs/planning/publication_plan_v1.md)(v1.2) — 작업 전체를 관장한다; 그 인벤토리 + Open Decisions의 완료 = 공개 시점. 가장 먼저 읽을 것.
- **프레이밍(소유자):** *코드보다 결정과 과정*을 전면에 둘 것; 과장 금지; 사실당 단일 진실의 원천(중복하지 말고 링크할 것); AI 협업을 정직하게 보여줄 것. 언어 전환 헤더를 갖춘 EN 기본 + KO 미러.
- **완료 및 커밋됨:** 공개 계획(v1.0→v1.2); `README.md`의 **Step 0 진실 점검 통과**(plan ref v1.28→v1.30, 선형 Phase 표 → 영역 기반 상태; 이후 초기 `extract`/`compact`/`verify` CLI 슬라이스가 도착하면서 구현 상태가 갱신되었으며, 실제 SDK 러너는 여전히 미구현으로 남아 있다).
- **공개 문서 초안 작성됨, 동결 안 됨:** [`docs/decisions.md`](docs/decisions.md), [`docs/case_study.md`](docs/case_study.md), [`docs/evaluation.md`](docs/evaluation.md), [`docs/audit_index.md`](docs/audit_index.md), 그리고 현재의 한국어 [`README.md`](README.md)는 공개 초안이지만 개발은 아직 진행 중이다. 소유자 결정(2026-06-01): 모든 이중 언어 미러는 프로젝트와 공개 카피가 동결된 이후에만 수행한다; `docs/daily_logs/2026-06-01/work_log.md`를 공개 문서 기준선으로 사용하고 그 로그 이후의 변경을 검토한 뒤 미러링한다. **부분 예외(소유자, 2026-06-08):** 변동성이 낮은 세 쇼케이스 문서는 일찍 미러링되었다 — `docs/case_study.ko.md`, `docs/decisions.ko.md`, `docs/audit_index.ko.md`가 이제 완전한 패리티로 존재한다. §6.5 동결 패스까지 여전히 보류된 것: `evaluation.ko.md`(수치가 계속 변함), `HANDOFF.ko.md`, `publication_plan_v1.ko.md`, README EN/KO 전환, 전체 EN 구현 계획 미러, 그리고 그 대상이 존재하게 된 후 세 신규 `.ko` 파일 내부의 KO→KO 교차 링크(`evaluation.md`, `../README.md`) 재작성.
- **결정 기록 초안:** `docs/decisions.md`는 11개 비네트로 정리되어 있다(2026-05-31, 소유자가 "중간" 깊이 선택): A1 사용자로서의 에이전트, A2 거부된 L3/L8/L9 범위 경계, A3 check-vs-gate(이제 gate 차단 범위 논점도 흡수), A4 린트 사고방식 전환(역불변), B1 `validated`→단계화→3-way, B2 합집합 컴팩팅, B3 verification_mode, B4 소스 스냅샷 그라운딩, B5 fail-loud/조용한 비활성화 금지, C1 검증 규율 + 철회된 Rule 3 판정, C2 plan-is-SoT/HANDOFF-not-spec. **정리 중 제외됨**(git/work_log로 복구 가능): A5 gate-범위(A3로 통합), A6 임계값에 대한 무의견, B6 review는 절대 자동 수락하지 않음, B7 결정 기록 키 최소주의, B8 raw/audit-trace 분리. **목소리 고정됨:** 1인칭("나는 결정했다"), AI 협업 명시, 정직성 부연(예: "라이브 사고 없음 — 계약 수준에서 포착됨"). 그 목소리를 유지할 것.

### 다음 작업: publication_plan Step 1 (이중 언어 스캐폴드) / Step 2 (사례 연구)

4개 섹션 결정 수확과 정리는 **완료**되었다. `decisions.md`에는 11개 비네트 초안이 있지만, Phase 2 개발이 계속되는 동안 공개 동결 상태는 아니다. 다음:

- **Step 1 — 이중 언어 스캐폴드(부분, 2026-05-31):**
  - **완료:** Mermaid 아키텍처 다이어그램을 `README.md`에 삽입(흐름 개요 아래 ASCII 흐름을 대체; 구현된 것과 기반 전용인 것을 정직하게 표시). 영어 문서 `HANDOFF.md` / `AGENTS.md` / `CLAUDE.md`에 언어 전환 헤더 추가(`decisions.md`는 이미 가지고 있었음).
  - **소유자 확인(2026-05-31):** **영어가 정식(`*.md`)이고, 한국어가 미러(`*.ko.md`)이며, 둘은 완전 패리티**이다 — 어느 버전도 다른 쪽보다 더 상세하게 작성되지 않는다(publication_plan §1.5 + §6 이중 언어 패리티 게이트). 대상 시장이 국내 중심임에도 이 원칙은 유지된다. 마무리(§6.5)에서 현재의 한국어 `README.md` 내용은 `README.ko.md`로 이동하고 새 영어 `README.md`가 작성된다. 따라서 README 언어 전환 헤더는 그 전환까지 보류된다(오늘의 한국어 `README.md`에 "EN" 배지를 다는 것은 거짓일 것이다); 다른 모든 문서는 이미 그것을 달고 있다.
  - **생성 보류:** `case_study.md` / `evaluation.md`는 작성될 때(Step 2/3) 헤더를 받는다.
- **Step 2 — 사례 연구(초안 2026-05-31):** `docs/case_study.md`를 영어(정식)로, 언어 전환 헤더와 함께 작성. 서사 구조 — 문제 / 목표 / 정리된 5개 핵심 결정(A1, A2+A4, A3, B1, C1, 각각 `decisions.md`로 링크) / 내가 만든 것(현재) / 검증 방식 / 한계 / 다음. 링크는 프래그먼트를 사용하지 않는다(견고함). `.ko` 미러는 최종 공개 동결까지 보류.
- **Step 3 — 평가(초안 2026-05-31, 재계산 2026-06-07):** `docs/evaluation.md`를 **실제 런**에서 영어로 작성(전사 아님), 날짜가 표기된 **이동하는 스냅샷**으로 프레이밍(소유자: 개발 중 수치가 계속 변함). 스냅샷 2026-06-07: `279 passed`(rules 95 / cli 110 / tools 10 / compacting 7 / agent-runner 27 / models 22 / fixtures 8); 측정된 `(high, med, info)` + review_queue와 별도의 next_actions 표를 갖춘 6개 그라운딩 fixture 전체에 대한 `check` 스모크 표; 입력 가드 표. **검증된 순서:** `check`는 `--policy`보다 *먼저* `--source-manifest`를 검증하므로 둘 다 생략 시 → `provide_source_manifest`. 재현 명령 포함(Docker 정식 + 직접 pytest). **다음:** 모든 개발 작업이 공개 동결에 도달한 후 Step 6.5(README EN/KO 전환을 포함한 이중 언어 미러).

수확 기록(네 출처 모두 완료 — audit용으로 보존; 더 있을 것이라 기대하며 재수확하지 말 것):

1. **일일 로그** — `docs/daily_logs/2026-05-2[5-9]/work_log.md` `### Decisions`. **완료(2026-05-31)** → A4(린트 전환, ideation 포함) + B5(fail-loud) + C2(plan-is-SoT), 그리고 정리 중 제외된 A5/A6/B6/B7/B8 산출.
2. **검증 기록** — `docs/verifications/2026-05-2[7-9]/*.md` Verdict/Issues. **완료(2026-05-31)** → B5 + gate-범위 논점 + review-안전성 논점(policy_completeness, review_safety_guards, gate_initial_slice 조건부 통과) 확증; 일일 로그 수확을 넘어서는 *새* 비네트 없음.
3. **Ideation** — `docs/planning/ideation_assessment_harness_v2.2.md` 수락/거부 근거. **완료** → L3/L8/L9 거부가 A2가 되었고; 린트 사고방식 전환이 A4가 됨.
4. **구현 계획 변경 로그** — §15, v1.0→v1.30. **완료** → v1.2/v1.3/v1.4/v1.5/v1.6/v1.7이 A1/A3/B1/B2/B3/B4가 됨.

### 남은 공개 단계 (publication_plan §4 기준)

- **Step 1 — 이중 언어 스캐폴드:** 쇼케이스 문서(README, case_study, decisions, evaluation)와 기술 문서(HANDOFF/AGENTS/CLAUDE)에 대한 EN/KO 쌍 + 언어 전환 헤더. README에 **Mermaid 아키텍처 다이어그램** 삽입(별도 아키텍처 문서를 대체).
- **Step 2 — 사례 연구 + 결정:** `decisions.md` 완성(수확 후); `docs/case_study.md` 작성(문제/목표/핵심 결정/내가 만든 것/검증/한계/다음).
- **Step 3 — 평가(`docs/evaluation.md`):** 테스트 + 스모크 표를 **실제 `docker compose run` / `pytest` 출력에서 작성, 절대 전사하지 않음**(2026-06-07 직접 `pytest` 스냅샷에서 279 통과; 공개 전 재계산).
- **Step 4 — AGENTS/CLAUDE 보강: 보류(소유자, 2026-05-31).** 이번 공개 패스에서 의도적으로 건너뜀. 근거: `AGENTS.md` / `CLAUDE.md`는 매 세션 컨텍스트에 로드되므로, 거기에 공개 전용 워크플로 규칙을 추가하면 향후 모든 *개발* 세션마다 토큰을 낭비한다. 정상 개발 중 정말로 빠진 에이전트 규칙이 드러날 때만 재검토 — 공개의 일부로서가 아니라.
- **Step 5 — 정리 + 안전: 완료(2026-05-31).** `LICENSE` 추가(Apache 2.0, `entangelk`). 트리 + 히스토리 전반 비밀 스캔 → API 키 / 토큰 / 개인 키 / 민감 파일 없음. PII(소유자 이메일 + 개인 절대 경로)는 발견되었으나 **소유자에 따라 그대로 유지**(정돈보다 audit 투명성; 정화 패스를 했다가 그 결정을 존중해 `16a8937`에서 되돌림). 정리된 `docs/audit_index.md` 추가(작업 로그 + 검증 기록, 주목할 것 우선, 원본 덤프 아님). 깨진 링크 없음(README `<repo>`는 의도된 자리표시).
- **Step 6 — 문서 지도: 완료(2026-05-31).** README `## 문서`를 목적별로 묶은 지도로 확장(3분 내 이해 / 스펙 / audit-trail / agent-ops), 이제 쇼케이스 문서(case_study, decisions, evaluation, audit_index), publication_plan, schemas를 링크. 여전히 한국어(정식 EN 전환은 §6.5).
- **Step 6.5 — 모든 문서 동결 + 미러**(§7b): 구현 계획의 전체 EN 미러, 공개 계획의 `.ko`, `HANDOFF.md` 미러, README EN/KO 전환, 쇼케이스/문서 미러 — 이동하는 대상을 반복 번역하지 않도록 마지막에 한 번에 수행. 미러링 전에 2026-06-01 작업 로그 기준선 이후의 문서 변경을 검토.
- **Step 7 — 가시성 전환(소유자, 수동):** 여기서는 `gh` 사용 불가. 소유자가 저장소 설명/토픽을 설정하고 공개로 전환한다. 붙여넣기 준비된 초안은 응답 히스토리와 publication_plan §7a에 있다; 설명 = "An agent-consumable CLI harness that validates assessment *design* … Proof-of-concept", 토픽 = `assessment` `spec-validation` `rubric` `cli` `json-schema` `llm-agents` `agent-tooling` `design-by-contract` `python` `proof-of-concept`.

## 빠른 시작 (개발)

```bash
docker compose build
docker compose run --rm test            # full pytest suite
docker compose run --rm harness --help  # CLI help
```

다른 프로젝트 디렉터리에서 콘솔 스크립트를 설치하지 않고도 다음 중 하나로 harness를 호출할 수 있다:

```bash
docker compose -f /workspace/assessment_poc/docker-compose.yml run --rm harness --output json schema --command check
PYTHONPATH=/workspace/assessment_poc/src python3 -m assessment_harness.cli --output json schema --command check
```

이 환경에서 단순 `assessment-harness` 실행 파일은 현재 PATH에 있지 않다.

clean fixture에 대한 종단 간 Rule 0 정합성 검사:

```bash
docker compose run --rm harness --output json check \
  --spec-items fixtures/clean_assignment/spec_items.yaml \
  --rubric-items fixtures/clean_assignment/rubric_items.yaml \
  --trace-links fixtures/clean_assignment/trace_links.yaml \
  --source-manifest fixtures/clean_assignment/source_manifest.yaml \
  --policy fixtures/clean_assignment/policy.yaml \
  --out work/findings.json \
  --diagnostics-out work/integrity_diagnostics.json
```

## 채택된 활성 결정 (Active Decisions)

- **정식 사양**: v1.28 구현 계획 우선, 그다음 `v2.2` ideation(2026-05-27 제자리 개정). v2.1 및 그 이전 ideation 버전은 역사적이다; v2.2는 영역 제한 없이 모든 중첩 영역에서 v2.1을 대체한다.
- **최종 검토 finding 키 최소주의**(plan v1.19 §5.6): `target_type: finding` 결정은 `target_key`에 생성된 식별자만 사용한다; `message`, `evidence`, 제목/설명/텍스트, 기타 페이로드 복사본은 없다. `findings.json` 내부의 오래된/중복 결정 키와 중복 정식 키는 잘못된 입력이다. 누락된 결정이나 `hold`/`rerun_requested`는 `gate`를 `pending_review`로 유지한다.
- **검토 초안 상태 가드**(소유자, 2026-05-28; plan v1.19 §5.6): `review`는 `findings.status=success` 또는 `provisional_findings`만 수용한다. `invalid_input` findings 문서는 초안 생성 전에 거부되어 Rule 0의 잘못된 빈 findings가 실수로 `gate success`가 되지 않도록 한다. `gate`는 상태 불가지론을 유지하며, 수동 복구/audit 워크플로를 위해 명시적 최종 검토 기록을 소비한다.
- **검토 초안 덮어쓰기 가드**(소유자, 2026-05-28; plan v1.19 §5.6): `review`는 기본적으로 기존 `<out-dir>/review.yaml`을 덮어써서는 안 된다. 의도적 재생성은 `--force`를 요구한다; 타임스탬프/버전 관리 초안 관리는 보류되며, 병렬 초안 히스토리를 원하는 호출자는 별도의 `--out-dir`을 사용해야 한다.
- **Gate 차단 범위**(plan v1.19 §5.6): `gate` 종료 코드 `1`은 확정된 `orphan_scored_rubric_item`, `optionality_mismatch`, `mandatory_spec_bonus_only_traced`로 제한된다. 확정된 Rule 2/L1/L5 finding은 검토 결과이지만 v0 차단 판정은 아니다.
- **Rule 1 finding 타입 명명 규약**(plan v1.19 §6): 무추적 finding은 `{prefix_}orphan_{role}_rubric_item`을 따른다. `possible_` 접두사는 `gate`가 이들을 확정으로 승격할 수 있으므로 scored 항목을 표시한다; bonus / qualitative는 대칭적 승격 경로가 없으므로 접두사를 생략한다. 향후 Rule 1 확장은 리터럴을 재결정하지 않고 동일 규약을 적용한다.
- **`--source-manifest`는 필수 `check` 입력**(plan v1.19 §5.0 / §5.1 / §11): Phase 0은 불변 소스 스냅샷 그라운딩을 요구한다. manifest 누락 → `status=invalid_input` / 종료 `2` / 진단 `source_manifest_required` / next_action `provide_source_manifest`. argparse는 플래그를 `default=None`으로 선언해 두어, 호출 에이전트가 stderr의 argparse 사용법 텍스트가 아니라 stdout의 구조화된 envelope를 항상 받도록 한다.
- **`--policy`는 필수 `check` 입력**(plan v1.20 §8 / §15): Phase 0은 `rules.optionality_mismatch.weight_threshold`를 요구한다. policy 누락 → `status=invalid_input` / 종료 `2` / next_action `provide_policy`; 그 필드가 빠진 스키마 유효 policy → `invalid_input` / `fix_input`. 이는 Rule 3가 조용히 비활성화되는 것을 방지한다.
- **Rule 1 최종 커버리지 경계**(plan v1.19 §6 Rule 1, §5.3.1): Rule 1에 대해 최종 커버리지로 인정되는 `semantic_status` 값은 `human_accepted`와 `human_overridden`뿐이다. 그 외 모든 것 — 검토 전(`pending_verification`, `agent_*`)과 검토 후 비커버리지(`human_rejected`, `rerun_requested`) — 는 `check`에서 `unconfirmed_trace_coverage`(medium / provisional)로 드러난다. `gate`만이 지속적 비커버리지를 확정 `orphan_scored_rubric_item`으로 승격할 수 있는 유일한 단계이다. **이 경계는 Rule 1과 `gate`에만 적용된다.** Rule 2와 Rule 3는 `semantic_status`를 참조하지 않는다(plan §6 Rule 2 / Rule 3의 구조적 조건을 사용). 린트 계열(Rule L1/L5/L6)도 `semantic_status`를 참조하지 않는다 — L-DET, 구조적 검사만.
- **Rule 2 finding 계약**(plan v1.19 §6; 처음 v1.14에서 고정): `uncovered_must_spec_item` / `review_uncovered_must_spec`가 공개 계약으로 고정되었다. 소유자 권장 `uncovered_*_spec_item` 명명은 루브릭 고아가 아니라 스펙 커버리지 격차를 반영한다.
- **Rule 3 finding 계약**(plan v1.19 §6): `optionality_mismatch` / `review_optionality_mismatch`가 기존 fixture 및 policy 네임스페이스와 일치하는 공개 계약으로 고정되었다.
- **린트 계열 명명 규약**(plan v1.19 §6, ideation v2.2 §3): 계열 접두사 `Rule L*`; finding 타입은 ideation 후보를 그대로 따른다(`double_scored_spec`, `bonus_grades_mandatory_only`, `mandatory_spec_bonus_only_traced`) — Rule 1의 `{prefix}_{role}_rubric_item` 패턴과의 일관성보다 가독성. 소유자 확인.
- **린트 보호장치 메커니즘**(plan v1.19 §5.7 / §6 Rule L1 / L6): medium/high 린트 finding은 확장 페이로드와 짝지어진 `review_queue` 항목을 모두 갖는다. 소유자는 Phase 0 `check`에서 결정론적 린트 보호장치 큐 산출물을 허용함으로써 Phase 0/Phase 2 문구 충돌을 해소했다; Rule 0 클린 런은 항목이 발화하지 않으면 빈 큐를 작성해 오래된 검토 상태를 피한다. L1은 `double_scoring_review`를, L6은 `mandatory_spec_bonus_review`를 구현한다.
- **Rule L6 정성 경계**(소유자, 2026-05-27; plan v1.19 §6): L6은 `must` 스펙의 모든 추적이 `bonus` 루브릭을 대상으로 할 때만 발화한다. `qualitative` 추적은 단독이든 bonus와 혼합되든 L6을 억제한다 — qualitative는 채점/보너스 크레딧이 아니기 때문이다; scored 커버리지 부재는 구현된 Rule 2가 다룬다.
- **`clean_assignment`는 자동화 전용 기준선**: trace link는 실제 에이전트 런이 만들어내는 상태에 fixture가 맞도록 `pending_verification`으로 유지된다. 따라서 정식 검토 전 결과는 `status=success`가 아니라 N개의 medium `unconfirmed_trace_coverage` finding을 가진 `status=provisional_findings`이다. `success`에 도달하려면 최종 검토 증거가 필요하며, 이는 Phase 3가 공급할 것이다.
- **Rule 0 증거 검증**: 항목별 `verification_mode`. `token_sequence`는 미리 삽입된 정량 마커의 옵트인 엄격 부분문자열 매칭을 수행한다; `ai_judgement`가 PoC 기본값이다. Phase 0은 `ai_judgement` 링크를 pending으로 유지한다; 초기 Phase 2 `verify`는 이제 컴팩팅된 링크를 재작성하지 않고 이들을 `ai_judgement_pending` 큐 항목과 mock 검증기 제안 단계를 통해 라우팅한다.
- **CLI 출력 안정성**: 4필드 안정 코어(`status`, `exit_code`, `command`, `next_actions`)에 더해 `schema --command <name>` 자기 발견 명령을 갖춘 정보성 필드.
- **Policy 통합**: `config/policy.yaml`이 `rules`, `compacting`, `runs`, `verification` 섹션을 갖춘 단일 policy 파일이다.
- **컴팩팅 모델**: `support` / `identity_basis` / `variants`를 보존한 모든 유효 후보의 합집합. 정족수 없음, 자동 수락 없음, 자동 제외 없음.
- **Trace link ID 계보**(소유자, 2026-05-28; plan v1.22 §5.0): trace link 내부 `rubric_id` / `spec_ids`는 spec/rubric item `id_map`을 통해 재매핑되는 종속 참조이며, trace link 항목 자체도 컴팩팅된 관계 산출물로서 정식 정체성을 갖는다. 따라서 `id_map.entity_type`은 `spec_item`, `rubric_item`과 함께 `trace_link`를 포함한다.
- **최종 검토 권한**: `accept` / `hold` / `rerun_requested` / `override`. `override`는 오타/누락 구체화로 제한된다; 의미적 재해석은 `rerun_requested`를 사용해야 한다. `materialize-review`는 override를 `sources`에 별도의 `kind: human_override` 출처 항목으로 기록한다.
- **Mock 러너 역할**: `agent_runners/mock.py`는 프로토콜 계약 테스트에만 사용되는 결정론적 fixture 재생 러너이다; 사람이 작성한 Phase 0/1 입력을 담는 `manual.py`와는 분리되어 있다.
- **Trace 분리**: `agent_trace.raw.jsonl`과 `agent_trace.audit.jsonl`은 별개의 보존/편집 기대치로 분리 저장된다. `agent_trace.schema.json`은 현재 한 번에 하나의 audit JSONL 이벤트를 검증한다; raw trace 보존/편집은 이후 결정으로 남는다.
- **Audit trace 역할 페이로드**(plan v1.23 §5.4.1): turn 이벤트는 역할별 audit 페이로드를 담아야 한다: `system`은 `content_ref`를, `agent`는 `tool_call`을, `tool`은 `name`과 `result_ref`를 요구한다.
- **결정 경계**: `check`는 잠정 finding을 생성한다; `gate`만이, 최종 사람 검토 후, 외부 차단 판정을 반환한다.
- **소스 그라운딩**: Phase 0은 불변 입력 스냅샷, 문서 해시, 라인/스팬 `source_ref`를 사용한다; DB/RAG 저장은 보류된다.
- **`extract` 소스 스냅샷 생성**(소유자, 2026-06-07; plan v1.32 §8): `extract`는 `--source-manifest`가 생략될 때 소스 스냅샷을 자동 생성할 수 있다. 구현은 `--out-dir` 옆에 형제 `source_snapshot/spec.md`, `source_snapshot/rubric.md`, `source_snapshot/manifest.yaml`을 작성한다; 명시적 `--source-manifest`는 권위를 유지하며 자동 생성을 억제한다.
- **정식 ID**: 컴팩팅은 런 로컬 ID를 정식 ID로 재매핑하고 `id_map` 출처를 유지한다.
- **의미 검증기 에이전트**: `ai_judgement` 링크는 별도의 읽기 전용 다중 런 검증기 실행으로 검사된다; 제안은 컴팩팅된 링크를 재작성하지 않고 `semantic_verifications.yaml`에 보존된다. 초기 mock 검증기는 보수적인 `agent_uncertain` 제안만 발행한다; 실제 SDK 검증기 판단은 보류 상태로 남는다.
- **도구 부작용 정책**(소유자, 2026-06-07; plan v1.32 §13): 프레임워크 도구는 읽기 전용으로 유지된다. 제안/쓰기 동작은 후보 파일에 직접 쓰는 것이 아니라 런 종료 시 러너가 수집해 후보 산출물로 발행해야 한다.

## 구현 결정 (Phase 0 반복 1 / 1.5 / 2)

- `src/` 레이아웃 채택(`src/assessment_harness/...`); 패키지 임포트 이름은 plan §7에서 변경 없음.
- Phase 0은 `agent_runners/`와 `tools/`를 범위 밖으로 두었다. Phase 2가 이제 `AgentRunner` 프로토콜, 결정론적 mock 재생, 후보 스키마, 러너 산출물 정규화, 후보/audit trace 귀속 검증, 정규화/심층 후보 런 무결성 분류, 읽기 전용 프레임워크 도구, 자동 생성 소스 스냅샷을 갖춘 mock `extract`, `compact`, mock `verify`, 초기 `materialize-review` 오케스트레이션과 함께 시작되었다; 러너 수집 제안 동작과 실제 SDK 러너는 미구현으로 남는다.
- `evidence_source_ref`는 엄격한 동등성이 아니라 참조된 `spec_item.source_ref` 내부의 스팬 포함으로 검증된다(같은 문서, 스펙 스팬 내부의 증거 스팬).
- 스키마는 entity 객체에서 `additionalProperties: true`를 허용해 Phase 2에서 추가된 후보 단계 필드(`confidence`, `agent_run_id`, ...)가 Phase 0 스키마를 깨지 않도록 한다. 런 수준 후보 산출물은 이제 `candidates.schema.json`으로 별도 검증된다.
- `review` 초기 구현은 의도적으로 안전한 초안만 작성한다. 사람의 선택을 대화식으로 수집하거나, finding을 자동 수락하거나, trace link를 재작성하거나, `human_override` 출처를 구체화하지 않는다.
- `gate`는 판정 전용이다. 이제 finding과 review_queue 최종 결정을 처리하지만, trace link나 review_queue 파일을 재작성하지 않는다. Trace-link override/status와 큐 상태 구체화는 `materialize-review`에 속한다.
- `AgentRunner` 프로토콜 기반은 타입 경계 + 결정론적 mock 재생 + 읽기 전용 도구 함수에서 의도적으로 멈춘다. SDK 자격증명, 러너 수집 제안 동작, 오케스트레이션, raw trace 보존 정책, 후보 컴팩팅 동작은 도입하지 않는다.
- Docker가 개발 환경이다; `docker-compose.yml`의 `harness`와 `test` 서비스는 source/schemas/fixtures/tests를 바인드 마운트해 반복 작업이 재빌드를 요구하지 않게 한다.
- 스냅샷 텍스트 그라운딩은 `spec_item.text`(다중 라인 스팬 허용)와 모든 인용에 대해 공백 정규화된 **부분문자열** 매칭을 사용한다. 루브릭 항목은 평가자 대상 요약이므로 `text`/`description` 그라운딩을 건너뛴다; `source_ref.quote`만 제공될 때 그라운딩된다.
- `evidence_quote_missing_for_spec_id`는 이미 dangling인 spec_id를 건너뛰어, 하나의 깨진 참조가 두 개의 진단을 일으키지 않게 한다.
- CLI `--output`은 루트 파서(기본 `text`)와 모든 하위 파서(기본 `argparse.SUPPRESS`)에 등록되어, 하위명령 이전/이후 형식이 모두 동작하고 둘 다 주어지면 하위명령 값이 루트 값을 재정의한다.
- Rule 1은 `Finding` 타입별로 슬라이스되었다; 각 분기는 under/over-strict 커버리지를 가지며, 공유 `orphan_scored_rubric` fixture가 세 분기를 함께 행사한다. Rule 1은 Rule 0이 high 진단 없음을 보고한 후에만 실행되므로 고유 루브릭 ID와 dangling 참조 없음을 신뢰할 수 있다.
- `check`는 절대 `blocking_count > 0`을 설정하지 않는다; 잠정 finding(`status=provisional_findings`, `exit_code=0`)은 검토를 위해 드러나지만 차단 판정은 최종 검토 후 `gate`에 예약된다.
- `next_actions`는 finding마다 그 `rubric_id`를 가진 타입 항목 하나를 담아, 호출 에이전트가 중복 제거 로직 없이 검토를 병렬화할 수 있게 한다.

## Phase 2 이전 미결 결정 (Open Decisions)

- Claude Agent SDK 자격증명 전달.
- `config/policy.yaml`에서 선택될 구체적 `identity_basis` 알고리즘 문자열(후보는 plan §13에 나열됨).
- `min_valid_runs` / `default_runs` / `max_runs` 수치 값과 정족수 미달 동작(오류 vs 경고 후 진행).
- 실제 SDK 러너 체크리스트: 첫 SDK 표면, 자격증명 전달, 샘플 과제, raw trace 보존/편집, 러너 제한, SDK 도구 등록, 라이브 출력 계약. `docs/guidelines/sdk_runner_decisions.md` 참조.
- Raw trace 보존 / 편집 / 접근 정책(특히 비공개 루브릭 내용에 대해).
- Override 사용 범위: plan v1.31에서 해소됨. `override` 구체화는 오타/누락 수정 전용이다; 의미적 재해석은 통상 `rerun_requested`를 트리거해야 한다.
- 남은 review queue 구성: `compact`는 상류 항목을 보존하고 중복되지 않는 `invalid_run`을 추가한다; `verify`는 상류 항목을 보존하고 중복되지 않는 `ai_judgement_pending`을 추가한다. 향후 `check`/`report`/`review` 배선은 Phase 0 `--review-queue-out`을 병합 대상으로 취급하지 않고 통합 큐를 소비해야 한다.

## 다음 작업

### 순서 결정 (소유자, 2026-05-27)

**Rule 0-3과 린트 계열 L1/L5/L6 완료. 초기 finding 수준 `review`/`gate` 경로 구현됨.**

근거: Rule 2와 Rule 3가 확립된 린트/출력 파이프라인 위의 남은 결정론적 구조 검사를 완성했다. plan v1.32는 이제 최소 최종 검토 finding 매핑, 안전한 검토 초안 생성, gate 경계 매트릭스, 초안 안전 가드, Phase 0 정책 완전성, 정책 스키마 검증 복구 명확화, trace link 정식 ID 계보, audit trace 역할 페이로드 요구사항, 후보 산출물 스키마 기반, 후보 audit-trace 귀속 검증, 러너 산출물 정규화, 단계화된 후보 런 무결성 분류, 명시적 진단-대-상태 라우팅을 갖춘 심층 후보 Rule 0 검증, 구현된 `materialize-review`, `extract` 소스 스냅샷 자동 생성, 그리고 채택된 읽기 전용/러너 수집 도구 부작용 정책을 공급한다.

### 공개 경계 (2026-05-27)

Rule L1과 L5, 그리고 plan v1.12 계약 해소가 소유자의 독립 AI 검증을 통과했으며, 소유자가 이 구현 배치들을 `origin/main`에 공개하도록 승인했다. `.serena/`는 로컬 온보딩 메타데이터로 남으며 공개 구현 배치의 일부가 아니다.

Rule L6과 plan v1.13의 보너스 전용/정성 경계 해소가 소유자의 독립 AI 검증을 통과했으며, 소유자가 이 구현 배치를 `origin/main`에 공개하도록 승인했다.

Rule 2와 plan v1.14의 `uncovered_must_spec_item` / `review_uncovered_must_spec` 계약 갱신이 소유자의 독립 AI 검증을 통과했으며 `origin/main`에 공개되었다.

Rule 3과 plan v1.15의 optional 전용 경계 강화가 소유자의 독립 AI 검증을 통과했으며, 소유자가 검증 기록 지침 및 audit 기록과 함께 `origin/main`에 공개하도록 승인했다.

### Rule 2 — 필수 스펙 커버리지 (완료)

- Rule 2는 `uncovered_must_spec_item`(`medium`, `provisional`)과 `review_uncovered_must_spec`를 발행한다; 리터럴 쌍은 plan v1.14 §6에 고정되어 있다.
- 구조적 검사일 뿐이다: 어떤 `scored` 추적도 `semantic_status`와 무관하게 must 스펙을 커버한다; 보너스 전용, 정성 전용, 무추적 must 스펙은 미커버로 남는다.
- 그라운딩된 `fixtures/uncovered_must_spec/`는 무추적, pending-scored, 보너스 전용, 정성 전용, optional, informational 경계를 고정한다. 기존 `bonus_misuse` fixture는 이제 S3/RB4에 대한 의도된 Rule 2 + L5 + L6 동시 발화도 기록한다.

### Rule 3 — 선택성 일관성 (완료)

- Rule 3는 `optionality_mismatch`(`high`, `provisional`)와 `review_optionality_mismatch`를 발행한다; 리터럴 쌍은 plan v1.19 §6에 고정되어 있다.
- scored 루브릭을 `rules.optionality_mismatch.weight_threshold`에 대해 평가한다; 임계값 이상에서 optional 전용으로 추적된 scored 루브릭만 발화한다.
- 구조적 검사일 뿐이다: pending 의미 상태도 발화한다; must/informational 혼합, 비-scored, 무추적, 임계값 미만 루브릭은 발화하지 않는다.
- 그라운딩된 `fixtures/optionality_mismatch/`는 high, 임계값, pending-status, must/informational 혼합, bonus/qualitative 역할, 임계값 미만 경계를 고정한다.

### `gate`와 이후 단계

- `final_review.schema.json`을 갖춘 초기 finding 수준 `review`/`gate`가 구현되었다. `review`는 최소 finding 키를 가진 안전한 `hold` 초안을 생성한다; `gate`는 지속적 `possible_orphan_scored_rubric_item` / `unconfirmed_trace_coverage`를 `orphan_scored_rubric_item`(high / confirmed)으로 승격할 수 있는 유일한 단계이다. 린트 계열과 Rule 3 finding은 최종 검토로 확정/기각될 수 있다; 현재 확정된 Rule L6과 Rule 3만 차단이다.
- 다음 gate/review 작업: 필요 시 더 풍부한 사람 결정 입력 지원, 구체적 워크플로가 요구할 때만 spec_item/rubric_item으로 구체화 확대.
- HTML 보고서 룰 카탈로그 구현됨: 보고서는 발행된 결과와 함께 Rule 0, Rule 1/2/3, 린트 L1/L5/L6의 의미를 finding 수준 룰 컨텍스트와 `--policy`의 선택적 구성된 Rule 3 임계값과 함께 보여준다. 이는 새 판정 계약이 아니라 기존 plan/policy/rule 정의에 대한 표현/컨텍스트로 남는다.
- Phase 2 러너/보존 파라미터도 여기서 해소된다. 실제 과제 권한/익명화 검토는 첫 PoC 샘플에 대해 보류되며 공개 동결에서 돌아온다.

### 린트 계열 (완료) — plan v1.19 §6

- **스펙 상태**: plan v1.19 §6에서 완료. Rule L1, L5, L6 구현됨.
- **L1 도착**: `findings.schema.json` 페이로드 ID, `review_queue.schema.json`, 기본/재정의 `--review-queue-out` 산출물 처리, `review_double_scoring`, 그라운딩된 `fixtures/bonus_misuse/` 도입.
- **L5 도착**: `bonus_grades_mandatory_only`와 `review_bonus_mandatory_only` 추가; `bonus_misuse`는 이제 RB1 L1+L5 동시 발화, RB2 optional 비발화, RB3 Rule 1 고아 분리를 고정한다.
- **L6 도착**: high/provisional `mandatory_spec_bonus_only_traced`, 짝지어진 `mandatory_spec_bonus_review`, `bonus_rubric_ids[]`, `review_mandatory_spec_bonus_only` 추가; 정성 참여는 소유자 승인 v1.13 경계 하에서 명시적으로 L6을 억제하며, Rule 2가 이제 남은 missing-scored 커버리지를 드러낸다.
- **Phase 2 후속 진행**: `compact` / `verify`는 이제 수신 큐 항목을 보존하고 자체 결정론적 항목을 추가한다. 이후 병합/갱신 경로가 구현되지 않는 한 Phase 0 `check --review-queue-out`을 통합 compact/검증기 큐로 겨냥하지 말 것; 현재 `check` 출력은 Phase 0 린트 보호장치 산출물로 남는다.
- **Fixture**: 세 L1/L5/L6 분기와 over-strict 가드를 모두 다루는 단일 공유 fixture(예: `fixtures/bonus_misuse/`), `orphan_scored_rubric`이 Rule 1의 세 분기를 다루는 방식을 반영. **결정적**: fixture와 테스트는 Rule 1 `orphan_bonus_rubric_item`, Rule L5 `bonus_grades_mandatory_only`, Rule L6 `mandatory_spec_bonus_only_traced` 사이의 상호 배타/동시 발화 경계를 시각화해야 한다 — 셋 모두 서로 다른 조건에서 보너스 루브릭을 건드리며 검토자가 혼동해서는 안 된다.
- **CLI envelope**: 각 린트 finding 타입은 `next_actions` 리터럴(`review_double_scoring`, `review_bonus_mandatory_only`, `review_mandatory_spec_bonus_only`)을 추가하고 필요 시 심각도 카운트를 추가할 수 있다. 스키마 계약 테스트(`schema --command check`)는 보조를 맞춰 확장되어야 한다 — 아래 "테스트 표면 교훈" 참조.
- **`drift_observations[]`(plan v1.19 §5.6)**: Rule L8 드리프트 관찰을 위한 수동 audit 채널로 `final_review.schema.json`에 표현됨. `check`/`gate` 결과 코드에 영향을 주지 않는다.

### L6 이후 린트 확장 (진입 전 소유자 결정 필요)

- Rule L2(`bonus_weight_encroachment`, 정책 임계값), Rule L4(`duplicate_trace_link`, 린트 독립 — 소유자에 따라 Rule 0에 흡수되지 *않음*), Rule L7 + C1(`forbidden_clause_rewarded` + `requirement_level: forbidden` 스키마 확장). 모두 ideation v2.2 §4-§6에 명세되어 있으나 아직 plan §6에는 없음.
- 유일하게 남은 ideation §9.2 미결 결정: L7-DET vs L7-SEM 우선순위(L7 plan 승격 시 해소).

### 오늘 세션의 테스트 표면 교훈 (Slice 3.1 회고)

새 envelope 필드, next_action 타입, 스키마 계약 항목을 추가할 때는 그것을 **명시적으로** 단언하는 회귀 테스트도 추가하라. CLI의 주 사용자는 AI 에이전트이다; 공개 계약은 디스크 상의 `findings.json`이 아니라 envelope(stdout JSON)이다. findings.json만 읽는 테스트는 envelope 형태 회귀를 놓친다 — slice 3는 세 개의 새 envelope 표면을 출하했으나 어느 것에도 테스트가 없었고, 그 격차는 소유자 검토를 통해서만 드러났다. `tests/test_fixtures.py`의 `_run_check`는 이제 이를 쉽게 하도록 envelope를 4-튜플로 반환한다. 그것을 사용하라.

**검증기**가 프로브에서 분기 커버리지를 주장할 때는, 분기를 구별하는 수준에서 측정하라 — 보통 종료 코드와 `next_action` 타입이 아니라 오류 메시지이다. 두 다른 코드 경로(예: 정책 스키마 검증 vs `_validate_check_policy`)는 완전히 다른 함수를 행사하면서도 동일한 envelope 결과(`exit 2` / `fix_input` / `status=invalid_input`)로 수렴할 수 있다. v1.20 정책 완전성 검증은 8개 입력 형태를 프로브하고 종료 코드와 `next_action`만으로 "8/8 PASS"를 보고했다; v1.21 강화 후속 작업이 그 형태 중 하나가 명명된 검증기에 전혀 도달하지 않았음을 드러냈다 — 같은 결과, 다른 경로. 수정은 검증기 측에 있다: 분기 커버리지를 주장하는 어떤 프로브 표에든 거부 메시지(또는 경로 귀속 단언)를 포함하라. 결과만 검사하는 프로브는 방어적 깊이와 1차 검사가 모두 같은 envelope로 이어질 때 거짓 커버리지 감각을 줄 수 있다.

## 검증

- 2026-06-07 독립 검증과 Codex 재검사 모두 `extract` 소스 스냅샷 자동 생성에 대해 통과: `docs/verifications/2026-06-07/extract_source_snapshot_auto_generation.md`와 `docs/verifications/2026-06-07/extract_source_snapshot_auto_generation_recheck.md` 참조. 언급된 `project_id` / 상대 `--out-dir` / mock 불일치 / 방어적 스키마 검증 관찰은 비차단이다.
- `extract` 소스 스냅샷 자동 생성 후 279개 테스트 통과(`PYTHONPATH=src python3 -m pytest -q`). 수집은 27개 agent-runner 계약, 110개 CLI 계약, 10개 도구 계약, 7개 컴팩팅, 8개 fixture, 22개 모델, 95개 룰 테스트를 보고한다. extract CLI 회귀는 스키마 자기 발견, `mock_fixture` 런 디렉터리 출력, 후보/audit trace 스키마 유효성, 쓰기 전 생성 산출물 검증, 런별 출처, `--source-manifest` 생략 시 자동 생성 소스 스냅샷, 명시적 manifest 우선, 스키마 유효 `integrity_diagnostics.json`을 갖춘 잘못된 런 격리, 미지원 SDK 러너 거부, `--runs` 1..7, extract→compact 호환성을 고정한다. 읽기 전용 도구 회귀는 Markdown 섹션 나열/조회, 인접 헤딩 누출 없는 빈 섹션의 비반전 스팬, 스키마 검증 루브릭 요약/전체 항목 조회, 모호한 루브릭 ID, 반환 값 불변성을 고정한다. compact CLI 회귀는 스키마 자기 발견, 계획상 정식 `--runs-dir`, 명시적 저수준 `--candidates`, 두 입력 모드 동시 전달 시 거부, 정식 YAML 출력, 독립 실행형 `id_map.yaml` 래퍼 검증, `--review-queue-in`에서의 review_queue 메타데이터/리스트 보존, 제외된 혼합/비검증 런에 대한 중복되지 않는 추가 `invalid_run` 항목, 그라운딩 fixture에 대한 compact→check 호환성을 고정한다. verify CLI 회귀는 스키마 자기 발견, mock `semantic_verifications.yaml` 출력, `ai_judgement_pending` review_queue 생성, 상류 큐 메타데이터/리스트 보존, 중복 pending 항목 억제, 미지원 SDK 검증기 거부, 보수적 `agent_uncertain` mock 제안, trace 순서가 바뀔 때 id_map 기반 trace-link 정식 ID 해석, `source_ref` 없는 `ai_judgement`이 여전히 빈 `source_refs`를 가진 `agent_uncertain`을 생성, 토큰 시퀀스 전용 over-strict 억제를 고정한다. 의미 소비 회귀는 `check --semantic-verifications --id-map`이 trace 파일을 재작성하지 않고 제안을 Rule 1 증거의 메모리 내 유효 상태로 적용, trace 순서가 바뀔 때 id_map 기반 trace-link 제안 결합, 계보를 가진 trace link가 `--id-map` 없이 의미 제안을 받을 때 invalid_input, 검토 후 상태 보존, 무관 제안 억제, `report`의 의미/review-queue 렌더링 + 잘못된 의미 거부, `review`의 의미/review queue 입력 검증/기록을 고정한다. review_queue 최종 검토 회귀는 `review --review-queue`가 미해결 항목에 대한 `review_queue_entry` 결정 초안 작성, 해결된 항목 건너뛰기, 누락된 큐 결정에 대한 `gate` pending, 차단 판정 없이 수락된 큐 결정 종결, 중복/오래된/비최소/무경로 큐 결정에 대한 분기별 invalid-input 가드를 고정한다. materialize-review 회귀는 스키마 자기 발견, id_map 기반 trace-link 결정 결합, 중복 trace-link 결정, trace accept/override/hold/rerun 상태 매핑, review_queue accept/override/hold/rerun 상태 매핑, 인플레이스 컴팩팅 trace 변형 없음, fail-loud 누락/미지/비최소/모호한 trace 결합, spec/rubric 보존 + `unsupported_decision_count`, finding 결정 무시, 중복/누락/무입력 큐 가드, 생성된 materialization-summary 스키마 실패 시 부분 산출물 없이 `invalid_input` 반환을 고정한다. 컴팩팅 회귀는 단일 런 후보 보존, 다중 런 union/id_map 계보, 혼합 상태 런 제외, 유효 런 support 분모 동작, 정규화 정체성 매칭 후 raw variant 보존, 증거 인용 spec-id 재매핑, 매핑되지 않은 trace 참조 거부, 구별되는 정체성 분리를 고정한다. 후보 스키마 회귀는 누락된 후보 출처, 잘못된 무결성 상태, 새 `source_grounding_mismatch` enum 리터럴, spec/rubric/trace 후보 전반의 잘못된 내장 `proposed_item` 형태를 고정한다; 후보 audit-trace 회귀는 일치하는 run ID, 누락된 trace 귀속, 스키마 오류, 세 후보 섹션 모두를 고정한다; 정규화 회귀는 후보 스키마 유효성, audit-trace 귀속 호환성, 출처 필드, 기본 `pending_check`, spec/rubric/trace 후보 전반의 컴팩팅 전용 필드 제거를 고정한다; 무결성 회귀는 깨끗한 구조적 `structurally_validated`, 후보/audit 스키마 `schema_violation`, 누락된 trace 귀속 `trace_attribution_error`, 원본 정규화 후보 무변형, 심층 Rule 0 클린 `validated` 승격, 증거 spec-id 불일치/dangling 내부 참조의 `invalid_reference`, 소스 그라운딩 실패의 `source_grounding_mismatch`, 토큰 시퀀스 인용 불일치의 `quote_mismatch`, `invalid_reference > source_grounding_mismatch > quote_mismatch` 우선순위, `ai_judgement` over-strict 가드를 고정한다. 정책 불완전 회귀는 `_validate_check_policy`가 잡아야 하는 네 형태(빈 문서, `rules` 누락, 빈 `rules`, 임계값 부재)에 걸쳐 파라미터화되어 리팩토링이 하나라도 조용히 통과시키지 못하게 한다.
- `schema --command review --output json`은 정보성 `review_path`, `decision_count`, `semantic_verifications_path`, `review_queue_path`, `input_error`를 노출한다.
- `schema --command gate --output json`은 `complete_final_review`, `fix_final_review`, `revise_assessment`, 그리고 정보성 `final_review_path`, `findings_path`, `blocking_count`, `confirmed_finding_count`, `dismissed_finding_count`, `pending_decision_count`, `blocking_findings`, `input_error`를 노출한다.
- `schema --command verify --output json`은 `fix_input`, 그리고 정보성 `compacted_dir`, `semantic_verifications_path`, `semantic_verification_count`, `review_queue_path`, `review_queue_count`, `run_count`, `runner`, `source_manifest_path`, `input_error`를 노출한다.
- `schema --command check --output json`은 `provide_policy`, `review_double_scoring`, `review_bonus_mandatory_only`, `review_mandatory_spec_bonus_only`, `review_uncovered_must_spec`, `review_optionality_mismatch`, 그리고 정보성 `semantic_verifications_path`, `id_map_path`, `review_queue_path`, `review_queue_count`를 노출한다.
- `schema --command report --output json`은 정보성 `report_path`, `report_format`, `semantic_verifications_path`, `review_queue_path`를 노출한다.
- 현재 상태에 대한 스모크 런:
  - `mock_fixture`로 컴팩팅된 `fixtures/clean_assignment` 형태 산출물에 대한 `verify`: 종료 `0`, `status=success`, `ai_judgement` trace(`T2`)에 대한 `agent_uncertain` 제안 하나, `ai_judgement_pending` 큐 항목 하나, 컴팩팅 trace-link 재작성 없음. `T2` ID는 컴팩팅 출력이 제공할 때 이제 `id_map.yaml`을 통해 고정된다.
  - 잠정 `optionality_mismatch`에 대한 결정이 없는 최종 검토 기록에 대한 `gate`: 종료 `0`, `status=pending_review`, `pending_decision_count=1`, `complete_final_review`.
  - 그라운딩된 `fixtures/orphan_scored_rubric` findings에 대한 `review`는 최소 finding 키를 가진 세 개의 `hold` 결정을 작성한다; 그 초안을 `gate`에 전달하면 `pending_decision_count=3`인 `pending_review`를 산출한다.
  - R2를 수락하고 R1/R3을 재정의하는 최소 키 최종 검토 후 그라운딩된 `fixtures/orphan_scored_rubric`에 대한 `gate`: 종료 `1`, `status=fail`; R2는 확정 `orphan_scored_rubric_item`으로 승격; `(blocking_count=1, confirmed_finding_count=1, dismissed_finding_count=2)`.
  - 그라운딩된 `fixtures/optionality_mismatch`에 대한 `check`: 종료 `0`, `status=provisional_findings`; Rule 3는 R_HIGH와 R_PENDING에만 `optionality_mismatch`를 산출; 임계값 미만 R_LOW, must 혼합 R_MIXED, informational 혼합 R_INFO_MIXED, bonus R_BONUS, qualitative R_QUAL은 올바르게 억제; R_PENDING은 Rule 1 `unconfirmed_trace_coverage`도 보존; `review_queue_count=0`; `(high=2, medium=1, informational=0)`.
  - 그라운딩된 `fixtures/uncovered_must_spec`에 대한 `check`: 종료 `0`, `status=provisional_findings`; Rule 2는 S_UNTRACED, S_BONUS_ONLY, S_QUAL_ONLY에 `uncovered_must_spec_item`을 산출하는 한편 pending scored S_COVERED는 커버됨; S_BONUS_ONLY는 L5/L6 동시 발화; `review_queue_count=1`; `(high=1, medium=5, informational=0)`.
  - 그라운딩된 `fixtures/bonus_misuse`에 대한 `check`: 종료 `0`, `status=provisional_findings`; 기존 R1/RB1/RB3 경계는 유지되고, S3/RB4는 이제 의도적으로 Rule 2 + L5 + L6을 동시 발화; `review_queue_count=2`; `(high=1, medium=5, informational=1)`.
  - manifest를 갖춘 그라운딩된 `fixtures/orphan_scored_rubric`에 대한 `check`: 종료 `0`, `status=provisional_findings`, 세 Rule 1 분기 모두 가시 — R1의 `unconfirmed_trace_coverage`(medium), R2의 `possible_orphan_scored_rubric_item`(high), R3의 `orphan_bonus_rubric_item`(informational). `provisional_high_count=1`, `provisional_medium_count=1`, `provisional_informational_count=1`.
  - manifest를 갖춘 그라운딩된 `fixtures/clean_assignment`에 대한 `check`: 종료 `0`, `status=provisional_findings`, R1과 R2에 두 개의 `unconfirmed_trace_coverage` finding.
  - manifest를 갖춘 그라운딩된 `fixtures/reference_integrity`에 대한 `check`: 종료 `2`, `status=invalid_input`, 여덟 개의 Rule 0 위반 코드 모두 존재(`evidence_quote_missing_for_spec_id`가 두 번 발화하므로 `high_integrity_count=9`; 기존 중복이며 회귀 아님).
  - `--source-manifest` 없는 `fixtures/clean_assignment`에 대한 `check`: 종료 `2`, `status=invalid_input`, 진단 `source_manifest_required`, next_action `provide_source_manifest`.
- 공개 승인은 L1, L5, L6, Rule 2, 그리고 경계 강화된 Rule 3 배치에 대한 독립 AI 검토 후 소유자로부터 받았다; Rule 3 배치와 동반 검증 지침/audit 문서는 `origin/main`에 공개하도록 승인되었다.

## 프로젝트 구조

- `README.md`: 사용자/에이전트 진입점.
- `AGENTS.md` / `CLAUDE.md`: 코딩 에이전트를 위한 행동 지침.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`: 정식 개발/실행 환경.
- `pyproject.toml`: src-레이아웃 Python 패키지, 진입점 `assessment-harness`.
- `src/assessment_harness/`: 패키지 코드.
  - `cli.py`: `check`, `extract`, `compact`, `verify`, `schema`, `report`, `review`, `gate` 하위명령; envelope/종료 코드 계약; 깨끗한 Rule 0 통과 후의 Rule 1/2/3 및 린트 계열 배선; finding 수준 최종 검토 초안/gate 결정; 초기 mock-fixture extract, 컴팩팅, 의미 검증 오케스트레이션.
  - `models.py`: YAML+스키마 로더, sha256과 라인/스팬 접근을 갖춘 `SourceSnapshot`/`Document`.
  - `rules.py`: Rule 0 참조 무결성 엔진; 완전한 Rule 1, Rule 2, Rule 3 구현; 린트 Rule L1/L5/L6 구현. `HUMAN_ACCEPTED_SEMANTIC_STATUSES`가 Rule-1 전용 최종 커버리지 경계를 고정한다.
  - `schemas.py`: `ASSESSMENT_HARNESS_SCHEMA_DIR` 환경 변수 재정의를 갖춘 스키마 로더.
  - `report.py`: Markdown 및 독립 실행형 HTML 렌더러.
  - `compacting.py`: 검증된 후보 산출물에 대한 헬퍼 수준 Phase 2 union 컴팩팅; support/identity_basis/variants와 정식 id_map 계보를 보존한다.
  - `tools/`: 소스/루브릭 검사를 위한 프레임워크 중립 읽기 전용 도구 함수.
    - `spec_tools.py`: Markdown `list_sections` / `read_spec_section`.
    - `rubric_tools.py`: 스키마 검증 `list_rubric_items` / `get_rubric_item`.
  - `agent_runners/`: 프레임워크 중립 러너 경계.
    - `base.py`: `AgentRunner` 프로토콜과 `AgentRunResult`.
    - `integrity.py`: 구조적 및 심층 Rule 0 후보 런 무결성 분류 헬퍼.
    - `mock.py`: 프로토콜 계약 테스트 전용 결정론적 fixture 재생 러너.
    - `normalization.py`: 러너 산출물에서 후보 산출물로의 정규화 헬퍼.
    - `validation.py`: 후보 산출물 / audit trace 귀속 검증 헬퍼.
- `schemas/`: 열여섯 개의 JSON Schema, Rule L1과 함께 도입된 `review_queue.schema.json`, 초기 `gate`와 함께 도입된 `final_review.schema.json`, Phase 2 계약 기반 `candidates.schema.json` / `compacting.schema.json` / `id_map.schema.json` / `semantic_verifications.schema.json` / `agent_trace.schema.json`, 그리고 `materialize-review` 출력 검증을 위한 `materialization_summary.schema.json` 포함.
- `config/policy.yaml`: 기본 policy.
- `fixtures/clean_assignment/`: 소스 manifest, sha256, spec.md, rubric.md를 갖춘 통과 fixture.
- `fixtures/reference_integrity/`: 현재 여덟 개의 Rule 0 진단 코드를 모두 다루는 그라운딩 실패 fixture; 자체 `source/spec.md`, `source/rubric.md`, `source_manifest.yaml`을 갖는다.
- `fixtures/orphan_scored_rubric/`: 세 분기를 모두 행사하는 그라운딩 Rule 1 종단 간 fixture: R1(scored, pending_verification으로 추적됨) → unconfirmed_trace_coverage, R2(scored, 무추적) → possible_orphan_scored_rubric_item, R3(bonus, 무추적) → orphan_bonus_rubric_item. 동일한 `source/` + manifest 레이아웃.
- `fixtures/bonus_misuse/`: 그라운딩 린트 fixture; S1/R1/RB1을 통한 L1/L5, RB2/S2 optional 비발화, RB3 무추적 Rule 1 informational 분리, 그리고 보너스 전용 필수 S3/RB4를 통한 Rule 2/L5/L6 동시 발화를 행사한다.
- `fixtures/uncovered_must_spec/`: 무추적, pending-scored-covered, 보너스 전용, 정성 전용, optional, informational 스펙 경계를 다루는 그라운딩 Rule 2 fixture.
- `fixtures/optionality_mismatch/`: optional 전용 high 가중치, 정책 임계값, pending-status 구조적 발행, must/informational 혼합 억제, bonus/qualitative 역할 제외, 임계값 미만 억제를 다루는 그라운딩 Rule 3 fixture.
- `examples/deskhive_assignment/`: 복잡한 합성 쇼케이스 과제. 두 계층: (1) harness 입력 `spec.md` / `rubric.md`(+ `notes.md` / `README.md`) — `deterministic_extraction`을 통해 종단 간 실행되는 원시 다단계 유지보수 과제(최신 반복 산출물은 `work/poc_report_runs/run{1,2,3}/deskhive/` 아래, gitignore됨), Rules 1/2/3/L1/L5/L6을 씨딩(14 findings, blocking=0); 그리고 (2) `codebase/` — 다섯 개 B1–B5 결함이 실제로 `app/services/*.py`에 존재하는 작은 실행 가능 FastAPI 백오피스 저장소로, 검토자가 스펙 주장이 실제 동작에 매핑됨을 확인할 수 있다(`python3 codebase/scripts/show_symptoms.py`가 표준 라이브러리만으로 다섯 개 모두 재현). harness는 두 마크다운 파일만 소비하며 `codebase/`는 결코 소비하지 않는다. `fixtures/`(룰별 사전 추출 YAML)와 구별됨: `examples/`는 독자 대상 과제이다. 여전히 보류된 공개 검토 결정의 대상. 작은 알려진 문서 정합성 위험: B1 스펙은 유한한 수를 말하지만 codebase 비즈니스 규칙은 무사용 표현으로 가능한 `null`을 언급한다.
- `examples/pulse_assignment/`: 세 번째 합성 예제 — **그린필드 Go 빌드** 과제(다른 두 개와 다른 언어 + 아키타입). harness 입력 `spec.md` / `rubric.md`(+ `notes.md` / `README.md`); `codebase/`는 동작하는 Go 참조 솔루션(`pulse` CLI: 서비스별 count/error-rate/p95, 잘못된 라인 복원력, JSON 출력)으로 `*_test.go`와 `testdata/expected.json`을 갖는다. 의도적으로 다른 finding 조합(10 findings: `orphan_bonus_rubric_item` informational, 정성 전용 `uncovered_must_spec_item`, `optionality_mismatch`, `possible_orphan_scored_rubric_item`, 그리고 깨끗한 과발화 가드 bonus). 최신 반복 harness 산출물은 `work/poc_report_runs/run{1,2,3}/pulse/` 아래(gitignore됨). 주의: Go 참조 솔루션은 작성/검토되었으나 여기서 실행되지 않았다(Go 툴체인 없음); harness 신호는 검증되었지만 `go test ./...`는 여전히 Go가 가능한 환경이 필요하다.
- `tests/`: `test_rules.py`, `test_cli_output_contract.py`, `test_fixtures.py`, `test_models.py`, `test_agent_runner_contract.py`, `test_tools.py`, `conftest.py`.
- `docs/planning/implementation_plan_assessment_harness_poc_v1.md`: 구현 진실의 원천(v1.32).
- `docs/guidelines/sdk_runner_decisions.md`: 자격증명 러너 구현 전 라이브 SDK 러너 결정 체크리스트.
- `docs/planning/ideation_assessment_harness_v2.2.md`: 최신 ideation(최종 2026-05-27, 같은 날 제자리 개정). Rubric Lint Rules 계열 추가 — 6개 수락(L1, L2, L4, L5, L6, L7), 3개 거부. plan v1.19 §6 린트 계열의 출처.
- `docs/planning/ideation_assessment_harness_v2.1.md`: 최신 ideation, 우선순위 2위.
- `docs/planning/ideation_assessment_harness_v2.md`, `docs/planning/ideation_assessment_harness_v1.ko.md`: 역사적 참조.
- `docs/verifications/YYYY-MM-DD/<slug>.md`: 날짜 기반 하위 디렉터리의 독립 audit 기록(`docs/daily_logs/`를 반영); Rule 3 경계 강화 기록이 초기 철회된 Rule 3 판정을 대체한다.
- `docs/daily_logs/2026-05-25/work_log.md`: 계획 반복(v1.0 → v1.7)과 Phase 0 반복 1 / 1.5의 전체 기록.
- `docs/daily_logs/2026-05-26/work_log.md`: Phase 0 반복 2 Rule 1 슬라이스, 계약 회귀 후속, 공개 검토 기록.
- `CHANGELOG.md`: 주요 마일스톤.
- `HANDOFF.md`: 이 파일.
