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
        
        # Real-time progress tracking
        self.current_progress: Dict[str, Any] = {
            "stage": None,  # "gitbook", "website", "blog", "indexing"
            "current_step": None,  # e.g., "Scraping page 5/63"
            "gitbook_pages_scraped": 0,
            "gitbook_pages_total": 0,
            "website_pages_scraped": 0,
            "website_pages_total": 0,
            "blog_posts_scraped": 0,
            "blog_posts_total": 0,
            "index_chunks_scraped": 0,
            "index_chunks_total": 0,
        }

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

        # Only rebuild if index doesn't exist or data changed
        # Skip rebuild if index already exists and data hasn't changed (pre-built in Docker image)
        if self.initial_scrape_done:
            # Check if rebuild is actually needed
            try:
                from build_complete_index import CompleteIndexBuilder
                builder = CompleteIndexBuilder()
                if builder._should_rebuild():
                    logger.info("Data changed; rebuilding index from disk...")
                    threading.Thread(
                        target=lambda: self._perform_scrape(build_only=True),
                        daemon=True,
                    ).start()
                else:
                    logger.info("✅ Index is up-to-date (pre-built in Docker image), skipping rebuild")
            except Exception as exc:
                logger.warning(f"Could not check if rebuild needed, skipping: {exc}")
        else:
            logger.info("No existing index found; scheduling initial full scrape...")
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
        scrape_type: str = "website",
    ):
        """
        Execute a scrape or index build in-process.

        Args:
            full_scrape: run GitBook + Website + Blog + index rebuild.
            build_only: rebuild index from existing scraped_data.
            scrape_type: One of "gitbook", "website", "blog", "full" (for full scrape)
        """
        if self.is_scraping:
            logger.warning("Scrape already in progress")
            return

        self.is_scraping = True
        start_time = datetime.now()
        if build_only:
            task_label = "build"
        elif scrape_type == "full" or full_scrape:
            task_label = "full"
        else:
            task_label = scrape_type  # "gitbook", "website", or "blog"
        logger.info("Running %s task...", task_label)

        errors: List[str] = []

        try:
            # Ensure imports resolve inside the container.
            if os.path.exists("/app"):
                sys.path.insert(0, "/app")

            if build_only:
                errors.extend(self._rebuild_index())
            elif full_scrape or scrape_type == "full":
                errors.extend(self._run_full_scrape())
            elif scrape_type == "gitbook":
                errors.extend(self._run_gitbook_scrape())
            elif scrape_type == "blog":
                errors.extend(self._run_blog_scrape())
            else:  # website
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

        # Reset progress tracking
        self.current_progress = {
            "stage": "gitbook",
            "current_step": "Initializing...",
            "gitbook_pages_scraped": 0,
            "gitbook_pages_total": 0,
            "website_pages_scraped": 0,
            "website_pages_total": 0,
            "blog_posts_scraped": 0,
            "blog_posts_total": 0,
            "index_chunks_scraped": 0,
            "index_chunks_total": 0,
        }

        try:
            from scrape_gitbook import GitBookScraper

            logger.info("[1/4] Scraping documentation...")
            self.current_progress["stage"] = "gitbook"
            self.current_progress["current_step"] = "Starting GitBook scrape..."
            logger.info("GitBook progress: Starting scrape...")
            
            doc_scraper = GitBookScraper("https://docs.auto.finance/")
            
            # Track progress during scraping
            original_scrape_page = doc_scraper.scrape_page
            pages_scraped = [0]
            
            def progress_wrapper(url):
                result = original_scrape_page(url)
                pages_scraped[0] += 1
                self.current_progress["gitbook_pages_scraped"] = pages_scraped[0]
                self.current_progress["current_step"] = f"Scraping page {pages_scraped[0]}..."
                if pages_scraped[0] % 5 == 0:  # Log every 5 pages
                    logger.info(f"GitBook progress: {pages_scraped[0]} pages scraped...")
                return result
            
            doc_scraper.scrape_page = progress_wrapper
            doc_scraper.scrape_all()
            gitbook_count = len(doc_scraper.scraped_content)
            
            self.current_progress["gitbook_pages_total"] = gitbook_count
            self.current_progress["gitbook_pages_scraped"] = gitbook_count
            self.current_progress["current_step"] = f"Completed GitBook scrape ({gitbook_count} pages)"
            logger.info("[OK] Documentation scraped (%s pages)", gitbook_count)
            
            doc_scraper.save_to_json()
            doc_scraper.save_to_markdown()
        except Exception as exc:
            errors.append(f"Docs: {exc}")
            logger.error("Failed to scrape docs: %s", exc, exc_info=True)
        else:
            if gitbook_count == 0:
                logger.warning("Documentation scrape returned zero pages")
                errors.append("Docs: No pages scraped")

        try:
            from scrape_website import WebsiteScraper

            logger.info("[2/4] Scraping website...")
            self.current_progress["stage"] = "website"
            self.current_progress["current_step"] = "Starting website scrape..."
            logger.info("Website progress: Starting scrape...")
            
            def website_progress_callback(current: int, total: int, message: str):
                """Progress callback for website scraper."""
                self.current_progress["website_pages_scraped"] = current
                self.current_progress["website_pages_total"] = total if total > 0 else current + 10
                self.current_progress["current_step"] = message
                logger.info(f"Website progress: {message} ({current}/{total if total > 0 else '?'} pages)")
            
            web_scraper = WebsiteScraper("https://app.auto.finance/")
            web_scraper.scrape_all(progress_callback=website_progress_callback)
            website_count = len(web_scraper.scraped_pages)
            
            self.current_progress["website_pages_total"] = website_count
            self.current_progress["website_pages_scraped"] = website_count
            self.current_progress["current_step"] = f"Completed website scrape ({website_count} pages)"
            logger.info("[OK] Website scraped (%s pages)", website_count)
            logger.info(f"Website progress: Completed {website_count} pages")
            
            web_scraper.save_to_json()
            web_scraper.save_to_markdown()
        except Exception as exc:
            errors.append(f"Website: {exc}")
            logger.error("Failed to scrape website: %s", exc, exc_info=True)
        else:
            if website_count == 0:
                logger.warning("Website scrape returned zero pages")
                errors.append("Website: No pages scraped")

        try:
            from scrape_blog import BlogScraper

            logger.info("[3/4] Scraping blog...")
            self.current_progress["stage"] = "blog"
            self.current_progress["current_step"] = "Starting blog scrape..."
            logger.info("Blog progress: Starting scrape...")
            
            def blog_progress_callback(current: int, total: int, message: str):
                """Progress callback for blog scraper."""
                self.current_progress["blog_posts_scraped"] = current
                self.current_progress["blog_posts_total"] = total if total > 0 else current + 5
                self.current_progress["current_step"] = message
                logger.info(f"Blog progress: {message} ({current}/{total if total > 0 else '?'} posts)")
            
            blog_scraper = BlogScraper("https://blog.tokemak.xyz/")
            blog_scraper.scrape_all(progress_callback=blog_progress_callback)
            blog_count = len(blog_scraper.blog_posts)
            
            self.current_progress["blog_posts_total"] = blog_count
            self.current_progress["blog_posts_scraped"] = blog_count
            self.current_progress["current_step"] = f"Completed blog scrape ({blog_count} posts)"
            logger.info("[OK] Blog scraped (%s posts)", blog_count)
            logger.info(f"Blog progress: Completed {blog_count} posts")
            
            blog_scraper.save_to_json()
            blog_scraper.save_to_markdown()
        except Exception as exc:
            errors.append(f"Blog: {exc}")
            logger.error("Failed to scrape blog: %s", exc, exc_info=True)
        else:
            if blog_count == 0:
                logger.warning("Blog scrape returned zero posts")
                errors.append("Blog: No posts scraped")

        # Rebuild index when all scrapers finish.
        if not errors:
            self.current_progress["stage"] = "indexing"
            self.current_progress["current_step"] = "Building ChromaDB index..."
            errors.extend(self._rebuild_index())
            self.current_progress["current_step"] = "Index build complete"

        self.chunk_counts.update(
            {
                "gitbook": gitbook_count,
                "website": website_count,
                "blog": blog_count,
            }
        )
        self._refresh_counts_from_chroma()
        
        # Clear progress when done
        if not errors:
            self.current_progress["stage"] = None
            self.current_progress["current_step"] = "Completed"

        return errors

    def _run_gitbook_scrape(self) -> List[str]:
        """Scrape only GitBook docs and rebuild index."""
        errors: List[str] = []
        
        # Reset progress tracking
        self.current_progress = {
            "stage": "gitbook",
            "current_step": "Initializing...",
            "gitbook_pages_scraped": 0,
            "gitbook_pages_total": 0,
            "website_pages_scraped": 0,
            "website_pages_total": 0,
            "blog_posts_scraped": 0,
            "blog_posts_total": 0,
            "index_chunks_scraped": 0,
            "index_chunks_total": 0,
        }
        
        try:
            from scrape_gitbook import GitBookScraper

            logger.info("[GitBook] Scraping documentation...")
            self.current_progress["stage"] = "gitbook"
            self.current_progress["current_step"] = "Starting GitBook scrape..."
            
            doc_scraper = GitBookScraper("https://docs.auto.finance/")
            doc_scraper.scrape_all()
            gitbook_count = len(doc_scraper.scraped_content)
            
            self.current_progress["gitbook_pages_total"] = gitbook_count
            self.current_progress["gitbook_pages_scraped"] = gitbook_count
            logger.info("[OK] GitBook scraped (%s pages)", gitbook_count)
            
            doc_scraper.save_to_json()
            doc_scraper.save_to_markdown()
            
            self.chunk_counts["gitbook"] = gitbook_count
            
            # Rebuild index after scraping
            logger.info("[GitBook] Rebuilding index with fresh GitBook data...")
            self.current_progress["stage"] = "indexing"
            self.current_progress["current_step"] = "Building index from GitBook data..."
            index_errors = self._rebuild_index(force=True)
            if index_errors:
                errors.extend(index_errors)
                logger.warning("Index rebuild had errors: %s", index_errors)
            
            self._refresh_counts_from_chroma()
            logger.info("[OK] GitBook scrape completed (%s pages) and index rebuilt", gitbook_count)
        except Exception as exc:
            errors.append(f"GitBook: {exc}")
            logger.error("Failed to scrape GitBook: %s", exc, exc_info=True)
        return errors

    def _run_blog_scrape(self) -> List[str]:
        """Scrape only blog and rebuild index."""
        errors: List[str] = []
        
        # Reset progress tracking
        self.current_progress = {
            "stage": "blog",
            "current_step": "Initializing...",
            "gitbook_pages_scraped": 0,
            "gitbook_pages_total": 0,
            "website_pages_scraped": 0,
            "website_pages_total": 0,
            "blog_posts_scraped": 0,
            "blog_posts_total": 0,
            "index_chunks_scraped": 0,
            "index_chunks_total": 0,
        }
        
        try:
            from scrape_blog import BlogScraper

            logger.info("[Blog] Scraping blog...")
            self.current_progress["stage"] = "blog"
            self.current_progress["current_step"] = "Starting blog scrape..."
            
            def blog_progress_callback(current: int, total: int, message: str):
                """Progress callback for blog scraper."""
                self.current_progress["blog_posts_scraped"] = current
                self.current_progress["blog_posts_total"] = total if total > 0 else current + 5
                self.current_progress["current_step"] = message
                logger.info(f"Blog progress: {message} ({current}/{total if total > 0 else '?'} posts)")
            
            blog_scraper = BlogScraper("https://blog.tokemak.xyz/")
            blog_scraper.scrape_all(progress_callback=blog_progress_callback)
            blog_count = len(blog_scraper.blog_posts)
            
            self.current_progress["blog_posts_total"] = blog_count
            self.current_progress["blog_posts_scraped"] = blog_count
            logger.info("[OK] Blog scraped (%s posts)", blog_count)
            
            blog_scraper.save_to_json()
            blog_scraper.save_to_markdown()
            
            self.chunk_counts["blog"] = blog_count
            
            # Rebuild index after scraping
            logger.info("[Blog] Rebuilding index with fresh blog data...")
            self.current_progress["stage"] = "indexing"
            self.current_progress["current_step"] = "Building index from blog data..."
            index_errors = self._rebuild_index(force=True)
            if index_errors:
                errors.extend(index_errors)
                logger.warning("Index rebuild had errors: %s", index_errors)
            
            self._refresh_counts_from_chroma()
            logger.info("[OK] Blog scrape completed (%s posts) and index rebuilt", blog_count)
        except Exception as exc:
            errors.append(f"Blog: {exc}")
            logger.error("Failed to scrape blog: %s", exc, exc_info=True)
        return errors

    def _run_website_scrape(self):
        """Scrape only the main app (fast path for scheduled runs)."""
        # Reset progress tracking
        self.current_progress = {
            "stage": "website",
            "current_step": "Initializing...",
            "gitbook_pages_scraped": 0,
            "gitbook_pages_total": 0,
            "website_pages_scraped": 0,
            "website_pages_total": 0,
            "blog_posts_scraped": 0,
            "blog_posts_total": 0,
            "index_chunks_scraped": 0,
            "index_chunks_total": 0,
        }
        
        from scrape_website import WebsiteScraper

        logger.info("Scraping website content...")
        self.current_progress["stage"] = "website"
        self.current_progress["current_step"] = "Starting website scrape..."
        
        def website_progress_callback(current: int, total: int, message: str):
            """Progress callback for website scraper."""
            self.current_progress["website_pages_scraped"] = current
            self.current_progress["website_pages_total"] = total if total > 0 else current + 10
            self.current_progress["current_step"] = message
            logger.info(f"Website progress: {message} ({current}/{total if total > 0 else '?'} pages)")
        
        scraper = WebsiteScraper("https://app.auto.finance/")
        scraper.scrape_all(progress_callback=website_progress_callback)
        scraper.save_to_json()
        scraper.save_to_markdown()

        self.chunk_counts["website"] = len(scraper.scraped_pages)
        
        # Rebuild index after scraping to update ChromaDB with fresh live data
        logger.info("Rebuilding index with fresh website data...")
        self.current_progress["stage"] = "indexing"
        self.current_progress["current_step"] = "Building index from website data..."
        index_errors = self._rebuild_index(force=True)
        if index_errors:
            logger.warning("Index rebuild had errors: %s", index_errors)
        
        self._refresh_counts_from_chroma()
        logger.info("[OK] Website scrape completed (%s pages) and index rebuilt", len(scraper.scraped_pages))

    def _rebuild_index(self, force: bool = False) -> List[str]:
        """Rebuild the complete Chroma index from the scraped data.
        
        Args:
            force: If True, force rebuild even if hash matches (used after individual scrapes)
        """
        errors: List[str] = []
        try:
            from build_complete_index import CompleteIndexBuilder

            logger.info("Building complete index...")
            self.current_progress["stage"] = "indexing"
            self.current_progress["current_step"] = "Initializing index builder..."
            
            builder = CompleteIndexBuilder()
            
            # Build index with progress callback
            def progress_callback(current: int, total: int, step: str):
                """Callback to update progress during index building."""
                self.current_progress["index_chunks_scraped"] = current
                self.current_progress["index_chunks_total"] = total
                self.current_progress["current_step"] = step
                logger.info(f"Indexing progress: {current}/{total} chunks - {step}")
            
            builder.build_index(progress_callback=progress_callback, force=force)
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
            # Import the global agent from api.py and reload its collection
            import sys
            if 'backend.api' in sys.modules:
                api_module = sys.modules['backend.api']
                if hasattr(api_module, 'agent') and api_module.agent:
                    if hasattr(api_module.agent, 'reload_collection'):
                        logger.info("Reloading RAG agent collection with fresh data...")
                        api_module.agent.reload_collection()
                        logger.info("✅ RAG agent collection reloaded")
                    else:
                        logger.warning("RAG agent does not support reload_collection()")
                else:
                    logger.warning("RAG agent not found in api module")
            else:
                logger.warning("backend.api module not loaded yet")
        except Exception as exc:
            logger.error("Error reloading RAG agents: %s", exc, exc_info=True)

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
            "current_progress": self.current_progress if self.is_scraping else None,
        }

    def trigger_manual_scrape(self, full_scrape: bool = True, scrape_type: str = "full") -> Dict[str, Any]:
        """Trigger a manual scrape.
        
        Args:
            full_scrape: If True, run full scrape (GitBook + Website + Blog). If False, website-only.
            scrape_type: One of "full", "gitbook", "website", "blog"
        """
        if not self.is_running:
            return {"success": False, "error": "Scraper service is not running"}

        if self.is_scraping:
            return {"success": False, "error": "Scrape already in progress"}

        # Override scrape_type if specified
        if scrape_type in ("gitbook", "website", "blog"):
            full_scrape = False
        elif scrape_type == "full":
            full_scrape = True
        else:
            scrape_type = "full" if full_scrape else "website"

        logger.info("Manual %s scrape triggered", scrape_type)

        thread = threading.Thread(
            target=lambda: self._perform_scrape(full_scrape=full_scrape, scrape_type=scrape_type),
            daemon=True,
        )
        thread.start()

        return {
            "success": True,
            "message": f"Manual {scrape_type} scrape started",
        }


# Global singleton used by the FastAPI backend.
scraper_service = DataScraperService(interval_minutes=10)
