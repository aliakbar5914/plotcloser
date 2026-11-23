"""Tool: qualify the customer as a lead and give a score."""
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.db.connection import fetch_one
from app.tools.helpers import format_pkr, get_ids


def calculate_score(lead: dict) -> tuple[int, str]:
    """Simple, explainable rules (no AI) so scores are consistent and free."""
    score = 0
    if lead["budget_pkr"]:
        score += 3
    months = lead["timeline_months"]
    if months is not None:
        score += 3 if months <= 1 else 2 if months <= 3 else 1 if months <= 6 else 0
    payment = lead["payment_type"]
    if payment == "cash":
        score += 2
    elif payment in ("bank_loan", "installment"):
        score += 1
    if lead["preferred_area"]:
        score += 1
    if lead["name"]:
        score += 1

    score = max(1, min(score, 10))
    temperature = "hot" if score >= 7 else "warm" if score >= 4 else "cold"
    return score, temperature


@tool
def qualify_lead(
    config: RunnableConfig,
    name: str | None = None,
    interest_type: Literal["property", "car"] | None = None,
    budget_pkr: int | None = None,
    preferred_area: str | None = None,
    timeline_months: int | None = None,
    payment_type: Literal["cash", "installment", "bank_loan"] | None = None,
) -> str:
    """Save what you learned about the customer and get their lead score (1-10).
    Call it as soon as you learn budget, timeline, payment type or area. Pass only known fields.

    Args:
        name: customer's name.
        interest_type: "property" or "car".
        budget_pkr: budget in PKR (1 crore = 10000000, 1 lakh = 100000).
        preferred_area: sector/society/city they want.
        timeline_months: they plan to buy within this many months (0 = now).
        payment_type: "cash", "installment" or "bank_loan".
    """
    user_id, _, _ = get_ids(config)

    # Insert a new lead, or update only the fields we just learned (COALESCE keeps old values).
    lead = fetch_one(
        """INSERT INTO leads (user_id, name, interest_type, budget_pkr, preferred_area,
                              timeline_months, payment_type)
           VALUES (%s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (user_id) DO UPDATE SET
               name            = COALESCE(EXCLUDED.name, leads.name),
               interest_type   = COALESCE(EXCLUDED.interest_type, leads.interest_type),
               budget_pkr      = COALESCE(EXCLUDED.budget_pkr, leads.budget_pkr),
               preferred_area  = COALESCE(EXCLUDED.preferred_area, leads.preferred_area),
               timeline_months = COALESCE(EXCLUDED.timeline_months, leads.timeline_months),
               payment_type    = COALESCE(EXCLUDED.payment_type, leads.payment_type),
               updated_at      = now()
           RETURNING *""",
        (user_id, name, interest_type, budget_pkr, preferred_area, timeline_months, payment_type),
    )

    score, temperature = calculate_score(lead)
    fetch_one(
        """UPDATE leads SET score = %s, temperature = %s,
               stage = CASE WHEN stage = 'new' THEN 'qualified' ELSE stage END
           WHERE user_id = %s RETURNING id""",
        (score, temperature, user_id),
    )

    missing = [
        label for field, label in [
            ("budget_pkr", "budget"), ("timeline_months", "timeline"),
            ("payment_type", "payment type"), ("preferred_area", "area"),
        ] if lead[field] is None  # "is None" so timeline 0 (buying now) counts as known
    ]
    budget = format_pkr(lead["budget_pkr"]) if lead["budget_pkr"] else "unknown"
    result = f"Lead saved. Score {score}/10 ({temperature}). Budget: {budget}."
    if missing:
        result += f" Still unknown: {', '.join(missing)}. Ask naturally, one at a time."
    return result
