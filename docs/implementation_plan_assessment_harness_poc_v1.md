# Assessment Spec Harness PoC 구현 계획서 v1.9

## 0. 문서 목적

본 문서는 `Assessment Spec Harness`의 기술 PoC를 구현하기 위한 실행 계획이다.

핵심 전제는 다음과 같다.

> Phase 0에서는 agent 실행을 제외해 deterministic validation core를 먼저 검증한다. 그러나 최종 PoC는 반드시 복수 agent 실행, 실행별 검증, 결과 취합, deterministic validation, 최종 human review의 전체 흐름을 포함한다.

따라서 수동 입력 단계는 최종 제품 범위의 축소가 아니라, 확률적 agent 결과와 규칙 엔진의 책임을 분리하여 테스트하기 위한 첫 단계다.

## 1. 문서 우선순위

본 PoC 구현 중 문서가 충돌할 경우 다음 순서로 해석한다.

1. 본 구현 계획서: 구현 범위, 단계, 입력/출력 계약, 완료 기준
2. `docs/ideation_assessment_harness_v2.1.md`: 제품 목적과 장기 방향
3. `docs/ideation_assessment_harness_v2.md`: historical reference
4. `docs/ideation_assessment_harness_v1.md`: historical ideation reference

본 계획서가 `v2.1`의 핵심 목적과 충돌하는 경우에는 임의 구현하지 않고 결정을 다시 기록한다.

## 2. PoC 목표

### 2.1 최종 목표

자유 형식의 candidate-facing spec과 evaluator-facing rubric을 입력받아:

1. agent runner가 독립 실행을 여러 번 수행하여 구조화 후보와 trace link 후보를 제안한다.
2. 하네스가 각 실행 산출물의 schema/reference/evidence integrity를 검사한다.
3. 하네스가 유효한 실행 결과를 **compacting**한다 (자동 채택/분류 없음, 중복 통합 + support·variants 보존).
4. 별도 semantic verifier-agent가 source snapshot과 compacted trace link를 읽기 전용으로 복수 검증하고, 의미적 support/reject/uncertain 제안을 저장한다.
5. deterministic rule engine이 compacted 입력과 semantic verification 산출물에서 diagnostic/finding을 산출한다. 이 단계는 판정 gate가 아니다.
6. 사람이 마지막에 compacted 결과, verifier 제안, compacting 자체의 타당성, finding, trace 근거를 검토한다.
7. 외부 호출자는 최종 review record를 입력으로 받는 별도 `gate` 명령을 통해서만 판정 결과를 소비한다.

최종 PoC의 정체성은 다음과 같다.

> Agent-assisted, multi-run, deterministically checked assessment design validator with final human review.

### 2.2 검증하려는 가설

- 기술 가설: agent 실행 경로가 달라도 동일한 compacted artifacts와 동일한 semantic verification artifacts가 주어지면 validation 결과는 동일하게 재현된다.
- 안정성 가설: 복수 실행 결과를 compacting하고 support/variants를 보존하면, 단일 확률적 실행보다 사람이 최종 검토하기 좋은 근거를 제공한다.
- 유용성 가설: 실제 과제 1건에서 공개 명세와 평가 rubric 사이의 검토할 만한 불일치를 surfaced 할 수 있다.
- compacting 가설: identity_basis(동일성 판정 알고리즘) 자체가 review 대상이 되어, 잘못된 compacting도 사람이 발견할 수 있다.

비즈니스 수요, 판매 모델, 외부 플랫폼 경쟁성은 본 PoC 완료 조건에 포함하지 않는다.

## 3. 원칙과 비범위

### 3.1 구현 원칙

- agent 출력은 후보이며 truth가 아니다.
- high severity assessment finding은 실행별 무결성 검사를 통과하고 compacted 데이터에 대한 deterministic rule에서만 생성한다. 단, 최종 review 전 finding은 `provisional`이며 외부 blocking verdict가 아니다.
- 실행별 candidate, 검증된 candidate, compacted artifact, 최종 human-reviewed 결과를 분리한다.
- **compacting은 분류·자동 채택이 아니다.** 동일 entry로 합쳐졌다는 사실(support/variants/identity_basis)을 모두 보존하며, 사람이 compacting 자체의 타당성을 검토할 수 있어야 한다.
- 각 phase는 이전 phase의 결과를 깨지 않고 기능을 추가한다.
- 실제 과제 원문 또는 비공개 rubric은 권한과 공개 범위를 확인한 뒤 fixture로 사용한다.
- **본 도구의 1차 실행 주체는 AI 에이전트다.** CLI 계약, 종료 코드, 출력 포맷, 에러 메시지는 모두 agent-consumable해야 한다. 사람은 최종 검토자로 참여하며, 검토 화면/리포트는 machine-readable 결과에서 파생한다.
- **Agent runner는 framework-agnostic protocol 위에 구현한다.** PoC는 Claude Agent SDK를 기본 구현으로 사용하되, Codex/Gemini/기타 에이전트 환경 통합은 단일 모듈 교체로 가능해야 한다.
- **하나의 판단을 하나의 agent run에 의존하지 않는다.** 동일 입력에 대한 복수 run을 개별 검증한 뒤 취합하고, 불일치는 숨기지 않고 review 대상으로 남긴다.
- **후보 생성과 의미 검증 agent 역할을 분리한다.** semantic verifier-agent는 원문 snapshot과 compacted link만 읽고 검증 제안을 저장하며, spec/rubric/trace 후보를 생성하거나 수정하지 않는다.
- **검사와 판정을 분리한다.** `check`는 diagnostic/finding을 생성하고, `gate`만 final review 이후의 외부 판정 상태를 반환한다.

### 3.2 최종 PoC 비범위

- 응시자 제출물 자동 채점
- 합격/불합격 추천
- 평가 결과 발송 시스템
- 법적 공정성 판정
- VectorDB, clustering, pattern provenance
- 여러 모델/프레임워크 간 consensus 자동 운영 (동일 configured runner의 복수 실행 취합은 PoC 범위에 포함)
- 시장 검증 또는 유료화 실험

### 3.3 Phase 0 비범위

- agent runner 실행 및 framework별 prompt/tool orchestration
- agent runner 모듈 (Phase 2에서 추가)
- `review_queue.json` 파일 생성 (Phase 2부터; Phase 0에는 데이터 계약만 정의)
- Time Budget Consistency
- Rubric Version Lock
- Disclosure/feedback 생성
- GitHub Action merge blocking

## 4. 최종 흐름

```text
caller agent (Claude Code / Codex / Gemini / ...)
  |
  | CLI invocation with structured I/O
  v
assessment-harness CLI
  |
  v
spec.md + rubric source
  |
  v
agent runner (framework-agnostic protocol)
  | - Claude Agent SDK (PoC default)
  | - tool set: read_spec_section, propose_spec_item,
  |             propose_trace_link, flag_ambiguity, ...
  | - multi-turn loop with recovery
  v
  +--> run_001/agent_trace.*
  +--> run_001/candidate artifacts -- run integrity check --+
  +--> run_002/agent_trace.*                               |
  +--> run_002/candidate artifacts -- run integrity check --+--> compacting
  +--> run_NNN/...                                         |      | (identity_basis,
                                                              v     support, variants)
                                                    compacted artifacts
                                                    + review_queue.json
                                                              |
                                                              v
                                                    semantic verifier-agent
                                                    (read-only, multi-run)
                                                              |
                                                              v
                                                    semantic_verifications.yaml
                                                    + verifier run records
                                                              |
                                                              v
                                                    deterministic validation core
                                                              |
                                                              +--> findings.json (provisional)
                                                              +--> report.md
                                                              |
                                                              v
                                                    final human review
                                                    (accept | hold | rerun | override)
                                                              |
                                                              v
                                                    external gate decision
```

`review_queue.json`은 다음을 통합 기록한다: 무결성 실패로 제외된 후보, compacting 시 identity 충돌이 명확하지 않은 variants, deterministic rule로 판정할 수 없는 모호성, 사람이 반드시 봐야 할 최종 검토 대상. 이는 `findings.json`과 분리한다. Phase 0에는 schema/계약만 정의하고 실제 파일 생성은 Phase 2부터 수행한다.

`compacting`은 분류가 아니다. 자동 채택은 발생하지 않으며, 모든 candidate(invalid run에서 제외된 것 제외)는 사람이 검토해야 할 entry로 남는다. 동일한 entity로 합쳐진 경우 `support`(어느 run에서 발견되었는지), `identity_basis`(동일성 판단 기준), `variants`(약간 다른 표현들)를 보존하여 compacting 자체의 타당성도 review 대상이 된다.

각 run은 독립된 trace를 가진다. 같은 입력에서도 agent path가 갈라질 수 있으므로 candidate는 trace 참조를 보존한다. validation core의 결정성은 compacted artifacts와 semantic verification artifacts가 입력으로 확정된 시점부터 시작하며, agent 단계의 비결정성은 run별 trace와 review_queue에 격리된다.

compacting 또는 verifier 실행 자체는 reproducibility를 보장하지 않는다 (입력 candidate 및 검증 제안 집합이 같지 않을 수 있으므로). invariant는 "동일 compacted artifacts + 동일 semantic verification artifacts → 동일 findings"에 한정한다.

trace는 목적별로 분리한다.

- `agent_trace.raw.jsonl`: SDK가 노출하는 원본 event/tool interaction 기록. 디버깅 및 하네스 개선용으로 별도 보호 저장한다.
- `agent_trace.audit.jsonl`: tool call, tool result reference, 산출 후보, 종료 사유, 관측 가능한 결정 요약을 담는 운영/audit 기록이다.

하네스는 모델의 비공개 내부 추론을 생성하도록 요구하지 않는다. SDK가 제공하는 원본 기록을 보관할지는 자격 증명, 비공개 rubric, 개인정보의 redaction/retention 정책과 함께 결정한다.

### 4.1 검사, 검토, 판정의 경계

하네스는 다음 네 종류의 상태를 혼합하지 않는다.

| Layer | 산출물 | 의미 | 외부 blocking 여부 |
|---|---|---|---|
| Integrity check | `integrity_diagnostics.json` | 입력/run이 해석 가능한 구조인지 | 실행 불가 입력이면 exit `2` |
| Semantic verification | `semantic_verifications.yaml` | verifier-agent가 제안한 trace 의미 상태 | 제안일 뿐이며 blocking 아님 |
| Assessment check | `findings.json` | compacted artifact에서 관찰된 규칙 위반 후보 | 최종 review 전에는 `provisional`, blocking 아님 |
| Final decision | `final_review/` + `gate` output | 사람이 확인한 최종 판단 | 이 단계에서만 외부 blocking 가능 |

