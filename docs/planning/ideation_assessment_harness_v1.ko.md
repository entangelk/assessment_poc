<p align="center">
  <a href="./ideation_assessment_harness_v1.md"><img src="https://img.shields.io/badge/Language-EN-6B7280?style=for-the-badge" alt="English"></a>
  <a href="./ideation_assessment_harness_v1.ko.md"><img src="https://img.shields.io/badge/Language-KO-111111?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Ideation — 채용 과제 평가 하네스 (Assessment Harness)

> 작성: 2026-05-22 / 본 repo 의 한 라운드 응시 + 평가 자료 정독 후 떠오른 아이디에이션
> 성격: 미완성 사고. 구체 시스템 사양이 아니라 "이런 방향이 가능할까" 의 질문 모음

## 0. 작성 동기

한 라운드의 응시 + 회사에서 공유한 회고 자료 (`dfinite_applicant_share_v1/00_FINAL_REPORT.md`) 를 정독한 결과, 평가 프로세스 안에 몇 가지 **시스템적 약점이 패턴으로 반복**된다는 인상을 받았다. 개별 평가자의 실수가 아니라 **평가를 운영하는 인프라 자체의 공백** 처럼 보이는 영역들.

이 약점들은 채용 측이 AI 도구를 도입했다고는 하지만 채점·검수·통계 운영이 여전히 사람·문서 중심으로 느슨하게 돌아간다는 사인 처럼 읽혔다. "테스트 하네스" 가 코드 변경의 안전망이 되듯, **채용 평가에도 비슷한 형태의 하네스** 가 가치 있을 수 있다는 가설.

본 문서는 그 가설을 펼쳐본 사고 메모.

---

## 1. 관찰된 문제 카테고리

본 라운드에서 직접 관찰된 사례 (회사·라운드 무관, 일반화 가능한 패턴).

### A. 정보 비대칭 — README 와 실제 평가의 거리

- README 권장 시간 (10~18h) ↔ 회고 자료가 시사한 작업 깊이 (26개 unique 시도 list, 분포 정점 2~5일)
- "선택" 으로 표기된 Phase 가 실제로는 결정적 차별 시그널
- 평가 기준 (B7 자체 발견, D6 환불 정책 충돌) 이 README 명세에 명시되지 않음

응시자는 README 를 기준으로 우선순위를 정하지만, 평가는 그 외부에 있는 기준으로 이루어짐. 같은 시간 투자에 누가 무엇을 알았느냐의 운에 가까운 결과가 나옴.

### B. 통계 방법론 — N 작은 경우의 시각화·해석

- 응시자 N 이 작은 환경 (한 라운드 13~20명 추정) 에서 시각화·정규화 표현이 자연스러운 의미를 가지는가
- spline / 박스플롯 / 정규화 같은 표현은 N 이 일정 크기 이상일 때 해석이 안정. 작은 N 에서는 표현 선택 자체가 결과 인상을 좌우

### C. 사후 평가 기준 추가

- README 에 없던 항목이 사후 평가에서 가중치를 가짐 (B7, D6 같은 자율 발견 항목)
- 응시자 입장에서는 사전 안내되지 않은 기준으로 평가되는 셈

### D. IP/출처 처리 — Cookbook 외부화

- 한 응시자의 누적 작업 방식 (CookBook) 이 평가 자료의 "외부 상위 cluster 결정적 시그널" list 로 익명 노출
- 사전 공유 동의 절차가 없는 상태에서 외부화

### E. 평가축의 selection bias

- "Library 버그 발견·workaround" 같이 응시자가 마음만 먹으면 발생 가능한 영역을 결정적 시그널로 잡으면, 평가가 실력보다 운·재량에 의해 좌우되는 형태
- 평가축 자체가 게임이론적으로 안정한가의 검토 부재

---

## 2. 가설

"테스트 하네스" 의 컨셉을 채용 평가에 옮긴다 — **정해진 rubric 을 일관되게 적용하고, 정합성·재현성·투명성을 시스템 수준에서 보장하는 인프라**.

핵심 질문 3개:

1. **평가 전 정합성 (Coherence)** — README 와 rubric 이 1:1 매핑되는가
2. **평가 중 재현성 (Reproducibility)** — 같은 입력에 같은 score 가 나오는가
3. **평가 후 투명성 (Transparency)** — 응시자가 본인 결과를 디버깅 가능한가

이 세 축이 모두 만족되면, 위 §1 의 문제 카테고리 다수가 자연 해소될 것으로 보인다.

---

## 3. 하네스가 다뤄야 할 layer

이론적 구획이며, 실제 시스템은 일부만 구현해도 가치 있을 수 있다. Layer 0~5 는 baseline 필수 영역, Layer 6+ 는 스케일이 커진 시점에 도입하는 옵셔널 영역.

