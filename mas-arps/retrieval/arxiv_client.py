import requests
import hashlib
import datetime
import time
import xml.etree.ElementTree as ET

ARXIV_URL = "http://export.arxiv.org/api/query"
ATOM_NS   = "http://www.w3.org/2005/Atom"

def query_arxiv(topics: list, iteration: int = 0) -> list:
    chunks = []

    for topic in topics:
        try:
            print(f"[arXiv] Querying: '{topic}'...")

            # ── Rate limit protection ─────────────────────
            time.sleep(1)

            params = {
                "search_query": f"all:{topic}",
                "start":        iteration * 5,
                "max_results":  5,
                "sortBy":       "relevance",
                "sortOrder":    "descending",
            }

            resp = requests.get(
                ARXIV_URL,
                params=params,
                timeout=15,
            )
            resp.raise_for_status()

            # ── Parse XML ─────────────────────────────────
            root    = ET.fromstring(resp.content)
            entries = root.findall(f"{{{ATOM_NS}}}entry")
            print(f"[arXiv] Got {len(entries)} entries")

            for entry in entries:
                def get(tag):
                    el = entry.find(f"{{{ATOM_NS}}}{tag}")
                    return el.text.strip() if el is not None and el.text else ""

                title_text   = get("title").replace("\n", " ")
                summary_text = get("summary").replace("\n", " ")
                url          = get("id")
                published    = get("published")
                year_str     = published[:4] if published else \
                               str(datetime.datetime.now().year)

                if not summary_text:
                    print(f"  [!] Skipping entry with no summary")
                    continue

                # ── Authors ───────────────────────────────
                author_els  = entry.findall(f"{{{ATOM_NS}}}author")
                author_names = []
                for a in author_els:
                    name = a.find(f"{{{ATOM_NS}}}name")
                    if name is not None and name.text:
                        author_names.append(name.text.strip())

                author_str = author_names[0] if author_names else "Unknown"
                chunk_id   = hashlib.sha256(summary_text.encode()).hexdigest()

                chunks.append({
                    "chunk_id":   chunk_id,
                    "text":       summary_text,
                    "title":      title_text,
                    "url":        url,
                    "source":     "academic",
                    "author":     author_str,
                    "year":       year_str,
                    "venue":      "arXiv preprint",
                    "similarity": 0.80,
                })
                print(f"  [+] {title_text[:60]} ({year_str})")

        except requests.exceptions.Timeout:
            print(f"  [!] arXiv timeout for '{topic}'")
        except requests.exceptions.RequestException as e:
            print(f"  [!] arXiv request error: {e}")
        except ET.ParseError as e:
            print(f"  [!] arXiv XML parse error: {e}")
        except Exception as e:
            print(f"  [!] arXiv unexpected error: {e}")

    print(f"[arXiv] {len(chunks)} chunks retrieved")
    return chunks