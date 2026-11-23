"""Tool: save a fact about the user to LONG-TERM memory (kept across conversations)."""
import re
from typing import Annotated, Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore

from app.tools.helpers import get_ids

# Things we must never store: CNIC, card/bank numbers, passwords, phone numbers.
SENSITIVE_PATTERNS = [
    r"\b\d{5}-?\d{7}-?\d\b",          # CNIC
    r"\b(?:\d[ -]?){13,19}\b",        # card / bank account numbers
    r"\b(?:\+92|0)3\d{2}[ -]?\d{7}\b",  # Pakistani mobile numbers
    r"password|passcode|\bpin\b|\bcvv\b|\biban\b",
]


def memory_namespace(user_id: str) -> tuple[str, str]:
    """Each user gets their own memory 'folder', so users never share memories."""
    return ("memories", user_id)


@tool
def save_user_memory(
    category: Literal["name", "budget", "preferred_area", "property_size",
                      "timeline", "payment_type", "interest", "other"],
    value: str,
    config: RunnableConfig,
    store: Annotated[BaseStore, InjectedStore()],
) -> str:
    """Remember a lasting preference about this customer for future conversations
    (name, budget, area, size, timeline, payment type, interest).
    Do NOT save one-time questions, phone numbers, CNIC, bank details or passwords.

    Args:
        category: what kind of fact this is.
        value: short fact, e.g. "3 crore", "DHA Phase 2", "10 marla".
    """
    if any(re.search(p, value, re.IGNORECASE) for p in SENSITIVE_PATTERNS):
        return "NOT SAVED: this looks like private/sensitive data. Never store it."

    user_id, _, _ = get_ids(config)
    # Same category overwrites the old value (e.g. a new budget replaces the old one).
    key = category if category != "other" else f"other:{value[:40].lower()}"
    store.put(memory_namespace(user_id), key, {"value": value[:200]})
    return f"Remembered {category}: {value}"
