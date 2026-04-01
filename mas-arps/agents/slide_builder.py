import os
import json
import datetime
from litellm import completion
from state.schema import MASARPSState

SLIDE_STRUCTURE = [
    "Title Slide",
    "Learning Objectives",
    "Background / Context",
    "Literature Review",
    "Core Concepts / Theory",
    "Analysis / Discussion",
    "Applications / Case Studies",
    "Limitations",
    "Future Directions",
    "Conclusion",
    "References"
]

SLIDE_SYSTEM_PROMPT = f"""
You are an academic slide architect generating university-level presentations.
Required slide structure (in this order): {SLIDE_STRUCTURE}

Output a JSON array of slide objects with EXACTLY this structure:
[
  {{
    "slide_number": 1,
    "title": "Descriptive slide title",
    "bullets": ["bullet 1", "bullet 2"],
    "speaker_notes": "Full academic explanation in complete sentences with citations.",
    "citations": ["(Author, Year)"],
    "references": ["Author, F. (Year). Title. Journal, vol(issue), pages."]
  }}
]

STRICT EDITORIAL RULES — VIOLATIONS WILL CAUSE REJECTION:
- Return ONLY the JSON array. No markdown, no backticks, no explanation.
- Generate between 10 and 20 slides total.
- Maximum 6 bullets per slide — exceeding this WILL be rejected.
- Maximum 15 words per bullet — exceeding this WILL be rejected.
- Parallel grammatical structure across bullets.
- Every slide title must be descriptive and specific — never vague.
- Speaker notes: minimum 2 full academic sentences per slide.
- At least one APA in-text citation per conceptual slide e.g. (Smith, 2022).
- References slide must be the LAST slide, alphabetically ordered, APA 7th edition.
- No placeholder text, no [TBD], no [Insert here].
- No unsupported claims.
"""

def slide_builder_node(state: MASARPSState) -> dict:
    key_points = state.get("key_points", [])
    overview   = state.get("overview_text", "")
    topics     = state.get("topics", [])
    errors     = state.get("validation_errors", [])
    attempts   = state.get("correction_attempts", 0)
    now        = datetime.datetime.utcnow().isoformat()

    # ── Build key points context ──────────────────────────
    kp_text = "\n".join([
        f"- [{kp['id']}] {kp['statement']} "
        f"(Citations: {[c['author'] + ' ' + c['year'] for c in kp.get('citations', [])]})"
        + (f"\n  EXPANSION: {kp['expansion_text']}"
           if kp.get("expanded") and kp.get("expansion_text") else "")
        for kp in key_points
    ])

    # ── Build correction instruction if needed ────────────
    correction_note = ""
    if errors and attempts > 0:
        correction_note = (
            f"\n\nCRITICAL — THIS IS CORRECTION ATTEMPT {attempts}.\n"
            f"Your previous output was REJECTED for these specific reasons:\n"
            + "\n".join([f"  - {e}" for e in errors])
            + "\n\nFix ALL of the above issues. Do not repeat these mistakes."
        )

    user_msg = (
        f"Topics: {topics}\n\n"
        f"Overview:\n{overview}\n\n"
        f"Key Points:\n{kp_text}"
        f"{correction_note}"
    )

    action = "correction" if attempts > 0 else "initial generation"
    print(f"[SlideBuilder] Slide {action} (attempt {attempts + 1})...")

    response = completion(
        model=os.getenv("LLM_PROVIDER", "groq/llama-3.3-70b-versatile"),
        messages=[
            {"role": "system", "content": SLIDE_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=8192,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        slides = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[SlideBuilder] JSON parse error: {e}")
        print(f"[SlideBuilder] Raw response: {raw[:200]}...")
        slides = state.get("slides", [])  # keep previous if parse fails

    print(f"[SlideBuilder] Generated {len(slides)} slides")

    log_entry = {
        "timestamp": now,
        "node":      "slide_builder",
        "action":    f"slides_{action.replace(' ', '_')}",
        "detail":    f"{len(slides)} slides, attempt={attempts + 1}"
    }

    return {
        "slides":      slides,
        "session_log": [*state.get("session_log", []), log_entry],
    }