Phase 0 규칙 회귀 테스트도 `provisional` finding의 존재와 severity를 검증한다. 일반 실행에서 exit `1`은 final review record를 입력받은 `gate`만 반환한다. agent multi-run 흐름에서 final review 이전의 high finding은 `status: provisional_findings`/exit `0`으로 반환하며, caller agent는 이를 실패 판정이 아니라 review/rerun 입력으로 취급한다.

최종 판정 명령:

```bash
assessment-harness gate \
  --final-review work/final_review/review.yaml \
  --policy config/policy.yaml \
  --output json
```

`gate`는 unresolved `hold`, `rerun_requested`, pending semantic verification이 있으면 `pending_review`를 반환한다. 사람이 수락하거나 명시적 override로 닫은 항목만 최종 pass/fail 산정에 반영한다.

## 5. 데이터 계약

### 5.0 Source Manifest와 Canonical ID

PoC는 DB/RAG 없이도 원문 grounding을 검증해야 한다. 입력 문서를 실행 시작 시 immutable snapshot으로 복사하고 manifest에 hash를 기록한다.

```yaml
project_id: assessment_demo
assessment_version: v1
documents:
  - document_id: DOC_SPEC
    role: candidate_spec
    path: work/source_snapshot/README.md
    sha256: "<sha256>"
  - document_id: DOC_RUBRIC
    role: evaluator_rubric
    path: work/source_snapshot/rubric.md
    sha256: "<sha256>"
```

각 run의 ID는 run-local reference일 뿐이다. `compact`는 spec/rubric item을 먼저 compacting하여 canonical item ID를 부여하고, 이후 trace link의 run-local reference를 canonical ID로 remap한다.

```yaml
id_map:
  - canonical_id: S1
    entity_type: spec_item
    run_refs:
      - { run_id: "run_..._a1b2", local_id: "S4" }
      - { run_id: "run_..._c3d4", local_id: "S1" }
```

향후 프로젝트/버전 관리가 추가되면 `project_id`, `assessment_version`, canonical ID lineage를 확장한다. PoC에서는 snapshot manifest, run-local reference, compacted canonical ID, `id_map`까지 구현 범위로 둔다.

### 5.1 Compacted Spec Item

```yaml
spec_items:
  - id: S1
    source: README.md
    section: "Requirements > Refund Policy"
    text: "Implement refund handling for cancelled orders."
    source_ref:
      document_id: DOC_SPEC
      start_line: 42
      end_line: 42
      quote: "Implement refund handling for cancelled orders."
    visibility: candidate_facing
    requirement_level: must
    support:
      total_valid_runs: 3
      found_in_runs: ["run_..._a1b2", "run_..._c3d4", "run_..._e5f6"]
    identity_basis: "source+section+normalized_text"
    variants: []
```

`source_ref`는 immutable source snapshot의 실제 line/span과 quote를 가리킨다. Rule 0는 `spec_item.text`끼리의 자기 일관성만 보지 않고 snapshot 원문에 대한 일치도 확인한다. `support`, `identity_basis`, `variants`는 compacting 산물이다. 단일 run에서만 발견되어도 entry는 그대로 보존되며, `found_in_runs` 길이가 1일 뿐이다 (자동 채택/배제 없음). `variants`는 동일성으로 판정되었으나 표현이 약간 다른 원본들의 목록이다. 빈 배열이면 모든 발견이 동일한 표현이다.

`requirement_level`:

- `must`: Rule 2의 coverage 대상
- `optional`: Rule 3의 optionality 대상
- `informational`: 평가 연결 의무가 없는 문맥

### 5.2 Compacted Rubric Item

```yaml
rubric_items:
  - id: R1
    title: "Refund policy handling"
    description: "Implements documented refund behavior."
    source_ref:
      document_id: DOC_RUBRIC
      start_line: 18
      end_line: 22
    evaluation_role: scored
    weight: 12
    evidence_required:
      - code
      - test
    support:
      total_valid_runs: 3
      found_in_runs: ["run_..._a1b2", "run_..._c3d4"]
    identity_basis: "title+normalized_description"
    variants:
      - run_id: "run_..._c3d4"
        title: "Refund policy handling"
        description: "Implements the documented refund behavior."   # 미세한 차이
```

`evaluation_role`:

- `scored`: 총점에 반영되며 Rule 1/Rule 3 대상
- `bonus`: 명시적 가산점. v0에서는 Rule 1 차단 대상에서 제외하고, orphan인 경우 `informational` finding으로 report에 표시한다.
- `qualitative`: 점수에 반영하지 않으며 Rule 1 대상이 아님

v0에서는 `scored`만 차단성 검사 대상으로 삼는다. `bonus`는 report에 표시하되 fail을 발생시키지 않는다.

`source_ref`는 rubric 원문 snapshot에 대한 anchor다. spec과 rubric 모두 원문 anchor를 가져야, agent가 존재하지 않는 requirement 또는 rubric item을 생성했을 때 Rule 0에서 배제할 수 있다.

### 5.3 Compacted Trace Link

```yaml
trace_links:
  - rubric_id: R1
    spec_ids:
      - S1
    rationale: "R1 evaluates the documented refund requirement in S1."
    evidence_quotes:
      - spec_id: S1
        quote: "Implement refund handling for cancelled orders."
        verification_mode: token_sequence
        source_ref:
          document_id: DOC_SPEC
          start_line: 42
          end_line: 42
    support:
      total_valid_runs: 3
      found_in_runs: ["run_..._a1b2", "run_..._c3d4", "run_..._e5f6"]
    identity_basis: "rubric_id+sorted(spec_ids)"
    variants: []
    semantic_status: pending_verification
    sources:
      - kind: agent_run
        run_id: "run_..._a1b2"
      - kind: agent_run
        run_id: "run_..._c3d4"
      - kind: agent_run
        run_id: "run_..._e5f6"
    reviewed_by: null
    reviewed_at: null
```

`spec_ids` 배열과 rubric item 여러 개의 반복 참조로 N:M 관계를 표현한다. 별도 trace link 구조를 사용하는 이유는 관계 수용량 때문이 아니라 link별 support 근거와 review 결과를 보존하기 위해서다.

필드 의미:

- `rationale`: trace의 제안 사유. PoC에서는 설명 자료이며 단독으로 신뢰하지 않는다. 복수 run에서 다른 rationale이 나오면 `variants`에 보존한다.
- `evidence_quotes`: 각 `spec_id`에 대응하는 spec 원문 발췌와 `verification_mode`. 모든 `spec_ids` 원소에 대응되어야 한다.
  - `verification_mode: token_sequence`: Rule 0가 strict substring 매칭으로 잔존·누락 정량 검증. 미리 삽입된 마커 검증에 사용 (예: "디버깅 섹션이 사라졌는지", "잘못된 코드가 잔존하는지" 같은 정량 확인 가능한 명시적 항목).
  - `verification_mode: ai_judgement` (PoC default): Rule 0는 reference integrity만 검증(spec_id 유효, quote 비어있지 않음). substring 매칭은 skip하고 `review_queue`에 `type: ai_judgement_pending` entry로 보내 semantic verifier-agent의 read-only 복수 검증과 최종 사람 검토를 거친다. 신규 구현·기능처럼 substring으로 검증 불가한 영역.
- `support`: compacting 산물. `total_valid_runs`는 invalid run을 제외한 전체 분모, `found_in_runs`는 이 link를 제안한 run ID 목록.
- `identity_basis`: 동일성 판단 알고리즘 식별자. 사람이 review에서 이 알고리즘이 적절했는지 평가할 수 있어야 한다 (예: `rubric_id+sorted(spec_ids)` vs `rubric_id+sorted(spec_ids)+normalized_rationale`).
- `variants`: 동일성으로 판정되었으나 표현이 약간 다른 원본들 (예: rationale 문장이 미세하게 다름). 빈 배열이면 모든 발견이 동일.
- `sources`: provenance 목록. `kind: agent_run` (run_id 포함), `kind: manual` (Phase 0/1), `kind: human_override` (최종 review에서 수정된 경우).
- `reviewed_by`, `reviewed_at`: 최종 human review audit metadata. Phase 0/2에서는 null이며, Phase 3 최종 시연 산출물에서는 필수다.
- `semantic_status`: link의 의미 검토 상태. `pending_verification | agent_supported | agent_rejected | agent_uncertain | human_accepted | human_rejected | human_overridden | rerun_requested` 중 하나이며, `ai_judgement` link는 final review 전 Rule 1의 confirmed coverage로 사용하지 않는다.

`evidence_quotes`의 substring 검사는 PoC에서 참조 무결성만 보장한다. 문장이 rubric의 의미를 충분히 공개하는지에 대한 semantic disclosure 판정은 장기 목표이며, PoC에서는 review_queue와 최종 human review 대상으로 남긴다.

### 5.3.1 Semantic Verification 상태와 채택 흐름

`ai_judgement` link가 많아질 경우 사람이 모든 link의 1차 의미 판단을 직접 수행하면 “사람은 마지막에 검토한다”는 목표가 약해진다. 따라서 semantic verifier-agent 단계를 Phase 2/3의 필수 흐름으로 채택한다.

```text
candidate-generation runs
  -> compact
  -> semantic verifier-agent runs (read-only, trace link별 supported/rejected/uncertain 제안)
  -> compact semantic verification proposals (자동 확정 없음)
  -> check (finding은 provisional)
  -> final human review
  -> gate
```

verifier-agent는 immutable source snapshot, compacted spec/rubric/trace link, evidence quote만 읽는다. 새 item/link를 생성하거나 기존 compacted artifact를 수정하지 않으며, 결과는 run별 기록과 `semantic_verifications.yaml`에 별도로 보존한다. verifier 결과 역시 복수 run의 제안이므로 불일치는 숨기지 않고 `support`/`variants`와 함께 최종 review 자료로 남긴다.

