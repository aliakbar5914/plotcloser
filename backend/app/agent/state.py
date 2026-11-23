"""What the graph remembers while it runs (saved by the checkpointer per thread)."""
from langgraph.graph import MessagesState


class AgentState(MessagesState):
    # "messages" comes from MessagesState: new messages are APPENDED, not replaced.
    blocked: bool          # True if the guard refused this message
    user_facts: str        # long-term facts loaded for this user
    active_agent: str      # "sales" or "booking", chosen by the router
    tokens_in: int         # tokens used in THIS turn (reset by the guard)
    tokens_out: int
    tool_calls: list[dict] # tools called in THIS turn, returned by /chat
