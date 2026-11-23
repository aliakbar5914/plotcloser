"""Joins the nodes into a LangGraph multi-agent graph (router pattern).

START -> guard --blocked--> END
           | safe
           v
     memory_loader -> router --sales-----> sales_agent   <-> sales_tools
                             \--booking--> booking_agent <-> booking_tools
                     (each agent goes to END when it has answered)
"""
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.nodes import (
    booking_agent_node, guard_node, memory_loader_node, route_after_guard,
    route_to_agent, router_node, sales_agent_node,
)
from app.agent.state import AgentState
from app.memory.setup import checkpointer, store
from app.tools import BOOKING_TOOLS, SALES_TOOLS


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("guard", guard_node)
    builder.add_node("memory_loader", memory_loader_node)
    builder.add_node("router", router_node)
    builder.add_node("sales_agent", sales_agent_node)
    builder.add_node("sales_tools", ToolNode(SALES_TOOLS))
    builder.add_node("booking_agent", booking_agent_node)
    builder.add_node("booking_tools", ToolNode(BOOKING_TOOLS))

    builder.add_edge(START, "guard")
    builder.add_conditional_edges("guard", route_after_guard, {"blocked": END, "safe": "memory_loader"})
    builder.add_edge("memory_loader", "router")
    builder.add_conditional_edges("router", route_to_agent,
                                  {"sales": "sales_agent", "booking": "booking_agent"})

    # Each agent has its own tool loop: agent -> tools -> back to the SAME agent.
    builder.add_conditional_edges("sales_agent", tools_condition, {"tools": "sales_tools", END: END})
    builder.add_edge("sales_tools", "sales_agent")
    builder.add_conditional_edges("booking_agent", tools_condition, {"tools": "booking_tools", END: END})
    builder.add_edge("booking_tools", "booking_agent")

    # checkpointer = short-term memory per thread, store = long-term memory per user
    return builder.compile(checkpointer=checkpointer, store=store)
