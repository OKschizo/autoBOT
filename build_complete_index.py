"""
Build complete index merging docs + website + blog.
Creates new collection: "auto_finance_complete".
Keeps original "auto_finance_docs" untouched.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions


class CompleteIndexBuilder:
    """Builds complete index with all data sources."""

    def __init__(self) -> None:
        print("[BUILDER] Initializing CompleteIndexBuilder...", flush=True)
        self.chunker_size = 800
        self.chunker_overlap = 100

        chroma_path = "/app/chroma_db" if os.path.exists("/app/chroma_db") else "./chroma_db"
        print(f"[BUILDER] Setting up ChromaDB client at {chroma_path}...", flush=True)
        self.client = chromadb.PersistentClient(path=chroma_path)

        print("[BUILDER] Loading embedding function (all-MiniLM-L6-v2)...", flush=True)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        print("[BUILDER] Initialization complete.", flush=True)

        self.docs_path = Path("scraped_data/gitbook_data.json")
        self.website_path = Path("scraped_data/website/website_data.json")
        self.blog_path = Path("scraped_data/blog/blog_posts.json")

    # ------------------------------------------------------------------#
    # Loading helpers
    # ------------------------------------------------------------------#

    def _load_source_file(self, path: Path, expected_source: str) -> List[Dict[str, Any]]:
        if not path.exists():
            print(f"[WARN] No data found for {expected_source} at {path}", flush=True)
            return []

        with path.open("r", encoding="utf-8") as handle:
            try:
                records = json.load(handle)
            except json.JSONDecodeError as exc:
                print(f"[ERROR] Failed to parse {path}: {exc}", flush=True)
                return []

        normalized: List[Dict[str, Any]] = []
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue

            content = record.get("content") or ""
            if not content.strip():
                continue

            title = record.get("title") or record.get("url") or f"{expected_source}_{index}"
            url = record.get("url") or f"{expected_source}_{index}"

            metadata = record.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}

            normalized.append(
                {
                    "title": title,
                    "url": url,
                    "content": content,
                    "scraped_at": record.get("scraped_at"),
                    "metadata": metadata,
                    "source": record.get("source") or expected_source,
                }
            )

        print(f"[INFO] Loaded {len(normalized)} {expected_source} records", flush=True)
        return normalized

    def load_docs_data(self) -> List[Dict[str, Any]]:
        return self._load_source_file(self.docs_path, "gitbook")

    def load_website_data(self) -> List[Dict[str, Any]]:
        return self._load_source_file(self.website_path, "website")

    def load_blog_data(self) -> List[Dict[str, Any]]:
        return self._load_source_file(self.blog_path, "blog")

    # ------------------------------------------------------------------#
    # Chunk helpers
    # ------------------------------------------------------------------#

    def _build_chunk_metadata(
        self, record: Dict[str, Any], fallback_source: str
    ) -> Dict[str, Any]:
        metadata = dict(record.get("metadata") or {})
        metadata["source"] = record.get("source") or fallback_source
        if record.get("scraped_at"):
            metadata["scraped_at"] = record["scraped_at"]
        return metadata

    def _render_pool_summary(self, url: str, pool_data: Optional[Dict[str, Any]]) -> str:
        if not pool_data:
            return ""

        summary_lines: List[str] = []

        if "/pools/" in url:
            pool_name = url.split("/pools/")[-1]
            summary_lines.append(f"=== {pool_name.upper()} AUTOPOOL ===")
        elif url.endswith("/pools"):
            summary_lines.append("=== AUTOPOOLS OVERVIEW ===")
        elif url.endswith("/stoke"):
            summary_lines.append("=== STOKE STAKING OVERVIEW ===")
        elif url.endswith("/tokelp"):
            summary_lines.append("=== TOKELP OVERVIEW ===")
        else:
            summary_lines.append("=== LIVE POOL METRICS ===")

        mapping = [
            ("apy", "APY"),
            ("tvl", "TVL (Total Value Locked)"),
            ("daily_returns", "Daily Returns"),
            ("volume", "Total Automated Volume"),
        ]

        for key, label in mapping:
            if pool_data.get(key):
                summary_lines.append(f"{label}: {pool_data[key]}")

        tokens = pool_data.get("tokens")
        if isinstance(tokens, list) and tokens:
            summary_lines.append(f"Tokens: {', '.join(tokens)}")

        if pool_data.get("summary_metrics"):
            summary_lines.append(f"Summary Metrics: {pool_data['summary_metrics']}")

        return "\n".join(summary_lines)

    def chunk_content(
        self,
        content: str,
        title: str,
        url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        metadata = metadata or {}

        if len(content) <= self.chunker_size:
            return [
                {
                    "text": content,
                    "title": title,
                    "url": url,
                    "metadata": metadata,
                }
            ]

        paragraphs = content.split("\n\n")
        current_chunk = ""
        chunk_id = 0

        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > self.chunker_size and current_chunk:
                chunks.append(
                    {
                        "text": current_chunk.strip(),
                        "title": title,
                        "url": url,
                        "chunk_id": chunk_id,
                        "metadata": metadata,
                    }
                )

                words = current_chunk.split()
                overlap_text = (
                    " ".join(words[-self.chunker_overlap :])
                    if len(words) > self.chunker_overlap
                    else ""
                )
                current_chunk = (overlap_text + "\n\n" + paragraph).strip()
                chunk_id += 1
            else:
                current_chunk = (
                    current_chunk + "\n\n" + paragraph if current_chunk else paragraph
                )

        if current_chunk.strip():
            chunks.append(
                {
                    "text": current_chunk.strip(),
                    "title": title,
                    "url": url,
                    "chunk_id": chunk_id,
                    "metadata": metadata,
                }
            )

        return chunks

    def prepare_all_chunks(self) -> List[Dict[str, Any]]:
        all_chunks: List[Dict[str, Any]] = []

        docs = self.load_docs_data()
        website = self.load_website_data()
        blog = self.load_blog_data()

        print("\n[STEP] Chunking documentation...", flush=True)
        for doc in docs:
            metadata = self._build_chunk_metadata(doc, "gitbook")
            chunks = self.chunk_content(
                doc["content"],
                doc["title"],
                doc["url"],
                metadata,
            )
            all_chunks.extend(chunks)
        print(f"  Created {len(all_chunks)} doc chunks", flush=True)

        print("\n[STEP] Chunking website pages...", flush=True)
        website_chunk_start = len(all_chunks)
        for page in website:
            metadata = self._build_chunk_metadata(page, "website")
            pool_summary = self._render_pool_summary(page["url"], metadata.get("pool_data"))
            content = f"{pool_summary}\n\n{page['content']}".strip() if pool_summary else page["content"]

            chunks = self.chunk_content(
                content,
                page["title"],
                page["url"],
                metadata,
            )
            all_chunks.extend(chunks)
        print(f"  Created {len(all_chunks) - website_chunk_start} website chunks", flush=True)

        print("\n[STEP] Chunking blog posts...", flush=True)
        blog_chunk_start = len(all_chunks)
        for post in blog:
            metadata = self._build_chunk_metadata(post, "blog")
            chunks = self.chunk_content(
                post["content"],
                post["title"],
                post["url"],
                metadata,
            )
            all_chunks.extend(chunks)
        print(f"  Created {len(all_chunks) - blog_chunk_start} blog chunks", flush=True)

        print(f"\n[INFO] Total chunks prepared: {len(all_chunks)}", flush=True)
        return all_chunks

    # ------------------------------------------------------------------#
    # Build / verify
    # ------------------------------------------------------------------#

    def build_index(self) -> None:
        print("\n" + "=" * 60, flush=True)
        print("Building Complete Index", flush=True)
        print("=" * 60, flush=True)

        all_chunks = self.prepare_all_chunks()

        if not all_chunks:
            print("[ERROR] No chunks generated; aborting index build.", flush=True)
            return

        try:
            self.client.delete_collection(name="auto_finance_complete")
            print("[INFO] Deleted existing 'auto_finance_complete' collection", flush=True)
        except Exception:
            pass

        collection = self.client.create_collection(
            name="auto_finance_complete",
            embedding_function=self.embedding_function,
            metadata={"description": "Complete Auto Finance data: docs + website + blog"},
        )

        print("\n[STEP] Indexing chunks...", flush=True)
        batch_size = 100
        for index in range(0, len(all_chunks), batch_size):
            batch = all_chunks[index : index + batch_size]
            metadatas = []
            for chunk in batch:
                chunk_meta = dict(chunk["metadata"] or {})
                metadata_entry = {
                    "title": chunk["title"],
                    "url": chunk["url"],
                    "chunk_id": str(chunk.get("chunk_id", 0)),
                    "source": chunk_meta.get("source", "unknown"),
                }
                if "pool_data" in chunk_meta:
                    metadata_entry["has_live_data"] = "true"
                if chunk_meta.get("scraped_at"):
                    metadata_entry["scraped_at"] = chunk_meta["scraped_at"]

                metadatas.append(metadata_entry)

            collection.add(
                documents=[chunk["text"] for chunk in batch],
                metadatas=metadatas,
                ids=[f"chunk_{index + offset}" for offset in range(len(batch))],
            )

            print(
                f"  Batch {index // batch_size + 1}/{(len(all_chunks) - 1) // batch_size + 1}",
                flush=True,
            )

        print(f"\n[OK] Index built successfully with {len(all_chunks)} chunks.", flush=True)

    def verify_index(self) -> bool:
        try:
            collection = self.client.get_collection(
                name="auto_finance_complete",
                embedding_function=self.embedding_function,
            )

            count = collection.count()
            print(f"[OK] Verification: collection has {count} chunks", flush=True)

            results = collection.query(
                query_texts=["What are Autopools?"],
                n_results=3,
            )
            print(f"[OK] Test search returned {len(results['ids'][0])} results", flush=True)
            return True
        except Exception as exc:
            print(f"[ERROR] Verification failed: {exc}", flush=True)
            return False


def main() -> None:
    builder = CompleteIndexBuilder()
    builder.build_index()

    print("\n" + "=" * 60, flush=True)
    print("Verifying Index", flush=True)
    print("=" * 60, flush=True)
    builder.verify_index()

    print("\n" + "=" * 60, flush=True)
    print("Complete! Your bot can now use the new collection.", flush=True)
    print("Original docs-only collection is still available as backup.", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
