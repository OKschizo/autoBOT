# Cloud Storage Setup Guide

## Overview

The bot manager uses a **hybrid storage approach**:

- **Vector DB (ChromaDB)**: Ephemeral, rebuilt on startup (~2 min)
- **Conversations**: Persistent in Google Cloud Storage (GCS)
- **Bot Configs**: Persistent in GCS

This approach is optimal because:
- ✅ Always fresh data (auto-scrapes on startup)
- ✅ User conversations persist across restarts
- ✅ Cost-effective (~$0.10/month)
- ✅ No external vector DB subscription needed

---

## Setup Steps

### 1. Create a GCS Bucket

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Create bucket (choose a unique name)
gsutil mb -p $PROJECT_ID gs://autofinance-bot-data

# Or use the console:
# https://console.cloud.google.com/storage/browser
```

### 2. Create a Service Account

```bash
# Create service account
gcloud iam service-accounts create autofinance-bot \
    --display-name="Auto Finance Bot" \
    --project=$PROJECT_ID

# Grant Storage Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:autofinance-bot@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=autofinance-bot@$PROJECT_ID.iam.gserviceaccount.com
```

### 3. Configure Environment Variables

Update your `.env` file:

```bash
# Google Cloud Storage
GCS_BUCKET_NAME=autofinance-bot-data
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
```

### 4. Update Dockerfile

Add the service account key to your Docker image:

```dockerfile
# Copy service account key (for GCS access)
COPY service-account-key.json /app/service-account-key.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
```

### 5. Deploy to Cloud Run

```bash
# Build and deploy
cd cloud
gcloud builds submit --tag gcr.io/$PROJECT_ID/autofinance-bot
gcloud run deploy autofinance-bot \
    --image gcr.io/$PROJECT_ID/autofinance-bot \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars="GCS_BUCKET_NAME=autofinance-bot-data" \
    --service-account=autofinance-bot@$PROJECT_ID.iam.gserviceaccount.com
```

---

## How It Works

### On Startup:
1. **Restore conversations** from GCS (`conversations.db`)
2. **Scrape fresh data** (GitBook + Website + Blog) → ~2 minutes
3. **Build ChromaDB** locally in container
4. **Start serving** requests

### During Operation:
- Conversations saved to local SQLite
- Periodic backup to GCS (every 5 minutes)
- Data re-scraped every 10 minutes (website only)

### On Shutdown:
- **Backup conversations** to GCS
- Discard ephemeral ChromaDB (will rebuild on next startup)

---

## Local Testing (Without GCS)

For local development, GCS is **optional**:

```bash
# Run without GCS
cd cloud/backend
python api.py

# Conversations will be stored locally in conversations.db
# (Lost on container restart, but fine for testing)
```

---

## Cost Estimate

**GCS Storage:**
- Conversations DB: ~10 MB
- Bot configs: ~1 KB
- **Total: $0.02/month**

**Data Transfer:**
- Backup on shutdown: ~10 MB
- Restore on startup: ~10 MB
- Daily restarts: ~20 MB/day = 600 MB/month
- **Total: $0.08/month**

**Grand Total: ~$0.10/month** 🎉

---

## Troubleshooting

### "GCS storage not available"
- Check that `google-cloud-storage` is installed
- Verify `GCS_BUCKET_NAME` is set
- Ensure service account has Storage Admin role

### "Permission denied" on GCS
- Verify service account key is valid
- Check IAM permissions in Cloud Console
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to correct file

### Conversations not persisting
- Check logs for "Backing up conversations to GCS"
- Verify bucket exists: `gsutil ls gs://your-bucket-name`
- Test manually: `gsutil cp conversations.db gs://your-bucket-name/`

---

## Alternative: Skip GCS (Ephemeral Mode)

If you don't need persistent conversations:

1. **Don't set** `GCS_BUCKET_NAME`
2. System will work fine, but conversations reset on restart
3. Good for testing or if you don't care about history

---

## Next Steps

1. ✅ Set up GCS bucket
2. ✅ Create service account
3. ✅ Update `.env` and Dockerfile
4. ✅ Deploy to Cloud Run
5. ✅ Test that conversations persist across restarts

**Ready to deploy!** 🚀


