from dotenv import load_dotenv
load_dotenv()

import time
import uuid
from graph.graph import graph

def run_timed_test(topic: str, sources: list) -> dict:
    """
    Run a full automated pipeline pass and measure performance
    against NFR-3 targets from the requirements specification.
    """
    session_id = str(uuid.uuid4())
    config     = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "session_id":         "",
        "topics":             [topic],
        "sources_selected":   sources,
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
        "output_path":        f"output/perf_test_{session_id[:8]}.pptx",
        "validation_passed":  False,
        "validation_errors":  [],
        "correction_attempts": 0,
        "session_log":        [],
        "error":              None,
    }

    timings = {}

    # ── Phase 1: Research + Summary ───────────────────────
    print(f"\n[PerfTest] Topic: {topic}")
    print(f"[PerfTest] Sources: {sources}")
    print(f"[PerfTest] Running research + summary phase...")

    t0     = time.time()
    result = graph.invoke(initial_state, config)
    t1     = time.time()

    timings["research_summary_seconds"] = round(t1 - t0, 2)

    # ── Phase 2: Auto-approve and generate slides ─────────
    print(f"[PerfTest] Auto-approving and generating slides...")

    graph.update_state(config, {"user_decision": "approve"})

    t2    = time.time()
    final = graph.invoke(None, config)
    t3    = time.time()

    timings["slide_generation_seconds"] = round(t3 - t2, 2)
    timings["total_seconds"]            = round(t3 - t0, 2)

    # ── NFR-3 targets from requirements spec ──────────────
    # Research + summary: 120s normal, 180s MVP acceptable
    # Slide generation:   60s
    research_target = 180
    slides_target   = 60

    research_pass = timings["research_summary_seconds"] <= research_target
    slides_pass   = timings["slide_generation_seconds"] <= slides_target

    # ── Report ────────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  PERFORMANCE TEST REPORT")
    print(f"{'='*55}")
    print(f"  Topic:              {topic}")
    print(f"  Sources:            {sources}")
    print(f"  Chunks retrieved:   {len(final.get('retrieved_chunks', []))}")
    print(f"  Key points:         {len(final.get('key_points', []))}")
    print(f"  Slides generated:   {len(final.get('slides', []))}")
    print(f"  Confidence score:   {final.get('confidence_score', 0.0)}")
    print(f"  Validation passed:  {final.get('validation_passed')}")
    print(f"  Correction attempts:{final.get('correction_attempts', 0)}")
    print(f"{'='*55}")
    print(f"  TIMING RESULTS vs NFR-3 TARGETS:")
    print(f"{'='*55}")
    print(f"  Research + Summary: {timings['research_summary_seconds']}s "
          f"/ {research_target}s target "
          f"{'✓ PASS' if research_pass else '✗ FAIL'}")
    print(f"  Slide Generation:   {timings['slide_generation_seconds']}s "
          f"/ {slides_target}s target "
          f"{'✓ PASS' if slides_pass else '✗ FAIL'}")
    print(f"  Total:              {timings['total_seconds']}s")
    print(f"{'='*55}")

    if final.get("validation_errors"):
        print(f"\n  Validation errors:")
        for e in final["validation_errors"]:
            print(f"    - {e}")

    overall = research_pass and slides_pass
    print(f"\n  OVERALL: {'✓ ALL NFR-3 TARGETS MET' if overall else '✗ SOME TARGETS MISSED'}")
    print(f"{'='*55}\n")

    return {
        "timings":    timings,
        "passed":     overall,
        "final_state": final,
    }


if __name__ == "__main__":
    # ── Test 1: Web only ──────────────────────────────────
    run_timed_test(
        topic="Machine Learning in Healthcare",
        sources=["web"],
    )

    print("\nWaiting 5s before next test...\n")
    time.sleep(5)

    # ── Test 2: Web + Academic ────────────────────────────
    run_timed_test(
        topic="Neural Networks in Climate Science",
        sources=["web", "academic"],
    )