# DeskHive 데이터 모델

PoC는 데이터베이스 없이 `app/seed.py`의 인메모리 데이터를 사용한다. 모델
정의는 `app/models.py`에 있다.

## Member

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | str | 회원 식별자 (예: `M1`) |
| `name` | str | 이름 |
| `joined_at` | datetime | 가입 시각 (**UTC 저장**) |
| `credit_balance` | float | 크레딧 잔액 |
| `membership_start` | date | 멤버십 시작일 |
| `membership_duration_days` | int | 멤버십 기간(일) |
| `free_trial_passes` | int | 무료 체험 패스 수 |
| `paid_passes` | int | 유료 데이 패스 수 |
| `desired_specialty` | str | 추천 시 원하는 호스트 전문 분야 |

## Visit

| 필드 | 타입 | 설명 |
|------|------|------|
| `member_id` | str | 방문 회원 |
| `visited_on` | date | 방문일 |

## Freeze

| 필드 | 타입 | 설명 |
|------|------|------|
| `member_id` | str | 동결 회원 |
| `start` | date | 동결 시작일 |
| `end` | date | 동결 종료일 (**inclusive**, 마지막 동결일) |

## Host

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | str | 호스트 식별자 (예: `H1`) |
| `name` | str | 이름 |
| `specialties` | list[str] | 전문 분야 목록 |
| `active` | bool | 활성 여부 |

## 시드 데이터 요약

- **M1 Alice** — 최근 방문 없음 (BR-1 비활성 케이스).
- **M2 Bob** — 1/20~1/25(6일) 동결 이력 (BR-2).
- **M3 Carol** — 무료 2 + 유료 3 패스 (BR-3).
- **M4 Dave** — UTC `2026-01-31 21:30` 가입 = KST 2월 1일 (BR-4 경계).
- **M5 Erin** — 2월 가입 (어떤 해석으로도 2월).
- **H1~H3** — `quiet-zone` 전문 호스트 다수 (BR-5 분산 대상), **H4**는 비활성.