```yaml
semantic_verifications:
  - trace_link_id: T1
    status_proposal: agent_supported
    rationale: "Rubric criterion is explicitly disclosed by the referenced requirement."
    source_refs:
      - { document_id: DOC_SPEC, start_line: 42, end_line: 42 }
      - { document_id: DOC_RUBRIC, start_line: 18, end_line: 22 }
    support:
      total_valid_runs: 3
      found_in_runs: ["verify_..._a1b2", "verify_..._c3d4"]
    variants: []
```

`check`는 compacted trace link의 초기 `pending_verification` 상태와 이 별도 산출물을 함께 읽어 effective semantic status를 계산한다. 검증 제안을 원본 link에 덮어쓰지 않는다.

상태 의미:

| semantic_status | 의미 | Rule 1 coverage 기여 |
|---|---|---|
| `pending_verification` | compact 직후, 의미 확인 전 | confirmed coverage 아님 |
| `agent_supported` | verifier-agent가 근거와 함께 support | provisional coverage만 제공 |
| `agent_rejected` | verifier-agent가 link 근거 불충분을 제안 | coverage 아님, review 대상 |
| `agent_uncertain` | verifier-agent run이 갈리거나 판단 보류 | coverage 아님, review 대상 |
| `human_accepted` | 최종 reviewer가 수락 | final coverage |
| `human_rejected` | 최종 reviewer가 거절 | coverage 아님 |
| `human_overridden` | reviewer가 수정 후 채택 | final coverage |
| `rerun_requested` | 추가 검증 필요 | coverage 아님 |

이 방식이면 agent가 후보 생성과 의미 검증을 분리 수행하되, 최종 판정은 사람의 마지막 검토와 `gate`에만 남는다.

### 5.4 Candidate Artifact

```yaml
spec_item_candidates:
  - candidate_id: SC1
    proposed_item:
      id: S1
      text: "Implement refund handling for cancelled orders."
      requirement_level: must
      source_ref:
        document_id: DOC_SPEC
        start_line: 42
        end_line: 42
        quote: "Implement refund handling for cancelled orders."
    agent_runner: claude_agent_sdk
    agent_run_id: "run_2026-05-25T00:00:00Z_a1b2"
    source_excerpt: "Implement refund handling for cancelled orders."
    confidence: 0.82
    integrity_status: pending_check
```

`agent_runner`는 후보를 생성한 runner의 식별자다. `agent_run_id`는 같은 run의 모든 candidate가 공유하며, 해당 run의 trace로 역추적할 수 있다.

`integrity_status` enum:

- `pending_check`: integrity check 이전 초기 상태
- `validated`: 모든 Rule 0 항목 통과. compacting 대상이 됨
- `invalid_reference`: dangling rubric/spec id, evidence_quote spec_id 불일치 등
- `quote_mismatch`: evidence_quote가 spec_item.text의 substring이 아님
- `schema_violation`: candidate schema 위반
- `blocked_by_runner_error`: max_turns 초과, tool error, partial output 등 runner 측 사유

`validated` 외의 status는 모두 compacting/assessment 단계에서 제외되며, 해당 사유는 `integrity_diagnostics.json`과 `review_queue.json`에 보존된다.

Candidate artifact는 assessment rule 입력이 될 수 없다. 먼저 run integrity check를 통과(`validated`)하고 compacting을 거쳐 compacted artifact가 된 후 rule engine에 입력한다. 최종 human review는 rule engine의 결과와 compacting 근거를 함께 확인한다.

### 5.4.1 Agent Audit Trace

```jsonl
{"run_id":"run_2026-05-25T00:00:00Z_a1b2","turn":0,"role":"system","content_ref":"prompts/extract_v1.md"}
{"run_id":"run_2026-05-25T00:00:00Z_a1b2","turn":1,"role":"agent","tool_call":{"name":"read_spec_section","args":{"section":"Requirements"}}}
{"run_id":"run_2026-05-25T00:00:00Z_a1b2","turn":1,"role":"tool","name":"read_spec_section","result_ref":"work/trace/run_..._t1_result.txt"}
{"run_id":"run_2026-05-25T00:00:00Z_a1b2","turn":2,"role":"agent","tool_call":{"name":"propose_spec_item","args":{"id":"S1","text":"...","requirement_level":"must"}}}
{"run_id":"run_2026-05-25T00:00:00Z_a1b2","finish_reason":"complete","turns":7,"tool_call_count":12}
```

audit trace는 append-only JSONL이며, 각 candidate는 자신의 run_id로 trace 부분집합을 식별한다. 큰 tool 결과는 외부 file로 분리하고 trace에는 ref만 남긴다. raw trace 저장 계약은 Phase 2 진입 전 retention/redaction 정책과 함께 확정한다.

### 5.5 Finding

```json
{
  "type": "orphan_scored_rubric_item",
  "severity": "high",
  "decision_status": "provisional",
  "rubric_id": "R2",
  "message": "Scored rubric item R2 has no validated compacted candidate-facing trace link."
}
```

`decision_status`:

- `provisional`: final review 전 생성된 관찰 결과. 외부 blocking verdict가 아님.
- `confirmed`: final review와 `gate`가 반영한 최종 finding.
- `dismissed`: final review에서 오탐 또는 해소됨으로 처리된 finding.

### 5.6 Final Review Record

```yaml
review_id: "review_2026-05-25T11:30:00Z"
reviewer: "kdt"
reviewed_at: "2026-05-25T11:45:00Z"
inputs:
  compacted_dir: "work/compacted"
  findings_path: "work/findings.json"
  diagnostics_path: "work/integrity_diagnostics.json"
  review_queue_path: "work/compacted/review_queue.json"
  report_path: "work/report.md"
decisions:
  - target_type: trace_link
    target_key: { rubric_id: "R1", spec_ids: ["S1"] }
    action: accept
    note: "3/3 runs agree; identity_basis sound."
  - target_type: trace_link
    target_key: { rubric_id: "R7", spec_ids: ["S5"] }
    action: override
    note: "Quote misspelled in 2/2 runs; corrected from spec."
    override_payload:
      evidence_quotes:
        - spec_id: S5
          quote: "Handle edge-case refund for partially shipped orders."
  - target_type: spec_item
    target_key: { id: "S12" }
    action: hold
    note: "Single-run finding; needs another extract pass."
  - target_type: review_queue_entry
    target_key: { entry_id: "rq_42" }
    action: rerun_requested
    note: "Identity_basis collapsed two distinct requirements."
```

review action enum:

- `accept`: compacted entry를 그대로 채택
- `hold`: 결정 보류. 다음 review 사이클에서 재검토
- `rerun_requested`: 해당 영역에 대해 새 agent run 필요
- `override`: 사람이 직접 수정. 결과는 trace_link의 `sources`에 `kind: human_override`로 추가 기록되고, audit log에 reviewer/reviewed_at/reason이 보존된다.

`override`는 단순 오타·누락 수정에 사용한다. 해석이 갈리는 의미적 결정은 `rerun_requested`로 새 run을 요청하여 다시 compacting/review를 거치는 것이 원칙이다.

### 5.7 Review Queue Entry

`review_queue.json`은 다음 종류의 entry를 통합 기록한다.

```yaml
review_queue:
  - entry_id: "rq_001"
    type: invalid_run
    target: { run_id: "run_..._b9c0" }
    reason: "Rule 0 quote_mismatch on R3↔S2 (token_sequence)."
    related_runs: ["run_..._b9c0"]
    status: open

  - entry_id: "rq_002"
    type: ai_judgement_pending
    target:
      rubric_id: R7
      spec_ids: [S5]
      evidence_quote_index: 0
    reason: "verification_mode=ai_judgement; semantic disclosure check required."
    related_runs: ["run_..._a1b2", "run_..._c3d4"]
    status: open

  - entry_id: "rq_003"
    type: identity_collision
    target: { compacted_entry_key: "trace_link/R4_S6" }
    reason: "Two runs proposed structurally identical trace links with divergent rationale variants. Review identity_basis."
    related_runs: ["run_..._a1b2", "run_..._e5f6"]
    status: open

  - entry_id: "rq_004"
    type: low_support
    target: { compacted_entry_key: "spec_item/S12" }
    reason: "Single-run finding (1/3). Review whether to keep, hold, or rerun."
    related_runs: ["run_..._c3d4"]
    status: open

  - entry_id: "rq_005"
    type: semantic_disclosure
    target:
      rubric_id: R9
      spec_ids: [S8]
    reason: "rationale claims trace, but evidence_quote does not clearly disclose the rubric axis. Outside PoC auto-detect scope; raised for human review."
    related_runs: ["run_..._a1b2"]
    status: open
```

entry `type` enum:

- `invalid_run`: Rule 0 위반으로 run/입력이 평가에서 제외됨
- `ai_judgement_pending`: `verification_mode: ai_judgement`인 evidence의 verifier-agent 및 최종 사람 확인 대기
- `identity_collision`: compacting 중 동일성 판단이 애매한 variants
- `low_support`: 단일 run에서만 발견된 entry (자동 배제 없음 — 사람이 keep/hold/rerun 결정)
- `semantic_disclosure`: 장기 목표 영역(PoC 자동 검출 비범위)으로 사람이 봐야 할 항목

`status`: `open | held | rerun_pending | resolved`.

- `accept`, `override`: `resolved`
- `hold`: `held`
- `rerun_requested`: `rerun_pending`

후속 run/review에서 결론이 난 경우에만 `resolved`로 전환한다. entry는 audit 보존을 위해 삭제하지 않는다.

## 6. v0 결정 규칙

### Rule 0. Reference Integrity Diagnostic

- 조건 (어느 하나라도):
  - `spec_items` 또는 `rubric_items`의 `id`가 중복됨
  - `trace_links.rubric_id`가 존재하지 않는 rubric을 참조
  - `trace_links.spec_ids`가 존재하지 않는 spec을 참조
  - `trace_links.evidence_quotes[*].spec_id`가 같은 link의 `spec_ids`에 없음
  - `trace_links.evidence_quotes[*].quote`가 비어 있음
  - `spec_items[*].source_ref` 또는 `rubric_items[*].source_ref`가 snapshot manifest의 문서/hash/span에 맞지 않음
  - `trace_links.evidence_quotes[*].source_ref`가 referenced spec item의 snapshot anchor와 일치하지 않음
  - `trace_links.evidence_quotes[*].verification_mode == token_sequence`이고 `quote`가 referenced `spec_item.text`의 부분문자열이 아님