### Layer 0: 2중 SoT (Foundational)

평가 시스템의 모든 일관성은 **두 개의 Source of Truth 가 분리되고 cross-validated 된다는 전제** 위에서 성립한다.

- **Spec SoT** — 응시자에게 공개되는 진실 (README, BR, PRD, data_model)
- **Rubric SoT** — 평가자가 사용하는 진실 (scoring criteria, weight matrix, evaluator instructions)
- **Invariant**: Rubric SoT 의 모든 항목은 Spec SoT 에 trace 되어야 한다. orphan rubric 항목 (Spec 에 없는 평가 기준) 은 자동 차단.
- **Versioning**: 두 SoT 는 semver 로 함께 관리. Rubric 변경 시 Spec coverage 자동 재검증.

이 layer 가 강제되면 사후 평가 기준 추가 (§1.C) 와 정보 비대칭 (§1.A) 의 다수가 **구조적으로 불가능**해진다. orphan rubric 항목으로 자동 검출되기 때문.

기능 예시: rubric YAML 변경 PR 마다 CI 에서 spec coverage 자동 검증. 매핑 실패 시 PR merge 차단.

### Layer 1: 시험 전 정합성 검사 (Pre-flight)

Layer 0 위에서 동작하는 검증 layer.

- README ↔ rubric 항목 1:1 매핑 점검 (Layer 0 invariant 의 정기 실행)
- 평가축 사전 공개 (자율 발견, 명세 외 영역 포함)
- 권장 시간 ↔ rubric 깊이의 정합성 (예: rubric 항목 수 × 평균 작업 시간 ≤ 권장 시간)
- 챗봇 같은 "선택" 항목의 실제 가중치 명시

기능 예시: 라운드 시작 전에 Spec SoT + Rubric SoT 를 입력 받아 매핑 누락·가중치 모순·시간 예산 위반 등을 자동 리포트.

### Layer 2: 채점 재현성 (Reproducibility)

- Machine-checkable 항목은 LLM/regex/AST 기반 자동 채점
- AI 채점 결과는 항상 human override loop 동반
- Multi-evaluator consensus 측정 (κ statistic 등)
- 평가 결과에 audit trail (어느 rubric 버전, 어느 평가자, 어느 AI 출력 의지)

기능 예시: 응시자 제출물 + rubric 입력 → JSON score sheet 출력, 각 항목별 evidence (file:line) 첨부.

### Layer 3: 통계 유효성 (Statistical Validity)

- 응시자 N 에 적절한 시각화 자동 선택 (N<10 시 individual dot, N<30 시 박스플롯+점, N≥30 시 분포곡선)
- 신뢰구간 표시 강제
- Bias detection — anchor effect (앞 응시자 점수가 뒷 응시자에 영향), halo effect, selection bias

기능 예시: score 데이터셋 + 시각화 요청 → 유효 시각화만 출력, 무효한 시각화는 경고 후 거부.

### Layer 4: 사후 투명성 (Post-test Disclosure)

- 응시자 피드백 채널 (anonymous + identified 두 종류)
- 평가축 사후 공개 표준 (어느 항목이 어느 가중치였는지)
- 외부 공유 자료에 출처 표기 절차 — 특정 응시자 자산이 anchor 가 된 경우 사전 동의 또는 일반화

기능 예시: 평가 종료 후 응시자에게 자동 송부되는 score breakdown, audit trail 일부, 피드백 form.

### Layer 5: 회기간 개선 (Cross-round Learning)

- Rubric versioning (semver) — Layer 0 의 SoT versioning 과 동기
- 응시자 피드백 → rubric 개선 PR
- 회기간 score 분포 비교 (rubric 변경으로 인한 drift 측정)

기능 예시: rubric repo + change log + 매 라운드 종료 후 retrospective PR template.

### Layer 6: 대용량 처리 + Pattern Provenance (Optional, Scale-gated)

응시자 N 이 회사 스케일 (라운드당 50+ 응시자, 응시자당 100+ 파일, 라운드 누적 1000+ 응시자) 에 도달했을 때 도입을 검토하는 옵셔널 layer. **소규모 라운드 (N≤30) 에서는 도입 가치보다 운영 비용이 큼.**

- **VectorDB** — code/doc embedding 저장, semantic search 인덱싱
- **Cross-applicant Pattern Miner** — embedding cluster + attribution. §4.9 같은 "unique 시도 list" 가 사람 큐레이션이 아니라 자동 추출
- **Pattern Provenance** — 특정 패턴의 최초 등장 응시자 추적. IP/cookbook (§1.D) 문제의 자동 해결
- **Outlier Detection** — 의미적으로 다른 접근을 자동 감지 → human review 큐로 라우팅. selection bias (§1.E) 완화
- **RAG-augmented LLM Grader** — LLM grader 가 응시자 코드 채점 시 다른 응시자의 유사 패턴을 context 로 참조. 비교적 평가 가능

