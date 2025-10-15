"""
Master scraper - runs all scrapers and rebuilds index
Run this daily to keep data fresh!
"""

import sys
from pathlib import Path

def run_all_scrapers():
    """Run all scrapers in sequence"""
    print("\n" + "="*70)
    print(" AUTO FINANCE - COMPLETE DATA SCRAPER")
    print("="*70)
    print("\nThis will scrape:")
    print("  1. Documentation (docs.auto.finance)")
    print("  2. Website (app.auto.finance)")
    print("  3. Blog (blog.tokemak.xyz)")
    print("  4. Rebuild complete index\n")
    
    # Confirmation
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        print("Running in auto mode (no confirmation)...")
    else:
        response = input("Continue? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return False
    
    print("\n" + "="*70)
    
    # Step 1: Scrape docs (fast, we already have this)
    print("\n[1/4] Scraping Documentation...")
    print("-"*70)
    try:
        from scrape_gitbook import GitBookScraper
        scraper = GitBookScraper("https://docs.auto.finance/")
        scraper.scrape_all()
        scraper.save_to_json()
        scraper.save_to_markdown()
        print("[OK] Documentation scraped")
    except Exception as e:
        print(f"[ERROR] Error scraping docs: {e}")
        print("  (Continuing with existing docs data...)")
    
    # Step 2: Scrape website
    print("\n[2/4] Scraping Website (app.auto.finance)...")
    print("-"*70)
    try:
        from scrape_website import WebsiteScraper
        scraper = WebsiteScraper()
        scraper.scrape_all()
        scraper.save_to_json()
        scraper.save_to_markdown()
        print("[OK] Website scraped")
    except Exception as e:
        print(f"[ERROR] Error scraping website: {e}")
        return False
    
    # Step 3: Scrape blog
    print("\n[3/4] Scraping Blog (blog.tokemak.xyz)...")
    print("-"*70)
    try:
        from scrape_blog import BlogScraper
        scraper = BlogScraper()
        scraper.scrape_all()
        scraper.save_to_json()
        scraper.save_to_markdown()
        print("[OK] Blog scraped")
    except Exception as e:
        print(f"[ERROR] Error scraping blog: {e}")
        print("  (Continuing without blog data...)")
    
    # Step 4: Build complete index
    print("\n[4/4] Building Complete Index...")
    print("-"*70)
    try:
        from build_complete_index import CompleteIndexBuilder
        builder = CompleteIndexBuilder()
        builder.build_index()
        builder.verify_index()
        print("[OK] Complete index built")
    except Exception as e:
        print(f"[ERROR] Error building index: {e}")
        return False
    
    # Summary
    print("\n" + "="*70)
    print(" SCRAPING COMPLETE!")
    print("="*70)
    print("\n[OK] All data scraped and indexed")
    print("[OK] New collection: 'auto_finance_complete'")
    print("[OK] Original collection preserved as backup")
    print("\nYour bot can now use the complete dataset!")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    success = run_all_scrapers()
    sys.exit(0 if success else 1)