- 결과:
  - diagnostic artifact (`integrity_diagnostics.json`)에는 `high` integrity issue로 기록한다.
  - 해당 입력 또는 agent run은 invalid로 표시하고 Rule 1-3 평가 대상에서 제외한다.
  - 단일 `check` 명령의 프로세스 종료 코드는 input error인 `2`다.
  - **`findings.json`은 항상 생성한다** (caller agent의 파일 존재 가정 보호). invalid 시 내용:
    ```json
    {
      "status": "invalid_input",
      "findings": [],
      "diagnostics_ref": "integrity_diagnostics.json",
      "blocking_count": 0
    }
    ```
- verification_mode별 처리:
  - `token_sequence`: source snapshot의 anchor text와 evidence quote에 strict 비교를 적용한다. 비교는 normalized whitespace 기준의 토큰 시퀀스 동일성을 사용한다.
  - `ai_judgement` (PoC default): substring 매칭 skip. 해당 evidence는 `review_queue`에 `type: ai_judgement_pending` entry로 추가되어 semantic verifier-agent와 최종 사람 검토 대상이 된다. Rule 0의 input error 판정 대상이 아니다.
- 실행 지속 불가 여부: 예, 구조/참조 무결성 위반은 exit `2` input error다. 이는 `gate`의 외부 assessment blocking verdict가 아니다. 단, `ai_judgement` evidence의 의미 미확인은 input error가 아니다.
- 의도: 손으로 작성했거나 agent가 제안한 구조화 입력의 참조 무결성을 검사한다. semantic disclosure 판정은 PoC 비범위이며 review_queue를 통해 사람이 본다.

token_sequence 비교는 normalized whitespace 기준의 토큰 시퀀스 동일성을 사용한다. 더 느슨한 일치 정책(예: lemmatization)은 실제 과제 1건 적용 후 §13에 따라 조정한다.

### Rule 1. Scored Rubric Coverage

- 조건/결과:
  - compacted trace link 자체가 없음: `possible_orphan_scored_rubric_item`, `high`, `provisional`
  - link는 있으나 **어떤 link도** `semantic_status`가 `human_accepted` / `human_overridden`이 아님: `unconfirmed_trace_coverage`, `medium`, `provisional`. 이 분기는 pre-review 상태 (`pending_verification`, `agent_supported`, `agent_rejected`, `agent_uncertain`)와 post-review non-coverage 상태 (`human_rejected`, `rerun_requested`)를 모두 포함한다. §5.3.1 상태표에서 `Rule 1 coverage 기여`가 "coverage 아님"인 모든 상태가 여기에 해당한다.
  - final review 이후 위 medium provisional이 지속되고 reviewer가 orphan을 확정: `orphan_scored_rubric_item`, `high`, `confirmed`. 이 confirmed finding은 `check`가 아닌 `gate`만 발행한다 (`gate`는 final review record를 읽어 medium provisional을 high confirmed로 승급한다).
- 판정 상태: `human_accepted` / `human_overridden` link만 final coverage로 인정한다 (§5.3.1과 정합).
- 차단 대상: `gate`의 confirmed finding에서만 예
- 의도: 공개 명세와 무관한 점수 항목 탐지
- bonus 처리: `evaluation_role == bonus`인 orphan은 별도 `informational` finding으로 report에 표시하되 차단하지 않는다.

본 규칙의 final-coverage 경계 (`{human_accepted, human_overridden}`)는 Rule 1과 `gate`에서만 적용한다. Rule 2와 Rule 3은 `semantic_status`와 무관하게 §6의 본문 조건만으로 finding을 발화한다.

### Rule 2. Required Spec Coverage

- 조건: `requirement_level == must`이고 이를 참조하는 `scored` rubric item이 없음
- 결과: `medium` finding
- 판정 상태: final human review 전 `provisional`
- 차단 대상: 아니오
- 의도: 공개 핵심 요구사항이 실제 평가에서 누락되었는지 검토
- severity 근거: Rule 1과 정합성 결함의 무게는 같지만, "rubric에 없는 must spec"은 평가자가 의도적으로 제외했을 여지가 있어 차단까지는 무리다. 검토 권장(medium)으로 두고 실제 과제 적용 후 high 승격 여부를 §13에 따라 재검토한다.

### Rule 3. Optionality Consistency

- 조건: `requirement_level == optional`인 spec에만 trace된 `scored` rubric item의 `weight >= policy.optionality_mismatch.weight_threshold`
- 결과: `high` finding
- 판정 상태: final human review 전 `provisional`; `gate`의 confirmed finding에서만 차단
- 차단 대상: final confirmed 상태에서만 예
- 의도: 선택 항목이 실질적인 핵심 평가축으로 작동하는 경우 탐지

초기 임계값 `10`은 `policy.yaml`의 PoC 기본값이다. 실제 사례를 적용한 뒤 configurable policy 또는 상대 가중치 기준으로 바꿀지 결정한다.

### 후속 규칙

- Time Budget Consistency: effort 산정 방식이 정의된 뒤 추가
- Rubric Version Lock: locked baseline, round state, approval log 계약이 정의된 뒤 추가
- Disclosure Readiness: scoring evidence와 feedback 범위가 정의된 뒤 추가

## 7. 모듈 구성

```text
assessment_poc/
  pyproject.toml
  assessment_harness/
    __init__.py
    cli.py
    models.py
    schemas.py
    rules.py
    report.py
    final_review.py
    compacting.py       # union 기반 compacting (분류·자동 채택 없음, support/variants/identity_basis 보존)
    semantic_verification.py # read-only verifier run 결과 취합 및 상태 제안
    orchestrator.py
    gate.py              # final review 이후 외부 판정 전용
    agent_runners/
      __init__.py
      base.py            # AgentRunner protocol (framework-agnostic)
      manual.py          # Phase 0/1: 사람이 직접 작성한 compacted 입력 사용
      mock.py            # Phase 2: fixture YAML을 결정적으로 반환하는 fake runner (protocol contract test 전용)
      # claude_sdk.py    — Phase 2에서 추가 (PoC default)
      # codex.py         — 후속 MVP (실제 portability 검증용)
      # gemini.py        — 후속
    tools/
      __init__.py
      # spec_tools.py    — Phase 2: read_spec_section, list_sections
      # rubric_tools.py  — Phase 2: list_rubric_items, get_rubric_item
      # propose_tools.py — Phase 2: propose_spec_item, propose_trace_link, flag_ambiguity
  schemas/
    spec_items.schema.json
    rubric_items.schema.json
    trace_links.schema.json
    candidates.schema.json
    findings.schema.json
    integrity_diagnostics.schema.json
    review_queue.schema.json
    final_review.schema.json
    semantic_verifications.schema.json
    source_manifest.schema.json
    id_map.schema.json
    compacting.schema.json
    policy.schema.json        # rules, compacting, runs, verification 섹션 통합
    agent_trace.schema.json
    cli_output.schema.json
  fixtures/
    clean_assignment/
    orphan_scored_rubric/
    required_spec_unscored/
    optionality_mismatch/
    reference_integrity/      # Rule 0 회귀 fixture
    real_assignment/
  tests/
    test_models.py
    test_rules.py
    test_fixtures.py
    test_report.py
    # test_final_review.py          — Phase 3에서 추가
    # test_compacting.py            — Phase 2에서 추가 (identity_basis, support, variants)
    # test_semantic_verification.py — Phase 2에서 추가 (read-only verifier, proposal compacting)
    test_cli_output_contract.py # CLI의 agent-consumable JSON 출력 회귀
    # test_agent_runner_contract.py — Phase 2에서 추가
    # test_agent_trace_contract.py  — Phase 2에서 추가
    # test_orchestrator.py          — Phase 2에서 추가
```

`agent_runners/base.py`는 framework-agnostic protocol을 정의한다. PoC default 구현은 `claude_sdk.py`이며 Phase 2에 추가한다. `mock.py`는 fixture YAML을 결정적으로 반환하는 fake runner로, protocol contract test 전용이며 실제 평가에는 사용하지 않는다 (manual.py는 Phase 0/1의 사람 입력용, mock은 Phase 2의 contract 분리 증명용으로 역할이 다르다). 실제 Codex/Gemini 등 두 번째 framework 연동과 교체 비용 실증은 후속 MVP의 범위다.

`tools/`는 agent runner가 사용하는 framework-agnostic tool 정의를 둔다. tool 자체는 Python 함수이며, 각 runner가 자신의 framework가 요구하는 형태(JSON schema, function definition 등)로 등록한다.

정책 파일은 `config/policy.yaml` 하나로 통합한다. 섹션 구조:

```yaml
rules:
  optionality_mismatch:
    weight_threshold: 10
compacting:
  identity_basis:
    spec_item: "source+section+normalized_text"
    rubric_item: "title+normalized_description"
    trace_link: "rubric_id+sorted(spec_ids)"
runs:
  min_valid_runs: 2
  default_runs: 3
  max_runs: 7
verification:
  default_mode: ai_judgement
```

CLI는 `--policy config/policy.yaml` 하나로 모든 정책을 받는다. 이전 v1.4의 `--identity-basis-config` flag는 통합되어 제거된다.

## 8. CLI 계약

### Phase 0 명령

```bash
assessment-harness check \
  --spec-items fixtures/orphan_scored_rubric/spec_items.yaml \
  --rubric-items fixtures/orphan_scored_rubric/rubric_items.yaml \
  --trace-links fixtures/orphan_scored_rubric/trace_links.yaml \
  --source-manifest fixtures/orphan_scored_rubric/source_manifest.yaml \
  --policy fixtures/orphan_scored_rubric/policy.yaml \
  --out findings.json \
  --diagnostics-out integrity_diagnostics.json

assessment-harness report \
  --findings findings.json \
  --diagnostics integrity_diagnostics.json \
  --out report.md
```

`--source-manifest`는 Phase 0의 필수 인자다 (§5.0 / §5.1 / §11). 생략하면 `check`는 `status=invalid_input`, exit `2`, 진단 코드 `source_manifest_required`, next_action `provide_source_manifest`를 반환한다. argparse 단계에서 거부하지 않고 구조화된 envelope을 stdout에 출력하므로 caller agent는 인자 누락도 정상 흐름의 결과로 복구 가능하다.

Phase 0에서 `--semantic-verifications`가 생략된 경우 `token_sequence` evidence만 결정적으로 검사하며, `ai_judgement` trace link는 `pending_verification`으로 취급한다. Phase 2 이후 agent-assisted 흐름에서는 `verify` 산출물을 `check`/`report`/`review`에 명시적으로 전달한다.

