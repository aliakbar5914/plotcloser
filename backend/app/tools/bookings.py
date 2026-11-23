"""Tools: book visits, schedule follow-ups, list my visits.

Booking and follow-ups are "risky actions": they need the user's YES first.
Step 1 (confirmed=False): save a draft and ask the user.
Step 2 (confirmed=True):  works only if the user replied after the draft.
"""
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.db.connection import execute, fetch_all, fetch_one
from app.tools.helpers import get_ids, save_draft, take_confirmed_draft


def _mark_lead_stage(user_id: str, stage: str) -> None:
    execute(
        """INSERT INTO leads (user_id, stage) VALUES (%s, %s)
           ON CONFLICT (user_id) DO UPDATE SET stage = EXCLUDED.stage, updated_at = now()""",
        (user_id, stage),
    )


@tool
def book_visit(listing_id: int, requested_time: str, config: RunnableConfig, confirmed: bool = False) -> str:
    """Book a site visit (property) or test drive (car). ALWAYS a two-step action:
    1) call with confirmed=false -> then ask the customer to confirm the details;
    2) only after the customer says yes in their NEXT message, call again with confirmed=true.

    Args:
        listing_id: the listing number, e.g. 3 for "#3".
        requested_time: day and time, e.g. "Saturday 4 PM".
        confirmed: true only after the customer clearly said yes.
    """
    user_id, thread_key, turn_id = get_ids(config)

    if confirmed:
        draft = take_confirmed_draft(user_id, thread_key, turn_id, "book_visit")
        if not draft:
            return ("NOT BOOKED: there is no earlier draft the customer confirmed. "
                    "Call book_visit with confirmed=false first and ask the customer.")
        visit = fetch_one(
            """INSERT INTO visits (user_id, thread_id, listing_id, requested_time)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (user_id, thread_key, draft["listing_id"], draft["requested_time"]),
        )
        _mark_lead_stage(user_id, "visit_booked")
        return (f"BOOKED. Visit #{visit['id']} for listing #{draft['listing_id']} "
                f"({draft['title']}) on {draft['requested_time']}. Our agent will call to confirm.")

    listing = fetch_one(
        "SELECT id, title, area, status FROM listings WHERE id = %s", (listing_id,)
    )
    if not listing or listing["status"] != "available":
        return f"Listing #{listing_id} is not available. Search again."

    save_draft(user_id, thread_key, turn_id, "book_visit", {
        "listing_id": listing_id, "requested_time": requested_time, "title": listing["title"],
    })
    return (f"DRAFT ONLY (not booked yet): visit to #{listing_id} {listing['title']}, "
            f"{listing['area']} on {requested_time}. Ask the customer to reply yes to confirm.")


@tool
def schedule_follow_up(due: str, note: str, config: RunnableConfig, confirmed: bool = False) -> str:
    """Schedule a follow-up message/call to the customer. Two-step like book_visit:
    call with confirmed=false, ask the customer, then confirmed=true after they say yes.

    Args:
        due: when to follow up, e.g. "next Monday" or "in 3 days".
        note: short reason, e.g. "send new DHA listings under 3 crore".
        confirmed: true only after the customer clearly said yes.
    """
    user_id, thread_key, turn_id = get_ids(config)

    if confirmed:
        draft = take_confirmed_draft(user_id, thread_key, turn_id, "schedule_follow_up")
        if not draft:
            return ("NOT SCHEDULED: no earlier draft was confirmed. "
                    "Call with confirmed=false first and ask the customer.")
        row = fetch_one(
            "INSERT INTO follow_ups (user_id, due, note) VALUES (%s, %s, %s) RETURNING id",
            (user_id, draft["due"], draft["note"]),
        )
        return f"SCHEDULED. Follow-up #{row['id']} on {draft['due']}: {draft['note']}."

    save_draft(user_id, thread_key, turn_id, "schedule_follow_up", {"due": due, "note": note})
    return f"DRAFT ONLY: follow-up on {due} ({note}). Ask the customer to reply yes to confirm."


@tool
def get_my_visits(config: RunnableConfig) -> str:
    """Show THIS customer's own booked visits and follow-ups. Never shows other customers."""
    user_id, _, _ = get_ids(config)
    visits = fetch_all(
        """SELECT v.id, v.requested_time, v.status, l.title, l.area
           FROM visits v JOIN listings l ON l.id = v.listing_id
           WHERE v.user_id = %s ORDER BY v.id DESC LIMIT 5""",
        (user_id,),
    )
    follow_ups = fetch_all(
        "SELECT id, due, note FROM follow_ups WHERE user_id = %s ORDER BY id DESC LIMIT 5",
        (user_id,),
    )
    if not visits and not follow_ups:
        return "This customer has no booked visits or follow-ups."
    lines = [f"Visit #{v['id']}: {v['title']}, {v['area']} on {v['requested_time']} ({v['status']})"
             for v in visits]
    lines += [f"Follow-up #{f['id']}: {f['due']} - {f['note']}" for f in follow_ups]
    return "\n".join(lines)
