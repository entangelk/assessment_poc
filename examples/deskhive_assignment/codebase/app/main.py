"""DeskHive back-office API (PoC).

Thin HTTP layer over the service functions. The endpoints below are the ones
operations used to reproduce the reported symptoms.
"""

from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException, Response

from app import seed
from app.services import analytics, matching, membership, passes

app = FastAPI(title="DeskHive Back-Office PoC")


def _json(data: dict) -> Response:
    # Plain json.dumps keeps non-finite floats (e.g. Infinity) on the wire
    # instead of coercing them to null, matching what operations actually sees.
    return Response(content=json.dumps(data), media_type="application/json")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/members")
def list_members() -> list[dict]:
    return [{"id": m.id, "name": m.name} for m in seed.MEMBERS]


@app.get("/api/members/{member_id}/detail")
def member_detail(member_id: str) -> dict:
    member = seed.get_member(member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="member not found")
    return _json(membership.member_detail(member, seed.VISITS, seed.FREEZES, seed.TODAY))


@app.get("/api/passes/remaining/{member_id}")
def remaining_passes(member_id: str) -> dict:
    member = seed.get_member(member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="member not found")
    return passes.remaining_passes(member)


@app.get("/api/analytics/new-members")
def new_members(year: int, month: int) -> dict:
    count = analytics.new_members_in_month(seed.MEMBERS, year, month)
    return {"year": year, "month": month, "new_member_count": count}


@app.get("/api/matching/recommend/{member_id}")
def recommend(member_id: str) -> dict:
    member = seed.get_member(member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="member not found")
    host = matching.recommend_host(member, seed.HOSTS)
    if host is None:
        return {"member_id": member_id, "recommended_host": None}
    return {"member_id": member_id, "recommended_host": {"id": host.id, "name": host.name}}