`policy.yaml` 예시:

```yaml
rules:
  optionality_mismatch:
    weight_threshold: 10
verification:
  default_mode: ai_judgement
```

`--policy`가 생략되면 패키지에 포함된 기본 policy를 사용한다. fixture에는 명시적으로 포함시켜 회귀 시 정책 변동을 격리한다.

### 8.1 Agent-consumable 출력 계약

본 도구의 1차 user는 AI 에이전트다. 모든 명령은 다음을 만족해야 한다.

- **종료 코드 표준**:
  - `0`: 성공/검토 대기/provisional finding 존재; final blocking verdict 없음
  - `1`: `gate`가 final review 이후 confirmed blocking finding을 판정함
  - `2`: 입력/무결성 오류 (파일 없음, schema 위반, Rule 0 reference integrity 실패). 관련 diagnostic artifact는 가능한 범위에서 함께 생성한다.
  - `3`: 내부 오류 (runner 실패, tool error 등)
- **stdout / stderr 분리**:
  - stdout: machine-readable 산출물 (`--output json` 시 JSON, 기본은 사람용 요약)
  - stderr: progress, 경고, 디버그 메시지
- **`--output json` 플래그**: 모든 명령이 지원. 출력은 `schemas/cli_output.schema.json`을 따른다.
- **에러 메시지는 actionable**: 단순 "validation failed"가 아니라 "S5 referenced by R7.trace_links does not exist. Add S5 to spec_items.yaml or remove the reference from R7."처럼 다음 단계를 명시. 가능하면 `file:line` 포함.

```bash
assessment-harness check --output json ... 2>/dev/null
# stdout 예시 (요약):
# {
#   "status": "provisional_findings",
#   "blocking_count": 0,
#   "findings_path": "findings.json",
#   "report_path": "report.md",
#   "next_actions": [
#     {"type": "add_trace_link", "rubric_id": "R7"},
#     ...
#   ]
# }
```

`next_actions`는 caller 에이전트가 다음 tool call로 자연스럽게 이어갈 수 있는 hint다. PoC에서는 보수적으로 생성하고, 신뢰할 수 있는 종류만 포함한다.

### 8.1.1 Stable Core vs Informational Fields

`cli_output.schema.json`은 두 계층으로 나뉜다.

- **stable core**: 모든 명령 출력에 반드시 존재하며 변경 시 명시적 deprecation 절차를 거친다.
  - `status`: 명령 결과 (`success` | `provisional_findings` | `pending_review` | `fail` | `invalid_input` | `internal_error`)
  - `exit_code`: 종료 코드 (0/1/2/3)
  - `command`: 실행된 명령 이름
  - `next_actions`: caller agent용 hint 배열. 항목이 없으면 빈 배열로 항상 출력하며 형식은 stable.
- **informational**: 명령별 추가 필드. 사전 통지 없이 추가/변경 가능. schema에 `"stability": "informational"`로 annotation.

caller agent가 의존해도 안전한 것은 stable core뿐이다. 그 외 필드 사용은 §8.1.2 self-discovery 결과로만 한다. 안정 범위 확장은 실제 테스트 코드와 caller agent 사용 패턴이 누적된 후 점진적으로 승격한다.

### 8.1.2 Self-discovery Command

caller agent가 현재 contract를 매번 직접 확인할 수 있도록 introspection 명령을 제공한다.

```bash
assessment-harness schema --command check --output json
# stdout 예시:
# {
#   "command": "check",
#   "stable_core": ["status", "exit_code", "command", "next_actions"],
#   "informational": ["findings_path", "report_path", "blocking_count", "diagnostics_path"],
#   "exit_codes": {
#     "0": "success/provisional/pending; no final blocking verdict",
#     "1": "gate confirmed blocking finding after final review",
#     "2": "input/integrity error",
#     "3": "internal error"
#   },
#   "next_actions_types": ["add_trace_link", "review_orphan_rubric", ...]
# }
```

이 명령으로 caller agent는 문서 동기화 없이 현재 stable contract와 informational 필드, exit code 의미, `next_actions` 가능 type을 알 수 있다. 새 caller agent 통합은 이 introspection 결과부터 읽어 시작한다.

### 최종 PoC 명령

```bash
assessment-harness extract \
  --spec assignment/README.md \
  --rubric assignment/rubric.md \
  --runner claude_sdk \
  --runs 3 \
  --out-dir work/runs

assessment-harness compact \
  --runs-dir work/runs \
  --policy config/policy.yaml \
  --out-dir work/compacted

assessment-harness verify \
  --compacted-dir work/compacted \
  --source-manifest work/source_snapshot/manifest.yaml \
  --runner claude_sdk \
  --runs 3 \
  --policy config/policy.yaml \
  --out-dir work/semantic_verification

assessment-harness check \
  --spec-items work/compacted/spec_items.yaml \
  --rubric-items work/compacted/rubric_items.yaml \
  --trace-links work/compacted/trace_links.yaml \
  --semantic-verifications work/semantic_verification/semantic_verifications.yaml \
  --policy work/compacted/policy.yaml \
  --out work/findings.json \
  --diagnostics-out work/integrity_diagnostics.json

assessment-harness report \
  --findings work/findings.json \
  --diagnostics work/integrity_diagnostics.json \
  --semantic-verifications work/semantic_verification/semantic_verifications.yaml \
  --review-queue work/compacted/review_queue.json \
  --out work/report.md

assessment-harness review \
  --compacted-dir work/compacted \
  --findings work/findings.json \
  --diagnostics work/integrity_diagnostics.json \
  --semantic-verifications work/semantic_verification/semantic_verifications.yaml \
  --review-queue work/compacted/review_queue.json \
  --report work/report.md \
  --out-dir work/final_review

assessment-harness gate \
  --final-review work/final_review/review.yaml \
  --policy config/policy.yaml \
  --output json
```

`compact`는 union 기반이며 자동 분류·채택을 하지 않는다. 모든 유효 candidate를 entry로 보존하고, 동일성으로 판정된 것만 하나의 entry로 묶으면서 `support`/`identity_basis`/`variants`를 기록한다.

`verify`는 `ai_judgement` link에 대한 별도 read-only verifier-agent 실행이다. 각 run의 제안과 취합 결과를 저장하되 compacted artifact 또는 최종 판단을 수정하지 않는다.

`review`는 최종 human review를 기록한다. 중간 candidate는 사람이 승인하는 대신 자동 integrity check와 compacting을 거치며, 모든 entry(단일 run 발견 포함)와 compacting 근거가 review 자료에 보존되어야 한다.

`gate`는 외부 호출자가 pass/fail 또는 pending 상태를 소비하는 유일한 명령이다. `check`/`report`는 final review 전에는 provisional finding을 생성할 수 있으나 blocking exit `1`을 반환하지 않는다.

## 9. 단계별 구현 계획

### Phase 0 - Deterministic Validation Core

목표:

- agent 실행과 무관하게 compacted YAML을 검사하는 validation core를 완성한다.

작업:

- Python package 및 CLI scaffold 생성
- source manifest/id map/spec/rubric/trace/semantic verification/finding/policy 모델과 schema 작성
- Rule 0-3 구현
- JSON finding/integrity diagnostic과 Markdown report 생성
- 수동 fixture 작성

완료 기준:

- `clean_assignment`는 blocking finding 없이 통과한다.
- `reference_integrity`는 Rule 0 high integrity diagnostic을 생성하고 단일 `check`가 exit `2`로 종료된다 (중복 ID, dangling reference, quote non-substring 각 케이스).
- `orphan_scored_rubric`은 Rule 1 high `provisional` finding을 생성하되 final gate 이전에는 exit `1`로 차단하지 않는다.
- `required_spec_unscored`는 Rule 2 medium finding을 생성한다.
- `optionality_mismatch`는 Rule 3 high finding을 생성한다.
- 각 규칙 테스트는 under-strict와 over-strict 정상 사례를 함께 가진다.

### Phase 1 - Real Assignment Manual Run

목표:

- toy fixture 밖에서 deterministic core가 검토 가치가 있는 결과를 내는지 확인한다.

작업:

- (선결) 자료 사용 권한 확인: 본인 응시 라운드 자료라면 NDA/공개 정책 검토, 익명화 기준 합의. 권한 미확정 시 Phase 1 진입 보류.
- 사용 가능한 실제 과제 문서와 rubric을 수동으로 YAML화
- 원문 snapshot manifest와 각 item/quote의 source reference를 함께 작성
- 공개 불가 원문은 커밋하지 않고, 필요 시 익명화된 구조화 fixture만 저장
- 생성 finding을 사람이 리뷰하여 true issue, false positive, policy question으로 분류

완료 기준:

- 실제 과제 1건이 end-to-end manual flow로 report까지 생성된다.
- finding별로 사람이 판단한 결과와 필요한 schema/rule 수정사항이 기록된다.

### Phase 2 - Agent Runner & Compacting

목표:

- 최종 PoC에 필수인 candidate-generation 및 semantic-verifier 복수 실행 단계를 작동하도록 한다.
- 실행별 산출물의 검증, compacting, read-only semantic verification 경계를 검증한다.

작업:

- `AgentRunner` protocol 정의 (framework-agnostic; `run(spec_path, rubric_path, tools, max_turns, policy) -> AgentRunResult`)
- Tool 집합 정의: `read_spec_section`, `list_sections`, `list_rubric_items`, `get_rubric_item`, `propose_spec_item`, `propose_trace_link`, `flag_ambiguity`
- Claude Agent SDK 기반 첫 runner 구현 (PoC default)
- 동일 입력에 대해 복수 독립 run을 실행하는 orchestrator 구현 (`--runs N`, 기본 3, 최대 7)
- compacting 모듈 구현: union 기반, 자동 채택/분류 없음, support/identity_basis/variants 보존
- run-local item ID를 compacted canonical ID로 remap하고 `id_map` provenance를 저장
- identity_basis 알고리즘 초기 구현 (§13 Phase 2/3 결정 사항에 따라 선정)
- mock runner contract test로 protocol 경계가 특정 SDK 구현에 결합되지 않았음을 확인
- `agent_trace.raw.jsonl`/`agent_trace.audit.jsonl` 산출 및 저장 방침 정의 (큰 tool 결과는 외부 파일로 분리, audit trace에는 ref)
- 회복 정책: max_turns 초과, tool error, schema-invalid output은 run 단위로 격리하고 audit trace의 `finish_reason`에 사유 기록. `integrity_status: blocked_by_runner_error`로 표시.
- candidate에 `agent_runner`, `agent_run_id` 필드 채움
- partial run failure 정책 적용: 최소 유효 run 수(`min_valid_runs`) 미달 시 동작 정의 (§13)
- `ai_judgement` link를 별도 read-only verifier-agent 복수 run으로 검토하여 `semantic_status` 제안을 생성
- verifier run별 결과와 취합 결과를 `semantic_verifications.yaml`에 저장하되 compacted link를 덮어쓰지 않음

