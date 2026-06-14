"""In-memory seed data for the PoC.

The PoC runs without a database or network connection: the back-office reads
this fixed dataset. A reference "current time" is pinned so the reported
symptoms are reproducible.
"""

from __future__ import annotations

from datetime import date, datetime

from app.models import Freeze, Host, Member, Visit

# Pinned reference clock for the PoC.
NOW_UTC = datetime(2026, 2, 10, 0, 0, 0)
TODAY = date(2026, 2, 10)

MEMBERS: list[Member] = [
    # Long inactive member: no recent visits at all.
    Member(
        id="M1",
        name="Alice Kim",
        joined_at=datetime(2026, 1, 5, 1, 0, 0),
        credit_balance=30.0,
        membership_start=date(2026, 1, 5),
        membership_duration_days=30,
        free_trial_passes=0,
        paid_passes=4,
        desired_specialty="quiet-zone",
    ),
    # Member with a freeze on record.
    Member(
        id="M2",
        name="Bob Lee",
        joined_at=datetime(2026, 1, 10, 2, 0, 0),
        credit_balance=12.0,
        membership_start=date(2026, 1, 10),
        membership_duration_days=30,
        free_trial_passes=1,
        paid_passes=2,
        desired_specialty="meeting",
    ),
    # Mixed free-trial and paid passes.
    Member(
        id="M3",
        name="Carol Park",
        joined_at=datetime(2026, 1, 15, 5, 0, 0),
        credit_balance=20.0,
        membership_start=date(2026, 1, 15),
        membership_duration_days=30,
        free_trial_passes=2,
        paid_passes=3,
        desired_specialty="quiet-zone",
    ),
    # Joined just after midnight KST on Feb 1 (= Jan 31 21:30 UTC).
    Member(
        id="M4",
        name="Dave Choi",
        joined_at=datetime(2026, 1, 31, 21, 30, 0),
        credit_balance=10.0,
        membership_start=date(2026, 2, 1),
        membership_duration_days=30,
        free_trial_passes=1,
        paid_passes=0,
        desired_specialty="meeting",
    ),
    # Clearly joined in February under any reading.
    Member(
        id="M5",
        name="Erin Jung",
        joined_at=datetime(2026, 2, 3, 2, 0, 0),
        credit_balance=15.0,
        membership_start=date(2026, 2, 3),
        membership_duration_days=30,
        free_trial_passes=0,
        paid_passes=5,
        desired_specialty="quiet-zone",
    ),
]

VISITS: list[Visit] = [
    # Bob is active recently -> finite exhaustion estimate.
    Visit(member_id="M2", visited_on=date(2026, 2, 1)),
    Visit(member_id="M2", visited_on=date(2026, 2, 4)),
    Visit(member_id="M2", visited_on=date(2026, 2, 8)),
    Visit(member_id="M3", visited_on=date(2026, 2, 2)),
    Visit(member_id="M3", visited_on=date(2026, 2, 9)),
    Visit(member_id="M5", visited_on=date(2026, 2, 6)),
    # Alice (M1) intentionally has no visits.
]

FREEZES: list[Freeze] = [
    # Bob froze from Jan 20 through Jan 25 inclusive (6 frozen days).
    Freeze(member_id="M2", start=date(2026, 1, 20), end=date(2026, 1, 25)),
]

HOSTS: list[Host] = [
    Host(id="H1", name="Host Han", specialties=["quiet-zone", "meeting"]),
    Host(id="H2", name="Host Oh", specialties=["quiet-zone"]),
    Host(id="H3", name="Host Seo", specialties=["quiet-zone", "meeting"]),
    Host(id="H4", name="Host Yoon", specialties=["meeting"], active=False),
]


def get_member(member_id: str) -> Member | None:
    return next((m for m in MEMBERS if m.id == member_id), None)
