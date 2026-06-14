"""Domain models for the DeskHive back-office PoC.

Plain dataclasses with no framework dependency so the service layer can be
exercised from a script or a test without booting the API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Member:
    id: str
    name: str
    joined_at: datetime  # stored as UTC
    credit_balance: float
    membership_start: date
    membership_duration_days: int
    free_trial_passes: int = 0
    paid_passes: int = 0
    desired_specialty: str | None = None


@dataclass
class Visit:
    member_id: str
    visited_on: date


@dataclass
class Freeze:
    member_id: str
    start: date
    end: date  # inclusive: this is the last frozen day


@dataclass
class Host:
    id: str
    name: str
    specialties: list[str] = field(default_factory=list)
    active: bool = True