완료 기준:

- 실제 과제 입력을 복수 실행하여 run별 candidate artifacts와 audit trace가 함께 생성된다.
- Rule 0에 실패한 run은 diagnostic을 남기고 compacting 대상에서 제외된다.
- 유효한 run들에서 compacted artifacts와 review_queue가 생성된다.
- 단일 run에서만 발견된 entry도 compacted artifacts에 보존된다 (자동 배제 없음 확인).
- 같은 compacted YAML과 같은 semantic verification artifact를 사용하면 Manual flow와 Agent-assisted flow의 findings/report가 동일하다.
- Runner contract test가 Claude SDK runner 외에 최소 한 개의 mock runner로 통과한다 (protocol 분리 확인).
- compacting 결과의 `identity_basis`가 audit 가능한 형태로 저장되고, fixture 기반 테스트로 알고리즘 변경 영향이 회귀 검증된다.
- 서로 다른 run-local ID가 같은 compacted canonical ID와 trace link로 remap되는 fixture가 통과한다.
- verifier-agent가 새 spec/rubric/trace candidate를 생성하지 않는 read-only 계약 테스트가 통과하고, 서로 다른 verifier 제안은 취합 산출물에 보존된다.

### Phase 3 - Final Human Review and PoC Demonstration

목표:

- agent runner 복수 실행부터 deterministic report와 최종 human review까지 전체 흐름을 시연한다.
- caller agent 시나리오에서도 종단간 작동을 확인한다.

작업:

- compacted result -> final review 기록 명령 구현
- review action 4가지(`accept` / `hold` / `rerun_requested` / `override`) 처리 및 audit metadata (`reviewed_by`, `reviewed_at`) 저장
- `override` 발생 시 trace_link/spec_item/rubric_item의 `sources`에 `kind: human_override` 추가 기록
- 제외되거나 단일 run 발견 candidate의 retention 정책 적용 (§13에 따라 결정)
- 실제 과제에 대해 agent-generated compacted artifacts, semantic verifier 제안, finding/review_queue를 사람이 최종 검토
- 최종 findings/report 산출 및 결과 기록
- final review record에 기반한 `gate` 판정 산출
- (선택) caller agent 시나리오 1건 시연: Claude Code가 본 도구를 CLI로 호출하여 end-to-end 수행

완료 기준:

- `extract -> compact -> verify -> check -> report -> review -> gate` 흐름이 실제 과제 1건에서 실행된다.
- 무결성 실패 또는 단일 run 발견 항목이 review 자료에서 추적 가능하고, invalid candidate가 deterministic assessment 판정으로 유입되지 않음이 확인된다.
- review에서 `override` 액션 1건 이상 시연되며, 결과가 `sources`에 별도 provenance로 기록됨이 확인된다.
- high assessment finding은 agent confidence가 아니라 compacted YAML과 Rule 1-3만으로 재현된다. Rule 0 diagnostic은 별도로 추적된다.
- mock runner 계약 테스트로 protocol 경계를 확인한다. 실제 두 번째 framework 통합 실증은 후속 MVP 범위로 남긴다.
- `gate`만 confirmed blocking finding에 대해 exit `1`을 반환하고, review 전 `check`는 provisional 상태를 유지한다.
- 모든 CLI 명령이 `--output json` 모드에서 `cli_output.schema.json`을 통과한다.

## 10. 테스트 전략

### 10.1 Deterministic 규칙 테스트

각 규칙에는 두 방향의 회귀 방어를 둔다.

| Rule | Under-strict guard | Over-strict guard |
|---|---|---|
| Rule 0 | 중복 ID, dangling reference, quote non-substring의 diagnostic/exit `2` 처리를 놓치면 실패 | 정상 substring 및 유효한 reference를 invalid로 잡으면 실패 |
| Rule 1 | scored orphan이 provisional/confirmed lifecycle에서 누락되면 실패 | pending semantic link를 final coverage로 처리하거나 human-accepted trace를 orphan으로 잡으면 실패 |
| Rule 2 | must spec 미평가를 놓치면 실패 | optional/informational 미평가를 finding으로 잡으면 실패 |
| Rule 3 | optional 고가중치 항목을 놓치면 실패 | 임계값 미만 또는 must 연결 항목을 mismatch로 잡으면 실패 |

### 10.2 Agent Runner 계약 테스트

- runner 출력은 candidate schema로 normalize되어야 한다.
- malformed runner output (schema 위반, partial output)은 compacted artifact나 assessment finding을 만들지 않고 run 단계에서 격리되어야 한다.
- confidence 값은 deterministic severity 결과를 변경하지 않아야 한다.
- 모든 runner는 동일한 `AgentRunner` protocol을 만족해야 한다 (mock runner로 contract test 작성, PoC에서는 protocol 분리만 확인).
- audit trace는 schema validation을 통과하고, 모든 candidate의 `agent_run_id`가 audit trace에 존재해야 한다.
- max_turns 초과 / tool error 시 partial candidate는 `integrity_status: blocked_by_runner_error`로 표시되고, audit trace의 `finish_reason`에 사유가 남아야 한다.
- 복수 유효 run의 compacting 결과는 `compacting.schema.json`에 따라 재현 가능하게 출력되어야 한다. 같은 입력 candidate 집합과 같은 identity_basis 설정에서 같은 compacted artifacts가 생성되어야 한다.
- compacting은 자동 채택/분류를 하지 않는다. 단일 run에서만 발견된 entry도 compacted artifacts에 포함되어야 한다.
- 동일 entity에 대한 run-local ID 차이가 canonical ID remap으로 정규화되어야 한다.
- verifier-agent는 immutable snapshot과 compacted link만 읽고 `semantic_verifications.yaml`을 생성해야 하며, candidate artifacts를 변경하면 실패한다.
- verifier run 간 `supported`/`rejected`/`uncertain` 차이는 자동 확정되지 않고 variants 또는 review 대상에 보존되어야 한다.

### 10.3 CLI 출력 계약 테스트

- 모든 명령의 `--output json` 출력은 `cli_output.schema.json`을 통과해야 한다.
- 종료 코드는 §8.1의 정의를 따라야 한다 (0/1/2/3).
- stderr 메시지가 stdout JSON에 섞이지 않아야 한다.
- 에러 메시지는 `next_actions` 또는 actionable hint를 포함해야 한다 (regex/keyword 기반 lint).
- `check`는 pre-review high finding에서 `provisional_findings`/exit `0`을 반환하고, `gate`만 confirmed high finding에서 exit `1`을 반환해야 한다.

### 10.4 End-to-End 테스트

- Manual fixture와 Agent-assisted flow가 동일한 compacted artifact 및 semantic verification artifact를 입력으로 받으면 같은 report를 생성해야 한다.
- 실제 과제 실행 기록에는 run별 candidate/trace, compacted artifacts, verifier run/result, review_queue, findings, report, final review 산출물이 남아야 한다.

## 11. 검증 산출물

Phase 0:

- source snapshot manifest와 item/quote `source_ref`
- `findings.json`
- `integrity_diagnostics.json`
- `report.md`
- fixture별 expected findings
- 테스트 결과

최종 PoC:

- agent run별 candidate artifacts와 분리 저장된 trace (`agent_trace.raw.jsonl`, `agent_trace.audit.jsonl`)
- compacted artifacts (`support`, `identity_basis`, `variants` 포함)와 canonical `id_map`
- semantic verifier run 기록과 취합된 `semantic_verifications.yaml`
- `review_queue.json` (무결성 실패 사유, 모호성, 검토 대상 통합)
- `integrity_diagnostics.json`
- deterministic `findings.json`
- human-readable `report.md`
- final human review 기록 (`final_review/`)
- external `gate` decision 출력
- 실제 과제 적용 결과 요약

## 12. 구현 순서와 게이트

| 단계 | 진입 조건 | 완료 확인 | 다음 단계 차단 조건 |
|---|---|---|---|
| Phase 0 | 본 계획서 기준 승인 | Rule 0-3 fixture/test 통과 | 데이터 계약이 흔들리거나 규칙 결과가 재현되지 않음 |
| Phase 1 | Phase 0 통과, 실제 자료 사용 권한 확인 완료, 익명화 기준 합의 | 실제 manual report 생성 | 자료 사용 권한 미확정 또는 익명화 기준 불일치 |
| Phase 2 | compacted 데이터 구조 안정화, identity_basis 알고리즘 선정 | 실제 candidate/verifier multi-run 생성·격리·compacting | run output이 schema로 안정 정규화되지 않거나 identity_basis가 미정 |
| Phase 3 | Phase 2 runner/compacting 동작 | 실제 E2E demo/report/final review/`gate` decision 생성 | invalid run 데이터가 판정에 섞임 |

## 13. 남은 결정

Phase 0 전 확정 (v1.5에서 채택됨):

1. ✓ 본 계획서와 `v2.1`을 PoC 구현의 기준 문서로 채택 (§1 우선순위 그대로).
2. ✓ Rule 0 evidence_quote 검증은 entry별 `verification_mode`로 분기: `token_sequence`(strict substring)와 `ai_judgement`(reference integrity만, 의미 검증은 review_queue로). PoC default는 `ai_judgement`. 정량 검증 필요한 명시적 marker만 `token_sequence`로 opt-in. (§5.3, §6 Rule 0)
3. ✓ `cli_output.schema.json`은 stable core(`status`/`exit_code`/`command`/`next_actions`)와 informational 두 계층으로 분리. 안정 범위 확장은 실제 테스트 코드와 caller agent 사용 패턴을 보며 점진 확립. `assessment-harness schema --command <name>` self-discovery 명령으로 caller agent가 매번 직접 contract 확인 가능. (§8.1.1, §8.1.2)

Phase 0/공통 계약으로 v1.6에서 채택:

