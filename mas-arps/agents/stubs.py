import datetime
from state.schema import MASARPSState

def log(state: MASARPSState, node: str) -> list:
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "node": node,
        "action": "stub_called",
        "detail": f"{node} stub executed successfully"
    }
    return [*state.get("session_log", []), entry]

def user_review_node(state: MASARPSState) -> dict:
    print("✓ user_review_node stub called")
    return {
        "user_decision": "approve",
        "session_log": log(state, "user_review")
    }

def keypoint_expand_node(state: MASARPSState) -> dict:
    print("✓ keypoint_expand_node stub called")
    return {"session_log": log(state, "expand_point")}

def validation_node(state: MASARPSState) -> dict:
    print("✓ validation_node stub called")
    return {
        "validation_passed": True,
        "validation_errors": [],
        "session_log": log(state, "validation")
    }