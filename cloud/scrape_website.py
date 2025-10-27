"""
Scrape app.auto.finance with Playwright.
Handles JavaScript-heavy React app.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from scraper_common import (
    ScrapedDocument,
    save_documents_json,
    save_documents_markdown,
)


class WebsiteScraper:
    """Scrapes app.auto.finance with live data."""

    def __init__(
        self,
        base_url: str = "https://app.auto.finance",
        output_dir: str = "scraped_data/website",
    ):
        self.base_url = base_url.rstrip("/")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.launch_timeout = int(
            os.getenv("PLAYWRIGHT_LAUNCH_TIMEOUT_MS", "1800000")
        )  # default 30 mins
        self.page_timeout = int(
            os.getenv("PLAYWRIGHT_OPERATION_TIMEOUT_MS", "90000")
        )  # default 90 seconds

        self.visited_urls: Set[str] = set()
        self.scraped_pages: List[ScrapedDocument] = []
        self.skip_patterns = ["/portfolio"]

    def should_skip(self, url: str) -> bool:
        """Check if URL should be skipped."""
        return any(pattern in url for pattern in self.skip_patterns)

    def extract_page_data(self, page, url: str) -> Optional[ScrapedDocument]:
        """Extract all relevant data from a page."""
        print(f"Extracting data from: {url}", flush=True)

        try:
            page.wait_for_load_state("networkidle", timeout=60000)
            time.sleep(2)

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

    def scrape_all(self, start_urls: Optional[List[str]] = None, max_pages: int = 50) -> None:
        """Scrape all pages starting from provided URLs."""
        if start_urls is None:
            start_urls = [
                self.base_url,
                f"{self.base_url}/pools",
                f"{self.base_url}/stoke",
                f"{self.base_url}/tokelp",
            ]

        print(f"Starting scrape of {self.base_url}", flush=True)
        print(f"Start URLs: {start_urls}", flush=True)

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

            to_visit = list(start_urls)
            visited_count = 0

            while to_visit and visited_count < max_pages:
                current_url = to_visit.pop(0).rstrip("/")
                new_links = self.scrape_page(page, current_url)
                to_visit.extend(link for link in new_links if link not in self.visited_urls)
                visited_count += 1

                print(
                    f"Progress: {visited_count} pages scraped, {len(to_visit)} in queue",
                    flush=True,
                )

            browser.close()

        print(f"\n[OK] Completed! Scraped {len(self.scraped_pages)} pages", flush=True)

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