1. ✓ `check`는 final verdict를 내리지 않고 `provisional` findings만 산출한다. 외부 blocking verdict는 final review 이후 `gate` 명령만 반환한다.
2. ✓ 원문 grounding은 DB/RAG 없이 immutable source snapshot manifest, document hash, line/span `source_ref`로 구현한다. RAG/DB화는 후속 범위다.
3. ✓ 독립 run의 local ID는 compact 단계에서 canonical ID로 remap하고 `id_map` provenance를 보존한다. 프로젝트/버전 계층은 후속 확장 가능하게 둔다.

Phase 2/3 공통 계약으로 v1.7에서 채택:

1. ✓ `ai_judgement` semantic 확인은 별도 read-only verifier-agent가 복수 run으로 제안하고, 최종 human review가 승인/거절/override한다.
2. ✓ verifier-agent 산출물은 compacted artifact를 수정하지 않고 별도 `semantic_verifications.yaml`과 run 기록으로 보존한다.

Phase 1 전 확정할 사항:

1. 첫 실제 과제로 사용할 자료의 위치, NDA/공개 정책, 익명화 범위.

Phase 2/3 전 확정할 사항:

1. Phase 2에서 연결할 Claude Agent SDK 자격 증명 제공 방식.
2. compacting의 `identity_basis` 알고리즘:
   - spec_item: 후보군 예시 — `source+section+normalized_text`, `source+normalized_text`, `normalized_text only`
   - rubric_item: 후보군 예시 — `title+normalized_description`, `normalized_title only`
   - trace_link: 후보군 예시 — `rubric_id+sorted(spec_ids)`, `rubric_id+sorted(spec_ids)+normalized_rationale`
   - PoC default 권고: 가장 보수적(상세) 기준으로 시작 → 너무 자주 갈라지면 완화
3. 복수 run 정책: 기본 run 수(권고 3), 최대 run 수(권고 7), 최소 유효 run 수(`min_valid_runs`, 권고 2). 미달 시 동작: error 종료 vs warn-and-proceed.
4. 최종 human review의 `override` 사용 범위: 단순 오타·누락만인지, 의미적 결정도 허용할지. 의미적 override는 새 run 권장.
5. `trace_link.rationale`의 최소 length 또는 quality guard 적용 여부.
6. 제외/단일 발견 agent candidate 및 raw trace의 retention/redaction/access 정책.
7. Agent runner `max_turns`, cost ceiling 정책.
8. Tool 호출 사이드이펙트 정책: tool은 read-only로 시작할지, propose 계열이 candidate file에 직접 쓸지 vs runner가 collect 후 일괄 출력할지.
9. 복수 run의 형태: PoC는 candidate-generation role과 채택된 read-only semantic-verifier role 각각에서 동일 설정의 독립 반복으로 한정. 추가 critic/resolver 역할은 후속 MVP 범위.
10. reproducibility 범위: "같은 candidate 집합 + 같은 identity_basis 설정 → 같은 compacted artifacts", "같은 compacted artifacts + 같은 semantic verification artifacts → 같은 findings"까지만 보장한다. 같은 spec/rubric을 N회 실행했을 때 같은 candidate 또는 verifier 제안이 나오는 것은 보장하지 않는다.

구현하며 조정 가능한 사항:

- `config/policy.yaml`의 `rules.optionality_mismatch.weight_threshold` 후속 조정
- bonus orphan의 `informational` finding 표시 형식
- Rule 2 severity의 high 승격 여부 (실제 과제 적용 후 재검토)
- report 출력 문구와 정렬 방식
- `next_actions` 출력의 종류 및 신뢰도 정책
- `verification.default_mode`를 `token_sequence`로 승격할지 여부 (정량 검증 사용처 누적 후)
- mock runner의 fixture 응답 형식 확장
- `cli_output.schema.json`의 informational → stable core 승격 정책

## 14. 최종 완료 정의

다음 조건을 모두 만족해야 PoC를 완료로 본다.

- source snapshot으로 grounding된 compacted YAML과 semantic verification artifact를 입력으로 Rule 0-3을 재현 가능하게 실행한다.
- 수동 fixture와 실제 과제 manual run이 완료된다.
- Claude Agent SDK 기반 agent runner가 복수 run의 spec/rubric/trace 후보와 분리된 trace(`agent_trace.raw.jsonl` + `agent_trace.audit.jsonl`)를 생성한다.
- 하네스가 각 run을 검증하고 유효한 결과를 compacted artifacts(union, 자동 채택 없음)와 review_queue로 정리한다.
- 하네스가 run-local ID를 canonical ID로 remap하고 provenance를 보존한다.
- 별도 read-only verifier-agent가 `ai_judgement` trace link를 복수 실행으로 검토하고, 그 제안과 불일치를 원본 link와 분리해 저장한다.
- 사람이 마지막에 compacted artifacts, semantic verifier 제안, compacting 근거(`identity_basis`/`support`/`variants`), 무결성 제외 내역, findings, report를 검토한다.
- 실제 과제 1건에서 `extract -> compact -> verify -> check -> report -> review -> gate`가 실행되며, `review`에서 `override` 액션 1건 이상이 시연된다.
- final review 이전 finding은 provisional이며, 외부 blocking 판정은 `gate`에서만 발생한다.
- 동일한 compacted artifacts와 semantic verification artifacts에 대해서는 agent runner 사용 여부와 무관하게 findings/report가 동일하다.
- mock runner contract test가 통과하여 framework-agnostic protocol 경계를 확인한다. 실제 다른 framework 연동 실증은 후속 MVP에서 수행한다.
- 모든 CLI 명령이 `--output json` 모드에서 agent-consumable 출력 계약(§8.1)을 만족한다.

즉, agent runner 없는 Phase 0은 기반 공사이며, 복수 candidate-generation/verifier run의 검증·compacting과 최종 human review까지 이어지는 실행이 없는 상태는 최종 PoC 완료가 아니다.

---

## 15. 변경 이력

### v1.9 (2026-05-26)

핵심 변경: **§6 Rule 1의 `unconfirmed_trace_coverage` 분기를 §5.3.1 상태표와 정합화**.

- **이유**: v1.8까지의 §6 Rule 1은 `unconfirmed_trace_coverage` 발화 대상으로 `pending_verification` / `agent_supported` / `agent_rejected` / `agent_uncertain`만 열거했지만, §5.3.1 상태표는 `human_rejected`와 `rerun_requested`도 "coverage 아님"으로 분류한다. 두 절이 어긋나서, post-review non-coverage 상태가 `check` 단계에서 어떤 finding을 emit하는지 spec gap이 있었다. 구현 (Phase 0 iteration 2 slice 2)이 §5.3.1과 자동화 흐름의 의도에 맞게 두 상태도 medium provisional로 처리하고 있었으나, plan 본문은 그대로였다.
- **§6 Rule 1 본문 갱신**: medium provisional 분기를 "어떤 link도 `human_accepted` / `human_overridden`이 아닌 경우"로 일반화하여 §5.3.1과 정합. 셋째 분기 (confirmed orphan)는 `gate`가 final review 이후 medium provisional을 high confirmed로 승급한다는 흐름을 명시.
- **경계 적용 범위 명시**: final-coverage 경계 (`{human_accepted, human_overridden}`)는 Rule 1과 `gate`에서만 사용한다. Rule 2/3은 `semantic_status`와 무관하게 §6의 본문 조건만으로 finding을 발화한다 (HANDOFF Active Decisions 정정과 정합).
- **구현 영향 없음**: rules.py / cli.py / 테스트는 이미 v1.9 본문과 일치한다. 본 v1.9는 plan 본문이 구현·§5.3.1과 정합하도록 spec gap을 닫는 변경이다.

### v1.8 (2026-05-26)

핵심 변경: **`--source-manifest`를 Phase 0 `check`의 필수 인자로 확정**.

- **이유**: §5.0 ("PoC는 DB/RAG 없이도 원문 grounding을 검증해야 한다"), §5.1 ("Rule 0는 snapshot 원문에 대한 일치도 확인한다"), §11 ("Phase 0 산출물: source snapshot manifest와 item/quote `source_ref`") 세 절이 manifest를 입력 계약의 필수 요소로 못박는다. v1.7까지의 §8 CLI 예시가 manifest를 생략하고 있어 내부 충돌이 있었으나, 자동화 흐름은 `extract` 단계에서 manifest를 자동 생성하는 모델이므로 "필수" 쪽이 spec 정신과 운영 흐름 모두에 정합한다.
- **CLI 동작**: `--source-manifest` 누락 시 argparse는 통과시키되 `_cmd_check`가 즉시 `status=invalid_input` / exit `2` / 진단 코드 `source_manifest_required` (severity `high`) / next_action `provide_source_manifest`를 반환한다. 이렇게 처리해야 caller agent가 stdout JSON envelope을 읽고 자동 복구할 수 있다 (argparse `required=True`는 usage text를 stderr로 내보내어 contract 위반).
- **§8 예시 갱신**: §8 Phase 0 CLI 예시에 `--source-manifest` 인자 추가.
- **fixture 갱신**: `fixtures/orphan_scored_rubric/`과 `fixtures/reference_integrity/`에 `source/spec.md`, `source/rubric.md`, `source_manifest.yaml`을 추가하여 grounded 입력으로 변환. `clean_assignment`는 이미 grounded.

### v1.7 (2026-05-25)

핵심 변경: **semantic verifier-agent를 권고안에서 최종 PoC 필수 단계로 채택**.

- **검증 역할 분리**: candidate-generation agent와 별도 read-only semantic verifier-agent를 분리하고, verifier도 복수 run으로 실행한다.
- **보존 경계**: verifier 제안은 compacted trace link를 덮어쓰지 않고 `semantic_verifications.yaml`과 run 기록으로 저장한다.
- **실행 흐름 확정**: 최종 흐름을 `extract -> compact -> verify -> check -> report -> review -> gate`로 확정한다.
- **사람의 역할 유지**: verifier의 `agent_supported`/`agent_rejected`/`agent_uncertain`은 제안이며, final coverage 및 외부 판정은 human review와 `gate`에서만 확정된다.

### v1.6 (2026-05-25)

핵심 변경: **검사 결과와 외부 판정을 분리하고, 원문 grounding 및 canonical ID 경계를 명시**.

