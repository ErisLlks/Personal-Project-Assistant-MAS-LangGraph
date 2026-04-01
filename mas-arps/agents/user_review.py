import datetime
from state.schema import MASARPSState

def user_review_node(state: MASARPSState) -> dict:
    """
    Human-in-the-loop node.
    LangGraph interrupts BEFORE this node.
    This node runs AFTER the human resumes with a decision.
    """
    now      = datetime.datetime.utcnow().isoformat()
    decision = state.get("user_decision", "")
    iteration = state.get("iteration_count", 0)
    max_iter  = state.get("max_iterations", 5)

    # Guard: if research_more but max iterations reached, force terminate
    if decision == "research_more" and iteration >= max_iter:
        print(f"[UserReview] Max iterations ({max_iter}) reached — terminating")
        decision = "terminate"

    print(f"[UserReview] Decision received: {decision}")

    log_entry = {
        "timestamp": now,
        "node":      "user_review",
        "action":    f"decision_{decision}",
        "detail":    f"iteration={iteration}, decision={decision}"
    }

    return {
        "user_decision": decision,
        "session_log":   [*state.get("session_log", []), log_entry],
    }


def display_summary(state: MASARPSState) -> None:
    print("\n" + "="*60)
    print("RESEARCH SUMMARY")
    print("="*60)
    print(f"\nTopics: {state.get('topics', [])}")
    print(f"Confidence Score: {state.get('confidence_score', 0.0)}")
    print(f"Iteration: {state.get('iteration_count', 0)}")
    print(f"\nOVERVIEW:\n{state.get('overview_text', '')}")
    print(f"\nKEY POINTS:")

    for kp in state.get("key_points", []):
        citations = [
            f"({c['author']}, {c['year']})"
            for c in kp.get("citations", [])
        ]
        print(f"\n  [{kp['id']}] {kp['statement']}")
        print(f"  Citations:  {', '.join(citations)}")
        print(f"  Confidence: {kp.get('confidence', 0.0)}")

        # ── Show expansion if it exists ───────────────────
        if kp.get("expanded") and kp.get("expansion_text"):
            print(f"\n  ── EXPANDED ANALYSIS ──")
            print(f"  {kp['expansion_text']}")
            print(f"  ── END EXPANSION ──")

    print("\n" + "="*60)
    print("OPTIONS:")
    print("  approve       — proceed to slide generation")
    print("  research_more — search for additional content")
    print("  expand_point  — deep dive on a specific key point")
    print("  terminate     — end session")
    print("="*60 + "\n")