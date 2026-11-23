"""Small helpers shared by all tools."""
from langchain_core.runnables import RunnableConfig
from psycopg.types.json import Jsonb

from app.db.connection import execute, fetch_one


def get_ids(config: RunnableConfig) -> tuple[str, str, str]:
    """Return (user_id, thread_key, turn_id) set by the SERVER for this request.

    Tools never take user_id from the AI. This is what keeps users separate.
    """
    settings = config.get("configurable", {})
    return settings["user_id"], settings["thread_id"], settings["turn_id"]


def format_pkr(amount: int) -> str:
    """30000000 -> '3 crore', 7200000 -> '72 lakh'."""
    if amount >= 10_000_000:
        return f"{amount / 10_000_000:g} crore"
    if amount >= 100_000:
        return f"{amount / 100_000:g} lakh"
    return f"{amount:,}"


# ---------- Human-in-the-loop drafts for risky actions ----------

def save_draft(user_id: str, thread_key: str, turn_id: str, action: str, payload: dict) -> None:
    """Remember a risky action that is waiting for the user's 'yes'."""
    execute(
        "DELETE FROM pending_actions WHERE user_id = %s AND thread_id = %s AND action = %s",
        (user_id, thread_key, action),
    )
    execute(
        """INSERT INTO pending_actions (user_id, thread_id, action, payload, turn_id)
           VALUES (%s, %s, %s, %s, %s)""",
        (user_id, thread_key, action, Jsonb(payload), turn_id),
    )


def take_confirmed_draft(user_id: str, thread_key: str, turn_id: str, action: str) -> dict | None:
    """Return (and remove) the draft ONLY if it was created in an EARLIER message.

    A draft made in this same turn doesn't count, so the AI can't
    "ask and confirm" by itself without the user replying in between.
    """
    row = fetch_one(
        """DELETE FROM pending_actions
           WHERE id = (
               SELECT id FROM pending_actions
               WHERE user_id = %s AND thread_id = %s AND action = %s
                 AND turn_id <> %s
                 AND created_at > now() - interval '1 day'
               ORDER BY id DESC LIMIT 1
           )
           RETURNING payload""",
        (user_id, thread_key, action, turn_id),
    )
    return row["payload"] if row else None
