import requests
import hashlib
import datetime
import time

SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

def query_semantic_scholar(topics: list, iteration: int = 0) -> list:
    chunks = []

    for topic in topics:
        try:
            print(f"[SemanticScholar] Querying: '{topic}'...")

            # ── Rate limit protection ─────────────────────
            time.sleep(2)

            params = {
                "query":  topic,
                "limit":  5,
                "fields": "title,authors,year,abstract,venue,externalIds"
            }

            resp = requests.get(
                SEMANTIC_SCHOLAR_URL,
                params=params,
                timeout=15,
                headers={"User-Agent": "MAS-ARPS-Research-Tool/1.0"}
            )
            resp.raise_for_status()

            data = resp.json().get("data", [])
            print(f"[SemanticScholar] Got {len(data)} results")

            for paper in data:
                abstract = paper.get("abstract") or ""
                if not abstract.strip():
                    continue

                authors    = paper.get("authors", [])
                author_str = authors[0]["name"] if authors else "Unknown"
                ext_ids    = paper.get("externalIds") or {}
                doi        = ext_ids.get("DOI", "")
                url        = f"https://doi.org/{doi}" if doi else ""
                venue      = paper.get("venue") or "Unknown Journal"
                year       = str(paper.get("year") or datetime.datetime.now().year)
                chunk_id   = hashlib.sha256(abstract.encode()).hexdigest()

                chunks.append({
                    "chunk_id":   chunk_id,
                    "text":       abstract,
                    "title":      paper.get("title", "Untitled"),
                    "url":        url,
                    "source":     "academic",
                    "author":     author_str,
                    "year":       year,
                    "venue":      venue,
                    "similarity": 0.85,
                })
                print(f"  [+] {paper.get('title', '')[:60]} ({year})")

        except requests.exceptions.HTTPError as e:
            if "429" in str(e):
                print(f"  [!] Semantic Scholar rate limited — waiting 10s...")
                time.sleep(10)
            else:
                print(f"  [!] Semantic Scholar HTTP error: {e}")
        except Exception as e:
            print(f"  [!] Semantic Scholar error: {e}")

    print(f"[SemanticScholar] {len(chunks)} chunks retrieved")
    return chunks