"""
Selective Scraping System
Allows updating specific data sources without re-scraping everything
"""

import json
from pathlib import Path
from datetime import datetime
import sys


class SelectiveScraper:
    """Manages selective scraping and smart merging"""
    
    def __init__(self):
        self.config_file = Path("update_config.json")
        self.load_config()
    
    def load_config(self):
        """Load or create config"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "last_updates": {
                    "docs": None,
                    "website": None,
                    "blog": None,
                    "full": None
                },
                "schedule": {
                    "enabled": False,
                    "daily_time": "03:00",
                    "daily_type": "quick",
                    "weekly_day": "sunday",
                    "weekly_enabled": True
                }
            }
            self.save_config()
    
    def save_config(self):
        """Save config"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def update_timestamp(self, source_type):
        """Update last update timestamp"""
        self.config['last_updates'][source_type] = datetime.now().isoformat()
        self.save_config()
    
    def quick_update(self):
        """Quick update - website only"""
        print("\n" + "="*70)
        print(" QUICK UPDATE - Website Only")
        print("="*70)
        print("\nThis will:")
        print("  • Scrape app.auto.finance (live data)")
        print("  • Merge with existing docs and blog")
        print("  • Rebuild index")
        print("\nTime: ~5-10 minutes")
        print("="*70 + "\n")
        
        try:
            # Scrape website
            print("[1/2] Scraping website...")
            from scrape_website import WebsiteScraper
            scraper = WebsiteScraper()
            scraper.scrape_all()
            scraper.save_to_json()
            scraper.save_to_markdown()
            
            # Update timestamp
            self.update_timestamp('website')
            
            # Merge and rebuild
            print("\n[2/2] Merging and rebuilding index...")
            self._merge_website_only()
            
            print("\n[OK] Quick update complete!")
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Quick update failed: {e}")
            return False
    
    def blog_only_update(self):
        """Blog only update"""
        print("\n" + "="*70)
        print(" BLOG UPDATE - Blog Posts Only")
        print("="*70)
        print("\nThis will:")
        print("  • Scrape blog.tokemak.xyz")
        print("  • Merge with existing docs and website")
        print("  • Rebuild index")
        print("\nTime: ~3-5 minutes")
        print("="*70 + "\n")
        
        try:
            # Scrape blog
            print("[1/2] Scraping blog...")
            from scrape_blog import BlogScraper
            scraper = BlogScraper()
            scraper.scrape_all()
            scraper.save_to_json()
            scraper.save_to_markdown()
            
            # Update timestamp
            self.update_timestamp('blog')
            
            # Merge and rebuild
            print("\n[2/2] Merging and rebuilding index...")
            self._merge_blog_only()
            
            print("\n[OK] Blog update complete!")
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Blog update failed: {e}")
            return False
    
    def docs_only_update(self):
        """Docs only update"""
        print("\n" + "="*70)
        print(" DOCS UPDATE - Documentation Only")
        print("="*70)
        print("\nThis will:")
        print("  • Scrape docs.auto.finance")
        print("  • Merge with existing website and blog")
        print("  • Rebuild index")
        print("\nTime: ~3-5 minutes")
        print("="*70 + "\n")
        
        try:
            # Scrape docs
            print("[1/2] Scraping documentation...")
            from scrape_gitbook import GitBookScraper
            scraper = GitBookScraper("https://docs.auto.finance/")
            scraper.scrape_all()
            scraper.save_to_json()
            scraper.save_to_markdown()
            
            # Update timestamp
            self.update_timestamp('docs')
            
            # Merge and rebuild
            print("\n[2/2] Merging and rebuilding index...")
            self._merge_docs_only()
            
            print("\n[OK] Docs update complete!")
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Docs update failed: {e}")
            return False
    
    def full_update(self):
        """Full update - everything"""
        print("\n" + "="*70)
        print(" FULL UPDATE - All Sources")
        print("="*70)
        print("\nThis will:")
        print("  • Scrape docs.auto.finance")
        print("  • Scrape app.auto.finance")
        print("  • Scrape blog.tokemak.xyz")
        print("  • Rebuild complete index")
        print("\nTime: ~15-20 minutes")
        print("="*70 + "\n")
        
        try:
            from scrape_all_data import run_all_scrapers
            success = run_all_scrapers()
            
            if success:
                self.update_timestamp('full')
                self.update_timestamp('docs')
                self.update_timestamp('website')
                self.update_timestamp('blog')
            
            return success
            
        except Exception as e:
            print(f"\n✗ Full update failed: {e}")
            return False
    
    def _merge_website_only(self):
        """Merge new website data with existing docs and blog"""
        from build_complete_index import CompleteIndexBuilder
        builder = CompleteIndexBuilder()
        
        # This will reload all data sources and rebuild
        # Website data is fresh, docs and blog are existing
        builder.build_index()
    
    def _merge_blog_only(self):
        """Merge new blog data with existing docs and website"""
        from build_complete_index import CompleteIndexBuilder
        builder = CompleteIndexBuilder()
        builder.build_index()
    
    def _merge_docs_only(self):
        """Merge new docs with existing website and blog"""
        from build_complete_index import CompleteIndexBuilder
        builder = CompleteIndexBuilder()
        builder.build_index()
    
    def get_last_update_info(self):
        """Get last update information"""
        return self.config['last_updates']
    
    def get_schedule_config(self):
        """Get schedule configuration"""
        return self.config['schedule']
    
    def update_schedule(self, schedule_config):
        """Update schedule configuration"""
        self.config['schedule'].update(schedule_config)
        self.save_config()


def main():
    """Command line interface"""
    scraper = SelectiveScraper()
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python scrape_selective.py [quick|full|blog|docs]")
        print("\nOptions:")
        print("  quick - Website only (5-10 mins)")
        print("  full  - Everything (20 mins)")
        print("  blog  - Blog posts only (3-5 mins)")
        print("  docs  - Documentation only (3-5 mins)")
        return
    
    update_type = sys.argv[1].lower()
    
    if update_type == 'quick':
        scraper.quick_update()
    elif update_type == 'full':
        scraper.full_update()
    elif update_type == 'blog':
        scraper.blog_only_update()
    elif update_type == 'docs':
        scraper.docs_only_update()
    else:
        print(f"Unknown update type: {update_type}")


if __name__ == "__main__":
    main()

