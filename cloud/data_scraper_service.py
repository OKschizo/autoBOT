"""
Cloud background data scraper service.
Runs GitBook / Website / Blog scrapers in-process and keeps ChromaDB fresh.
"""

import logging
import os
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Make shared modules importable both locally and inside the container.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

logger = logging.getLogger(__name__)


class DataScraperService:
    """Background service that manages scheduled and manual scrapes."""

    def __init__(self, interval_minutes: int = 10):
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60

        self.is_running = False
        self.is_scraping = False
        self.thread: Optional[threading.Thread] = None

        self.last_scrape_time: Optional[datetime] = None
        self.last_scrape_status = "Not started"
        self.scrape_count = 0
        self.error_count = 0
        self.initial_scrape_done = False

        self.chunk_counts: Dict[str, int] = {
            "gitbook": 0,
            "website": 0,
            "blog": 0,
            "total": 0,
        }
        self.scrape_history: List[Dict[str, Any]] = []
        self.max_history = 50
        self.update_callbacks: List = []

        # Populate counters if a Chroma collection already exists.
        self._check_existing_data()

    # ------------------------------------------------------------------#
    # Service lifecycle
    # ------------------------------------------------------------------#

    def start(self):
        """Start the background scraper loop."""
        if self.is_running:
            logger.warning("Scraper service is already running")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(
            "Data scraper service started (interval: %s minutes)",
            self.interval_minutes,
        )

        # Run an initial task without blocking startup.
        if self.initial_scrape_done:
            logger.info("Existing data detected; rebuilding index from disk...")
            threading.Thread(
                target=lambda: self._perform_scrape(build_only=True),
                daemon=True,
            ).start()
        else:
            logger.info("Scheduling initial full scrape (GitBook + Website + Blog)...")
            threading.Thread(
                target=lambda: self._perform_scrape(full_scrape=True),
                daemon=True,
            ).start()

    def stop(self):
        """Stop the background scraper loop."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Data scraper service stopped")

    def _run_loop(self):
        """Periodic scheduler that runs lightweight scrapes."""
        while self.is_running:
            try:
                time.sleep(self.interval_seconds)
                if not self.is_running:
                    break

                logger.info("Starting scheduled website scrape...")
                self._perform_scrape(full_scrape=False)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Error in scraper loop: %s", exc, exc_info=True)
                self.error_count += 1

    # ------------------------------------------------------------------#
    # Core scrape execution
    # ------------------------------------------------------------------#

    def _perform_scrape(
        self,
        full_scrape: bool = False,
        build_only: bool = False,
    ):
        """
        Execute a scrape or index build in-process.

        Args:
            full_scrape: run GitBook + Website + Blog + index rebuild.
            build_only: rebuild index from existing scraped_data.
        """
        if self.is_scraping:
            logger.warning("Scrape already in progress")
            return

        self.is_scraping = True
        start_time = datetime.now()
        task_label = "build" if build_only else ("full" if full_scrape else "website")
        logger.info("Running %s task...", task_label)

        errors: List[str] = []

        try:
            # Ensure imports resolve inside the container.
            if os.path.exists("/app"):
                sys.path.insert(0, "/app")

            if build_only:
                errors.extend(self._rebuild_index())
            elif full_scrape:
                errors.extend(self._run_full_scrape())
            else:
                self._run_website_scrape()

            if errors:
                self.last_scrape_status = f"Partial: {'; '.join(errors)}"
                self.error_count += 1
            else:
                self.last_scrape_status = "Success"

            self.last_scrape_time = start_time
            self.scrape_count += 1
            self.initial_scrape_done = True

            logger.info(
                "Scrape task finished with status '%s' (total chunks: %s)",
                self.last_scrape_status,
                self.chunk_counts.get("total", 0),
            )

            self._reload_rag_agents()
            self._notify_update_callbacks()

        except Exception as exc:  # pragma: no cover - defensive logging
            self.last_scrape_status = f"Error: {exc}"
            self.error_count += 1
            logger.error("Scrape error: %s", exc, exc_info=True)
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            self._add_to_history(
                {
                    "timestamp": start_time.isoformat(),
                    "status": "success"
                    if "Success" in self.last_scrape_status
                    else "failed",
                    "scrape_type": task_label,
                    "chunks": self.chunk_counts.copy(),
                    "duration_seconds": duration,
                    "error": None
                    if "Success" in self.last_scrape_status
                    else self.last_scrape_status[:200],
                }
            )
            self.is_scraping = False

    def _run_full_scrape(self) -> List[str]:
        """Run GitBook, Website, Blog scrapers and rebuild the index."""
        errors: List[str] = []
        gitbook_count = 0
        website_count = 0
        blog_count = 0

        try:
            from scrape_gitbook import GitBookScraper

            logger.info("[1/4] Scraping documentation...")
            doc_scraper = GitBookScraper("https://docs.auto.finance/")
            doc_scraper.scrape_all()
            doc_scraper.save_to_json()
            doc_scraper.save_to_markdown()
            gitbook_count = len(doc_scraper.scraped_content)
            logger.info("[OK] Documentation scraped (%s pages)", gitbook_count)
        except Exception as exc:
            errors.append(f"Docs: {exc}")
            logger.error("Failed to scrape docs: %s", exc, exc_info=True)

        try:
            from scrape_website import WebsiteScraper

            logger.info("[2/4] Scraping website...")
            web_scraper = WebsiteScraper("https://app.auto.finance/")
            web_scraper.scrape_all()
            web_scraper.save_to_json()
            web_scraper.save_to_markdown()
            website_count = len(web_scraper.scraped_pages)
            logger.info("[OK] Website scraped (%s pages)", website_count)
        except Exception as exc:
            errors.append(f"Website: {exc}")
            logger.error("Failed to scrape website: %s", exc, exc_info=True)

        try:
            from scrape_blog import BlogScraper

            logger.info("[3/4] Scraping blog...")
            blog_scraper = BlogScraper("https://blog.tokemak.xyz/")
            blog_scraper.scrape_all()
            blog_scraper.save_to_json()
            blog_scraper.save_to_markdown()
            blog_count = len(blog_scraper.blog_posts)
            logger.info("[OK] Blog scraped (%s posts)", blog_count)
        except Exception as exc:
            errors.append(f"Blog: {exc}")
            logger.error("Failed to scrape blog: %s", exc, exc_info=True)

        # Rebuild index when all scrapers finish.
        if not errors:
            errors.extend(self._rebuild_index())

        self.chunk_counts.update(
            {
                "gitbook": gitbook_count,
                "website": website_count,
                "blog": blog_count,
            }
        )
        self._refresh_counts_from_chroma()

        return errors

    def _run_website_scrape(self):
        """Scrape only the main app (fast path for scheduled runs)."""
        from scrape_website import WebsiteScraper

        logger.info("Scraping website content...")
        scraper = WebsiteScraper("https://app.auto.finance/")
        scraper.scrape_all()
        scraper.save_to_json()
        scraper.save_to_markdown()

        self.chunk_counts["website"] = len(scraper.scraped_pages)
        self._refresh_counts_from_chroma()
        logger.info("[OK] Website scrape completed (%s pages)", len(scraper.scraped_pages))

    def _rebuild_index(self) -> List[str]:
        """Rebuild the complete Chroma index from the scraped data."""
        errors: List[str] = []
        try:
            from build_complete_index import CompleteIndexBuilder

            logger.info("[4/4] Building complete index...")
            builder = CompleteIndexBuilder()
            builder.build_index()
            builder.verify_index()
            logger.info("[OK] Complete index rebuilt")
            self._refresh_counts_from_chroma()
        except Exception as exc:
            errors.append(f"Index: {exc}")
            logger.error("Failed to rebuild index: %s", exc, exc_info=True)
        return errors

    # ------------------------------------------------------------------#
    # Status helpers
    # ------------------------------------------------------------------#

    def _refresh_counts_from_chroma(self):
        """Update chunk counters using whichever Chroma collection is present."""
        try:
            import chromadb

            chroma_path = self._resolve_chroma_path()
            if not chroma_path:
                return

            client = chromadb.PersistentClient(path=chroma_path)

            collection = None
            selected = None
            for name in ("auto_finance_complete", "auto_finance_docs"):
                try:
                    collection = client.get_collection(name)
                    selected = name
                    break
                except Exception:
                    continue

            if not collection:
                return

            total = collection.count()
            self.chunk_counts["total"] = total

            if selected == "auto_finance_complete" and total:
                try:
                    records = collection.get(include=["metadatas"], limit=total)
                    source_counts = {"gitbook": 0, "website": 0, "blog": 0}
                    for meta in records.get("metadatas", []):
                        if not meta:
                            continue
                        source = meta.get("source")
                        if source in ("docs", "gitbook"):
                            source_counts["gitbook"] += 1
                        elif source in ("website", "site"):
                            source_counts["website"] += 1
                        elif source in ("blog", "posts"):
                            source_counts["blog"] += 1
                    for key, value in source_counts.items():
                        if value:
                            self.chunk_counts[key] = value
                except Exception as exc:
                    logger.debug("Could not derive per-source counts: %s", exc)
            elif total:
                # Legacy collection without per-source metadata.
                self.chunk_counts["gitbook"] = int(total * 0.65)
                self.chunk_counts["website"] = int(total * 0.20)
                self.chunk_counts["blog"] = total - (
                    self.chunk_counts["gitbook"] + self.chunk_counts["website"]
                )
        except Exception as exc:
            logger.debug("Unable to refresh Chroma counts: %s", exc)

    def _check_existing_data(self):
        """Detect pre-built Chroma data and populate counters."""
        try:
            import chromadb

            chroma_path = self._resolve_chroma_path()
            if not chroma_path:
                logger.debug("No existing Chroma directory found")
                return

            client = chromadb.PersistentClient(path=chroma_path)

            collection = None
            selected = None
            for name in ("auto_finance_complete", "auto_finance_docs"):
                try:
                    collection = client.get_collection(name)
                    selected = name
                    break
                except Exception:
                    continue

            if not collection:
                logger.debug("No target Chroma collections available")
                return

            count = collection.count()
            if count == 0:
                return

            self.chunk_counts["total"] = count

            if selected == "auto_finance_complete":
                try:
                    records = collection.get(include=["metadatas"], limit=count)
                    source_counts = {"gitbook": 0, "website": 0, "blog": 0}
                    for meta in records.get("metadatas", []):
                        if not meta:
                            continue
                        source = meta.get("source")
                        if source in ("docs", "gitbook"):
                            source_counts["gitbook"] += 1
                        elif source in ("website", "site"):
                            source_counts["website"] += 1
                        elif source in ("blog", "posts"):
                            source_counts["blog"] += 1
                    for key, value in source_counts.items():
                        if value:
                            self.chunk_counts[key] = value
                except Exception as exc:
                    logger.debug("Could not derive per-source counts: %s", exc)
            else:
                self.chunk_counts["gitbook"] = int(count * 0.65)
                self.chunk_counts["website"] = int(count * 0.20)
                self.chunk_counts["blog"] = count - (
                    self.chunk_counts["gitbook"] + self.chunk_counts["website"]
                )

            self.last_scrape_status = "Existing data loaded"
            self.initial_scrape_done = True
            logger.info(
                "Found existing Chroma data (%s chunks) using collection '%s'",
                count,
                selected,
            )
        except Exception as exc:
            logger.debug("Could not check existing data: %s", exc)

    def _resolve_chroma_path(self) -> Optional[str]:
        """Locate the persistent Chroma directory."""
        docker_path = "/app/chroma_db"
        local_path = os.path.join(os.path.dirname(__file__), "../../chroma_db")
        if os.path.exists(docker_path):
            return docker_path
        if os.path.exists(local_path):
            return local_path
        return None

    # ------------------------------------------------------------------#
    # Callbacks / status exposure
    # ------------------------------------------------------------------#

    def register_update_callback(self, callback):
        """Register a callback triggered after successful scrapes."""
        self.update_callbacks.append(callback)
        logger.info(
            "Registered update callback: %s",
            getattr(callback, "__name__", str(callback)),
        )

    def _notify_update_callbacks(self):
        for callback in self.update_callbacks:
            try:
                callback()
            except Exception as exc:
                logger.error(
                    "Error in update callback %s: %s",
                    getattr(callback, "__name__", str(callback)),
                    exc,
                    exc_info=True,
                )

    def _reload_rag_agents(self):
        """Inform RAG agents that the knowledge base changed."""
        try:
            logger.info("RAG agents will be reloaded on next query")
        except Exception as exc:
            logger.error("Error reloading RAG agents: %s", exc)

    def _add_to_history(self, entry: Dict[str, Any]):
        """Record limited scrape history for the status endpoint."""
        self.scrape_history.append(entry)
        if len(self.scrape_history) > self.max_history:
            self.scrape_history.pop(0)

    def get_status(self) -> Dict[str, Any]:
        """Expose current status for the API."""
        next_scrape_seconds: Optional[int] = None
        if self.last_scrape_time and not self.is_scraping:
            elapsed = (datetime.now() - self.last_scrape_time).total_seconds()
            remaining = max(0, self.interval_seconds - elapsed)
            next_scrape_seconds = int(remaining)

        return {
            "is_running": self.is_running,
            "is_scraping": self.is_scraping,
            "interval_minutes": self.interval_minutes,
            "last_scrape_time": self.last_scrape_time.isoformat()
            if self.last_scrape_time
            else None,
            "last_scrape_status": self.last_scrape_status,
            "next_scrape_in_seconds": next_scrape_seconds,
            "scrape_count": self.scrape_count,
            "error_count": self.error_count,
            "chunk_counts": self.chunk_counts,
            "recent_history": self.scrape_history[-10:],
        }

    def trigger_manual_scrape(self, full_scrape: bool = True) -> Dict[str, Any]:
        """Trigger a manual scrape (full or website-only)."""
        if not self.is_running:
            return {"success": False, "error": "Scraper service is not running"}

        if self.is_scraping:
            return {"success": False, "error": "Scrape already in progress"}

        scrape_type = "full" if full_scrape else "website"
        logger.info("Manual %s scrape triggered", scrape_type)

        thread = threading.Thread(
            target=lambda: self._perform_scrape(full_scrape=full_scrape),
            daemon=True,
        )
        thread.start()

        return {
            "success": True,
            "message": f"Manual {scrape_type} scrape started",
        }


# Global singleton used by the FastAPI backend.
scraper_service = DataScraperService(interval_minutes=10)

