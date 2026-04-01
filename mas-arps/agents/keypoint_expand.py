import os
import hashlib
import datetime
from tavily import TavilyClient
from litellm import completion
from state.schema import MASARPSState

EXPAND_SYSTEM_PROMPT = """
You are an academic research specialist performing a deep-dive analysis.
You will be given a key point statement and additional retrieved content.
Your task is to produce an expanded academic explanation of that key point.

Output a JSON object with EXACTLY this structure:
{
  "expansion_text": "200-400 word academic expansion in full sentences",
  "additional_citations": [
    {
      "author": "Last, F.",
      "year": "2023",
      "title": "Source title",
      "source": "web or academic",
      "url": "url or empty string",
      "page": "page or empty string",
      "chunk_id": "chunk id",
      "similarity": 0.85
    }
  ]
}

RULES:
- Return ONLY the JSON object. No markdown, no backticks.
- Expansion must be 200-400 words in formal academic language.
- Every claim must be supported by the provided context.
- Do NOT fabricate authors, years, or journals.
- Include definitions, mechanisms, current research, and limitations.
"""

def keypoint_expand_node(state: MASARPSState) -> dict:
    target_id    = state.get("expand_target_id")
    key_points   = state.get("key_points", [])
    topics       = state.get("topics", [])
    sources      = set(state.get("sources_selected", []))
    seen_ids     = set(state.get("ingested_chunk_ids", set()))
    existing     = list(state.get("retrieved_chunks", []))
    now          = datetime.datetime.utcnow().isoformat()

    # ── Find the target key point ─────────────────────────
    target_kp = next(
        (kp for kp in key_points if kp["id"] == target_id),
        None
    )

    if not target_kp:
        print(f"[ExpandAgent] Key point '{target_id}' not found — skipping")
        return {
            "user_decision":   "",
            "expand_target_id": None,
            "session_log": [*state.get("session_log", []), {
                "timestamp": now,
                "node":      "expand_point",
                "action":    "expand_skipped",
                "detail":    f"target_id '{target_id}' not found"
            }],
        }

    print(f"[ExpandAgent] Expanding: [{target_id}] {target_kp['statement'][:60]}...")

    # ── Focused retrieval on this key point ───────────────
    new_chunks = []
    if "web" in sources:
        try:
            client  = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            # Use the key point statement as a focused query
            query   = f"{target_kp['statement']} {' '.join(topics)}"
            results = client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_raw_content=True,
            )
            for r in results.get("results", []):
                text = r.get("content") or r.get("raw_content") or ""
                if not text.strip():
                    continue
                chunk_id = hashlib.sha256(text.encode()).hexdigest()
                if chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)
                new_chunks.append({
                    "chunk_id":   chunk_id,
                    "text":       text,
                    "title":      r.get("title", ""),
                    "url":        r.get("url", ""),
                    "source":     "web",
                    "author":     "Unknown",
                    "year":       str(datetime.datetime.now().year),
                    "similarity": r.get("score", 0.7),
                })
                print(f"  [+] {r.get('title', '')[:60]}")
        except Exception as e:
            print(f"  [!] Tavily error during expand: {e}")

    print(f"[ExpandAgent] {len(new_chunks)} new focused chunks retrieved")

    # ── Build context for LLM ─────────────────────────────
    # Use new chunks + original citations context
    context_chunks = new_chunks if new_chunks else existing[:5]
    context = "\n---\n".join([
        f"[Source] {c.get('title','Untitled')} | "
        f"{c.get('author','Unknown')} | {c.get('year','n/a')}\n"
        f"{c.get('text','')[:800]}"
        for c in context_chunks
    ])

    user_msg = (
        f"Key Point to expand: {target_kp['statement']}\n\n"
        f"Topic context: {topics}\n\n"
        f"Retrieved content:\n{context}"
    )

    # ── Call LLM for expansion ────────────────────────────
    print("[ExpandAgent] Calling LLM for expansion...")
    import json

    response = completion(
        model=os.getenv("LLM_PROVIDER", "groq/llama-3.3-70b-versatile"),
        messages=[
            {"role": "system", "content": EXPAND_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=2048,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    parsed           = json.loads(raw)
    expansion_text   = parsed.get("expansion_text", "")
    extra_citations  = parsed.get("additional_citations", [])

    print(f"[ExpandAgent] Expansion generated ({len(expansion_text)} chars)")

    # ── Update the target key point ───────────────────────
    updated_key_points = [
        {
            **kp,
            "expansion_text": expansion_text,
            "expanded":       True,
            "citations":      kp.get("citations", []) + extra_citations,
        }
        if kp["id"] == target_id else kp
        for kp in key_points
    ]

    log_entry = {
        "timestamp": now,
        "node":      "expand_point",
        "action":    "expansion_complete",
        "detail":    f"target={target_id}, new_chunks={len(new_chunks)}"
    }

    return {
        "key_points":         updated_key_points,
        "retrieved_chunks":   existing + new_chunks,
        "ingested_chunk_ids": seen_ids,
        "user_decision":      "",      # ← clear so graph re-interrupts
        "expand_target_id":   None,    # ← clear after use
        "session_log":        [*state.get("session_log", []), log_entry],
    }