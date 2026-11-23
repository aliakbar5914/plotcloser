"""Creates LangGraph's two memories, both saved in Neon Postgres.

- checkpointer (SHORT-TERM): full state of each conversation, keyed by thread_id.
- store (LONG-TERM): facts about each user, keyed by ("memories", user_id).
"""
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

from app.db.connection import pool

checkpointer = PostgresSaver(pool)
store = PostgresStore(pool)


def setup_memory_tables() -> None:
    """Creates LangGraph's own tables (safe to run every start)."""
    checkpointer.setup()
    store.setup()
