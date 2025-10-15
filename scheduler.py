"""
Automated Scheduler for Data Updates
Runs in background, triggers updates at scheduled times
"""

import schedule
import time
import threading
from datetime import datetime
import json
from pathlib import Path


class UpdateScheduler:
    """Manages scheduled updates"""
    
    def __init__(self):
        self.config_file = Path("update_config.json")
        self.running = False
        self.scheduler_thread = None
        self.load_config()
    
    def load_config(self):
        """Load config"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "schedule": {
                    "enabled": False,
                    "daily_time": "03:00",
                    "daily_type": "quick",
                    "weekly_day": "sunday",
                    "weekly_time": "03:00",
                    "weekly_enabled": True
                },
                "last_updates": {
                    "docs": None,
                    "website": None,
                    "blog": None,
                    "full": None
                }
            }
    
    def save_config(self):
        """Save config"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _run_quick_update(self):
        """Run quick update"""
        print(f"\n[{datetime.now()}] Running scheduled quick update...")
        try:
            from scrape_selective import SelectiveScraper
            scraper = SelectiveScraper()
            scraper.quick_update()
            print("✓ Scheduled quick update completed")
        except Exception as e:
            print(f"✗ Scheduled quick update failed: {e}")
    
    def _run_full_update(self):
        """Run full update"""
        print(f"\n[{datetime.now()}] Running scheduled full update...")
        try:
            from scrape_selective import SelectiveScraper
            scraper = SelectiveScraper()
            scraper.full_update()
            print("✓ Scheduled full update completed")
        except Exception as e:
            print(f"✗ Scheduled full update failed: {e}")
    
    def setup_schedule(self):
        """Setup scheduled tasks based on config"""
        schedule.clear()
        
        if not self.config['schedule']['enabled']:
            print("Scheduler disabled")
            return
        
        # Daily quick update
        daily_time = self.config['schedule']['daily_time']
        daily_type = self.config['schedule']['daily_type']
        
        if daily_type == 'quick':
            schedule.every().day.at(daily_time).do(self._run_quick_update)
            print(f"Scheduled: Quick update daily at {daily_time}")
        elif daily_type == 'full':
            schedule.every().day.at(daily_time).do(self._run_full_update)
            print(f"Scheduled: Full update daily at {daily_time}")
        
        # Weekly full update
        if self.config['schedule'].get('weekly_enabled', False):
            weekly_day = self.config['schedule']['weekly_day']
            weekly_time = self.config['schedule']['weekly_time']
            
            schedule_func = getattr(schedule.every(), weekly_day.lower())
            schedule_func.at(weekly_time).do(self._run_full_update)
            print(f"Scheduled: Full update every {weekly_day} at {weekly_time}")
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            print("Scheduler already running")
            return
        
        self.setup_schedule()
        self.running = True
        
        def run_scheduler():
            print(f"Scheduler started at {datetime.now()}")
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            print("Scheduler stopped")
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
    
    def get_next_run(self):
        """Get next scheduled run time"""
        jobs = schedule.get_jobs()
        if not jobs:
            return None
        
        next_job = min(jobs, key=lambda j: j.next_run)
        return next_job.next_run
    
    def is_running(self):
        """Check if scheduler is running"""
        return self.running


# Standalone scheduler (can run separately)
def run_standalone_scheduler():
    """Run scheduler as standalone process"""
    print("="*70)
    print(" AUTO FINANCE - UPDATE SCHEDULER")
    print("="*70)
    print("\nStarting automated update scheduler...")
    print("This will run in the background and trigger updates at scheduled times.")
    print("Press Ctrl+C to stop.\n")
    
    scheduler = UpdateScheduler()
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping scheduler...")
        scheduler.stop()
        print("Scheduler stopped.")


if __name__ == "__main__":
    run_standalone_scheduler()

