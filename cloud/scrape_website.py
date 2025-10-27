"""
Scrape app.auto.finance with Playwright
Handles JavaScript-heavy React app
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urljoin, urlparse
import os
import re


class WebsiteScraper:
    """Scrapes app.auto.finance with live data"""
    
    def __init__(self, base_url="https://app.auto.finance", output_dir="scraped_data/website"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.launch_timeout = int(os.getenv('PLAYWRIGHT_LAUNCH_TIMEOUT_MS', '1800000'))  # default 30 mins
        self.page_timeout = int(os.getenv('PLAYWRIGHT_OPERATION_TIMEOUT_MS', '90000'))  # default 90 seconds
        
        self.visited_urls = set()
        self.scraped_pages = []
        self.skip_patterns = ['/portfolio']  # Skip these URLs
        
    def should_skip(self, url):
        """Check if URL should be skipped"""
        return any(pattern in url for pattern in self.skip_patterns)
    
    def extract_page_data(self, page, url):
        """Extract all relevant data from a page"""
        print(f"Extracting data from: {url}", flush=True)
        
        try:
            # Wait for page to load
            page.wait_for_load_state('networkidle', timeout=60000)  # Increased from 10 to 60 seconds
            time.sleep(2)  # Extra wait for dynamic content
            
            # Get page title
            title = page.title()
            
            # Get all text content
            content = page.inner_text('body')
            
            # Try to extract structured data if it's a pool page
            pool_data = None
            if '/pools/' in url or '/stoke/' in url or url.endswith('/pools') or url.endswith('/stoke') or url.endswith('/tokelp'):
                pool_data = self.extract_pool_data(page)
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'pool_data': pool_data,
                'scraped_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
        except Exception as e:
            print(f"  Error extracting data: {e}", flush=True)
            return None
    
    def extract_pool_data(self, page):
        """Extract structured data from pool/staking pages"""
        pool_data = {}
        
        try:
            # Get ALL text first to parse
            page_text = page.inner_text('body')
            
            # Different extraction for individual pool pages vs main pools page
            current_url = page.url
            
            if '/pools/' in current_url:
                # INDIVIDUAL POOL PAGE - Extract pool-specific data
                # Look for the pool card section (skip site-wide header)
                
                # Find pool name to locate the right section
                pool_name_match = re.search(r'/pools/(\w+)', current_url)
                if pool_name_match:
                    pool_name = pool_name_match.group(1)
                    
                    # Find the section with pool name
                    pool_section_start = page_text.find(pool_name)
                    if pool_section_start > 0:
                        # Get a larger section to capture all data
                        pool_section = page_text[pool_section_start:pool_section_start+3000]
                        
                        # Basic metrics
                        apy_match = re.search(r'APY\s+([\d.]+)%', pool_section)
                        if apy_match:
                            pool_data['apy'] = apy_match.group(1) + '%'
                        
                        tvl_match = re.search(r'TVL\s+\$([0-9.]+[MKB]?)', pool_section)
                        if tvl_match:
                            pool_data['tvl'] = f"${tvl_match.group(1)}"
                        
                        daily_match = re.search(r'DAILY RETURNS\s+\$([0-9,.]+[MK]?)', pool_section, re.IGNORECASE)
                        if daily_match:
                            pool_data['daily_returns'] = f"${daily_match.group(1)}"
                        
                        volume_match = re.search(r'TOTAL AUTOMATED VOLUME\s+\$([0-9,.]+[MK]?)', pool_section, re.IGNORECASE)
                        if volume_match:
                            pool_data['volume'] = f"${volume_match.group(1)}"
                        
                        # Extract tokens
                        tokens_section = re.search(r'Tokens\s+(.*?)\s+Protocols', pool_section, re.DOTALL)
                        if tokens_section:
                            tokens_text = tokens_section.group(1).strip()
                            # Clean up the tokens list
                            tokens = [t.strip() for t in tokens_text.split('\n') if t.strip() and '+' not in t]
                            if tokens:
                                pool_data['tokens'] = ', '.join(tokens[:10])  # First 10
                        
                        # Extract protocols
                        protocols_section = re.search(r'Protocols\s+(.*?)\s+Chain', pool_section, re.DOTALL)
                        if protocols_section:
                            protocols_text = protocols_section.group(1).strip()
                            protocols = [p.strip() for p in protocols_text.split('\n') if p.strip()]
                            if protocols:
                                pool_data['protocols'] = ', '.join(protocols[:10])
                        
                        # Extract chain
                        chain_match = re.search(r'Chain\s+(\w+)', pool_section)
                        if chain_match:
                            pool_data['chain'] = chain_match.group(1)
                        
                        # Extract top destinations from allocations
                        destinations = []
                        dest_matches = re.findall(r'([\d.]+)%\s+([\w\-/]+)\s+DESTINATIONS', pool_section)
                        for perc, dest in dest_matches[:5]:  # Top 5 destinations
                            destinations.append(f"{dest} ({perc}%)")
                        if destinations:
                            pool_data['top_destinations'] = ', '.join(destinations)
            
            else:
                # MAIN POOLS PAGE - Extract site-wide stats
                # Get Total TVL
                total_tvl_match = re.search(r'Total Value Locked\s+\$([0-9,.]+[MKB]?)', page_text)
                if total_tvl_match:
                    pool_data['total_tvl'] = f"${total_tvl_match.group(1)}"
                
                # Get Total Volume
                total_vol_match = re.search(r'Total Automated Volume\s+\$([0-9,.]+[MKB]?)', page_text)
                if total_vol_match:
                    pool_data['total_volume'] = f"${total_vol_match.group(1)}"
                
                # Extract pool count
                count_match = re.search(r'All\s+•\s+(\d+)', page_text)
                if count_match:
                    pool_data['total_pools'] = count_match.group(1)
            
        except Exception as e:
            print(f"  Error extracting pool data: {e}", flush=True)
        
        return pool_data if pool_data else None
    
    def discover_pool_pages(self, page, url):
        """Discover all pool pages from the pools listing"""
        pool_urls = set()
        
        # Only run on the main pools page
        if not url.endswith('/pools'):
            return pool_urls
        
        print("  Discovering pool pages...", flush=True)
        
        try:
            # Look for "VIEW" buttons or links that go to individual pools
            # Try to find pool links in various ways
            
            # Method 1: Find links that match /pools/poolName pattern
            all_links = page.locator('a[href]').all()
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href and '/pools/' in href and href.count('/') >= 2:
                        pool_url = urljoin(self.base_url, href)
                        clean_url = pool_url.split('#')[0].split('?')[0]
                        if not self.should_skip(clean_url):
                            pool_urls.add(clean_url)
                except:
                    continue
            
            # Method 2: Extract pool names from the table/list
            # Look for pool names in the data
            page_content = page.inner_text('body')
            
            # Common pool name patterns
            pool_patterns = [
                r'\b(auto[A-Z]+)\b',
                r'\b(base[A-Z]+)\b',
                r'\b(plasma[A-Z]+)\b',
                r'\b(arb[A-Z]+)\b',
                r'\b(silo[A-Z]+)\b',
                r'\b(dinero[A-Z]+)\b',
                r'\b(sonic[A-Z]+)\b',
                r'\b(bal[A-Z]+)\b',
            ]
            
            import re
            discovered_pools = set()
            for pattern in pool_patterns:
                matches = re.findall(pattern, page_content)
                discovered_pools.update(matches)
            
            # Create URLs for discovered pools
            for pool_name in discovered_pools:
                pool_url = f"{self.base_url}/pools/{pool_name}"
                if not self.should_skip(pool_url):
                    pool_urls.add(pool_url)
            
            if pool_urls:
                print(f"  Discovered {len(pool_urls)} pool pages to scrape", flush=True)
            
        except Exception as e:
            print(f"  Error discovering pools: {e}", flush=True)
        
        return pool_urls
    
    def find_links(self, page):
        """Find all internal links on the page"""
        links = set()
        
        try:
            # Get all links
            link_elements = page.locator('a[href]').all()
            
            for element in link_elements:
                try:
                    href = element.get_attribute('href')
                    if not href:
                        continue
                    
                    # Convert to absolute URL
                    absolute_url = urljoin(self.base_url, href)
                    
                    # Check if it's an internal link
                    if absolute_url.startswith(self.base_url):
                        # Clean URL (remove fragments, query params)
                        clean_url = absolute_url.split('#')[0].split('?')[0]
                        
                        # Skip if already visited or should skip
                        if clean_url not in self.visited_urls and not self.should_skip(clean_url):
                            links.add(clean_url)
                except:
                    continue
                    
        except Exception as e:
            print(f"  Error finding links: {e}", flush=True)
        
        return links
    
    def scrape_page(self, page, url):
        """Scrape a single page"""
        if url in self.visited_urls:
            return []
        
        print(f"\n[VISIT] {url}", flush=True)
        self.visited_urls.add(url)
        
        try:
            # Navigate to page
            start_time = time.time()
            page.goto(url, wait_until='domcontentloaded', timeout=self.page_timeout)
            print(f"[OK] Loaded in {time.time() - start_time:.1f}s", flush=True)
            
            # Extract data
            data = self.extract_page_data(page, url)
            if data:
                self.scraped_pages.append(data)
                print(f"  [OK] Extracted: {data['title'][:60]}", flush=True)
            
            # Find new links
            new_links = self.find_links(page)
            
            # If this is the pools page, discover all pool sub-pages
            if url.endswith('/pools'):
                pool_links = self.discover_pool_pages(page, url)
                new_links.update(pool_links)
            
            # Be polite - wait between requests
            time.sleep(2.5)
            
            return list(new_links)
        
        except PlaywrightTimeoutError as e:
            print(f"  [TIMEOUT] {url} ({e})", flush=True)
            return []
        except Exception as e:
            print(f"  [ERROR] {url} -> {e}", flush=True)
            return []
    
    def scrape_all(self, start_urls=None, max_pages: int = 50):
        """Scrape all pages starting from start_urls"""
        if start_urls is None:
            start_urls = [
                self.base_url,  # Homepage
                f"{self.base_url}/pools",
                f"{self.base_url}/stoke",
                f"{self.base_url}/tokelp"
            ]
        
        print(f"Starting scrape of {self.base_url}", flush=True)
        print(f"Start URLs: {start_urls}", flush=True)
        
        with sync_playwright() as p:
            # Launch browser with Docker-friendly args and increased timeout
            browser = p.chromium.launch(
                headless=True,
                timeout=self.launch_timeout,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            page = browser.new_page()
            page.set_default_timeout(self.page_timeout)
            
            # Queue of URLs to visit
            to_visit = list(start_urls)
            visited_count = 0
            
            while to_visit and visited_count < max_pages:
                current_url = to_visit.pop(0)
                
                # Scrape page and get new links
                new_links = self.scrape_page(page, current_url)
                
                # Add new links to queue
                to_visit.extend(new_links)
                visited_count += 1
                
                print(f"Progress: {visited_count} pages scraped, {len(to_visit)} in queue", flush=True)
            
            browser.close()
        
        print(f"\n[OK] Completed! Scraped {len(self.scraped_pages)} pages", flush=True)
    
    def save_to_json(self, filename="website_data.json"):
        """Save to JSON"""
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_pages, f, indent=2, ensure_ascii=False)
        print(f"Saved to {output_path}", flush=True)
    
    def save_to_markdown(self):
        """Save each page as markdown"""
        md_dir = self.output_dir / "markdown"
        md_dir.mkdir(exist_ok=True)
        
        for i, page_data in enumerate(self.scraped_pages):
            # Create filename from URL path
            url_path = urlparse(page_data['url']).path
            filename = url_path.replace('/', '_').strip('_') or 'homepage'
            filename = f"{filename}.md"
            
            filepath = md_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {page_data['title']}\n\n")
                f.write(f"URL: {page_data['url']}\n")
                f.write(f"Scraped: {page_data['scraped_at']}\n\n")
                
                # Add pool data if available
                if page_data.get('pool_data'):
                    f.write("## Live Data\n\n")
                    for key, value in page_data['pool_data'].items():
                        f.write(f"- **{key.upper()}**: {value}\n")
                    f.write("\n")
                
                f.write("## Content\n\n")
                f.write(page_data['content'])
        
        print(f"Saved {len(self.scraped_pages)} markdown files to {md_dir}", flush=True)


def main():
    """Main function"""
    scraper = WebsiteScraper()
    
    print("="*60)
    print("Auto Finance Website Scraper")
    print("="*60)
    
    # Scrape everything
    scraper.scrape_all()
    
    # Save results
    scraper.save_to_json()
    scraper.save_to_markdown()
    
    print("\n" + "="*60)
    print("Summary:")
    print(f"Total pages scraped: {len(scraper.scraped_pages)}", flush=True)
    
    # Count pages with live data
    live_data_count = sum(1 for p in scraper.scraped_pages if p.get('pool_data'))
    print(f"Pages with live data: {live_data_count}", flush=True)
    print("="*60)


if __name__ == "__main__":
    main()