#### 도입 시 주의 — 임베딩 모델 의존성 취약점

VectorDB 기반 기능들은 **임베딩 모델의 성능·특성에 직접 의존**하며, 이로 인해 하네스 자체의 reproducibility 와 평가 일관성에 새 취약점이 생긴다.

| 취약점 | 발생 원인 | 영향 |
|---|---|---|
| **모델 교체 시 cluster 결과 drift** | 모델 A 와 모델 B 의 embedding space 가 다름 | 동일 응시자의 "유사도 X%" 가 모델 따라 달라짐 |
| **Pattern provenance 의 retroactive 변동** | 새 모델 적용 시 과거 라운드 attribution 재계산 결과 변경 가능 | "이 패턴은 응시자 X 가 먼저" 의 진실값 흔들림 |
| **하네스 파라미터 수 증가** | 모델별 cluster threshold, similarity cutoff, outlier z-score 등 다수 파라미터 등장 | 운영자가 "어떤 임계값이 옳은가" 의 책임을 떠안음. rubric 외부에 채점 영향 변수 발생 |
| **Domain-specific 모델 한계** | code 영역 embedding (CodeBERT, GraphCodeBERT 등) 은 일반 텍스트 모델과 다른 strength·weakness | 모델 선택 자체가 평가 편향 source 가 됨 |

완화 방안:

- 임베딩 모델 버전 핀 + 라운드 종료까지 변경 금지 (Layer 0 의 SoT versioning 과 동일 원칙)
- 모델 교체 시 baseline 라운드 데이터로 회귀 검증 (모델 A 채점 ≈ 모델 B 채점 within tolerance)
- VectorDB 유사도는 **단일 진실값이 아닌 신호 중 하나** 로 취급. 최종 평가는 항상 Layer 2 의 deterministic check + LLM grader + human override 조합
- 모델 의존 파라미터 (threshold, cutoff) 도 SoT 에 포함시켜 audit log 와 함께 보관

---

## 4. 개념 아키텍처 스케치

```
┌─────────────────────────────────────────────────────────┐
│  Layer 0: 2중 SoT (Foundational)                        │
│  ┌──────────────────┐    ┌──────────────────────┐       │
│  │  Spec SoT        │◄──►│  Rubric SoT          │       │
│  │  README+BR+PRD   │    │  scoring+weights     │       │
│  │  +data_model     │    │  +evaluator instr.   │       │
│  └────────┬─────────┘    └──────────┬───────────┘       │
│           │  Invariant: rubric ⊆ spec                   │
│           └──────────────┬───────────┘                  │
│                          │ (CI cross-validates)         │
└──────────────────────────┼──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2-5: Core Pipeline                               │
│                                                         │
│  [Applicant Repo Ingestion]                             │
│        │                                                │
│        ├── AST/static analyzer                          │
│        ├── Document chunker                             │
│        └── (optional → Layer 6 embedding)               │
│        │                                                │
│        ▼                                                │
│  [Evaluator Pipeline]                                   │
│    ├── Static checker (deterministic)                   │
│    ├── LLM grader (rubric prompt)                       │
│    ├── Human reviewer (override)                        │
│    └── Audit log writer                                 │
│        │                                                │
│        ▼                                                │
│  [Aggregator]                                           │
│        │                                                │
│        ├── Statistical Validator (Layer 3)              │
│        ├── Disclosure Layer (Layer 4)                   │
│        └── Round Retro Loop (Layer 5)                   │
└─────────────────────────────────────────────────────────┘

   ↓ (scale-gated, N≥30 ~ 50 라운드 도달 시)

┌─────────────────────────────────────────────────────────┐
│  Layer 6: 대용량 + Pattern Provenance (Optional)        │
│                                                         │
│  [Embedding Generator]                                  │
│        │ (model version pinned in Layer 0 SoT)          │
│        ▼                                                │
│  [VectorDB]                                             │
│        │                                                │
│        ├── Cross-applicant Pattern Miner                │
│        ├── Pattern Provenance Tracker                   │
│        ├── Outlier Detector → Human Review Queue        │
│        └── RAG context for LLM Grader                   │
│                                                         │
│  ⚠ Vulnerability: embedding model 의존성 (§3 Layer 6)   │
└─────────────────────────────────────────────────────────┘
```

각 컴포넌트는 독립 도입 가능.

- **가장 작은 시작**: Layer 0 만 — 2중 SoT 분리 + invariant CI 검증. 이것만으로도 §1.A·§1.C 의 80% 해소.
- **다음 단계**: Layer 2-5 — LLM grader + 통계 validator + disclosure + round retro
- **스케일 시점**: Layer 6 — VectorDB 와 pattern provenance. 단 임베딩 모델 의존성 취약점 (§3 Layer 6 끝부분) 을 함께 도입.

