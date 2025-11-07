import os
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from scraper_common import (
    ScrapedDocument,
    save_documents_json,
    save_documents_markdown,
)

logger = logging.getLogger(__name__)


class GitBookScraper:
    """Scraper for GitBook-based documentation."""

    def __init__(self, base_url: str, output_dir: str = "scraped_data"):
        self.base_url = base_url.rstrip("/")
        self.domain = urlparse(base_url).netloc
        # Use absolute paths to ensure we save to the correct location
        base_path = Path("/app") if os.path.exists("/app") else Path(".")
        if os.path.isabs(output_dir):
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = base_path / output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.visited_urls: set[str] = set()
        self.scraped_content: List[ScrapedDocument] = []

    def is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to the same GitBook site."""
        parsed = urlparse(url)
        return parsed.netloc == self.domain and url not in self.visited_urls

    def extract_content(
        self, soup: BeautifulSoup, url: str
    ) -> Optional[ScrapedDocument]:
        """Extract main content from a GitBook page."""
        title_text = ""
        metadata: Dict[str, Any] = {}
        headings: List[Dict[str, str]] = []

        title_tag = soup.find("title")
        if title_tag:
            page_title = title_tag.get_text(strip=True)
            title_text = page_title.split("|")[0].strip()

        main_content = (
            soup.find("div", {"data-testid": "page-content"})
            or soup.find("article")
            or soup.find("main")
            or soup.find("div", {"class": "page-inner"})
            or soup.find("div", {"role": "main"})
        )

        if not main_content:
            print(f"Warning: Using fallback content extraction for {url}")
            main_content = soup.find("body")

        if not main_content:
            print(f"Error: Could not find any content for {url}")
            return None

        for element in main_content(
            ["script", "style", "nav", "header", "footer", "aside"]
        ):
            element.decompose()

        for nav_class in ["navigation", "sidebar", "nav-menu", "breadcrumb", "toc"]:
            for elem in main_content.find_all(
                class_=lambda x: x and nav_class in x.lower()
            ):
                elem.decompose()

        page_content = main_content.get_text(separator="\n", strip=True)

        for heading in main_content.find_all(["h1", "h2", "h3", "h4", "h5"]):
            heading_text = heading.get_text(strip=True)
            if heading_text:
                headings.append({"level": heading.name, "text": heading_text})

        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            metadata["description"] = meta_desc["content"]

        if headings:
            metadata["headings"] = headings

        if not page_content:
            return None

        return ScrapedDocument(
            title=title_text or url,
            url=url,
            content=page_content,
            source="gitbook",
            metadata=metadata,
        )

    def find_internal_links(self, soup: BeautifulSoup, current_url: str) -> set[str]:
        """Find all internal links on the page."""
        links: set[str] = set()
        for link in soup.find_all("a", href=True):
            href = link["href"]

            if href.startswith(("http://", "https://")) and self.base_url not in href:
                continue
            if href.startswith(("mailto:", "tel:", "javascript:")):
                continue

            absolute_url = urljoin(current_url, href)
            absolute_url = absolute_url.split("#")[0].split("?")[0]

            if self.is_valid_url(absolute_url):
                links.add(absolute_url)

        return links

    def scrape_page(self, url: str) -> List[str]:
        """Scrape a single page."""
        if url in self.visited_urls:
            return []

        print(f"Scraping: {url}", flush=True)
        self.visited_urls.add(url)

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            document = self.extract_content(soup, url)
            if document:
                self.scraped_content.append(document)
                print(f"  [OK] Extracted: {document.title[:50]}", flush=True)

            new_links = self.find_internal_links(soup, url)
            time.sleep(1)
            return list(new_links)
        except Exception as exc:
            print(f"  [ERROR] Error scraping {url}: {exc}", flush=True)
            return []

    def scrape_all(self, max_pages: Optional[int] = None) -> None:
        """Recursively scrape all pages starting from base_url."""
        print(f"Starting GitBook scrape: {self.base_url}", flush=True)
        logger.info(f"GitBook scraper: Starting scrape of {self.base_url}")
        to_visit = [self.base_url]
        pages_scraped = 0
        errors = []

        try:
            while to_visit and (max_pages is None or pages_scraped < max_pages):
                current_url = to_visit.pop(0)
                logger.info(f"GitBook scraper: Scraping page {pages_scraped + 1}: {current_url}")
                
                try:
                    new_links = self.scrape_page(current_url)
                    to_visit.extend(new_links)
                    pages_scraped += 1

                    print(
                        f"Progress: {pages_scraped} pages scraped, {len(to_visit)} in queue",
                        flush=True,
                    )
                    logger.info(f"GitBook scraper: Progress - {pages_scraped} pages scraped, {len(to_visit)} in queue")
                except Exception as exc:
                    error_msg = f"Error scraping {current_url}: {exc}"
                    logger.error(f"GitBook scraper: {error_msg}", exc_info=True)
                    errors.append(error_msg)
                    print(f"  [ERROR] {error_msg}", flush=True)
                    # Continue with next page instead of failing completely

            print(f"\nCompleted! Scraped {len(self.scraped_content)} pages", flush=True)
            logger.info(f"GitBook scraper: Completed - {len(self.scraped_content)} pages scraped")
            
            if errors:
                logger.warning(f"GitBook scraper: {len(errors)} errors occurred during scraping")
                print(f"\n⚠️  {len(errors)} errors occurred during scraping", flush=True)
        except Exception as exc:
            logger.error(f"GitBook scraper: Fatal error: {exc}", exc_info=True)
            print(f"\n[ERROR] GitBook scraper failed: {exc}", flush=True)
            raise

    def save_to_json(self, filename: str = "gitbook_data.json") -> None:
        """Save scraped content to JSON file."""
        output_path = self.output_dir / filename
        save_documents_json(self.scraped_content, output_path)
        print(f"Saved to {output_path}", flush=True)

    def save_to_markdown(self) -> None:
        """Save each page as a separate markdown file."""
        md_dir = self.output_dir / "markdown"
        save_documents_markdown(self.scraped_content, md_dir)
        print(f"Saved {len(self.scraped_content)} markdown files to {md_dir}", flush=True)


if __name__ == "__main__":
    GITBOOK_URL = "https://docs.auto.finance/"

    scraper = GitBookScraper(GITBOOK_URL)

    print("Starting scrape of docs.auto.finance...", flush=True)
    scraper.scrape_all()

    scraper.save_to_json()
    scraper.save_to_markdown()

    print("\nSample of scraped content:")
    for page in scraper.scraped_content[:3]:
        headings = page.metadata.get("headings", []) if page.metadata else []
        print(f"\nTitle: {page.title}")
        print(f"URL: {page.url}")
        print(f"Content length: {len(page.content)} characters")
        print(f"Headings: {len(headings)}")