- **판정 경계**: `check` finding은 final review 전 `provisional`이며 외부 blocking 판정이 아님. final review record를 읽는 `gate` 명령만 confirmed pass/fail/pending 결과를 반환한다.
- **semantic 상태**: trace link에 `semantic_status` lifecycle을 추가. `ai_judgement` link는 human-accepted/overridden 전에는 final Rule 1 coverage로 취급하지 않는다.
- **권고 단계**: semantic 검토 부담을 줄이기 위해 별도 verifier-agent run이 `agent_supported` 등 상태를 제안하는 흐름을 Phase 2/3 미결정 사항으로 추가.
- **원문 grounding**: DB/RAG 없이 immutable document snapshot, `sha256`, line/span `source_ref`로 item과 quote를 원문에 anchor한다.
- **ID lineage**: 독립 run의 local ID를 compact 과정에서 canonical ID로 remap하고 `id_map`을 보존한다. 향후 프로젝트/버전 관리 확장 경계를 마련한다.
- **review 상태**: `hold`와 `rerun_requested`를 resolved로 닫지 않고 `held`/`rerun_pending` 상태로 보존한다.
- **CLI/schema 보완**: `gate.py`, source/id/compacting schema를 모듈 계획에 추가하고, stable `next_actions`는 항상 배열로 출력하도록 정리했다.

### v1.5 (2026-05-25)

핵심 변경: **검증 모드 entry별 분기 + CLI 안정 contract 분리 + 정책 파일 통합 + 보조 명세 보강**.

- **verification_mode 도입** (§5.3, §6 Rule 0): evidence_quote별로 `token_sequence`(strict substring) vs `ai_judgement`(reference integrity만 + review_queue로) 분기. PoC default `ai_judgement`. 정량 검증 가능한 명시적 marker만 opt-in으로 `token_sequence`.
- **Rule 0 findings.json 처리 명세화** (§6 Rule 0): invalid 시에도 `findings.json` 항상 생성하여 caller agent의 파일 존재 가정 보호. 내용은 `{"status":"invalid_input","findings":[],...}`.
- **review_queue entry schema 신설** (§5.7): 5종 entry type — `invalid_run` / `ai_judgement_pending` / `identity_collision` / `low_support` / `semantic_disclosure`. resolved는 삭제 없이 status 표시.
- **Mock runner 자리 신설** (§7): `agent_runners/mock.py`. fixture YAML 결정적 반환, protocol contract test 전용. `manual.py`(사람 입력용)와 역할 분리.
- **정책 파일 통합** (§7, §8): `config/policy.yaml` 단일 파일에 `rules`/`compacting`/`runs`/`verification` 섹션 통합. CLI는 `--policy` 단일 flag. v1.4의 `--identity-basis-config` 제거.
- **CLI Stable Core / Introspection** (§8.1.1, §8.1.2): stable core 4개 필드 명시(`status`, `exit_code`, `command`, `next_actions`) + informational 분리. `assessment-harness schema --command <name>` introspection 명령으로 caller agent self-discovery 지원.
- **§13 결정 정리**: Phase 0 전 결정 3건 모두 채택 표시. 구현 중 조정 사항에 verification mode/informational 승격 정책 추가.

### v1.4 (2026-05-25)

핵심 시프트: **aggregation의 의미가 "분류된 합집합"에서 "audit 가능한 compacting"으로 재정의**. 자동 채택/분류 없음. 단일 run 발견 entry도 보존되며, compacting 자체의 타당성도 review 대상.

- **개념 변경**: `aggregation` → `compacting`. union 기반, 자동 분류·채택 없음. `consolidated artifacts` → `compacted artifacts`로 용어 통일.
- **데이터 계약**: §5.1/5.2/5.3에 `support`(`total_valid_runs`, `found_in_runs`), `identity_basis`, `variants` 추가. trace_link의 `consolidation_status` 제거.
- **`integrity_status` enum 명시** (보강 A): `pending_check` / `validated` / `invalid_reference` / `quote_mismatch` / `schema_violation` / `blocked_by_runner_error` (§5.4).
- **§5.6 Final Review Record 신설** (보강 D): review action 4가지(`accept`/`hold`/`rerun_requested`/`override`), `override`는 sources에 `kind: human_override`로 audit.
- **명명 통일** (보강 B): "disagreement queue" 표현 모두 `review_queue`로 통일.
- **partial run failure 자리 마련** (보강 C): §13 Phase 2/3 결정 3번에 `min_valid_runs`, 미달 시 동작 명시.
- **CLI**: `aggregate` → `compact` 명령으로 변경. `--identity-basis-config` flag 추가. `--consolidated-dir` → `--compacted-dir`.
- **모듈**: `aggregation.py` → `compacting.py`, `aggregation.schema.json` → `compacting.schema.json`, `test_aggregation.py` → `test_compacting.py`.
- **§13 결정 사항 정리**: quorum/합의 임계값 제거(자동 채택 없음). identity_basis 알고리즘 후보군, 복수 run 형태(동일 반복), reproducibility 범위, override 사용 범위 추가.
- **흐름 다이어그램** (§4): compacting 단계 명시, "정답 없음, 모든 entry 보존" 의미 반영. aggregation reproducibility는 미보장(같은 compacted YAML → 같은 findings만 보장).
- **Phase 2/3 작업** 재정렬: compacting 구현, identity_basis 알고리즘 선정, `override` 시연 추가.

### v1.3 (2026-05-25)

핵심 정리: **단일 agent run의 후보를 사람이 중간 승인하는 흐름이 아니라, 복수 agent run을 검증·취합한 뒤 사람이 최종 결과만 review하는 하네스**로 정의한다.

- **목표/경계 변경**: 중간 `human approval`을 제거하고 `multi-run -> integrity check -> aggregation -> deterministic validation -> final human review` 흐름으로 교체.
- **데이터 계약**: `approved` 중심 용어를 `consolidated`/`reviewed` 중심으로 교체. candidate는 `integrity_status`로 실행별 검증 상태를 갖는다.
- **무결성 이중 처리**: Rule 0 위반은 최종 리뷰용 diagnostic에 남기면서 해당 입력/run은 invalid로 제외하고 단일 `check`에서는 exit `2`로 처리.
- **trace 정책**: raw trace와 audit trace를 분리하며, 내부 추론 생성을 요구하지 않고 관측 가능한 기록 및 SDK 제공 원본의 보호 저장만 다룬다.
- **CLI 흐름**: `extract --runs N -> aggregate -> check -> report -> review`로 변경.
- **portability 범위**: PoC는 mock runner로 protocol 분리를 확인하고, 실제 두 번째 framework 연동 실증은 후속 MVP로 이관.
- **남은 핵심 결정**: aggregation quorum/합의 기준, 최종 review 결과 상태, raw trace 보관 정책.

### v1.2 (2026-05-25)

핵심 시프트: **본 도구의 1차 user는 AI 에이전트**이며, LLM 통합 부분은 **framework-agnostic agent runner protocol** 위에 구현한다. PoC default는 Claude Agent SDK, 후속 통합은 단일 모듈 교체로 가능.

- **원칙 추가**: §3.1에 agent-as-user 원칙과 framework portability 원칙 명시.
- **흐름 재정의**: §4 최종 흐름의 진입점에 caller agent를 명시. "LLM adapter"가 아닌 "agent runner (multi-turn, tool use)"로 변경. `agent_trace.jsonl` 산출물 추가.
- **데이터 계약**: candidate에 `agent_runner`, `agent_run_id` 필드 추가. `source_model`은 제거. §5.4.1 `agent_trace.jsonl` schema 신설.
- **모듈 구성**: `adapters/` → `agent_runners/` 명명. `tools/` 디렉토리 신설 (framework-agnostic tool 정의). `cli_output.schema.json`, `agent_trace.schema.json` 추가. Phase 0에서 `test_cli_output_contract.py` 포함.
- **CLI 계약**: §8.1 agent-consumable 출력 표준 신설 — 종료 코드(0/1/2/3), `--output json`, stdout/stderr 분리, actionable error, `next_actions` hint.
- **Phase 2 재정의**: §9 Phase 2를 "Agent Runner & Candidate Generation"으로 개편. AgentRunner protocol, tool 집합, Claude SDK runner, framework portability contract test, agent_trace 저장, 회복 정책.
- **Phase 3 보강**: caller agent 시연 시나리오, framework 교체 portability 증명, `--output json` 계약 통과 추가.
- **테스트**: §10.2를 Agent Runner 계약 테스트로 개편. §10.3 CLI 출력 계약 테스트 신설. trace replay, partial output 격리 케이스 추가.
- **남은 결정**: 7~9번 추가 (CLI schema 안정 범위, max_turns/cost ceiling, tool side-effect 정책).
- **최종 완료 정의**: agent_trace 산출, framework portability contract test, CLI `--output json` 계약 통과를 완료 조건에 추가.

### v1.1 (2026-05-25)

교차 검토(상대 AI + 자체 검토) 반영. 주요 변경:

- **데이터 계약**: `trace_links`에 `evidence_quotes`, `source`, `approved_by`, `approved_at` 추가 (§5.3). rationale 단독 신뢰의 위험을 객관 증거(spec 원문 발췌)로 보완.
- **규칙**: Rule 0 (Reference Integrity) 신설, blocking high (§6). ID 중복/dangling reference/quote non-substring을 통합 검사.
- **규칙 정책**: Rule 1의 bonus 처리 명시 (orphan 시 `informational`만, 차단 안 함), Rule 2 severity 근거 1줄 추가 (§5.2, §6).
- **CLI**: `--policy` flag 추가, `policy.yaml`로 임계값 외부화 (§6, §8).
- **모듈**: Phase 0에서 `llm_provider.py`, `test_llm_adapter_contract.py` 제외하고 Phase 2부터 생성 (§3.3, §7).
- **데이터 계약 vs 파일 생성 분리**: `review_queue.json`은 schema/계약만 Phase 0에 정의하고 실제 파일 생성은 Phase 2부터 (§3.3, §4).
- **게이트**: Phase 1 진입 조건에 자료 사용 권한 확인과 익명화 기준 합의 명시 (§9, §12).
- **남은 결정**: trace_link rationale quality guard, evidence_quote substring 비교 정책, 거절 candidate retention 정책 추가 (§13).

### v1.0 (2026-05-25)

초안. v2.1 ideation을 PoC 구현 명세로 변환. 문서 우선순위 §1로 명시, `evaluation_role` 의미 계약 §5.2, Time Budget / Version Lock은 후속 규칙으로 분리 §6.
