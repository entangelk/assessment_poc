# DeskHive 백오피스 PoC — 인수인계 과제

안녕하세요, 지원자님.

이 과제는 시험이 아닙니다. **함께 일할 수 있는지 서로 확인하는 과정**입니다.
정답을 맞히는 것보다, 문제를 어떻게 파악하고 어떤 판단을 내리는지가 더 중요합니다.

> 이 저장소는 Assessment Spec Harness PoC의 **합성 예시(synthetic example)**입니다.
> 실제 회사·지원자 데이터가 아니며, 결함은 시연을 위해 의도적으로 심어 두었습니다.

---

## 과제 배경

**DeskHive**는 한 수도권 도시에서 5개 공유 오피스 허브를 운영하는 가상의 코워킹
멤버십 사업자입니다. 월 단위 데스크 멤버십, 데이 패스, 멤버십 동결(freeze),
회의실 호스트 추천을 통합한 백오피스 PoC를 개발 중이었으나, 담당 개발자(AI 코딩
도구를 활용)가 퇴사하면서 인수인계가 필요한 상황입니다.

지원자님이 이 프로젝트를 인수받아 **결함을 진단·수정**하고, **검증 체계를
설계**하며, **CTO에게 보고할 종합 보고서를 작성**하는 것이 핵심입니다.

---

## 환경 실행 (Phase 0)

의존성은 FastAPI / uvicorn 둘뿐입니다.

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8000

# 또는 Docker
docker compose up
```

헬스체크와 회원 목록이 응답하면 정상입니다.

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/members
```

> 의존성 없이 5개 증상을 한 번에 재현하려면:
> `python3 scripts/show_symptoms.py` (표준 라이브러리만 사용)

---

## Phase 1: 결함 진단 + 수정 [필수]

운영팀이 보고한 5개 증상입니다. 각 결함을 진단하고 수정해 주세요.

| ID | 증상 | 확인 방법 | 기대 결과 |
|----|------|-----------|-----------|
| **B1** | 비활성 회원의 소진 예상일이 `Infinity`로 표시됨 | `GET /api/members/M1/detail` | `estimated_exhaustion_days`가 유한한 값 |
| **B2** | 동결 이력이 있는 회원의 만료일이 연장되지 않음 | `GET /api/members/M2/detail` | `expiry_date`가 동결 일수만큼 연장 |
| **B3** | 잔여 패스가 무료/유료 구분 없이 합산됨 | `GET /api/passes/remaining/M3` | 무료·유료 패스가 분리되어 보고 |
| **B4** | 월별 신규 가입 수치가 회원 목록과 불일치 | `GET /api/analytics/new-members?year=2026&month=2` | 해당 월(KST) 실제 가입자 수와 일치 |
| **B5** | 호스트 추천이 특정 호스트만 반복 | `GET /api/matching/recommend/M1` | 조건에 맞는 호스트가 다양하게 추천 |

비즈니스 규칙은 [docs/business_rules.md](docs/business_rules.md), 데이터 구조는
[docs/data_model.md](docs/data_model.md)를 참고하세요.

### 진행 방법

1. 위 API를 직접 호출하여 증상을 확인합니다.
2. 코드를 추적하여 근본 원인을 파악합니다.
3. 수정 후 동일 API로 결과를 검증합니다.
4. 각 결함의 진단 과정을 `diagnosis_log.md`에 기록합니다.

---

## Phase 2: 검증 체계 설계 [필수]

수정한 결함이 재발하지 않도록 검증 체계를 설계하고 구현합니다.

- 각 결함(B1~B5)마다 최소 1개의 pytest 테스트를 `tests/`에 작성합니다.
- `pytest`로 전체 통과(green)되어야 합니다.
- 검증 설계의 의도와 구조를 `verification_design.md`에 정리합니다.

---

## Phase 3: 대시보드 개선 [선택]

여유가 있으면 운영 대시보드에 회의실 점유율 요약 패널을 추가해도 좋습니다.
이 Phase는 선택이며, 건너뛰어도 제출은 완료된 것으로 봅니다.

---

## Phase 4: 종합 보고서 [필수]

CTO에게 보고하는 형식으로 `report.md`를 작성합니다.
현황 요약 / 결함 분석 / 검증 전략 / 기술 부채 / 개선 제안을 포함해 주세요.

---

## 제출물 체크리스트

- [ ] 수정 코드 (의미 있는 단위의 Git 커밋 이력)
- [ ] 진단 기록 `diagnosis_log.md`
- [ ] 검증 설계서 `verification_design.md`
- [ ] 검증 코드 `tests/` (pytest 실행 가능)
- [ ] 종합 보고서 `report.md`
- [ ] **AI 사용 이력** (대화·세션 로그 등) — 필수 제출물

> AI 도구의 출력을 그대로 제출하는 것이 아니라, AI의 결과를 **검증하고 판단한
> 과정**이 평가의 핵심입니다.
