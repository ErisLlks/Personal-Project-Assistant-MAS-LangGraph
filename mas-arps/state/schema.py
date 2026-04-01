from typing import TypedDict, Literal, Optional
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────
# Source Metadata
# ─────────────────────────────────────────────────────────────

class SourceMeta(TypedDict):
    author: str
    year: str
    title: str
    source: str                  # "local" | "drive" | "web" | "academic"
    url: Optional[str]
    page: Optional[str]
    chunk_id: str                # unique hash of retrieved chunk


# ─────────────────────────────────────────────────────────────
# Key Research Point
# ─────────────────────────────────────────────────────────────

class KeyPoint(TypedDict):
    id: str                      # "kp_01" ... "kp_10"
    statement: str
    citations: list[SourceMeta]
    confidence: float            # 0.0 – 1.0
    expanded: bool
    expansion_text: Optional[str]


# ─────────────────────────────────────────────────────────────
# Slide Structure
# ─────────────────────────────────────────────────────────────

class SlideContent(TypedDict):
    slide_number: int
    title: str
    bullets: list[str]           # max 6 bullets, max 15 words each
    speaker_notes: str
    citations: list[str]         # in-text APA strings e.g. "(Smith, 2022)"
    references: list[str]        # full APA reference strings


# ─────────────────────────────────────────────────────────────
# Session Logging
# ─────────────────────────────────────────────────────────────

class SessionLog(TypedDict):
    timestamp: str
    node: str
    action: str
    detail: Optional[str]


# ─────────────────────────────────────────────────────────────
# MAS ARPS State Schema
# ─────────────────────────────────────────────────────────────

class MASARPSState(TypedDict):
    # ── Identity ──────────────────────────────────────────
    session_id:          str
    topics:              list

    # ── Source Configuration ──────────────────────────────
    sources_selected:    list
    local_path:          Optional[str]
    drive_folder_id:     Optional[str]

    # ── Research State ────────────────────────────────────
    retrieved_chunks:    list
    ingested_chunk_ids:  set
    iteration_count:     int
    max_iterations:      int

    # ── Summary Output ────────────────────────────────────
    overview_text:       str
    key_points:          list
    confidence_score:    float

    # ── User Decision ─────────────────────────────────────
    user_decision:       str
    expand_target_id:    Optional[str]

    # ── Presentation ──────────────────────────────────────
    slides:              list
    citation_style:      str
    template_path:       str
    output_path:         str

    # ── Validation ────────────────────────────────────────
    validation_passed:   bool
    validation_errors:   list
    correction_attempts: int        # ← NEW: tracks self-correction loop

    # ── Logging ───────────────────────────────────────────
    session_log:         list
    error:               Optional[str]