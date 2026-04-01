from dotenv import load_dotenv
load_dotenv()

from graph.graph import graph
from agents.user_review import display_summary
import uuid

def test_end_to_end():
    session_id = str(uuid.uuid4())
    config     = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "session_id":         "",
        "topics":             ["Machine Learning in Healthcare"],
        "sources_selected":   ["web","academic"],
        "local_path":         None,
        "drive_folder_id":    None,
        "retrieved_chunks":   [],
        "ingested_chunk_ids": set(),
        "iteration_count":    0,
        "max_iterations":     5,
        "overview_text":      "",
        "key_points":         [],
        "confidence_score":   0.0,
        "user_decision":      "",
        "expand_target_id":   None,
        "slides":             [],
        "citation_style":     "APA7",
        "template_path":      "",
        "output_path":        "output/test_presentation.pptx",
        "validation_passed":  False,
        "validation_errors":  [],
        "session_log":        [],
        "correction_attempts": 0,   
        "error":              None,
    }

    print("\n── Running Phase 2 end-to-end test ──\n")

    # ── First run until interrupt ─────────────────────────
    result = graph.invoke(initial_state, config)

    # ── Interactive loop ──────────────────────────────────
    while True:
        display_summary(result)

        decision = input("Enter your decision: ").strip().lower()

        # Validate input
        if decision not in ["approve", "research_more", "expand_point", "terminate"]:
            print(f"  [!] Invalid option. Choose: approve / research_more / expand_point / terminate")
            continue

        expand_id = None
        if decision == "expand_point":
            kp_ids = [kp["id"] for kp in result.get("key_points", [])]
            print(f"  Available key point IDs: {kp_ids}")
            expand_id = input("  Enter key point ID to expand: ").strip()
            if expand_id not in kp_ids:
                print(f"  [!] '{expand_id}' not found. Try again.")
                continue

        # Resume graph with decision
        graph.update_state(config, {
            "user_decision":    decision,
            "expand_target_id": expand_id,
        })

        result = graph.invoke(None, config)

        # Check if graph has finished
        if decision == "approve" or decision == "terminate":
            break

        # After research_more or expand_point, loop back
        # to display the updated summary
        print(f"\n[Test] Looping back to review updated summary...\n")

    # ── Final results ─────────────────────────────────────
    print("\n── Final Results ──")
    print(f"Slides generated:  {len(result.get('slides', []))}")
    print(f"Validation passed: {result.get('validation_passed')}")

    errors = result.get("validation_errors", [])
    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  - {e}")

    print(f"Output file:       {result.get('output_path')}")
    print(f"\n✓ Phase 2 test complete")

if __name__ == "__main__":
    test_end_to_end()