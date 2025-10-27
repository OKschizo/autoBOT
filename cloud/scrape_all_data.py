"""
Master scraper - runs all scrapers and rebuilds index
Run this daily to keep data fresh!
"""

import sys
from pathlib import Path

def run_all_scrapers():
    """Run all scrapers in sequence"""
    print("\n" + "="*70, flush=True)
    print(" AUTO FINANCE - COMPLETE DATA SCRAPER", flush=True)
    print("="*70, flush=True)
    print("\nThis will scrape:", flush=True)
    print("  1. Documentation (docs.auto.finance)", flush=True)
    print("  2. Website (app.auto.finance)", flush=True)
    print("  3. Blog (blog.tokemak.xyz)", flush=True)
    print("  4. Rebuild complete index\n", flush=True)
    
    # Confirmation
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        print("Running in auto mode (no confirmation)...", flush=True)
    else:
        response = input("Continue? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.", flush=True)
            return False
    
    print("\n" + "="*70, flush=True)
    
    # Step 1: Scrape docs (fast, we already have this)
    print("\n[1/4] Scraping Documentation...", flush=True)
    print("-"*70, flush=True)
    try:
        from scrape_gitbook import GitBookScraper
        scraper = GitBookScraper("https://docs.auto.finance/")
        scraper.scrape_all()
        scraper.save_to_json()
        scraper.save_to_markdown()
        print("[OK] Documentation scraped", flush=True)
    except Exception as e:
        print(f"[ERROR] Failed to scrape documentation: {e}", flush=True)
        return False
        
    # Step 2: Scrape website
    print("\n[2/4] Scraping Website...", flush=True)
    print("-"*70, flush=True)
    try:
        from scrape_website import WebsiteScraper
        scraper = WebsiteScraper("https://app.auto.finance/")
        scraper.scrape_all()
        scraper.save_to_json()
        scraper.save_to_markdown()
        print("[OK] Website scraped", flush=True)
    except Exception as e:
        print(f"[ERROR] Failed to scrape website: {e}", flush=True)
        return False
        
    # Step 3: Scrape blog
    print("\n[3/4] Scraping Blog...", flush=True)
    print("-"*70, flush=True)
    try:
        from scrape_blog import BlogScraper
        scraper = BlogScraper("https://blog.tokemak.xyz/")
        scraper.scrape_all()
        scraper.save_to_json()
        scraper.save_to_markdown()
        print("[OK] Blog scraped", flush=True)
    except Exception as e:
        print(f"[ERROR] Failed to scrape blog: {e}", flush=True)
        return False
        
    # Step 4: Build complete index
    print("\n[4/4] Building Complete Index...", flush=True)
    print("-"*70, flush=True)
    try:
        from build_complete_index import CompleteIndexBuilder
        builder = CompleteIndexBuilder()
        builder.build_index()
        builder.verify_index()
        print("[OK] Complete index built", flush=True)
    except Exception as e:
        print(f"[ERROR] Failed to build complete index: {e}", flush=True)
        return False
        
    print("\n" + "="*70, flush=True)
    print("✅ ALL TASKS COMPLETED SUCCESSFULLY!", flush=True)
    print("="*70, flush=True)
    return True

if __name__ == '__main__':
    success = run_all_scrapers()
    sys.exit(0 if success else 1)

