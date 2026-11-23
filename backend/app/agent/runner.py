"""Runs one chat turn: the bridge between the API and the graph."""
import json
import logging
import time
import uuid

import anthropic
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.errors import GraphRecursionError
from psycopg.types.json import Jsonb

from app.db.connection import execute

logger = logging.getLogger("plotcloser")

MAX_GRAPH_STEPS = 12  # stops endless tool loops (each loop = more cost)


def make_thread_key(user_id: str, thread_id: str) -> str:
    """Unique per user AND thread. User B sending A's thread_id gets a different key."""
    return json.dumps([user_id, thread_id])


def _empty_result(reply: str) -> dict:
    return {"reply": reply, "tool_calls": [], "tokens": {"in": 0, "out": 0}}


def run_chat(graph, user_id: str, thread_id: str, message: str, background_tasks=None) -> dict:
    """Run one turn. If background_tasks is given, the chat log is saved AFTER the reply is sent."""
    started = time.perf_counter()
    run_config = {
        "configurable": {
            "thread_id": make_thread_key(user_id, thread_id),
            "user_id": user_id,
            "turn_id": uuid.uuid4().hex,
        },
        "recursion_limit": MAX_GRAPH_STEPS,
    }

    try:
        # durability="exit": save the conversation ONCE at the end of the turn,
        # not after every step. Far fewer database trips = much faster replies.
        state = graph.invoke({"messages": [HumanMessage(content=message)]}, run_config,
                             durability="exit")
        last = state["messages"][-1]
        reply = last.text if isinstance(last, AIMessage) and last.text.strip() else (
            "Sorry, I couldn't finish that. Could you rephrase your request?")
        result = {
            "reply": reply,
            "tool_calls": state.get("tool_calls", []),
            "tokens": {"in": state.get("tokens_in", 0), "out": state.get("tokens_out", 0)},
        }
        blocked = state.get("blocked", False)
    except GraphRecursionError:
        result, blocked = _empty_result("Sorry, that took too many steps. Please ask in a simpler way."), False
    except anthropic.RateLimitError:
        logger.warning("Rate limited by Anthropic")
        result, blocked = _empty_result("I'm getting a lot of messages right now. Please try again in a minute."), False
    except (anthropic.APITimeoutError, anthropic.APIConnectionError):
        logger.warning("Anthropic timeout/connection error")
        result, blocked = _empty_result("Sorry, I'm having trouble connecting. Please try again."), False
    except anthropic.APIStatusError as error:
        logger.error("Anthropic API error %s: %s", error.status_code, error.message)
        result, blocked = _empty_result("Sorry, something went wrong on my side. Please try again."), False

    latency_ms = int((time.perf_counter() - started) * 1000)
    log_args = (user_id, thread_id, message, result, latency_ms, blocked)
    if background_tasks is not None:
        background_tasks.add_task(_log_chat, *log_args)  # customer doesn't wait for this
    else:
        _log_chat(*log_args)
    return result


def _log_chat(user_id, thread_id, message, result, latency_ms, blocked) -> None:
    """Save the turn for the admin dashboard. Never let logging break the reply."""
    try:
        execute(
            """INSERT INTO chat_logs (user_id, thread_id, user_message, reply, tool_calls,
                                      tokens_in, tokens_out, latency_ms, blocked)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, thread_id, message, result["reply"], Jsonb(result["tool_calls"]),
             result["tokens"]["in"], result["tokens"]["out"], latency_ms, blocked),
        )
    except Exception:
        logger.exception("Could not save chat log")
