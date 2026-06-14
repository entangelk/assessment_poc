"""Day-pass balance reporting.

Members hold two kinds of passes: free trial passes (granted at signup) and paid
day passes (purchased). Operations reports that the remaining-balance view does
not let staff tell the two apart.
"""

from __future__ import annotations

from app.models import Member


def remaining_passes(member: Member) -> dict:
    """Remaining pass balance for the member."""
    total = member.free_trial_passes + member.paid_passes
    return {"member_id": member.id, "remaining": total}
