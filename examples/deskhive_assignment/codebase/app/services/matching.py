"""Meeting-room host recommendation.

When a member books a room, the system recommends an eligible host (active, with
a matching specialty). Operations reports that the same host keeps getting
recommended even when several hosts qualify.
"""

from __future__ import annotations

from app.models import Host, Member


def eligible_hosts(member: Member, hosts: list[Host]) -> list[Host]:
    return [
        h
        for h in hosts
        if h.active and member.desired_specialty in h.specialties
    ]


def recommend_host(member: Member, hosts: list[Host]) -> Host | None:
    """Recommend one eligible host for the member."""
    candidates = eligible_hosts(member, hosts)
    if not candidates:
        return None
    return sorted(candidates, key=lambda h: h.id)[0]
