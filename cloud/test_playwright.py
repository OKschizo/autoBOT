#!/usr/bin/env python3
"""Test if Playwright can launch in Docker"""
import sys
print("Starting Playwright test...", flush=True)

try:
    from playwright.sync_api import sync_playwright
    print("✓ Playwright imported successfully", flush=True)
    
    with sync_playwright() as p:
        print("✓ sync_playwright context created", flush=True)
        
        print("Attempting to launch Chromium with Docker-safe args...", flush=True)
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        print("✓ Browser launched successfully!", flush=True)
        
        page = browser.new_page()
        print("✓ Page created", flush=True)
        
        page.goto('https://example.com')
        print(f"✓ Navigated to page: {page.title()}", flush=True)
        
        browser.close()
        print("✓ Browser closed", flush=True)
        print("\n✅ ALL TESTS PASSED!", flush=True)
        
except Exception as e:
    print(f"\n❌ ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

