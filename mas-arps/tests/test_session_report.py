from dotenv import load_dotenv
load_dotenv()

import uuid
import json
from graph.graph import graph

def print_session_report(final_state: dict) -> None:
    """
    Print a full traceability report from the session log.
    Satisfies NFR-2: full session traceability.
    """
    log = final_state.get("session_log", [])

    print(f"\n{'='*60}")
    print(f"  SESSION TRACEABILITY REPORT")
    print(f"{'='*60}")
    print(f"  Session ID:    {final_state.get('session_id')}")
    print(f"  Topics:        {final_state.get('topics')}")
    print(f"  Sources used:  {final_state.get('sources_selected')}")
    print(f"  Iterations:    {final_state.get('iteration_count')}")
    print(f"  Confidence:    {final_state.get('confidence_score')}")
    print(f"  Slides:        {len(final_state.get('slides', []))}")
    print(f"  Validation:    {final_state.get('validation_passed')}")
    print(f"  Corrections:   {final_state.get('correction_attempts', 0)}")
    print(f"\n  AGENT EXECUTION LOG:")
    print(f"  {'-'*50}")

    for entry in log:
        print(f"  [{entry['timestamp']}]")
        print(f"    Node:   {entry['node']}")
        print(f"    Action: {entry['action']}")
        if entry.get("detail"):
            print(f"    Detail: {entry['detail']}")

    print(f"\n  KEY POINTS WITH CITATIONS:")
    print(f"  {'-'*50}")
    for kp in final_state.get("key_points", []):
        print(f"\n  [{kp['id']}] {kp['statement']}")
        for c in kp.get("citations", []):
            print(f"    - {c.get('author')} ({c.get('year')}) "
                  f"— {c.get('title', '')[:50]}")
        if kp.get("expanded"):
            print(f"    [EXPANDED] {kp.get('expansion_text', '')[:100]}...")

    print(f"\n  CHUNKS RETRIEVED: {len(final_state.get('retrieved_chunks', []))}")
    by_source = {}
    for c in final_state.get("retrieved_chunks", []):
        src = c.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
    for src, count in by_source.items():
        print(f"    {src}: {count} chunks")

    print(f"\n{'='*60}\n")


def test_with_report():
    session_id = str(uuid.uuid4())
    config     = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "session_id":          "",
        "topics":              ["Machine Learning in Healthcare"],
        "sources_selected":    ["web", "academic"],
        "local_path":          None,
        "drive_folder_id":     None,
        "retrieved_chunks":    [],
        "ingested_chunk_ids":  set(),
        "iteration_count":     0,
        "max_iterations":      5,
        "overview_text":       "",
        "key_points":          [],
        "confidence_score":    0.0,
        "user_decision":       "",
        "expand_target_id":    None,
        "slides":              [],
        "citation_style":      "APA7",
        "template_path":       "",
        "output_path":         "output/report_test.pptx",
        "validation_passed":   False,
        "validation_errors":   [],
        "correction_attempts": 0,
        "session_log":         [],
        "error":               None,
    }

    result = graph.invoke(initial_state, config)

    # Auto approve for report test
    graph.update_state(config, {"user_decision": "approve"})
    final = graph.invoke(None, config)

    print_session_report(final)


if __name__ == "__main__":
    test_with_report()