"""The graph's nodes. Only the two agent nodes call the AI; the others are free."""
import re

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from app import config
from app.agent.prompts import build_system_prompt
from app.agent.state import AgentState
from app.safety.guard import REFUSALS, check_message
from app.db.connection import fetch_one
from app.tools import BOOKING_TOOLS, SALES_TOOLS
from app.tools.helpers import format_pkr
from app.tools.memory import memory_namespace

llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=config.MAX_OUTPUT_TOKENS,
    reasoning_effort=config.REASONING_EFFORT,
    timeout=config.LLM_TIMEOUT_SECONDS,
    max_retries=config.LLM_MAX_RETRIES,
    # No temperature: Haiku 5.5 rejects non-default values.
)
# Same model, but each agent only "sees" its own tools.
sales_llm = llm.bind_tools(SALES_TOOLS)
booking_llm = llm.bind_tools(BOOKING_TOOLS)


def _last_human_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.text
    return ""


def trim_history(messages: list[BaseMessage], max_messages: int) -> list[BaseMessage]:
    """Keep the newest messages, always starting at a customer message.

    Starting at a HumanMessage keeps tool calls and their results together.
    The current turn is always kept, even if it is longer than max_messages.
    """
    human_positions = [i for i, m in enumerate(messages) if isinstance(m, HumanMessage)]
    if not human_positions:
        return messages
    start = human_positions[-1]
    for position in reversed(human_positions):
        if len(messages) - position <= max_messages:
            start = position
        else:
            break
    return messages[start:]


# ---------------- Node 1: Guard ----------------
def guard_node(state: AgentState) -> dict:
    turn_reset = {"blocked": False, "tokens_in": 0, "tokens_out": 0, "tool_calls": []}
    reason = check_message(_last_human_text(state["messages"]), config.MAX_MESSAGE_CHARS)
    if reason:
        return {**turn_reset, "blocked": True, "messages": [AIMessage(content=REFUSALS[reason])]}
    return turn_reset


def route_after_guard(state: AgentState) -> str:
    return "blocked" if state["blocked"] else "safe"


# ---------------- Node 2: Memory loader ----------------
def _lead_facts(user_id: str) -> list[str]:
    """Structured facts that qualify_lead saved for THIS user (name, budget, ...)."""
    lead = fetch_one("SELECT * FROM leads WHERE user_id = %s", (user_id,))
    if not lead:
        return []
    facts = []
    if lead["name"]:
        facts.append(f"- name: {lead['name']}")
    if lead["budget_pkr"]:
        facts.append(f"- budget: {format_pkr(lead['budget_pkr'])} PKR")
    if lead["preferred_area"]:
        facts.append(f"- preferred area: {lead['preferred_area']}")
    if lead["timeline_months"] is not None:
        facts.append(f"- buying within: {lead['timeline_months']} months")
    if lead["payment_type"]:
        facts.append(f"- payment: {lead['payment_type']}")
    if lead["stage"] == "visit_booked":
        facts.append("- has a visit booked (use get_my_visits for details)")
    return facts


def memory_loader_node(state: AgentState, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Loads LONG-TERM memory for this user only: saved preferences + their lead profile."""
    user_id = config["configurable"]["user_id"]
    items = store.search(memory_namespace(user_id), limit=20)
    facts = [f"- {item.key.split(':')[0]}: {item.value['value']}" for item in items]
    facts += _lead_facts(user_id)
    return {"user_facts": "\n".join(facts)}


# ---------------- Node 3: Router (rules, no AI) ----------------
BOOKING_WORDS = re.compile(
    r"\b(book|booked|bookings?|visits?|test[\s-]?drives?|appointments?|schedule|reschedule|"
    r"follow[\s-]?ups?|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"tomorrow|kal|\d{1,2}\s?(am|pm))\b",
    re.IGNORECASE,
)


def _has_pending_draft(config: RunnableConfig) -> bool:
    settings = config["configurable"]
    row = fetch_one(
        "SELECT 1 FROM pending_actions WHERE user_id = %s AND thread_id = %s LIMIT 1",
        (settings["user_id"], settings["thread_id"]),
    )
    return row is not None


def _last_ai_offered_booking(messages: list[BaseMessage]) -> bool:
    """Did our previous reply (before this customer message) invite a visit/test drive?"""
    for message in reversed(messages[:-1]):
        if isinstance(message, AIMessage) and message.text:
            return bool(re.search(r"\b(book|visit|test drive)\b", message.text, re.IGNORECASE))
    return False


SHORT_YES = re.compile(
    r"^\s*(yes|yeah|yep|sure|ok|okay|haan|han|ji|jee|please|confirm|theek hai|done)\b", re.IGNORECASE)


def router_node(state: AgentState, config: RunnableConfig) -> dict:
    """Pick the agent for this message. Free and instant: no AI call."""
    messages = state["messages"]
    text = _last_human_text(messages)
    said_short_yes = len(text) < 40 and SHORT_YES.search(text)
    if (BOOKING_WORDS.search(text)
            or _has_pending_draft(config)                              # a booking waits for "yes"
            or (said_short_yes and _last_ai_offered_booking(messages))):  # "yes" to our booking offer
        return {"active_agent": "booking"}
    return {"active_agent": "sales"}


def route_to_agent(state: AgentState) -> str:
    return state["active_agent"]


# ---------------- Nodes 4 + 5: the two AI agents ----------------
def _run_agent(state: AgentState, role: str, model) -> dict:
    history = trim_history(state["messages"], config.MAX_HISTORY_MESSAGES)
    system = SystemMessage(content=build_system_prompt(role, state.get("user_facts", "")))

    response = model.invoke([system] + history)

    usage = response.usage_metadata or {}
    new_calls = [{"name": call["name"], "args": call["args"]} for call in response.tool_calls]
    return {
        "messages": [response],
        "tokens_in": state.get("tokens_in", 0) + usage.get("input_tokens", 0),
        "tokens_out": state.get("tokens_out", 0) + usage.get("output_tokens", 0),
        "tool_calls": state.get("tool_calls", []) + new_calls,
    }


def sales_agent_node(state: AgentState) -> dict:
    return _run_agent(state, "sales", sales_llm)


def booking_agent_node(state: AgentState) -> dict:
    return _run_agent(state, "booking", booking_llm)
