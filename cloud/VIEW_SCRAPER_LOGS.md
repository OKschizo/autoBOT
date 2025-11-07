# Viewing Scraper Logs and Progress

## Frontend Progress Display

The frontend now shows real-time progress when a scrape is running:

1. **Go to Data Status tab** in the web interface
2. **Progress card appears** automatically when `is_scraping = true`
3. **Auto-refreshes every 2 seconds** during active scraping
4. **Shows:**
   - Current stage (GitBook/Website/Blog/Indexing)
   - Current step description
   - Progress bars with page/chunk counts

## Cloud Console Logs

For detailed page-by-page progress logs, use Google Cloud Console:

### Quick Access
1. **Direct URL:** https://console.cloud.google.com/logs/query
2. **Filter by service:** `resource.labels.service_name=autofinance-bot`
3. **Search for:** `scrape`, `progress`, `GitBook`, `Website`, `Blog`, `Indexing`

### Detailed Filter Query

```
resource.type="cloud_run_revision"
resource.labels.service_name="autofinance-bot"
(textPayload=~"scrape" OR textPayload=~"progress" OR textPayload=~"GitBook" OR textPayload=~"Website" OR textPayload=~"Blog" OR textPayload=~"Indexing")
```

### Viewing Specific Stages

**GitBook Scraping:**
```
resource.type="cloud_run_revision"
resource.labels.service_name="autofinance-bot"
textPayload=~"GitBook|docs.auto.finance"
```

**Website Scraping:**
```
resource.type="cloud_run_revision"
resource.labels.service_name="autofinance-bot"
textPayload=~"app.auto.finance|Website"
```

**Blog Scraping:**
```
resource.type="cloud_run_revision"
resource.labels.service_name="autofinance-bot"
textPayload=~"blog.tokemak|Blog"
```

**Index Building:**
```
resource.type="cloud_run_revision"
resource.labels.service_name="autofinance-bot"
textPayload=~"Indexing|Building|ChromaDB"
```

### Command Line Access

View recent scraper logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=autofinance-bot AND (textPayload=~'scrape' OR textPayload=~'progress')" --limit=50 --format="table(timestamp,severity,textPayload)" --freshness=1h
```

View logs for current revision:
```bash
REVISION=$(gcloud run services describe autofinance-bot --region=us-central1 --format="value(status.latestReadyRevisionName)")
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.revision_name=$REVISION" --limit=100 --format="value(textPayload)" --freshness=2h | grep -i "scrape\|progress"
```

## What Progress Shows

### Frontend (Real-time)
- ✅ Current stage name
- ✅ Stage status message
- ✅ Progress bars (when counts available)
- ✅ Auto-refresh every 2 seconds during scraping

### Cloud Console (Detailed)
- ✅ Page-by-page scraping progress
- ✅ URLs being scraped
- ✅ Errors and timeouts
- ✅ Completion messages
- ✅ Index building batch progress

## Example Log Output

```
[1/4] Scraping documentation...
Starting GitBook scrape: https://docs.auto.finance/
Scraping: https://docs.auto.finance/page1
  [OK] Extracted: Page Title
Progress: 1 pages scraped, 5 in queue
...
[OK] Documentation scraped (63 pages)

[2/4] Scraping website...
Starting scrape of https://app.auto.finance/
Progress: 1 pages scraped, 3 in queue
...
[OK] Website scraped (16 pages)

[3/4] Scraping blog...
Starting blog scrape: https://blog.tokemak.xyz/
[1/15] Scraping: https://blog.tokemak.xyz/post1
  [OK] Extracted: Post Title
...
[OK] Blog scraped (15 posts)

[4/4] Building complete index...
[STEP] Chunking documentation...
[STEP] Chunking website pages...
[STEP] Chunking blog posts...
[INFO] Total chunks prepared: 441
[STEP] Indexing chunks...
  Batch 1/5
  Batch 2/5
...
[OK] Index built successfully with 441 chunks.
```

## Troubleshooting

**No progress showing:**
- Check if scrape is actually running: `is_scraping` should be `true`
- Check browser console for API errors
- Verify `/api/scraper/status` endpoint returns `current_progress`

**Progress not updating:**
- Frontend auto-refreshes every 2 seconds when scraping
- If stuck, manually refresh the page
- Check Cloud Console for detailed logs

**Can't find logs:**
- Ensure you're logged into the correct GCP project
- Check the revision name matches the deployed service
- Use broader time range (last 2-4 hours)

