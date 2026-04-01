from dotenv import load_dotenv
load_dotenv()

import os
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver

# ─────────────────────────────────────────────────────────────
# State Schema Import
# ─────────────────────────────────────────────────────────────

from state.schema import MASARPSState


# ─────────────────────────────────────────────────────────────
# Node Imports — Real agents (Phase 1)
# ─────────────────────────────────────────────────────────────

from agents.session_init   import session_init_node
from agents.source_select  import source_select_node
from agents.research       import research_node
from agents.summary        import summary_node
from agents.slide_builder  import slide_builder_node
from agents.export_agent   import export_node


# ─────────────────────────────────────────────────────────────
# Node Imports — Stubs (not yet built, Phase 2+). Keypoint updated
# ─────────────────────────────────────────────────────────────

from agents.user_review import user_review_node
from agents.validation  import validation_node

# Keep only keypoint_expand as stub for now
from agents.keypoint_expand import keypoint_expand_node


# ─────────────────────────────────────────────────────────────
# Graph Construction
# ─────────────────────────────────────────────────────────────

builder = StateGraph(MASARPSState)

builder.add_node("session_init",  session_init_node)
builder.add_node("source_select", source_select_node)
builder.add_node("research",      research_node)
builder.add_node("summary",       summary_node)
builder.add_node("user_review",   user_review_node)
builder.add_node("expand_point",  keypoint_expand_node)
builder.add_node("slide_builder", slide_builder_node)
builder.add_node("validation",    validation_node)
builder.add_node("export",        export_node)


# ─────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────

builder.set_entry_point("session_init")


# ─────────────────────────────────────────────────────────────
# Linear Flow Edges
# ─────────────────────────────────────────────────────────────

builder.add_edge("session_init",  "source_select")
builder.add_edge("source_select", "research")
builder.add_edge("research",      "summary")
builder.add_edge("summary",       "user_review")
builder.add_edge("expand_point",  "user_review")


# ─────────────────────────────────────────────────────────────
# Conditional Routing from user_review (Feedback Loop)
# ─────────────────────────────────────────────────────────────

def route_user_decision(state: MASARPSState) -> str:
    decision  = state.get("user_decision", "").strip().lower()
    iteration = state.get("iteration_count", 0)
    max_iter  = state.get("max_iterations", 5)

    print(f"[Graph] Routing decision: '{decision}' (iteration {iteration}/{max_iter})")

    if decision == "approve":
        return "slide_builder"

    if decision == "expand_point":
        if not state.get("expand_target_id"):
            print("[Graph] expand_point requested but no target ID — terminating")
            return "terminate"
        return "expand_point"

    if decision == "research_more":
        if iteration >= max_iter:
            print(f"[Graph] Max iterations reached — terminating")
            return "terminate"
        return "research"

    # Empty string, "terminate", or anything unexpected
    return "terminate"


builder.add_conditional_edges(
    "user_review",
    route_user_decision,
    {
        "slide_builder": "slide_builder",
        "expand_point":  "expand_point",
        "research":      "research",
        "terminate":     END,
    }
)


# ─────────────────────────────────────────────────────────────
# Validation Conditional Flow
# ─────────────────────────────────────────────────────────────

def route_validation(state: MASARPSState) -> str:
    return "export" if state["validation_passed"] else "slide_builder"


builder.add_edge("slide_builder", "validation")

builder.add_conditional_edges(
    "validation",
    route_validation,
    {
        "export":        "export",
        "slide_builder": "slide_builder",
    }
)


# ─────────────────────────────────────────────────────────────
# Termination
# ─────────────────────────────────────────────────────────────

builder.add_edge("export", END)


# ─────────────────────────────────────────────────────────────
# Compile Graph (SQLite checkpointer for development)
# ─────────────────────────────────────────────────────────────


checkpointer = MemorySaver()

graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["user_review"],
)

print("✓ Graph compiled successfully")