"""
Scrape app.auto.finance with Playwright.
Handles JavaScript-heavy React app.
"""

from __future__ import annotations

import os
import re
import time
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
from playwright.async_api import Page as AsyncPage, Browser, BrowserContext  # For type hints
from playwright._impl._errors import TargetClosedError  # For handling closed connections
import logging

from scraper_common import (
    ScrapedDocument,
    save_documents_json,
    save_documents_markdown,
)

logger = logging.getLogger(__name__)


class WebsiteScraper:
    """Scrapes app.auto.finance with live data."""

    def __init__(
        self,
        base_url: str = "https://app.auto.finance",
        output_dir: str = "scraped_data/website",
    ):
        self.base_url = base_url.rstrip("/")
        # Use absolute paths to ensure we save to the correct location
        base_path = Path("/app") if os.path.exists("/app") else Path(".")
        if os.path.isabs(output_dir):
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = base_path / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Remote browser endpoint (if set, use remote browser instead of local)
        self.remote_browser_endpoint = os.getenv("PLAYWRIGHT_REMOTE_BROWSER_ENDPOINT", "")
        
        # Use shorter timeout for browser launch (30 seconds instead of 30 minutes)
        # If it takes longer than 30s, something is wrong
        self.launch_timeout = int(
            os.getenv("PLAYWRIGHT_LAUNCH_TIMEOUT_MS", "30000")
        )  # default 30 seconds
        self.page_timeout = int(
            os.getenv("PLAYWRIGHT_OPERATION_TIMEOUT_MS", "90000")
        )  # default 90 seconds

        self.visited_urls: Set[str] = set()
        self.scraped_pages: List[ScrapedDocument] = []
        self.skip_patterns = ["/portfolio"]

    def should_skip(self, url: str) -> bool:
        """Check if URL should be skipped."""
        return any(pattern in url for pattern in self.skip_patterns)

    async def extract_page_data_async(self, page: AsyncPage, url: str) -> Optional[ScrapedDocument]:
        """Extract page data (async version for use with async page)."""
        print(f"Extracting data from: {url}", flush=True)

        try:
            # Use "load" instead of "networkidle" - networkidle can wait forever on React SPAs
            # with continuous API calls, causing Browserless.io to timeout the connection
            # "load" waits for the page to finish loading, which is sufficient for most cases
            await page.wait_for_load_state("load", timeout=30000)  # Reduced from 60s to 30s
            await asyncio.sleep(2)  # Brief pause for any final rendering

            title = await page.title()
            content = await page.inner_text("body")

            pool_data = None
            if (
                "/pools/" in url
                or "/stoke/" in url
                or url.endswith("/pools")
                or url.endswith("/stoke")
                or url.endswith("/tokelp")
            ):
                pool_data = await self.extract_pool_data_async(page)

            scraped_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            metadata: Dict[str, Any] = {}
            if pool_data:
                metadata["pool_data"] = pool_data

            return ScrapedDocument(
                title=title or url,
                url=url,
                content=content,
                source="website",
                scraped_at=scraped_at,
                metadata=metadata,
            )
        except Exception as exc:
            print(f"  Error extracting data: {exc}", flush=True)
            return None
    
    def extract_page_data(self, page, url: str) -> Optional[ScrapedDocument]:
        """Extract all relevant data from a page (sync version)."""
        print(f"Extracting data from: {url}", flush=True)

        try:
            # Use "load" instead of "networkidle" - networkidle can wait forever on React SPAs
            page.wait_for_load_state("load", timeout=30000)  # Reduced from 60s to 30s
            time.sleep(2)  # Brief pause for any final rendering

            title = page.title()
            content = page.inner_text("body")

            pool_data = None
            if (
                "/pools/" in url
                or "/stoke/" in url
                or url.endswith("/pools")
                or url.endswith("/stoke")
                or url.endswith("/tokelp")
            ):
                pool_data = self.extract_pool_data(page)

            scraped_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            metadata: Dict[str, Any] = {}
            if pool_data:
                metadata["pool_data"] = pool_data

            return ScrapedDocument(
                title=title or url,
                url=url,
                content=content,
                source="website",
                scraped_at=scraped_at,
                metadata=metadata,
            )
        except Exception as exc:
            print(f"  Error extracting data: {exc}", flush=True)
            return None

    async def extract_pool_data_async(self, page: AsyncPage) -> Dict[str, str]:
        """Extract pool data (async version)."""
        pool_data: Dict[str, str] = {}
        try:
            page_text = await page.inner_text("body")
            current_url = page.url

            if "/pools/" in current_url:
                pool_name_match = re.search(r"/pools/([\w-]+)", current_url)
                if pool_name_match:
                    pool_name = pool_name_match.group(1)
                    pool_section_start = page_text.find(pool_name)
                    if pool_section_start > 0:
                        pool_section = page_text[pool_section_start : pool_section_start + 3000]

                        apy_match = re.search(r"APY\s+([\d.]+)%", pool_section)
                        if apy_match:
                            pool_data["apy"] = f"{apy_match.group(1)}%"

                        tvl_match = re.search(r"TVL\s+\$([0-9.]+[MKB]?)", pool_section)
                        if tvl_match:
                            pool_data["tvl"] = f"${tvl_match.group(1)}"

                        daily_match = re.search(
                            r"DAILY RETURNS\s+\$([0-9,.]+[MK]?)",
                            pool_section,
                            re.IGNORECASE,
                        )
                        if daily_match:
                            pool_data["daily_returns"] = f"${daily_match.group(1)}"

                        volume_match = re.search(
                            r"TOTAL AUTOMATED VOLUME\s+\$([0-9,.]+[MK]?)",
                            pool_section,
                            re.IGNORECASE,
                        )
                        if volume_match:
                            pool_data["volume"] = f"${volume_match.group(1)}"

                        tokens_section = re.search(
                            r"Tokens\s+(.*?)\s+Protocols", pool_section, re.DOTALL
                        )
                        if tokens_section:
                            tokens_text = tokens_section.group(1).strip()
                            tokens = [
                                token.strip()
                                for token in tokens_text.split("\n")
                                if token.strip() and "+" not in token
                            ]
                            if tokens:
                                pool_data["tokens"] = tokens

            if not pool_data:
                summary_matches = re.findall(
                    r"(?:APY|TVL|Daily Rewards?|Volume)\s+[:$]?\s*([0-9.,%$]+)",
                    page_text,
                )
                if summary_matches:
                    pool_data["summary_metrics"] = summary_matches

        except Exception as exc:
            print(f"  Error extracting pool data: {exc}", flush=True)

        return pool_data
    
    def extract_pool_data(self, page) -> Dict[str, str]:
        """Extract structured data from pool/staking pages."""
        pool_data: Dict[str, str] = {}

        try:
            page_text = page.inner_text("body")
            current_url = page.url

            if "/pools/" in current_url:
                pool_name_match = re.search(r"/pools/([\w-]+)", current_url)
                if pool_name_match:
                    pool_name = pool_name_match.group(1)
                    pool_section_start = page_text.find(pool_name)
                    if pool_section_start > 0:
                        pool_section = page_text[pool_section_start : pool_section_start + 3000]

                        apy_match = re.search(r"APY\s+([\d.]+)%", pool_section)
                        if apy_match:
                            pool_data["apy"] = f"{apy_match.group(1)}%"

                        tvl_match = re.search(r"TVL\s+\$([0-9.]+[MKB]?)", pool_section)
                        if tvl_match:
                            pool_data["tvl"] = f"${tvl_match.group(1)}"

                        daily_match = re.search(
                            r"DAILY RETURNS\s+\$([0-9,.]+[MK]?)",
                            pool_section,
                            re.IGNORECASE,
                        )
                        if daily_match:
                            pool_data["daily_returns"] = f"${daily_match.group(1)}"

                        volume_match = re.search(
                            r"TOTAL AUTOMATED VOLUME\s+\$([0-9,.]+[MK]?)",
                            pool_section,
                            re.IGNORECASE,
                        )
                        if volume_match:
                            pool_data["volume"] = f"${volume_match.group(1)}"

                        tokens_section = re.search(
                            r"Tokens\s+(.*?)\s+Protocols", pool_section, re.DOTALL
                        )
                        if tokens_section:
                            tokens_text = tokens_section.group(1).strip()
                            tokens = [
                                token.strip()
                                for token in tokens_text.split("\n")
                                if token.strip() and "+" not in token
                            ]
                            if tokens:
                                pool_data["tokens"] = tokens

            if not pool_data:
                summary_matches = re.findall(
                    r"(?:APY|TVL|Daily Rewards?|Volume)\s+[:$]?\s*([0-9.,%$]+)",
                    page_text,
                )
                if summary_matches:
                    pool_data["summary_metrics"] = summary_matches

        except Exception as exc:
            print(f"  Error extracting pool data: {exc}", flush=True)

        return pool_data

    async def discover_pool_pages_async(self, page: AsyncPage, url: str) -> Set[str]:
        """Discover pool pages (async version)."""
        links: Set[str] = set()
        try:
            pool_cards = await page.locator("a[href*='/pools/']").all()
            for element in pool_cards:
                try:
                    href = await element.get_attribute("href")
                    if not href:
                        continue
                    absolute_url = urljoin(url, href).split("#")[0]
                    if (
                        absolute_url.startswith(self.base_url)
                        and absolute_url not in self.visited_urls
                    ):
                        links.add(absolute_url)
                except Exception:
                    continue
        except TargetClosedError as closed_err:
            # Browser connection closed - this will be handled by the retry logic in scrape_all
            logger.warning(f"Website scraper: Browser closed while discovering pool pages: {closed_err}")
            print(f"  [WARNING] Browser closed while discovering pool pages, will reconnect...", flush=True)
            raise  # Re-raise so the retry logic can handle it
        except Exception as exc:
            logger.warning(f"Website scraper: Error discovering pool pages: {exc}")
            print(f"  [WARNING] Error discovering pool pages: {exc}", flush=True)
        return links
    
    def discover_pool_pages(self, page, url: str) -> Set[str]:
        """Discover pool sub-pages linked from a pools overview page."""
        links: Set[str] = set()
        try:
            pool_cards = page.locator("a[href*='/pools/']").all()
            for element in pool_cards:
                try:
                    href = element.get_attribute("href")
                    if not href:
                        continue
                    absolute_url = urljoin(url, href).split("#")[0]
                    if (
                        absolute_url.startswith(self.base_url)
                        and absolute_url not in self.visited_urls
                    ):
                        links.add(absolute_url)
                except Exception:
                    continue
        except Exception as exc:
            print(f"  Error discovering pool pages: {exc}", flush=True)
        return links

    async def find_links_async(self, page: AsyncPage, url: str) -> Set[str]:
        """Find links (async version)."""
        links: Set[str] = set()
        try:
            anchors = await page.locator("a[href]").all()
            for anchor in anchors:
                try:
                    href = await anchor.get_attribute("href")
                    if not href:
                        continue
                    absolute_url = urljoin(url, href).split("#")[0]
                    parsed = urlparse(absolute_url)
                    if (
                        absolute_url.startswith(self.base_url)
                        and parsed.scheme in ("http", "https")
                        and absolute_url not in self.visited_urls
                        and not self.should_skip(absolute_url)
                    ):
                        links.add(absolute_url)
                except Exception:
                    continue
        except TargetClosedError as closed_err:
            # Browser connection closed - this will be handled by the retry logic in scrape_all
            logger.warning(f"Website scraper: Browser closed while finding links: {closed_err}")
            print(f"  [WARNING] Browser closed while finding links, will reconnect...", flush=True)
            raise  # Re-raise so the retry logic can handle it
        except Exception as exc:
            logger.warning(f"Website scraper: Error finding links: {exc}")
            print(f"  [WARNING] Error finding links: {exc}", flush=True)
        return links
    
    def find_links(self, page, url: str) -> Set[str]:
        """Find new internal links from the current page."""
        links: Set[str] = set()
        try:
            anchors = page.locator("a[href]").all()
            for anchor in anchors:
                try:
                    href = anchor.get_attribute("href")
                    if not href:
                        continue
                    absolute_url = urljoin(url, href).split("#")[0]
                    parsed = urlparse(absolute_url)
                    if (
                        absolute_url.startswith(self.base_url)
                        and parsed.scheme in ("http", "https")
                        and absolute_url not in self.visited_urls
                        and not self.should_skip(absolute_url)
                    ):
                        links.add(absolute_url)
                except Exception:
                    continue
        except Exception as exc:
            print(f"  Error finding links: {exc}", flush=True)
        return links

    def scrape_page(self, page, url: str) -> List[str]:
        """Visit a page, extract data, and return new links."""
        if url in self.visited_urls:
            return []

        print(f"\nVisiting: {url}", flush=True)
        self.visited_urls.add(url)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self.page_timeout)
            document = self.extract_page_data(page, url)
            if document:
                self.scraped_pages.append(document)
                print(f"  [OK] Extracted: {document.title[:60]}", flush=True)

            new_links = self.find_links(page, url)
            if url.endswith("/pools"):
                new_links.update(self.discover_pool_pages(page, url))

            time.sleep(2.5)
            return list(new_links)

        except PlaywrightTimeoutError as exc:
            print(f"  [TIMEOUT] {url} ({exc})", flush=True)
            return []
        except Exception as exc:
            print(f"  [ERROR] {url} -> {exc}", flush=True)
            return []

    def scrape_all(self, start_urls: Optional[List[str]] = None, max_pages: int = 50, progress_callback=None) -> None:
        """Scrape all pages starting from provided URLs.
        
        Args:
            start_urls: URLs to start scraping from
            max_pages: Maximum number of pages to scrape
            progress_callback: Optional callback(current, total, message) for progress updates
        """
        if start_urls is None:
            start_urls = [
                self.base_url,
                f"{self.base_url}/pools",
                f"{self.base_url}/stoke",
                f"{self.base_url}/tokelp",
            ]

        print(f"Starting scrape of {self.base_url}", flush=True)
        print(f"Start URLs: {start_urls}", flush=True)
        if progress_callback:
            progress_callback(0, 0, f"Initializing browser...")
        logger.info("Website scraper: Initializing Playwright browser...")
        print("  [DEBUG] About to create Playwright context...", flush=True)

        try:
            # Check if we should use remote browser
            if self.remote_browser_endpoint:
                logger.info(f"Website scraper: Connecting to remote browser at {self.remote_browser_endpoint}")
                print(f"  [DEBUG] Connecting to remote browser: {self.remote_browser_endpoint}", flush=True)
                
                # Connect to remote browser via CDP (Chrome DevTools Protocol)
                # According to Browserless.io docs, we should use async Playwright for better reliability
                from playwright.async_api import async_playwright
                import asyncio
                
                # According to Browserless.io docs, use async Playwright for remote connections
                # This avoids the sync initialization that hangs in Cloud Run
                logger.info("Website scraper: Using async Playwright for remote browser connection...")
                print("  [DEBUG] Initializing async Playwright...", flush=True)
                
                async def connect_and_scrape():
                    """Connect to remote browser and perform scraping using async Playwright."""
                    # Use async context manager as per Browserless.io documentation
                    async with async_playwright() as p:
                        logger.info("Website scraper: Async Playwright started")
                        print("  [DEBUG] Async Playwright started", flush=True)
                        
                        import time as time_module
                        connect_start = time_module.time()
                        
                        # Connect to Browserless.io using CDP (recommended method per docs)
                        browser = await p.chromium.connect_over_cdp(
                            self.remote_browser_endpoint,
                            timeout=self.launch_timeout * 1000,  # milliseconds
                        )
                        connect_elapsed = time_module.time() - connect_start
                        logger.info(f"Website scraper: Connected to remote browser in {connect_elapsed:.2f}s")
                        print(f"  [DEBUG] Connected to remote browser in {connect_elapsed:.2f}s", flush=True)
                        
                        # Always create a fresh context and page when connecting via CDP
                        # Existing contexts/pages from Browserless.io may be closed or invalid
                        logger.info("Website scraper: Creating new browser context...")
                        print("  [DEBUG] Creating new browser context...", flush=True)
                        
                        context = None
                        page = None
                        max_retries = 3
                        
                        for attempt in range(max_retries):
                            try:
                                # Create a new context (don't reuse existing ones)
                                logger.info(f"Website scraper: Attempt {attempt + 1}/{max_retries} to create context...")
                                print(f"  [DEBUG] Attempt {attempt + 1}/{max_retries} to create context...", flush=True)
                                
                                context = await browser.new_context()
                                if context is None:
                                    raise RuntimeError("browser.new_context() returned None")
                                
                                logger.info("Website scraper: Context created successfully")
                                print("  [DEBUG] Context created successfully", flush=True)
                                
                                # Create a new page in the context
                                logger.info("Website scraper: Creating new page...")
                                print("  [DEBUG] Creating new page...", flush=True)
                                
                                page = await context.new_page()
                                if page is None:
                                    raise RuntimeError("context.new_page() returned None")
                                
                                logger.info("Website scraper: Page created successfully")
                                print("  [DEBUG] Page created successfully", flush=True)
                                
                                # Verify the page is usable
                                # Skip set_default_timeout() as it's causing issues with Browserless.io
                                # We'll use per-operation timeouts instead (already done in goto(), etc.)
                                logger.info("Website scraper: Verifying page is usable...")
                                print("  [DEBUG] Verifying page is usable...", flush=True)
                                
                                # Verify page is not None
                                if page is None:
                                    raise RuntimeError("Page is None after creation")
                                
                                # Verify page is accessible by checking a property
                                try:
                                    _ = page.url  # This will raise if page is invalid
                                    logger.info("Website scraper: Page verified successfully")
                                    print("  [DEBUG] Page verified successfully", flush=True)
                                except (AttributeError, TypeError) as verify_err:
                                    raise RuntimeError(f"Page object is invalid: {verify_err}")
                                
                                # Note: We skip set_default_timeout() because it's causing issues
                                # All operations (goto, etc.) already specify timeout explicitly
                                logger.info("Website scraper: Page ready (using per-operation timeouts)")
                                print("  [DEBUG] Page ready (using per-operation timeouts)", flush=True)
                                
                                # Success - break out of retry loop
                                break
                                
                            except Exception as create_err:
                                logger.warning(f"Website scraper: Attempt {attempt + 1} failed: {create_err}")
                                print(f"  [WARNING] Attempt {attempt + 1} failed: {create_err}", flush=True)
                                
                                # Clean up failed attempt
                                try:
                                    if page:
                                        await page.close()
                                except:
                                    pass
                                try:
                                    if context:
                                        await context.close()
                                except:
                                    pass
                                
                                page = None
                                context = None
                                
                                # If this was the last attempt, raise the error
                                if attempt == max_retries - 1:
                                    error_msg = f"Failed to create context/page after {max_retries} attempts: {create_err}"
                                    logger.error(f"Website scraper: {error_msg}")
                                    print(f"  [ERROR] {error_msg}", flush=True)
                                    raise RuntimeError(error_msg)
                                
                                # Wait a bit before retrying
                                import asyncio as asyncio_module
                                await asyncio_module.sleep(0.5)
                        
                        # Final verification
                        if page is None or context is None:
                            error_msg = f"Failed to create valid page/context. Page: {page is not None}, Context: {context is not None}"
                            logger.error(f"Website scraper: {error_msg}")
                            print(f"  [ERROR] {error_msg}", flush=True)
                            raise RuntimeError(error_msg)
                        
                        logger.info(f"Website scraper: Page object verified: {type(page).__name__}")
                        print(f"  [DEBUG] Page object verified: {type(page).__name__}", flush=True)
                        logger.info("Website scraper: Remote browser ready")
                        print("  [DEBUG] Remote browser ready, starting scrape loop", flush=True)
                        
                        # Helper function to reconnect browser and recreate page/context if closed
                        async def reconnect_browser_and_page():
                            """Reconnect to Browserless.io and recreate page/context if browser connection closed."""
                            nonlocal page, context, browser
                            logger.warning("Website scraper: Browser connection closed, reconnecting...")
                            print("  [WARNING] Browser connection closed, reconnecting to Browserless.io...", flush=True)
                            
                            # Clean up old page/context/browser
                            try:
                                if page:
                                    await page.close()
                            except:
                                pass
                            try:
                                if context:
                                    await context.close()
                            except:
                                pass
                            try:
                                if browser:
                                    await browser.close()
                            except:
                                pass
                            
                            # Reconnect to Browserless.io
                            import time as time_module
                            reconnect_start = time_module.time()
                            browser = await p.chromium.connect_over_cdp(
                                self.remote_browser_endpoint,
                                timeout=self.launch_timeout * 1000,  # milliseconds
                            )
                            reconnect_elapsed = time_module.time() - reconnect_start
                            logger.info(f"Website scraper: Reconnected to remote browser in {reconnect_elapsed:.2f}s")
                            print(f"  [DEBUG] Reconnected to remote browser in {reconnect_elapsed:.2f}s", flush=True)
                            
                            # Create new context and page
                            context = await browser.new_context()
                            if context is None:
                                raise RuntimeError("Failed to recreate context")
                            page = await context.new_page()
                            if page is None:
                                raise RuntimeError("Failed to recreate page")
                            
                            logger.info("Website scraper: Browser, context, and page recreated successfully")
                            print("  [DEBUG] Browser, context, and page recreated successfully", flush=True)
                        
                        # Perform scraping using async page operations
                        to_visit = list(start_urls)
                        visited_count = 0
                        total_estimated = len(start_urls) + 20

                        if progress_callback:
                            progress_callback(0, total_estimated, f"Starting scrape with {len(start_urls)} initial URLs...")

                        while to_visit and visited_count < max_pages:
                            current_url = to_visit.pop(0).rstrip("/")
                            
                            logger.info(f"Website scraper: Visiting page {visited_count + 1}: {current_url}")
                            if progress_callback:
                                progress_callback(visited_count, total_estimated, f"Scraping page {visited_count + 1}: {current_url}")
                            
                            # Retry logic for handling closed connections
                            max_page_retries = 2
                            page_scraped = False
                            
                            for page_attempt in range(max_page_retries):
                                try:
                                    # Visit page and extract data
                                    await page.goto(current_url, wait_until="domcontentloaded", timeout=self.page_timeout)
                                    
                                    # Extract page data
                                    if current_url not in self.visited_urls:
                                        self.visited_urls.add(current_url)
                                        document = await self.extract_page_data_async(page, current_url)
                                        if document:
                                            self.scraped_pages.append(document)
                                            print(f"  [OK] Extracted: {document.title[:60]}", flush=True)
                                    
                                    # Find links (using sync locator methods which work with async page)
                                    new_links = await self.find_links_async(page, current_url)
                                    if current_url.endswith("/pools"):
                                        pool_links = await self.discover_pool_pages_async(page, current_url)
                                        new_links.update(pool_links)
                                    
                                    to_visit.extend(link for link in new_links if link not in self.visited_urls)
                                    page_scraped = True
                                    break  # Success, exit retry loop
                                    
                                except TargetClosedError as closed_err:
                                    logger.warning(f"Website scraper: Target closed error on attempt {page_attempt + 1}: {closed_err}")
                                    print(f"  [WARNING] Target closed error on attempt {page_attempt + 1}, reconnecting browser...", flush=True)
                                    
                                    if page_attempt < max_page_retries - 1:
                                        # Reconnect browser and recreate page/context, then retry
                                        try:
                                            await reconnect_browser_and_page()
                                            await asyncio.sleep(2)  # Brief pause before retry
                                        except Exception as reconnect_err:
                                            logger.error(f"Website scraper: Failed to reconnect browser: {reconnect_err}")
                                            print(f"  [ERROR] Failed to reconnect browser: {reconnect_err}", flush=True)
                                            # If reconnection fails, break and try next URL
                                            break
                                    else:
                                        # Last attempt failed, log and continue to next URL
                                        logger.error(f"Website scraper: Failed to scrape {current_url} after {max_page_retries} attempts")
                                        print(f"  [ERROR] Failed to scrape {current_url} after {max_page_retries} attempts", flush=True)
                                        break
                                    
                                except Exception as page_err:
                                    logger.error(f"Website scraper: Error scraping {current_url}: {page_err}")
                                    print(f"  [ERROR] Error scraping {current_url}: {page_err}", flush=True)
                                    break  # Don't retry for other errors
                            
                            if page_scraped:
                                visited_count += 1
                                
                                if len(to_visit) > total_estimated:
                                    total_estimated = len(to_visit) + visited_count

                                print(f"Progress: {visited_count} pages scraped, {len(to_visit)} in queue", flush=True)
                                
                                if progress_callback and visited_count % 2 == 0:
                                    progress_callback(visited_count, total_estimated, f"Scraped {visited_count} pages, {len(to_visit)} remaining")
                            
                            await asyncio.sleep(2.5)  # Rate limiting

                        await browser.close()
                        logger.info("Website scraper: Disconnected from remote browser")
                        
                        # Context manager automatically cleans up Playwright instance
                        # No need for manual cleanup
                
                # Run the async scraping function
                # Note: scrape_all() is sync, so we use asyncio.run() to execute the async function
                asyncio.run(connect_and_scrape())
                print(f"\n[OK] Completed! Scraped {len(self.scraped_pages)} pages", flush=True)
                if progress_callback:
                    progress_callback(len(self.scraped_pages), len(self.scraped_pages), f"Completed scraping {len(self.scraped_pages)} pages")
                return  # Exit early since scraping is done
            else:
                # Use local browser (original code) - this may hang in Cloud Run
                print("  [DEBUG] Creating sync_playwright context...", flush=True)
                logger.info("Website scraper: Creating Playwright context (local browser)...")
                playwright_context = sync_playwright()
                print("  [DEBUG] sync_playwright() returned", flush=True)
                logger.info("Website scraper: sync_playwright() returned")
                
                # Enter context manager - this may hang in Cloud Run
                print("  [DEBUG] Entering Playwright context manager (this may take 10-30 seconds)...", flush=True)
                logger.info("Website scraper: Entering Playwright context manager...")
                
                with playwright_context as playwright:
                    print("  [DEBUG] Successfully entered Playwright context manager", flush=True)
                    logger.info("Website scraper: Successfully entered Playwright context")
                    
                    logger.info("Website scraper: Launching Chromium...")
                    print("  [DEBUG] Launching Chromium browser (this may take 10-30 seconds)...", flush=True)
                    print(f"  [DEBUG] Launch timeout set to: {self.launch_timeout}ms", flush=True)
                    
                    import time as time_module
                    launch_start = time_module.time()
                    browser = playwright.chromium.launch(
                        headless=True,
                        timeout=self.launch_timeout,
                        args=[
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-gpu",
                            "--single-process",
                        ],
                    )
                    launch_elapsed = time_module.time() - launch_start
                    logger.info(f"Website scraper: Browser launched successfully in {launch_elapsed:.2f}s")
                    print(f"  [DEBUG] Browser launched in {launch_elapsed:.2f}s", flush=True)
                    
                    logger.info("Website scraper: Creating new page...")
                    print("  [DEBUG] Creating new page...", flush=True)
                    page = browser.new_page()
                    page.set_default_timeout(self.page_timeout)
                    logger.info("Website scraper: Page created, starting scrape loop")
                    print("  [DEBUG] Page created successfully, starting scrape loop", flush=True)
                    
                    # Common scraping logic for local browser
                    to_visit = list(start_urls)
                    visited_count = 0
                    total_estimated = len(start_urls) + 20  # Initial estimate

                    if progress_callback:
                        progress_callback(0, total_estimated, f"Starting scrape with {len(start_urls)} initial URLs...")

                    while to_visit and visited_count < max_pages:
                        current_url = to_visit.pop(0).rstrip("/")
                        
                        logger.info(f"Website scraper: Visiting page {visited_count + 1}: {current_url}")
                        if progress_callback:
                            progress_callback(visited_count, total_estimated, f"Scraping page {visited_count + 1}: {current_url}")
                        
                        new_links = self.scrape_page(page, current_url)
                        to_visit.extend(link for link in new_links if link not in self.visited_urls)
                        visited_count += 1
                        
                        # Update total estimate if we discover more pages
                        if len(to_visit) > total_estimated:
                            total_estimated = len(to_visit) + visited_count

                        print(
                            f"Progress: {visited_count} pages scraped, {len(to_visit)} in queue",
                            flush=True,
                        )
                        
                        if progress_callback and visited_count % 2 == 0:  # Update every 2 pages
                            progress_callback(visited_count, total_estimated, f"Scraped {visited_count} pages, {len(to_visit)} remaining")

                    browser.close()
                    logger.info("Website scraper: Browser closed")

            print(f"\n[OK] Completed! Scraped {len(self.scraped_pages)} pages", flush=True)
            if progress_callback:
                progress_callback(len(self.scraped_pages), len(self.scraped_pages), f"Completed scraping {len(self.scraped_pages)} pages")
        except TimeoutError as exc:
            logger.error(f"Website scraper: Timeout error (likely at context manager entry): {exc}", exc_info=True)
            print(f"\n[ERROR] Website scraper timed out: {exc}", flush=True)
            if progress_callback:
                progress_callback(0, 0, f"Timeout error: {exc}")
            raise
        except Exception as exc:
            logger.error(f"Website scraper: Fatal error: {exc}", exc_info=True)
            print(f"\n[ERROR] Website scraper failed: {exc}", flush=True)
            if progress_callback:
                progress_callback(0, 0, f"Error: {exc}")
            raise

    def save_to_json(self, filename: str = "website_data.json") -> None:
        """Save to JSON."""
        output_path = self.output_dir / filename
        save_documents_json(self.scraped_pages, output_path)
        print(f"Saved to {output_path}", flush=True)

    def save_to_markdown(self) -> None:
        """Save each page as markdown."""
        md_dir = self.output_dir / "markdown"
        save_documents_markdown(self.scraped_pages, md_dir)
        print(f"Saved {len(self.scraped_pages)} markdown files to {md_dir}", flush=True)


def main() -> None:
    scraper = WebsiteScraper()

    print("=" * 60)
    print("Auto Finance Website Scraper")
    print("=" * 60)

    scraper.scrape_all()
    scraper.save_to_json()
    scraper.save_to_markdown()

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"Total pages scraped: {len(scraper.scraped_pages)}", flush=True)
    live_data_count = sum(1 for page in scraper.scraped_pages if page.metadata.get("pool_data"))
    print(f"Pages with live data: {live_data_count}", flush=True)
    print("=" * 60)


if __name__ == "__main__":
    main()
