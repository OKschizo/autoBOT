# 📊 How to View Deployment & Runtime Logs

## Option 1: Command Line (Real-time)

### View Live Logs:
```powershell
gcloud run services logs read autofinance-bot --region us-central1 --limit 100
```

### Stream Logs (Follow):
```powershell
gcloud run services logs tail autofinance-bot --region us-central1
```

### View Build Logs:
```powershell
# Get the latest build ID
gcloud builds list --limit 1

# View logs for that build
gcloud builds log <BUILD_ID>
```

## Option 2: Google Cloud Console (Best UI)

### Runtime Logs:
**Direct Link:**
```
https://console.cloud.google.com/run/detail/us-central1/autofinance-bot/logs?project=autobot-475622
```

### Build Logs:
**Direct Link:**
```
https://console.cloud.google.com/cloud-build/builds?project=autobot-475622
```

### All Logs (Unified):
**Direct Link:**
```
https://console.cloud.google.com/logs/query?project=autobot-475622
```

## Option 3: Quick Status Check

```powershell
# Check deployment status
gcloud run services describe autofinance-bot --region us-central1 --format="value(status.conditions[0].message)"

# Check if service is ready
gcloud run services describe autofinance-bot --region us-central1 --format="value(status.url)"
```

## What to Look For:

### ✅ Success Indicators:
- `INFO: Uvicorn running on http://0.0.0.0:8080`
- `Application startup complete`
- `Started server process`

### ❌ Error Indicators:
- `ModuleNotFoundError`
- `No collection found`
- `Container failed to start`
- `Port 8080 timeout`

### 📊 Scraper Activity:
- `Starting FULL scrape`
- `Scrape completed: 465 total chunks`
- `ChromaDB built successfully`

## Quick Commands:

```powershell
# Last 50 lines
gcloud run services logs read autofinance-bot --region us-central1 --limit 50

# Only errors
gcloud run services logs read autofinance-bot --region us-central1 --limit 50 | Select-String "ERROR"

# Only scraper logs
gcloud run services logs read autofinance-bot --region us-central1 --limit 100 | Select-String "scraper"
```

