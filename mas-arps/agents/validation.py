import datetime
from state.schema import MASARPSState

VAGUE_TITLES = {
    "more information", "details", "overview", "introduction",
    "conclusion", "summary", "slide", "content", "information",
    "background", "other", "misc", "additional", "untitled"
}

MAX_CORRECTION_ATTEMPTS = 3

def validation_node(state: MASARPSState) -> dict:
    slides   = state.get("slides", [])
    now      = datetime.datetime.utcnow().isoformat()
    errors   = []
    warnings = []

    # ── Guard: too many correction attempts ───────────────
    correction_attempts = state.get("correction_attempts", 0)
    if correction_attempts >= MAX_CORRECTION_ATTEMPTS:
        print(f"[Validation] Max correction attempts ({MAX_CORRECTION_ATTEMPTS}) reached — forcing export")
        log_entry = {
            "timestamp": now,
            "node":      "validation",
            "action":    "validation_forced_pass",
            "detail":    f"max correction attempts reached"
        }
        return {
            "validation_passed":     True,
            "validation_errors":     [],
            "correction_attempts":   correction_attempts,
            "session_log":           [*state.get("session_log", []), log_entry],
        }

    print(f"[Validation] Checking {len(slides)} slides "
          f"(attempt {correction_attempts + 1}/{MAX_CORRECTION_ATTEMPTS})...")

    # ── Check 1: slide count ──────────────────────────────
    if len(slides) < 10:
        errors.append(
            f"CRITICAL: Too few slides ({len(slides)}). "
            f"Generate at least 10 slides total."
        )
    if len(slides) > 20:
        errors.append(
            f"CRITICAL: Too many slides ({len(slides)}). "
            f"Maximum is 20 slides."
        )

    # ── Check 2: references slide ─────────────────────────
    has_references = any(
        "reference" in s.get("title", "").lower()
        for s in slides
    )
    if not has_references:
        errors.append(
            "CRITICAL: No References slide found. "
            "Add a final slide titled 'References' with APA citations."
        )

    # ── Per-slide checks ──────────────────────────────────
    all_inline     = []
    all_references = []

    for slide in slides:
        num      = slide.get("slide_number", "?")
        title    = slide.get("title", "").strip()
        bullets  = slide.get("bullets", [])
        notes    = slide.get("speaker_notes", "")
        citations = slide.get("citations", [])
        refs     = slide.get("references", [])

        all_inline.extend(citations)
        all_references.extend(refs)

        # Check 3: bullet count
        if len(bullets) > 6:
            errors.append(
                f"Slide {num} '{title}': has {len(bullets)} bullets. "
                f"Reduce to maximum 6 bullets."
            )

        # Check 4: bullet word count
        for i, b in enumerate(bullets):
            wc = len(b.split())
            if wc > 15:
                errors.append(
                    f"Slide {num} '{title}': bullet {i+1} has {wc} words. "
                    f"Shorten to maximum 15 words: '{b[:50]}...'"
                )

        # Check 5: speaker notes
        if not notes or len(notes.strip()) < 20:
            errors.append(
                f"Slide {num} '{title}': speaker notes are missing or too short. "
                f"Write at least 2 full academic sentences."
            )

        # Check 6: vague title
        if title.lower() in VAGUE_TITLES or not title:
            errors.append(
                f"Slide {num}: title '{title}' is vague or empty. "
                f"Use a descriptive, informative title."
            )

        # Check 7: citations on conceptual slides
        is_title   = slide.get("slide_number") == 1
        is_refs    = "reference" in title.lower()
        is_obj     = "objective" in title.lower()

        if not is_title and not is_refs and not is_obj:
            if not citations:
                errors.append(
                    f"Slide {num} '{title}': missing in-text citations. "
                    f"Add at least one APA citation e.g. (Author, Year)."
                )

        # Check 8: placeholder text
        full_text = f"{title} {' '.join(bullets)} {notes}".lower()
        for flag in ["[placeholder]", "[insert", "[tbd]", "[todo]",
                     "[add here]", "[content here]", "lorem ipsum"]:
            if flag in full_text:
                errors.append(
                    f"Slide {num} '{title}': contains placeholder text '{flag}'. "
                    f"Replace with real academic content."
                )

    # ── Check 9: references alphabetically ordered ────────
    ref_slide = next(
        (s for s in slides if "reference" in s.get("title", "").lower()),
        None
    )
    if ref_slide:
        ref_bullets = ref_slide.get("bullets", [])
        if ref_bullets and ref_bullets != sorted(ref_bullets):
            errors.append(
                "References slide is not alphabetically ordered. "
                "Sort all references A-Z by author last name."
            )

    # ── Check 10: cross-check inline vs references ────────
    for inline in set(all_inline):
        # Extract author name from "(Author, Year)" format
        author_part = inline.strip("()").split(",")[0].strip()
        if not any(author_part.lower() in ref.lower()
                   for ref in all_references):
            warnings.append(
                f"In-text citation '{inline}' may not appear "
                f"in References slide."
            )

    # ── Result ────────────────────────────────────────────
    passed = len(errors) == 0

    if passed:
        print(f"[Validation] ✓ All checks passed")
        if warnings:
            print(f"[Validation] {len(warnings)} warning(s):")
            for w in warnings:
                print(f"  ⚠ {w}")
    else:
        print(f"[Validation] ✗ {len(errors)} error(s) found:")
        for e in errors:
            print(f"  - {e}")

    log_entry = {
        "timestamp": now,
        "node":      "validation",
        "action":    "validation_complete",
        "detail":    f"passed={passed}, errors={len(errors)}, "
                     f"warnings={len(warnings)}, attempt={correction_attempts + 1}"
    }

    return {
        "validation_passed":   passed,
        "validation_errors":   errors,
        "correction_attempts": correction_attempts + 1,
        "session_log":         [*state.get("session_log", []), log_entry],
    }