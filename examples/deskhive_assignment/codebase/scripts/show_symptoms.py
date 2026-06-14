"""Reproduce the five reported symptoms without booting the API.

Run from the codebase root:

    python3 scripts/show_symptoms.py

Uses only the standard library and the in-memory seed data, so a reviewer can
confirm the reported behavior without installing FastAPI or any dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import seed  # noqa: E402
from app.services import analytics, matching, membership, passes  # noqa: E402


def main() -> None:
    print("DeskHive PoC — reported symptoms (reference date 2026-02-10)\n")

    # B1: inactive member's exhaustion estimate.
    alice = seed.get_member("M1")
    bob = seed.get_member("M2")
    print("B1  credit exhaustion estimate")
    print(
        f"    M1 Alice (no recent visits): "
        f"{membership.estimated_exhaustion_days(alice, seed.VISITS, seed.TODAY)}"
    )
    print(
        f"    M2 Bob   (active):           "
        f"{membership.estimated_exhaustion_days(bob, seed.VISITS, seed.TODAY):.1f}\n"
    )

    # B2: frozen membership expiry.
    print("B2  membership expiry (M2 Bob has a 6-day freeze on record)")
    print(f"    frozen days on record: {membership._frozen_days(bob, seed.FREEZES)}")
    print(f"    reported expiry_date:  {membership.membership_expiry(bob, seed.FREEZES)}\n")

    # B3: remaining pass balance.
    carol = seed.get_member("M3")
    print("B3  remaining passes (M3 Carol holds 2 free + 3 paid)")
    print(f"    reported balance: {passes.remaining_passes(carol)}\n")

    # B4: monthly analytics.
    print("B4  new-member count for 2026-02")
    print(f"    reported count: {analytics.new_members_in_month(seed.MEMBERS, 2026, 2)}")
    print("    member list joins in Feb (KST): M4 Dave (Feb 1), M5 Erin (Feb 3) -> 2\n")

    # B5: host recommendation spread.
    print("B5  host recommendation for M1 Alice (3 eligible quiet-zone hosts)")
    picks = {matching.recommend_host(alice, seed.HOSTS).id for _ in range(5)}
    print(f"    distinct hosts over 5 calls: {picks}\n")


if __name__ == "__main__":
    main()
