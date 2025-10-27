"""
Shared helpers for scraper outputs.

All scrapers should emit the same base schema so downstream indexing can
consume the data without per-source adapters.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format with Z suffix."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


@dataclass
class ScrapedDocument:
    """Canonical representation for scraped content."""

    title: str
    url: str
    content: str
    source: str
    scraped_at: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary suitable for JSON serialization."""
        # asdict handles nested structures and makes a shallow copy
        return asdict(self)


def documents_to_dicts(documents: Iterable[ScrapedDocument]) -> List[Dict[str, Any]]:
    """Convert an iterable of ScrapedDocument instances into JSON-ready dicts."""
    return [doc.to_dict() for doc in documents]


def save_documents_json(documents: Iterable[ScrapedDocument], output_path: Path) -> None:
    """Persist documents to JSON using the shared schema."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = documents_to_dicts(documents)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def save_documents_markdown(
    documents: Iterable[ScrapedDocument],
    output_dir: Path,
    *,
    include_metadata: bool = True,
) -> None:
    """Persist each document as a markdown file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, doc in enumerate(documents):
        safe_title = (doc.title or f"document_{index}").strip().replace("/", "-")
        filename = f"{safe_title[:80] or f'document_{index}'}.md"
        filepath = output_dir / filename
        with filepath.open("w", encoding="utf-8") as handle:
            handle.write(f"# {doc.title}\n\n")
            handle.write(f"Source: {doc.url}\n")
            handle.write(f"Scraped: {doc.scraped_at}\n\n")

            if include_metadata and doc.metadata:
                handle.write("## Metadata\n\n")
                for key, value in doc.metadata.items():
                    if isinstance(value, (dict, list)):
                        handle.write(f"- **{key}**: {json.dumps(value, ensure_ascii=False)}\n")
                    else:
                        handle.write(f"- **{key}**: {value}\n")
                handle.write("\n")

            handle.write("## Content\n\n")
            handle.write(doc.content)

