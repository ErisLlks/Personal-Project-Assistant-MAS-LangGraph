import uuid
import datetime
from state.schema import MASARPSState

def session_init_node(state: MASARPSState) -> dict:
    topics = state.get("topics", [])

    # Validate FR-1: 1–5 topics required
    if not topics or len(topics) < 1 or len(topics) > 5:
        raise ValueError(f"FR-1 violation: expected 1–5 topics, got {len(topics)}")

    # Validate each topic is a non-empty string
    for t in topics:
        if not isinstance(t, str) or len(t.strip()) < 3:
            raise ValueError(f"FR-1 violation: invalid topic '{t}'")

    session_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()

    print(f"[SessionInit] Session started: {session_id}")
    print(f"[SessionInit] Topics: {topics}")

    return {
        "session_id":         session_id,
        "iteration_count":    0,
        "max_iterations":     int(__import__('os').getenv("MAX_ITERATIONS", 5)),
        "ingested_chunk_ids": set(),
        "retrieved_chunks":   [],
        "key_points":         [],
        "slides":             [],
        "validation_errors":  [],
        "validation_passed":  False,
        "overview_text":      "",
        "confidence_score":   0.0,
        "user_decision":      "",
        "expand_target_id":   None,
        "error":              None,
        "session_log": [{
            "timestamp": now,
            "node":      "session_init",
            "action":    "session_started",
            "detail":    f"{len(topics)} topic(s) registered"
        }],
    }