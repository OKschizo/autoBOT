"""
Scrape blog.tokemak.xyz blog posts.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

import os
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from scraper_common import (
    ScrapedDocument,
    save_documents_json,
    save_documents_markdown,
)


class BlogScraper:
    """Scrapes blog.tokemak.xyz."""

    def __init__(
        self,
        base_url: str = "https://blog.tokemak.xyz",
        output_dir: str = "scraped_data/blog",
    ):
        self.base_url = base_url.rstrip("/")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.blog_posts: List[ScrapedDocument] = []
        self.launch_timeout = int(
            os.getenv("PLAYWRIGHT_LAUNCH_TIMEOUT_MS", "1800000")
        )  # default 30 mins
        self.page_timeout = int(
            os.getenv("PLAYWRIGHT_OPERATION_TIMEOUT_MS", "90000")
        )  # default 90 seconds

    def extract_blog_post(self, page, url: str) -> Optional[ScrapedDocument]:
        """Extract blog post content."""
        print(f"  [PARSE] {url}", flush=True)

        try:
            page.wait_for_load_state("networkidle", timeout=60000)
            time.sleep(2)

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

    def scrape_all(self) -> None:
        """Scrape all blog posts."""
        print(f"Starting blog scrape: {self.base_url}", flush=True)

        with sync_playwright() as playwright:
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
            page = browser.new_page()
            page.set_default_timeout(self.page_timeout)

            print("\nVisiting blog homepage...", flush=True)
            page.goto(
                self.base_url, wait_until="domcontentloaded", timeout=self.page_timeout
            )
            time.sleep(3)

            post_links = self.find_blog_post_links(page)
            print(f"Found {len(post_links)} blog post URLs", flush=True)

            for index, post_url in enumerate(sorted(post_links), 1):
                print(
                    f"\n[{index}/{len(post_links)}] Scraping: {post_url}", flush=True
                )

                try:
                    start_time = time.time()
                    page.goto(
                        post_url, wait_until="domcontentloaded", timeout=self.page_timeout
                    )
                    print(
                        f"  [OK] Loaded in {time.time() - start_time:.1f}s", flush=True
                    )

                    document = self.extract_blog_post(page, post_url)

                    if document:
                        self.blog_posts.append(document)
                        print(f"  [OK] Extracted: {document.title[:60]}", flush=True)

                    time.sleep(2.5)

                except PlaywrightTimeoutError as exc:
                    print(f"  [TIMEOUT] {post_url} ({exc})", flush=True)
                    continue
                except Exception as exc:
                    print(f"  [ERROR] Error scraping post: {exc}", flush=True)
                    continue

            browser.close()

        print(f"\n[OK] Completed! Scraped {len(self.blog_posts)} blog posts", flush=True)

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
