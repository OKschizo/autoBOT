"""
Scrape blog.tokemak.xyz blog posts
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urljoin, urlparse

import os

class BlogScraper:
    """Scrapes blog.tokemak.xyz"""
    
    def __init__(self, base_url="https://blog.tokemak.xyz", output_dir="scraped_data/blog"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.blog_posts = []
        self.launch_timeout = int(os.getenv('PLAYWRIGHT_LAUNCH_TIMEOUT_MS', '1800000'))  # default 30 mins
        self.page_timeout = int(os.getenv('PLAYWRIGHT_OPERATION_TIMEOUT_MS', '90000'))  # default 90 seconds
    
    def extract_blog_post(self, page, url):
        """Extract blog post content"""
        print(f"  [PARSE] {url}", flush=True)
        
        try:
            # Wait for content to load
            page.wait_for_load_state('networkidle', timeout=60000)  # Increased from 10 to 60 seconds
            time.sleep(2)
            
            # Get title
            title = page.title()
            
            # Try to find article content
            # Look for common blog post containers
            article_content = None
            
            # Try various selectors for blog content
            selectors = [
                'article',
                '[role="article"]',
                '.blog-post',
                '.post-content',
                'main'
            ]
            
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible():
                        article_content = element.inner_text()
                        break
                except:
                    continue
            
            # Fallback to body if no article found
            if not article_content:
                article_content = page.inner_text('body')
            
            # Try to extract metadata
            metadata = {}
            
            # Look for date
            date_selectors = [
                'time',
                '.date',
                '.published',
                '[datetime]'
            ]
            
            for selector in date_selectors:
                try:
                    date_element = page.locator(selector).first
                    if date_element.is_visible():
                        metadata['date'] = date_element.inner_text()
                        break
                except:
                    continue
            
            # Look for read time
            try:
                read_time = page.locator('text=/min read/i').first
                if read_time.is_visible():
                    metadata['read_time'] = read_time.inner_text()
            except:
                pass
            
            return {
                'url': url,
                'title': title,
                'content': article_content,
                'metadata': metadata,
                'scraped_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
        except Exception as e:
            print(f"  Error extracting post: {e}", flush=True)
            return None
    
    def find_blog_post_links(self, page):
        """Find all blog post links from the blog homepage"""
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
                    
                    # Check if it's a blog post (usually has path segments)
                    parsed = urlparse(absolute_url)
                    
                    # Skip if it's just the homepage or navigation
                    if (absolute_url.startswith(self.base_url) and 
                        parsed.path and 
                        parsed.path != '/' and
                        not parsed.path.startswith('/tag/') and
                        not parsed.path.startswith('/category/')):
                        links.add(absolute_url)
                        
                except:
                    continue
        
        except Exception as e:
            print(f"  Error finding links: {e}", flush=True)
        
        return links
    
    def scrape_all(self):
        """Scrape all blog posts"""
        print(f"Starting blog scrape: {self.base_url}", flush=True)

        with sync_playwright() as p:
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
            
            # First, visit the blog homepage to find all posts
            print(f"\nVisiting blog homepage...", flush=True)
            page.goto(self.base_url, wait_until='domcontentloaded', timeout=self.page_timeout)
            time.sleep(3)  # Wait for dynamic content
            # Find all blog post links
            post_links = self.find_blog_post_links(page)
            print(f"Found {len(post_links)} blog post URLs", flush=True)
            
            # Scrape each post
            for i, post_url in enumerate(post_links, 1):
                print(f"\n[{i}/{len(post_links)}] Scraping: {post_url}", flush=True)
                
                try:
                    start_time = time.time()
                    page.goto(post_url, wait_until='domcontentloaded', timeout=self.page_timeout)
                    print(f"  [OK] Loaded in {time.time() - start_time:.1f}s", flush=True)
                    
                    # Extract post data
                    post_data = self.extract_blog_post(page, post_url)
                    
                    if post_data:
                        self.blog_posts.append(post_data)
                        print(f"  [OK] Extracted: {post_data['title'][:60]}", flush=True)
                    
                    # Be polite
                    time.sleep(2.5)
                    
                except PlaywrightTimeoutError as e:
                    print(f"  [TIMEOUT] {post_url} ({e})", flush=True)
                    continue
                except Exception as e:
                    print(f"  [ERROR] Error scraping post: {e}", flush=True)
                    continue
            
            browser.close()
        
        print(f"\n[OK] Completed! Scraped {len(self.blog_posts)} blog posts", flush=True)
    
    def save_to_json(self, filename="blog_posts.json"):
        """Save blog posts to JSON"""
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.blog_posts, f, indent=2, ensure_ascii=False)
        print(f"Saved to {output_path}", flush=True)
    
    def save_to_markdown(self):
        """Save each post as markdown"""
        md_dir = self.output_dir / "markdown"
        md_dir.mkdir(exist_ok=True)
        
        for i, post in enumerate(self.blog_posts):
            # Create filename from title
            title = post['title'].replace('/', '-').replace(' ', '_')[:50]
            filename = f"post_{i}_{title}.md"
            
            filepath = md_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {post['title']}\n\n")
                f.write(f"URL: {post['url']}\n")
                f.write(f"Scraped: {post['scraped_at']}\n\n")
                
                if post.get('metadata'):
                    f.write("## Metadata\n\n")
                    for key, value in post['metadata'].items():
                        f.write(f"- **{key}**: {value}\n")
                    f.write("\n")
                
                f.write("## Content\n\n")
                f.write(post['content'])
        
        print(f"Saved {len(self.blog_posts)} markdown files to {md_dir}", flush=True)


def main():
    """Main function"""
    scraper = BlogScraper()
    
    print("="*60)
    print("Auto Finance Blog Scraper")
    print("="*60)
    
    # Scrape all posts
    scraper.scrape_all()
    
    # Save results
    scraper.save_to_json()
    scraper.save_to_markdown()
    
    print("\n" + "="*60)
    print(f"Total blog posts scraped: {len(scraper.blog_posts)}", flush=True)
    print("="*60)


if __name__ == "__main__":
    main()
