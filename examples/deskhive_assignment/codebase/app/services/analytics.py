"""Dashboard analytics.

DeskHive operates in a single metro area on local time (KST, UTC+9). Join
timestamps are stored in UTC. Operations reports that the monthly new-member
count on the dashboard does not match the member list for the month.
"""

from __future__ import annotations

from app.models import Member


def new_members_in_month(members: list[Member], year: int, month: int) -> int:
    """Count members who joined in the given calendar month."""
    return sum(
        1
        for m in members
        if m.joined_at.year == year and m.joined_at.month == month
    )
