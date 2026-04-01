import os
import hashlib
import datetime
from tavily import TavilyClient
from state.schema import MASARPSState

def research_node(state: MASARPSState) -> dict:
    topics    = state.get("topics", [])
    sources   = set(state.get("sources_selected", []))
    seen_ids  = set(state.get("ingested_chunk_ids", set()))
    existing  = list(state.get("retrieved_chunks", []))
    iteration = state.get("iteration_count", 0)
    now       = datetime.datetime.utcnow().isoformat()
    new_chunks = []

    print(f"\n[Research] Iteration {iteration + 1} — sources: {sources}")

    # ── Helper: dedup and add chunks ──────────────────────
    def ingest(raw_chunks: list):
        count = 0
        for chunk in raw_chunks:
            cid = chunk.get("chunk_id") or \
                  hashlib.sha256(chunk.get("text","").encode()).hexdigest()
            chunk["chunk_id"] = cid
            if cid not in seen_ids:
                seen_ids.add(cid)
                new_chunks.append(chunk)
                count += 1
        return count

    # ── Source 1: Web (Tavily) ────────────────────────────
    if "web" in sources:
        try:
            from tavily import TavilyClient
            client  = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            web_chunks = []
            for topic in topics:
                results = client.search(
                    query=f"{topic} research {iteration + 1}",
                    search_depth="advanced",
                    max_results=5,
                    include_raw_content=True,
                )
                for r in results.get("results", []):
                    text = r.get("content") or r.get("raw_content") or ""
                    if not text.strip():
                        continue
                    web_chunks.append({
                        "chunk_id":   hashlib.sha256(text.encode()).hexdigest(),
                        "text":       text,
                        "title":      r.get("title", ""),
                        "url":        r.get("url", ""),
                        "source":     "web",
                        "author":     "Unknown",
                        "year":       str(datetime.datetime.now().year),
                        "venue":      "Web",
                        "similarity": r.get("score", 0.7),
                    })
            added = ingest(web_chunks)
            print(f"[Research] Web: {added} new chunks")
        except Exception as e:
            print(f"[Research] Web error: {e}")

    # ── Source 2: Academic (Semantic Scholar) ─────────────
    if "academic" in sources:
        try:
            from retrieval.semantic_scholar import query_semantic_scholar
            ss_chunks = query_semantic_scholar(topics, iteration)
            added     = ingest(ss_chunks)
            print(f"[Research] Semantic Scholar: {added} new chunks")
        except Exception as e:
            print(f"[Research] Semantic Scholar error: {e}")

    # ── Source 3: Academic (arXiv) ────────────────────────
    if "academic" in sources:
        try:
            from retrieval.arxiv_client import query_arxiv
            arxiv_chunks = query_arxiv(topics, iteration)
            added        = ingest(arxiv_chunks)
            print(f"[Research] arXiv: {added} new chunks")
        except Exception as e:
            print(f"[Research] arXiv error: {e}")

    # ── Source 4: Local Folder ────────────────────────────
    if "local" in sources:
        try:
            from retrieval.local_index import query_local_index
            local_chunks = query_local_index(
                state.get("local_path", ""),
                topics,
            )
            added = ingest(local_chunks)
            print(f"[Research] Local: {added} new chunks")
        except Exception as e:
            print(f"[Research] Local error: {e}")

    # ── Source 5: Google Drive ────────────────────────────
    if "drive" in sources:
        try:
            from retrieval.drive_index import query_drive_index
            drive_chunks = query_drive_index(
                state.get("drive_folder_id", ""),
                topics,
            )
            added = ingest(drive_chunks)
            print(f"[Research] Drive: {added} new chunks")
        except Exception as e:
            print(f"[Research] Drive error: {e}")

    total_new = len(new_chunks)
    print(f"[Research] Total new chunks this iteration: {total_new}")
    print(f"[Research] Total chunks in session: {len(existing) + total_new}")

    log_entry = {
        "timestamp": now,
        "node":      "research",
        "action":    "retrieval_complete",
        "detail":    f"iteration={iteration+1}, sources={list(sources)}, new_chunks={total_new}"
    }

    return {
        "retrieved_chunks":   existing + new_chunks,
        "ingested_chunk_ids": seen_ids,
        "iteration_count":    iteration + 1,
        "user_decision":      "",    # clear so graph re-interrupts
        "expand_target_id":   None,
        "session_log":        [*state.get("session_log", []), log_entry],
    }