---

## 5. 단계별 도입 가능성

| 단계 | 도입 대상 | 비용 추정 | 해결 카테고리 | 스케일 게이트 |
|---|---|---|---|---|
| Phase 0 | 2중 SoT 분리 + invariant CI 검증 | 낮음 (Spec/Rubric YAML + 매핑 검증 스크립트) | §1.A 정보 비대칭, §1.C 사후 기준 추가 | — |
| Phase 1 | Pre-flight 검증 (시간 예산·가중치 모순 등) | 낮음 | §1.A | — |
| Phase 2 | LLM 보조 채점 + human override | 중 (LLM prompt 설계 + UI) | §1.E selection bias | — |
| Phase 3 | 통계 validator | 낮음 (N 기반 시각화 라이브러리) | §1.B 통계 방법론 | — |
| Phase 4 | Disclosure standard | 중 (응시자 리포트 템플릿 + 피드백 채널) | §1.D IP, §1.A 정보 비대칭 | — |
| Phase 5 | 회기간 학습 loop | 높음 (조직 프로세스 변경 필요) | 전체 | — |
| **Phase 6** | **VectorDB + Pattern Miner + RAG grader** (옵셔널) | **높음 (인프라 + 임베딩 모델 운영 + 파라미터 audit)** | **§1.D pattern provenance 자동화, §1.E 자동 outlier 감지** | **N≥30~50 / 회사 누적 1000+ 응시자 도달 시 검토** |

**Phase 0+3 만 도입해도 본 라운드에서 관찰된 약점의 다수가 해소**될 것으로 보임. Phase 6 은 스케일에 도달했을 때만 비용 정당화 가능.

---

## 6. 기대 효과 (방향성)

- **응시자 측**: 명확한 기준, 합리적 시간 안배, 사후 학습 가치
- **평가자 측**: 일관성, 재현성, audit trail, 회기간 개선 fuel
- **회사 측**: 채용 quality 향상, 외부 reputation, 법적 리스크 감소 (사후 평가 기준 추가 같은 issue 차단)
- **AI 도구 측**: 채점 보조 도구의 hallucination 추적 가능, 인간 평가자 보완 역할 확립

---

## 7. 한계 및 미지수

- **정성 평가의 자동화 한계** — 코드 품질·문서 깊이 같은 영역은 LLM 채점도 한계 있음. 완전 자동화는 비현실적
- **인간 평가자의 직관 가치** — 완전 알고리즘 평가가 항상 더 공정한가는 별개 질문. 직관 + 알고리즘의 어디까지 섞을지 design question
- **N 작은 환경의 본질적 통계 한계** — 하네스로도 N=15 의 통계 노이즈는 못 줄임. "통계 표시 자체를 줄이는" 방향이 더 정직할 수도
- **임베딩 모델 의존성 (Phase 6 도입 시)** — VectorDB layer 는 모델 성능에 직접 종속되며, 모델 교체 시 cluster·provenance 결과 drift, 운영자가 떠안는 파라미터 (threshold, cutoff) 증가, domain-specific 모델 편향 등 새 취약점이 생긴다. §3 Layer 6 끝부분의 완화 방안 (모델 버전 핀, 회귀 검증, 신호 중 하나로 취급) 을 함께 도입해야 함
- **IP/cookbook 처리** — 법무·HR 협업 필요. 기술 단독으로 해결 불가
- **조직 문화** — Phase 5 회기간 학습은 사람 사이의 피드백 받아들이는 문화가 전제

---

## 8. 다음 단계 (Optional)

본 ideation 을 더 구체화하고 싶다면:

- **Phase 1 PoC** — sample assignment + rubric YAML + 매핑 점검 스크립트만 만드는 데 1~2 일. 본인 사이드 프로젝트로 가능
- **외부 문헌 참고** — `Talent Analytics`, `Work Sample Tests` 학술 자료 / `Hiring Plan` (Lou Adler) / Google `re:Work` 채용 자료
- **유사 도구 조사** — Codility / HackerRank / Coderbyte 같은 기존 채용 플랫폼이 위 5개 layer 중 어디를 다루고 어디를 비웠는지

본인이 다음 채용 라운드에 응시할 때 또는 다른 회사가 채용 평가 시스템 컨설팅 의뢰가 들어왔을 때 활용 가능한 사고 자산으로 남겨둠.

---

## 9. 메모

본 문서는 ideation 단계라 다음 사이클에 갱신될 수 있음. 핵심은 **"평가 방법론도 코드처럼 검증 가능한 인프라가 있어야 한다"** 는 가설 — 그 가설이 맞다면 위 5 layer 중 가장 작은 단위부터 시도해볼 만함.
