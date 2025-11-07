"""
Scrape blog.tokemak.xyz blog posts.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

import os
import asyncio
import logging
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
from playwright.async_api import Page as AsyncPage, Browser, BrowserContext  # For type hints
from playwright._impl._errors import TargetClosedError  # For handling closed connections

from scraper_common import (
    ScrapedDocument,
    save_documents_json,
    save_documents_markdown,
)

logger = logging.getLogger(__name__)


class BlogScraper:
    """Scrapes blog.tokemak.xyz."""

    def __init__(
        self,
        base_url: str = "https://blog.tokemak.xyz",
        output_dir: str = "scraped_data/blog",
    ):
        self.base_url = base_url.rstrip("/")
        # Use absolute paths to ensure we save to the correct location
        base_path = Path("/app") if os.path.exists("/app") else Path(".")
        if os.path.isabs(output_dir):
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = base_path / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.blog_posts: List[ScrapedDocument] = []
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

    def extract_blog_post(self, page, url: str) -> Optional[ScrapedDocument]:
        """Extract blog post content."""
        print(f"  [PARSE] {url}", flush=True)

        try:
            # Use "load" instead of "networkidle" - networkidle can wait forever on React SPAs
            # with continuous API calls, causing Browserless.io to timeout the connection
            page.wait_for_load_state("load", timeout=30000)  # Reduced from 60s to 30s
            time.sleep(2)  # Brief pause for any final rendering

            title = page.title()
            article_content = None

            selectors = [
                "article",
                '[role=\"article\"]',
                ".blog-post",
                ".post-content",
                "main",
            ]

            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible():
                        article_content = element.inner_text()
                        break
                except Exception:
                    continue

            if not article_content:
                article_content = page.inner_text("body")

            metadata = {}

            date_selectors = ["time", ".date", ".published", "[datetime]"]
            for selector in date_selectors:
                try:
                    date_element = page.locator(selector).first
                    if date_element.is_visible():
                        metadata["date"] = date_element.inner_text()
                        break
                except Exception:
                    continue

            try:
                read_time = page.locator("text=/min read/i").first
                if read_time.is_visible():
                    metadata["read_time"] = read_time.inner_text()
            except Exception:
                pass

            if not article_content:
                return None

            return ScrapedDocument(
                title=title or url,
                url=url,
                content=article_content,
                source="blog",
                metadata=metadata,
            )

        except Exception as exc:
            print(f"  Error extracting post: {exc}", flush=True)
            return None

    async def extract_blog_post_async(self, page: AsyncPage, url: str) -> Optional[ScrapedDocument]:
        """Extract blog post content (async version for use with async page)."""
        print(f"  [PARSE] {url}", flush=True)

        try:
            # Use "load" instead of "networkidle" - networkidle can wait forever on React SPAs
            await page.wait_for_load_state("load", timeout=30000)  # Reduced from 60s to 30s
            await asyncio.sleep(2)  # Brief pause for any final rendering

            title = await page.title()
            article_content = None

            selectors = [
                "article",
                '[role=\"article\"]',
                ".blog-post",
                ".post-content",
                "main",
            ]

            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible():
                        article_content = await element.inner_text()
                        break
                except Exception:
                    continue

            if not article_content:
                article_content = await page.inner_text("body")

            metadata = {}

            date_selectors = ["time", ".date", ".published", "[datetime]"]
            for selector in date_selectors:
                try:
                    date_element = page.locator(selector).first
                    if await date_element.is_visible():
                        metadata["date"] = await date_element.inner_text()
                        break
                except Exception:
                    continue

            try:
                read_time = page.locator("text=/min read/i").first
                if await read_time.is_visible():
                    metadata["read_time"] = await read_time.inner_text()
            except Exception:
                pass

            if not article_content:
                return None

            scraped_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            return ScrapedDocument(
                title=title or url,
                url=url,
                content=article_content,
                source="blog",
                scraped_at=scraped_at,
                metadata=metadata,
            )

        except Exception as exc:
            print(f"  Error extracting post: {exc}", flush=True)
            return None

    def find_blog_post_links(self, page) -> Set[str]:
        """Find all blog post links from the blog homepage."""
        links: Set[str] = set()

        try:
            link_elements = page.locator("a[href]").all()

            for element in link_elements:
                try:
                    href = element.get_attribute("href")
                    if not href:
                        continue

                    absolute_url = urljoin(self.base_url, href)
                    parsed = urlparse(absolute_url)

                    if (
                        absolute_url.startswith(self.base_url)
                        and parsed.path
                        and parsed.path != "/"
                        and not parsed.path.startswith("/tag/")
                        and not parsed.path.startswith("/category/")
                    ):
                        links.add(absolute_url.rstrip("/"))
                except Exception:
                    continue

        except Exception as exc:
            print(f"  Error finding links: {exc}", flush=True)

        return links

    async def find_blog_post_links_async(self, page: AsyncPage) -> Set[str]:
        """Find all blog post links from the blog homepage (async version)."""
        links: Set[str] = set()

        try:
            link_elements = await page.locator("a[href]").all()

            for element in link_elements:
                try:
                    href = await element.get_attribute("href")
                    if not href:
                        continue

                    absolute_url = urljoin(self.base_url, href)
                    parsed = urlparse(absolute_url)

                    if (
                        absolute_url.startswith(self.base_url)
                        and parsed.path
                        and parsed.path != "/"
                        and not parsed.path.startswith("/tag/")
                        and not parsed.path.startswith("/category/")
                    ):
                        links.add(absolute_url.rstrip("/"))
                except Exception:
                    continue

        except TargetClosedError as closed_err:
            # Browser connection closed - this will be handled by the retry logic in scrape_all
            logger.warning(f"Blog scraper: Browser closed while finding links: {closed_err}")
            print(f"  [WARNING] Browser closed while finding links, will reconnect...", flush=True)
            raise  # Re-raise so the retry logic can handle it
        except Exception as exc:
            logger.warning(f"Blog scraper: Error finding links: {exc}")
            print(f"  [WARNING] Error finding links: {exc}", flush=True)

        return links

    def scrape_all(self, progress_callback=None) -> None:
        """Scrape all blog posts.
        
        Args:
            progress_callback: Optional callback(current, total, message) for progress updates
        """
        print(f"Starting blog scrape: {self.base_url}", flush=True)
        if progress_callback:
            progress_callback(0, 0, "Initializing browser...")
        logger.info("Blog scraper: Initializing Playwright browser...")

        try:
            # Check if we should use remote browser
            if self.remote_browser_endpoint:
                logger.info(f"Blog scraper: Connecting to remote browser at {self.remote_browser_endpoint}")
                print(f"  [DEBUG] Connecting to remote browser: {self.remote_browser_endpoint}", flush=True)
                
                # Use async Playwright for remote connections (better reliability with Browserless.io)
                from playwright.async_api import async_playwright
                
                async def connect_and_scrape():
                    """Connect to remote browser and perform scraping using async Playwright."""
                    async with async_playwright() as p:
                        logger.info("Blog scraper: Async Playwright started")
                        print("  [DEBUG] Async Playwright started", flush=True)
                        
                        import time as time_module
                        connect_start = time_module.time()
                        
                        # Connect to Browserless.io using CDP
                        browser = await p.chromium.connect_over_cdp(
                            self.remote_browser_endpoint,
                            timeout=self.launch_timeout * 1000,  # milliseconds
                        )
                        connect_elapsed = time_module.time() - connect_start
                        logger.info(f"Blog scraper: Connected to remote browser in {connect_elapsed:.2f}s")
                        print(f"  [DEBUG] Connected to remote browser in {connect_elapsed:.2f}s", flush=True)
                        
                        # Always create a fresh context and page when connecting via CDP
                        logger.info("Blog scraper: Creating new browser context...")
                        print("  [DEBUG] Creating new browser context...", flush=True)
                        
                        context = None
                        page = None
                        max_retries = 3
                        
                        for attempt in range(max_retries):
                            try:
                                context = await browser.new_context()
                                if context is None:
                                    raise RuntimeError("browser.new_context() returned None")
                                
                                page = await context.new_page()
                                if page is None:
                                    raise RuntimeError("context.new_page() returned None")
                                
                                # Verify page is usable
                                _ = page.url  # This will raise if page is invalid
                                
                                logger.info("Blog scraper: Page created successfully")
                                print("  [DEBUG] Page created successfully", flush=True)
                                break
                                
                            except Exception as create_err:
                                logger.warning(f"Blog scraper: Attempt {attempt + 1} failed: {create_err}")
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
                                
                                if attempt == max_retries - 1:
                                    raise RuntimeError(f"Failed to create context/page after {max_retries} attempts: {create_err}")
                                
                                await asyncio.sleep(0.5)
                        
                        if page is None or context is None:
                            raise RuntimeError("Failed to create valid page/context")
                        
                        logger.info("Blog scraper: Remote browser ready")
                        print("  [DEBUG] Remote browser ready", flush=True)
                        
                        # Helper function to reconnect browser and recreate page/context if closed
                        async def reconnect_browser_and_page():
                            """Reconnect to Browserless.io and recreate page/context if browser connection closed."""
                            nonlocal page, context, browser
                            logger.warning("Blog scraper: Browser connection closed, reconnecting...")
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
                            reconnect_start = time_module.time()
                            browser = await p.chromium.connect_over_cdp(
                                self.remote_browser_endpoint,
                                timeout=self.launch_timeout * 1000,
                            )
                            reconnect_elapsed = time_module.time() - reconnect_start
                            logger.info(f"Blog scraper: Reconnected to remote browser in {reconnect_elapsed:.2f}s")
                            print(f"  [DEBUG] Reconnected to remote browser in {reconnect_elapsed:.2f}s", flush=True)
                            
                            # Create new context and page
                            context = await browser.new_context()
                            if context is None:
                                raise RuntimeError("Failed to recreate context")
                            page = await context.new_page()
                            if page is None:
                                raise RuntimeError("Failed to recreate page")
                            
                            logger.info("Blog scraper: Browser, context, and page recreated successfully")
                            print("  [DEBUG] Browser, context, and page recreated successfully", flush=True)
                        
                        # Scraping logic using async page operations
                        print("\nVisiting blog homepage...", flush=True)
                        if progress_callback:
                            progress_callback(0, 0, "Loading blog homepage to discover posts...")
                        logger.info("Blog scraper: Visiting homepage to discover posts...")
                        
                        # Retry logic for homepage visit
                        homepage_loaded = False
                        for homepage_attempt in range(2):
                            try:
                                await page.goto(
                                    self.base_url, wait_until="domcontentloaded", timeout=self.page_timeout
                                )
                                await asyncio.sleep(3)
                                logger.info("Blog scraper: Homepage loaded")
                                homepage_loaded = True
                                break
                            except TargetClosedError:
                                if homepage_attempt < 1:
                                    await reconnect_browser_and_page()
                                    await asyncio.sleep(2)
                                else:
                                    raise
                        
                        if not homepage_loaded:
                            raise RuntimeError("Failed to load homepage after retries")
                        
                        post_links = await self.find_blog_post_links_async(page)
                        total_posts = len(post_links)
                        print(f"Found {total_posts} blog post URLs", flush=True)
                        logger.info(f"Blog scraper: Found {total_posts} blog posts to scrape")
                        
                        if progress_callback:
                            progress_callback(0, total_posts, f"Found {total_posts} blog posts to scrape")

                        for index, post_url in enumerate(sorted(post_links), 1):
                            print(
                                f"\n[{index}/{total_posts}] Scraping: {post_url}", flush=True
                            )
                            logger.info(f"Blog scraper: Scraping post {index}/{total_posts}: {post_url}")
                            
                            if progress_callback:
                                progress_callback(index - 1, total_posts, f"Scraping post {index}/{total_posts}: {post_url}")

                            # Retry logic for each post
                            max_post_retries = 2
                            post_scraped = False
                            
                            for post_attempt in range(max_post_retries):
                                try:
                                    start_time = time.time()
                                    await page.goto(
                                        post_url, wait_until="domcontentloaded", timeout=self.page_timeout
                                    )
                                    elapsed = time.time() - start_time
                                    print(
                                        f"  [OK] Loaded in {elapsed:.1f}s", flush=True
                                    )
                                    logger.info(f"Blog scraper: Post {index} loaded in {elapsed:.1f}s")

                                    document = await self.extract_blog_post_async(page, post_url)

                                    if document:
                                        self.blog_posts.append(document)
                                        print(f"  [OK] Extracted: {document.title[:60]}", flush=True)
                                        logger.info(f"Blog scraper: Successfully extracted post {index}: {document.title[:60]}")

                                    post_scraped = True
                                    break  # Success, exit retry loop
                                    
                                except TargetClosedError as closed_err:
                                    logger.warning(f"Blog scraper: Target closed error on attempt {post_attempt + 1}: {closed_err}")
                                    print(f"  [WARNING] Target closed error on attempt {post_attempt + 1}, reconnecting browser...", flush=True)
                                    
                                    if post_attempt < max_post_retries - 1:
                                        try:
                                            await reconnect_browser_and_page()
                                            await asyncio.sleep(2)
                                        except Exception as reconnect_err:
                                            logger.error(f"Blog scraper: Failed to reconnect browser: {reconnect_err}")
                                            print(f"  [ERROR] Failed to reconnect browser: {reconnect_err}", flush=True)
                                            break
                                    else:
                                        logger.error(f"Blog scraper: Failed to scrape {post_url} after {max_post_retries} attempts")
                                        print(f"  [ERROR] Failed to scrape {post_url} after {max_post_retries} attempts", flush=True)
                                        break
                                    
                                except Exception as post_err:
                                    logger.error(f"Blog scraper: Error scraping post {index} ({post_url}): {post_err}", exc_info=True)
                                    print(f"  [ERROR] Error scraping post: {post_err}", flush=True)
                                    break  # Don't retry for other errors

                            if post_scraped:
                                await asyncio.sleep(2.5)  # Rate limiting

                        await browser.close()
                        logger.info("Blog scraper: Disconnected from remote browser")
                
                # Run the async scraping function
                asyncio.run(connect_and_scrape())
                print(f"\n[OK] Completed! Scraped {len(self.blog_posts)} blog posts", flush=True)
                if progress_callback:
                    progress_callback(len(self.blog_posts), len(self.blog_posts), f"Completed scraping {len(self.blog_posts)} blog posts")
                return  # Exit early since scraping is done
            else:
                # Use local browser (original code)
                print("  [DEBUG] Creating sync_playwright context...", flush=True)
                logger.info("Blog scraper: Creating Playwright context (local browser)...")
                
                with sync_playwright() as playwright:
                    logger.info("Blog scraper: Launching Chromium...")
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
                        ],
                    )
                    launch_elapsed = time_module.time() - launch_start
                    logger.info(f"Blog scraper: Browser launched successfully in {launch_elapsed:.2f}s")
                    print(f"  [DEBUG] Browser launched in {launch_elapsed:.2f}s", flush=True)
                    
                    logger.info("Blog scraper: Creating new page...")
                    print("  [DEBUG] Creating new page...", flush=True)
                    page = browser.new_page()
                    # Note: We skip set_default_timeout() - use per-operation timeouts instead
                    logger.info("Blog scraper: Page created")
                    print("  [DEBUG] Page created successfully", flush=True)

                    # Common scraping logic for local browser
                    print("\nVisiting blog homepage...", flush=True)
                    if progress_callback:
                        progress_callback(0, 0, "Loading blog homepage to discover posts...")
                    logger.info("Blog scraper: Visiting homepage to discover posts...")
                    
                    page.goto(
                        self.base_url, wait_until="domcontentloaded", timeout=self.page_timeout
                    )
                    time.sleep(3)
                    logger.info("Blog scraper: Homepage loaded")

                    post_links = self.find_blog_post_links(page)
                    total_posts = len(post_links)
                    print(f"Found {total_posts} blog post URLs", flush=True)
                    logger.info(f"Blog scraper: Found {total_posts} blog posts to scrape")
                    
                    if progress_callback:
                        progress_callback(0, total_posts, f"Found {total_posts} blog posts to scrape")

                    for index, post_url in enumerate(sorted(post_links), 1):
                        print(
                            f"\n[{index}/{total_posts}] Scraping: {post_url}", flush=True
                        )
                        logger.info(f"Blog scraper: Scraping post {index}/{total_posts}: {post_url}")
                        
                        if progress_callback:
                            progress_callback(index - 1, total_posts, f"Scraping post {index}/{total_posts}: {post_url}")

                        try:
                            start_time = time.time()
                            page.goto(
                                post_url, wait_until="domcontentloaded", timeout=self.page_timeout
                            )
                            elapsed = time.time() - start_time
                            print(
                                f"  [OK] Loaded in {elapsed:.1f}s", flush=True
                            )
                            logger.info(f"Blog scraper: Post {index} loaded in {elapsed:.1f}s")

                            document = self.extract_blog_post(page, post_url)

                            if document:
                                self.blog_posts.append(document)
                                print(f"  [OK] Extracted: {document.title[:60]}", flush=True)
                                logger.info(f"Blog scraper: Successfully extracted post {index}: {document.title[:60]}")

                            time.sleep(2.5)

                        except PlaywrightTimeoutError as exc:
                            logger.warning(f"Blog scraper: Timeout on post {index} ({post_url}): {exc}")
                            print(f"  [TIMEOUT] {post_url} ({exc})", flush=True)
                            continue
                        except Exception as exc:
                            logger.error(f"Blog scraper: Error scraping post {index} ({post_url}): {exc}", exc_info=True)
                            print(f"  [ERROR] Error scraping post: {exc}", flush=True)
                            continue

                    browser.close()
                    logger.info("Blog scraper: Browser closed")

                    print(f"\n[OK] Completed! Scraped {len(self.blog_posts)} blog posts", flush=True)
                    if progress_callback:
                        progress_callback(total_posts, total_posts, f"Completed scraping {len(self.blog_posts)} blog posts")
        except Exception as exc:
            logger.error(f"Blog scraper: Fatal error: {exc}", exc_info=True)
            print(f"\n[ERROR] Blog scraper failed: {exc}", flush=True)
            if progress_callback:
                progress_callback(0, 0, f"Error: {exc}")
            raise

    def save_to_json(self, filename: str = "blog_posts.json") -> None:
        """Save blog posts to JSON."""
        output_path = self.output_dir / filename
        save_documents_json(self.blog_posts, output_path)
        print(f"Saved to {output_path}", flush=True)

    def save_to_markdown(self) -> None:
        """Save each post as markdown."""
        md_dir = self.output_dir / "markdown"
        save_documents_markdown(self.blog_posts, md_dir)
        print(f"Saved {len(self.blog_posts)} markdown files to {md_dir}", flush=True)


def main() -> None:
    scraper = BlogScraper()

    print("=" * 60)
    print("Auto Finance Blog Scraper")
    print("=" * 60)

    scraper.scrape_all()
    scraper.save_to_json()
    scraper.save_to_markdown()

    print("\n" + "=" * 60)
    print(f"Total blog posts scraped: {len(scraper.blog_posts)}", flush=True)
    print("=" * 60)


if __name__ == "__main__":
    main()
