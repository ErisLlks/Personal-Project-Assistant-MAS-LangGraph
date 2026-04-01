import os
import hashlib
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}

def query_local_index(local_path: str, topics: list) -> list:
    """
    Index and query local folder documents using LlamaIndex.
    Returns a list of chunk dicts ready for ingestion.
    """
    from llama_index.core import (
        VectorStoreIndex,
        SimpleDirectoryReader,
        Settings,
    )
    from llama_index.core.node_parser import SentenceSplitter

    chunks = []

    if not local_path or not os.path.isdir(local_path):
        print(f"[LocalIndex] Path not found: {local_path}")
        return chunks

    # ── Find supported files ──────────────────────────────
    files = [
        f for f in Path(local_path).rglob("*")
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print(f"[LocalIndex] No supported files found in {local_path}")
        return chunks

    print(f"[LocalIndex] Found {len(files)} files in {local_path}")

    try:
        # ── Load documents ────────────────────────────────
        reader = SimpleDirectoryReader(
            input_dir=local_path,
            recursive=True,
            required_exts=list(SUPPORTED_EXTENSIONS),
        )
        documents = reader.load_data()
        print(f"[LocalIndex] Loaded {len(documents)} documents")

        # ── Build index ───────────────────────────────────
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        index    = VectorStoreIndex.from_documents(
            documents,
            transformations=[splitter],
            show_progress=False,
        )

        # ── Query index for each topic ────────────────────
        retriever = index.as_retriever(similarity_top_k=5)

        for topic in topics:
            print(f"[LocalIndex] Querying for: '{topic}'")
            nodes = retriever.retrieve(topic)

            for node in nodes:
                text     = node.get_content()
                metadata = node.metadata or {}

                chunk_id  = hashlib.sha256(text.encode()).hexdigest()
                file_name = metadata.get("file_name", "Unknown Document")
                page_num  = str(metadata.get("page_label", ""))
                author    = metadata.get("author", "Unknown")
                year      = str(metadata.get("creation_date", "")[:4]) \
                            if metadata.get("creation_date") else "n/a"

                chunks.append({
                    "chunk_id":   chunk_id,
                    "text":       text,
                    "title":      file_name,
                    "url":        "",
                    "source":     "local",
                    "author":     author,
                    "year":       year,
                    "venue":      "Local Document",
                    "similarity": float(node.score) if node.score else 0.75,
                    "page":       page_num,
                })
                print(f"  [+] {file_name} (page {page_num}, score {node.score:.2f})")

    except Exception as e:
        print(f"  [!] Local index error: {e}")

    print(f"[LocalIndex] {len(chunks)} chunks retrieved")
    return chunks