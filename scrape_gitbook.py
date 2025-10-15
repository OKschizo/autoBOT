import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
from pathlib import Path

class GitBookScraper:
    def __init__(self, base_url, output_dir="scraped_data"):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.visited_urls = set()
        self.scraped_content = []
        
    def is_valid_url(self, url):
        """Check if URL belongs to the same GitBook site"""
        parsed = urlparse(url)
        return parsed.netloc == self.domain and url not in self.visited_urls
    
    def extract_content(self, soup, url):
        """Extract main content from GitBook page"""
        content = {
            'url': url,
            'title': '',
            'content': '',
            'headings': [],
            'metadata': {}
        }
        
        # Extract page title from <title> tag
        title_tag = soup.find('title')
        if title_tag:
            page_title = title_tag.get_text(strip=True)
            # Remove " | Auto Finance" or similar suffix
            content['title'] = page_title.split('|')[0].strip()
        
        # Modern GitBook uses these selectors
        main_content = (
            soup.find('div', {'data-testid': 'page-content'}) or
            soup.find('article') or
            soup.find('main') or
            soup.find('div', {'class': 'page-inner'}) or
            soup.find('div', {'role': 'main'})
        )
        
        if not main_content:
            # Fallback: try to find any content div
            print(f"Warning: Using fallback content extraction for {url}")
            main_content = soup.find('body')
        
        if not main_content:
            print(f"Error: Could not find any content for {url}")
            return None
        
        # Remove navigation, headers, footers, scripts
        for element in main_content(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Remove elements with common navigation classes
        for nav_class in ['navigation', 'sidebar', 'nav-menu', 'breadcrumb', 'toc']:
            for elem in main_content.find_all(class_=lambda x: x and nav_class in x.lower()):
                elem.decompose()
        
        # Extract all text content preserving structure
        content['content'] = main_content.get_text(separator='\n', strip=True)
        
        # Extract headings for structure
        for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
            heading_text = heading.get_text(strip=True)
            if heading_text:  # Only add non-empty headings
                content['headings'].append({
                    'level': heading.name,
                    'text': heading_text
                })
        
        # Extract metadata if available
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content['metadata']['description'] = meta_desc['content']
        
        return content
    
    def find_internal_links(self, soup, current_url):
        """Find all internal links on the page"""
        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip external links, mailto, tel, etc.
            if href.startswith(('http://', 'https://')) and self.base_url not in href:
                continue
            if href.startswith(('mailto:', 'tel:', 'javascript:')):
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(current_url, href)
            # Remove fragments and query parameters for deduplication
            absolute_url = absolute_url.split('#')[0].split('?')[0]
            
            if self.is_valid_url(absolute_url):
                links.add(absolute_url)
        
        return links
    
    def scrape_page(self, url):
        """Scrape a single page"""
        if url in self.visited_urls:
            return []
        
        print(f"Scraping: {url}")
        self.visited_urls.add(url)
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content
            content = self.extract_content(soup, url)
            if content and content['content']:
                self.scraped_content.append(content)
                print(f"  [OK] Extracted: {content['title'][:50]}")
            
            # Find new links to scrape
            new_links = self.find_internal_links(soup, url)
            
            # Be respectful - add delay
            time.sleep(1)
            
            return list(new_links)
            
        except Exception as e:
            print(f"  [ERROR] Error scraping {url}: {str(e)}")
            return []
    
    def scrape_all(self, max_pages=None):
        """Recursively scrape all pages starting from base_url"""
        to_visit = [self.base_url]
        pages_scraped = 0
        
        while to_visit and (max_pages is None or pages_scraped < max_pages):
            current_url = to_visit.pop(0)
            new_links = self.scrape_page(current_url)
            to_visit.extend(new_links)
            pages_scraped += 1
            
            print(f"Progress: {pages_scraped} pages scraped, {len(to_visit)} in queue")
        
        print(f"\nCompleted! Scraped {len(self.scraped_content)} pages")
    
    def save_to_json(self, filename="gitbook_data.json"):
        """Save scraped content to JSON file"""
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_content, f, indent=2, ensure_ascii=False)
        print(f"Saved to {output_path}")
    
    def save_to_markdown(self):
        """Save each page as a separate markdown file"""
        md_dir = self.output_dir / "markdown"
        md_dir.mkdir(exist_ok=True)
        
        for i, page in enumerate(self.scraped_content):
            # Create filename from title or URL
            filename = page['title'].replace('/', '-').replace(' ', '_')[:50]
            if not filename:
                filename = f"page_{i}"
            
            filepath = md_dir / f"{filename}.md"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {page['title']}\n\n")
                f.write(f"Source: {page['url']}\n\n")
                f.write("---\n\n")
                f.write(page['content'])
            
        print(f"Saved {len(self.scraped_content)} markdown files to {md_dir}")


# Example usage
if __name__ == "__main__":
    # Your Auto Finance GitBook URL
    GITBOOK_URL = "https://docs.auto.finance/"
    
    scraper = GitBookScraper(GITBOOK_URL)
    
    # Scrape all pages
    print("Starting scrape of docs.auto.finance...")
    scraper.scrape_all()  # No limit - scrape everything
    
    # Save results
    scraper.save_to_json()
    scraper.save_to_markdown()
    
    print("\nSample of scraped content:")
    for page in scraper.scraped_content[:3]:
        print(f"\nTitle: {page['title']}")
        print(f"URL: {page['url']}")
        print(f"Content length: {len(page['content'])} characters")
        print(f"Headings: {len(page['headings'])}")

