# Remote Browser Setup for Playwright

Since Playwright has issues launching browsers directly in Cloud Run, we're using a remote browser service. This allows Playwright to connect to a browser running elsewhere.

## Option 1: Browserless.io (Recommended - Easiest)

### Setup Steps:
1. Sign up at [Browserless.io](https://www.browserless.io/)
2. Get your API token from the dashboard
3. The CDP endpoint will be: `wss://production-sfo.browserless.io?token=YOUR_TOKEN`
   (Note: `wss://chrome.browserless.io` is a legacy endpoint and no longer works)

### Configuration:
Add to Cloud Run environment variables:
```
PLAYWRIGHT_REMOTE_BROWSER_ENDPOINT=wss://production-sfo.browserless.io?token=YOUR_TOKEN_HERE
```

### Pricing:
- Free tier: 6 hours/month
- Starter: $25/month for 20 hours
- Pro: $50/month for 50 hours

## Option 2: Self-Hosted Browserless (Free but requires setup)

### Setup Steps:
1. Deploy Browserless to a separate Cloud Run service or Compute Engine
2. Get the WebSocket endpoint (e.g., `wss://your-browserless-service.run.app`)
3. Configure authentication token

### Docker Compose Example:
```yaml
version: '3'
services:
  browserless:
    image: browserless/chrome:latest
    ports:
      - "3000:3000"
    environment:
      - CONNECTION_TIMEOUT=60000
      - MAX_CONCURRENT_SESSIONS=10
      - TOKEN=your-secret-token
```

### Configuration:
Add to Cloud Run environment variables:
```
PLAYWRIGHT_REMOTE_BROWSER_ENDPOINT=wss://your-browserless-service.run.app?token=your-secret-token
```

## Option 3: Other Remote Browser Services

### Puppeteer-as-a-Service
- Endpoint format: `wss://api.puppeteer-as-a-service.com?token=YOUR_TOKEN`

### ScrapingBee
- Requires using their API instead of CDP

## Testing the Connection

After setting up the remote browser endpoint, test it:

```python
from playwright.sync_api import sync_playwright

endpoint = "wss://production-sfo.browserless.io?token=YOUR_TOKEN"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(endpoint)
    page = browser.new_page()
    page.goto("https://example.com")
    print(page.title())
    browser.close()
```

## Troubleshooting

### Connection Timeout
- Check that the endpoint URL is correct
- Verify the token is valid
- Ensure the service is running

### Browser Not Found
- Make sure the endpoint supports CDP (Chrome DevTools Protocol)
- Some services use different protocols

### Cost Management
- Monitor usage if using a paid service
- Set up alerts for usage limits
- Consider caching scraped data to reduce requests

