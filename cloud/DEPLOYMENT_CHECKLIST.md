# 🚀 Cloud Deployment Checklist

## Pre-Deployment

### **1. Local Testing** ✅
- [x] Server runs without errors
- [x] Frontend loads correctly
- [x] Data Status shows 465 chunks
- [x] Bot registration works
- [x] Favicon loads (no 404)
- [ ] Google OAuth configured (needs origin authorization)
- [ ] Bot start tested (needs valid token)

### **2. Environment Variables** ⚠️
Check `.env` file has:
```bash
OPENAI_API_KEY=sk-proj-...              # ✅ Set
GOOGLE_CLIENT_ID=...apps.googleusercontent.com  # ✅ Set
OPENAI_MODEL=gpt-4o                     # ✅ Set
GCS_BUCKET_NAME=your-bucket-name        # ⚠️ Optional (for persistence)
```

### **3. Google Cloud Setup** ✅
- [x] Google Cloud SDK installed
- [x] Authenticated (`gcloud auth login`)
- [x] Project set (`gcloud config set project autobot-475622`)
- [ ] GCS bucket created (optional, for persistence)

---

## Deployment Steps

### **Step 1: Build & Deploy**
```powershell
cd C:\Users\anonw\Desktop\TOKE_SCRAPER\cloud
.\deploy.ps1
```

**Expected output:**
```
✅ Building Docker image...
✅ Pushing to Google Container Registry...
✅ Deploying to Cloud Run...
✅ Deployment complete!
URL: https://autofinance-bot-xxxxx.run.app
```

### **Step 2: Configure OAuth**
1. Go to: https://console.cloud.google.com/apis/credentials?project=autobot-475622
2. Click your OAuth 2.0 Client ID
3. Add **Authorized JavaScript origins:**
   ```
   https://autofinance-bot-xxxxx.run.app
   ```
4. Add **Authorized redirect URIs:**
   ```
   https://autofinance-bot-xxxxx.run.app
   ```
5. Click **Save**
6. Wait 1-2 minutes for changes to propagate

### **Step 3: Test Deployment**
1. Open Cloud Run URL in browser
2. Verify frontend loads
3. Click "Sign in with Google"
4. Ask a test question
5. Check Data Status tab
6. Try registering a bot (optional)

---

## Post-Deployment Verification

### **1. Health Check**
```bash
curl https://your-app.run.app/api/health
```
**Expected:**
```json
{
  "status": "running",
  "service": "Auto Finance Bot API",
  "model": "gpt-4o",
  "version": "1.0.0"
}
```

### **2. Scraper Status**
```bash
curl https://your-app.run.app/api/scraper/status
```
**Expected:**
```json
{
  "is_running": true,
  "chunk_counts": {
    "gitbook": 80,
    "website": 126,
    "blog": 259,
    "total": 465
  }
}
```

### **3. Frontend Test**
- [ ] UI loads correctly
- [ ] Google Sign-In works
- [ ] Q&A chat responds
- [ ] Data Status shows correct counts
- [ ] Bot management UI visible

---

## Troubleshooting

### **Issue: Deployment fails with "tiktoken requires Rust"**
**Fix:** Already resolved - using Python 3.11 base image

### **Issue: OAuth 403 error**
**Fix:** Add Cloud Run URL to authorized origins (see Step 2)

### **Issue: "Failed to fetch" in UI**
**Fix:** Check CORS settings in `api.py` include Cloud Run URL

### **Issue: Scraper not running**
**Fix:** Check logs: `gcloud run logs read --service autofinance-bot`

### **Issue: Conversations not persisting**
**Fix:** 
1. Create GCS bucket: `gsutil mb gs://your-bucket-name`
2. Set `GCS_BUCKET_NAME` in Cloud Run environment
3. Redeploy

---

## Monitoring

### **View Logs:**
```bash
gcloud run logs read --service autofinance-bot --limit 50
```

### **View Metrics:**
```bash
gcloud run services describe autofinance-bot
```

### **Check Container Status:**
Go to: https://console.cloud.google.com/run?project=autobot-475622

---

## Rollback

### **If deployment fails:**
```bash
# List revisions
gcloud run revisions list --service autofinance-bot

# Rollback to previous revision
gcloud run services update-traffic autofinance-bot --to-revisions=REVISION_NAME=100
```

---

## Cost Monitoring

### **Expected Costs:**
- **Cloud Run:** ~$5-10/month (depends on usage)
- **Container Registry:** ~$0.10/month
- **GCS Storage:** ~$0.02/month
- **Total:** **~$5-10/month**

### **Free Tier:**
- Cloud Run: 2 million requests/month
- GCS: 5 GB storage
- Container Registry: 0.5 GB storage

---

## Security Checklist

- [ ] OAuth client ID is for production
- [ ] API keys are in Cloud Run secrets (not in code)
- [ ] CORS only allows your domains
- [ ] Rate limiting enabled (future)
- [ ] HTTPS enforced (automatic on Cloud Run)

---

## Next Steps After Deployment

1. **Share URL** with team
2. **Monitor usage** for first 24 hours
3. **Set up alerts** for errors
4. **Configure GCS backups** for persistence
5. **Add custom domain** (optional)

---

## Quick Reference

| Resource | URL |
|----------|-----|
| **Cloud Run Console** | https://console.cloud.google.com/run?project=autobot-475622 |
| **OAuth Credentials** | https://console.cloud.google.com/apis/credentials?project=autobot-475622 |
| **Container Registry** | https://console.cloud.google.com/gcr?project=autobot-475622 |
| **GCS Buckets** | https://console.cloud.google.com/storage?project=autobot-475622 |

---

## Emergency Contacts

**If something goes wrong:**
1. Check logs: `gcloud run logs read --service autofinance-bot`
2. Check status: `gcloud run services describe autofinance-bot`
3. Rollback if needed (see Rollback section)
4. Local testing still works at `http://localhost:8000`

---

**🎯 Ready to deploy? Run `.\deploy.ps1` in the `cloud/` directory!**

