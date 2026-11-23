"""Admin dashboard API (password protected) + public listings for the website."""
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException

from app import config
from app.db.connection import fetch_all, fetch_one
from app.schemas import LeadStageUpdate, NewListing

public_router = APIRouter()
admin_router = APIRouter(prefix="/admin")


def require_admin(x_admin_password: str = Header(default="")) -> None:
    # compare_digest takes the same time for right and wrong guesses (stops timing attacks)
    if not secrets.compare_digest(x_admin_password, config.ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Wrong admin password")


# ---------------- Public ----------------
@public_router.get("/listings")
def list_listings(type: str | None = None, purpose: str | None = None):
    conditions, params = ["status = 'available'"], []
    if type:
        conditions.append("type = %s")
        params.append(type)
    if purpose:
        conditions.append("purpose = %s")
        params.append(purpose)
    return fetch_all(
        "SELECT id, type, title, city, area, size_label, price_pkr, purpose, bedrooms, description, image_url "
        "FROM listings WHERE " + " AND ".join(conditions) + " ORDER BY id",
        tuple(params),
    )


# ---------------- Admin ----------------
@admin_router.post("/login", dependencies=[Depends(require_admin)])
def admin_login():
    return {"ok": True}


@admin_router.get("/stats", dependencies=[Depends(require_admin)])
def admin_stats():
    chats = fetch_one(
        """SELECT COUNT(*) AS messages,
                  COUNT(DISTINCT user_id) AS users,
                  COALESCE(SUM(tokens_in), 0) AS tokens_in,
                  COALESCE(SUM(tokens_out), 0) AS tokens_out,
                  COALESCE(AVG(latency_ms), 0)::int AS avg_latency_ms,
                  COUNT(*) FILTER (WHERE blocked) AS blocked
           FROM chat_logs"""
    )
    stages = fetch_all("SELECT stage, COUNT(*) AS count FROM leads GROUP BY stage")
    temps = fetch_all("SELECT temperature, COUNT(*) AS count FROM leads WHERE temperature IS NOT NULL GROUP BY temperature")
    visits = fetch_one("SELECT COUNT(*) AS count FROM visits")
    cost = (chats["tokens_in"] * config.PRICE_INPUT_PER_MTOK
            + chats["tokens_out"] * config.PRICE_OUTPUT_PER_MTOK) / 1_000_000
    return {
        **chats,
        "visits_booked": visits["count"],
        "leads_by_stage": {row["stage"]: row["count"] for row in stages},
        "leads_by_temperature": {row["temperature"]: row["count"] for row in temps},
        "estimated_cost_usd": round(cost, 4),
    }


@admin_router.get("/leads", dependencies=[Depends(require_admin)])
def admin_leads():
    return fetch_all("SELECT * FROM leads ORDER BY score DESC NULLS LAST, updated_at DESC")


@admin_router.patch("/leads/{lead_id}", dependencies=[Depends(require_admin)])
def admin_update_lead(lead_id: int, body: LeadStageUpdate):
    row = fetch_one(
        "UPDATE leads SET stage = %s, updated_at = now() WHERE id = %s RETURNING *",
        (body.stage, lead_id),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return row


@admin_router.get("/visits", dependencies=[Depends(require_admin)])
def admin_visits():
    return fetch_all(
        """SELECT v.id, v.user_id, v.requested_time, v.status, v.created_at,
                  l.id AS listing_id, l.title, l.area, l.type,
                  ld.name AS lead_name, ld.score, ld.temperature
           FROM visits v
           JOIN listings l ON l.id = v.listing_id
           LEFT JOIN leads ld ON ld.user_id = v.user_id
           ORDER BY v.id DESC"""
    )


@admin_router.get("/follow-ups", dependencies=[Depends(require_admin)])
def admin_follow_ups():
    return fetch_all("SELECT * FROM follow_ups ORDER BY id DESC")


@admin_router.get("/chats", dependencies=[Depends(require_admin)])
def admin_chats(limit: int = 100):
    return fetch_all(
        "SELECT * FROM chat_logs ORDER BY id DESC LIMIT %s", (min(max(limit, 1), 500),)
    )


@admin_router.post("/listings", dependencies=[Depends(require_admin)])
def admin_add_listing(body: NewListing):
    return fetch_one(
        """INSERT INTO listings (type, title, city, area, size_label, size_marla, price_pkr,
                                 purpose, bedrooms, description, image_url)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *""",
        (body.type, body.title, body.city, body.area, body.size_label, body.size_marla,
         body.price_pkr, body.purpose, body.bedrooms, body.description, body.image_url),
    )
