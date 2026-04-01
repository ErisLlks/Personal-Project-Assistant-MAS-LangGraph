import os
import json
import datetime
from litellm import completion
from state.schema import MASARPSState

SUMMARY_SYSTEM_PROMPT = """
You are an academic research synthesizer.
Given retrieved document chunks, produce a JSON object with EXACTLY this structure:
{
  "overview": "string — 150 to 250 words, formal academic tone",
  "key_points": [
    {
      "id": "kp_01",
      "statement": "one clear academic sentence",
      "citations": [
        {
          "author": "Last, F.",
          "year": "2023",
          "title": "Source title",
          "source": "web or academic",
          "url": "url or empty string",
          "page": "page number or empty string",
          "chunk_id": "chunk id string",
          "similarity": 0.85
        }
      ],
      "confidence": 0.85,
      "expanded": false,
      "expansion_text": null
    }
  ]
}
STRICT RULES:
- Return ONLY the JSON object. No markdown, no explanation, no backticks.
- Generate between 5 and 10 key points.
- Every key point must cite at least one chunk from the provided context.
- Do NOT fabricate authors, journals, or years.
- Use formal, objective, evidence-based language.
- Acknowledge contradictory evidence where present.
"""

def format_chunks(chunks: list) -> str:
    formatted = []
    for i, c in enumerate(chunks[:15]):  # cap at 15 chunks
        formatted.append(
            f"[Chunk {i+1}] Source: {c.get('source','unknown')} | "
            f"Author: {c.get('author','Unknown')} | "
            f"Year: {c.get('year','n/a')} | "
            f"Title: {c.get('title','Untitled')}\n"
            f"{c.get('text','')[:800]}\n"
        )
    return "\n---\n".join(formatted)

def compute_confidence(key_points: list) -> float:
    import datetime
    scores = []
    current_year = datetime.datetime.now().year
    for kp in key_points:
        citations = kp.get("citations", [])
        if not citations:
            scores.append(0.0)
            continue
        source_score = min(len(citations) / 5.0, 1.0)
        years = [int(c["year"]) for c in citations
                 if str(c.get("year","")).isdigit()]
        recency = max(0.0, 1.0 - ((current_year - (sum(years)/len(years))) / 20.0)) \
                  if years else 0.0
        sims = [c.get("similarity", 0.7) for c in citations]
        similarity = sum(sims) / len(sims)
        scores.append((source_score * 0.4) + (recency * 0.3) + (similarity * 0.3))
    return round(sum(scores) / len(scores), 3) if scores else 0.0

def summary_node(state: MASARPSState) -> dict:
    chunks  = state.get("retrieved_chunks", [])
    topics  = state.get("topics", [])
    now     = datetime.datetime.utcnow().isoformat()

    if not chunks:
        raise ValueError("SummaryAgent: no retrieved chunks to summarize")

    context = format_chunks(chunks)
    user_msg = f"Topics: {topics}\n\nRetrieved Content:\n{context}"

    print("[Summary] Calling LLM for synthesis...")

    response = completion(
        model=os.getenv("LLM_PROVIDER", "groq/llama-3.3-70b-versatile"),
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg}
        ],
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    parsed     = json.loads(raw)
    key_points = parsed.get("key_points", [])
    confidence = compute_confidence(key_points)

    print(f"[Summary] Generated {len(key_points)} key points | confidence: {confidence}")

    log_entry = {
        "timestamp": now,
        "node":      "summary",
        "action":    "summary_generated",
        "detail":    f"{len(key_points)} key points, confidence={confidence}"
    }

    return {
        "overview_text":   parsed.get("overview", ""),
        "key_points":      key_points,
        "confidence_score": confidence,
        "session_log":     [*state.get("session_log", []), log_entry],
    }