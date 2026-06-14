"""Membership calculations: credit-exhaustion estimate and expiry date.

Inherited from the previous developer. Operations has reported issues with the
exhaustion estimate for inactive members and with expiry dates for members who
have frozen their membership.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from app.models import Freeze, Member, Visit

RECENT_WINDOW_DAYS = 14


def recent_usage_rate(member: Member, visits: list[Visit], as_of: date) -> float:
    """Average credits consumed per day over the recent window.

    Approximated as recent visit count divided by the window length.
    """
    window_start = as_of - timedelta(days=RECENT_WINDOW_DAYS)
    recent = [
        v
        for v in visits
        if v.member_id == member.id and window_start <= v.visited_on <= as_of
    ]
    return len(recent) / RECENT_WINDOW_DAYS


def estimated_exhaustion_days(
    member: Member, visits: list[Visit], as_of: date
) -> float:
    """Estimated days until the member's credit balance runs out."""
    rate = recent_usage_rate(member, visits, as_of)
    if rate == 0:
        # Previous dev "handled" the no-usage case by returning infinity.
        return float("inf")
    return member.credit_balance / rate


def _frozen_days(member: Member, freezes: list[Freeze]) -> int:
    """Total frozen days on record for the member (inclusive of both ends)."""
    total = 0
    for f in freezes:
        if f.member_id == member.id:
            total += (f.end - f.start).days + 1
    return total


def membership_expiry(member: Member, freezes: list[Freeze]) -> date:
    """Date the membership expires."""
    base_expiry = member.membership_start + timedelta(
        days=member.membership_duration_days
    )
    # TODO(handover): freeze should push the expiry out by the frozen days.
    # The frozen-day total is computed below but is not applied yet.
    _ = _frozen_days(member, freezes)
    return base_expiry


def member_detail(
    member: Member,
    visits: list[Visit],
    freezes: list[Freeze],
    as_of: date,
) -> dict:
    return {
        "id": member.id,
        "name": member.name,
        "credit_balance": member.credit_balance,
        "estimated_exhaustion_days": estimated_exhaustion_days(member, visits, as_of),
        "expiry_date": membership_expiry(member, freezes).isoformat(),
    }
