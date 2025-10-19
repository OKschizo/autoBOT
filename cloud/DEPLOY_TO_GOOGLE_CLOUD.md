# 🚀 Deploy to Google Cloud Run

Complete guide to deploy your Auto Finance Bot to Google Cloud.

---

## ✨ What You Get

- ✅ **Live web app** accessible from anywhere
- ✅ **Auto-scaling** (0 to 1000+ users)
- ✅ **HTTPS** included (automatic SSL)
- ✅ **Custom domain** support
- ✅ **Pay-per-use** (~$5-20/month for moderate traffic)
- ✅ **No server management** required

---

## 📋 Prerequisites

### 1. Install Google Cloud SDK

**Windows:**
```bash
https://cloud.google.com/sdk/docs/install
# Download and run installer
```

**Mac/Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### 2. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. **Enable billing** (required for Cloud Run)
4. Note your **Project ID**

### 3. Set Up Project

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

---

## 🔧 Configuration Steps

### Step 1: Copy Google Client ID to Frontend

1. Open your `cloud/.env` file
2. Copy the `GOOGLE_CLIENT_ID` value
3. Open `cloud/frontend/app.js`
4. **Replace line 3:**

```javascript
// FROM:
const GOOGLE_CLIENT_ID = 'PASTE_YOUR_ACTUAL_CLIENT_ID_HERE';

// TO:
const GOOGLE_CLIENT_ID = '123456789-abc123.apps.googleusercontent.com';  // Your actual ID
```

### Step 2: Verify Your .env File

Make sure `cloud/.env` has all required variables:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com

# AI Models (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...

# Model selection
BOT_MODEL=claude-sonnet-4-20250514
# OR
# BOT_MODEL=gpt-4o
```

---

## 🚀 Deploy!

### Automated Deployment (Recommended)

**Windows:**
```bash
cd cloud
deploy_gcloud.bat
```

**Mac/Linux:**
```bash
cd cloud
chmod +x deploy_gcloud.sh
./deploy_gcloud.sh
```

This will:
1. ✅ Check all requirements
2. ✅ Build Docker container
3. ✅ Upload to Google Cloud
4. ✅ Deploy to Cloud Run
5. ✅ Give you the live URL

---

### Manual Deployment

If you prefer step-by-step:

```bash
cd cloud

# Deploy
gcloud run deploy autofinance-bot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "ANTHROPIC_API_KEY=sk-ant-...,OPENAI_API_KEY=sk-proj-...,BOT_MODEL=claude-sonnet-4-20250514,GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com" \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10
```

---

## ⚙️ Post-Deployment Setup

### Update Google OAuth Settings

After deployment, you'll get a URL like:
```
https://autofinance-bot-abc123-uc.a.run.app
```

**You MUST add this to Google OAuth:**

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Click on your **OAuth 2.0 Client ID**
3. Under **Authorized JavaScript origins**, add:
   ```
   https://autofinance-bot-abc123-uc.a.run.app
   ```
4. Click **SAVE**

**Important:** Without this step, Google Sign-In will show a 400 error!

---

## 🎨 Custom Domain (Optional)

Want your own domain like `bot.yourcompany.com`?

```bash
# Map custom domain
gcloud run services update autofinance-bot \
  --platform managed \
  --region us-central1 \
  --add-env-vars CUSTOM_DOMAIN=bot.yourcompany.com

# Add domain mapping
gcloud run domain-mappings create \
  --service autofinance-bot \
  --domain bot.yourcompany.com \
  --region us-central1
```

Then update your DNS records as shown in the output.

---

## 📊 Monitoring & Logs

### View Logs
```bash
# Real-time logs
gcloud run services logs tail autofinance-bot --region us-central1

# Or in web console
https://console.cloud.google.com/run
```

### Check Status
```bash
gcloud run services describe autofinance-bot --region us-central1
```

### View Metrics
Go to: [Cloud Run Dashboard](https://console.cloud.google.com/run)
- Request count
- Latency
- Error rate
- Instance count

---

## 💰 Cost Estimate

### Free Tier (First 2M requests/month):
- ✅ **First 180,000 vCPU-seconds** free
- ✅ **First 360,000 GiB-seconds** free  
- ✅ **First 2M requests** free

### After Free Tier:
- **vCPU:** $0.00002400/vCPU-second
- **Memory:** $0.00000250/GiB-second
- **Requests:** $0.40/million

### Example Monthly Costs:

**Small team (1,000 questions/month):**
- Likely **$0** (within free tier)

**Medium usage (10,000 questions/month):**
- ~**$2-5/month** infrastructure
- + AI API costs

**High usage (100,000 questions/month):**
- ~**$15-30/month** infrastructure
- + AI API costs

**AI API Costs (separate):**
- Claude: ~$0.015 per question
- GPT-4o: ~$0.005 per question

---

## 🔄 Update Deployed App

Made changes? Redeploy with:

```bash
cd cloud
./deploy_gcloud.sh  # or deploy_gcloud.bat on Windows
```

Cloud Run will:
1. Build new container
2. Replace old version
3. Zero downtime deployment

---

## 🐛 Troubleshooting

### "Permission denied" error
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### "Billing not enabled"
- Go to [Billing](https://console.cloud.google.com/billing)
- Link a billing account (required for Cloud Run)

### "Build failed"
- Check that parent directory has `scraped_data/` folder
- Ensure all parent Python files exist
- Try: `gcloud builds submit --tag gcr.io/PROJECT_ID/autofinance-bot`

### "Google Sign-In 400 error"
- Make sure you added Cloud Run URL to OAuth authorized origins
- Check `GOOGLE_CLIENT_ID` in both `.env` AND `frontend/app.js`

### "No data / bot doesn't answer"
- Ensure `scraped_data/` was included in build
- Check logs: `gcloud run services logs tail autofinance-bot`
- May need to run `scrape_all_data.py` locally first

---

## 🔒 Security Best Practices

### 1. Restrict Access (Optional)

If you only want your team to access:

```bash
gcloud run services update autofinance-bot \
  --no-allow-unauthenticated \
  --region us-central1
```

Then set up IAM permissions for specific users.

### 2. Restrict OAuth Domain

In your Google OAuth consent screen:
- Add authorized domain
- Restrict to internal organization (if using Google Workspace)

### 3. Environment Variables

Never commit these to GitHub:
- ✅ `.env` is gitignored
- ✅ Variables passed securely via `--set-env-vars`
- ✅ Cloud Run encrypts environment variables

---

## 📈 Scaling Configuration

### Adjust Resources

```bash
# More power (for high traffic)
gcloud run services update autofinance-bot \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 100 \
  --region us-central1

# Cost-optimized (for low traffic)
gcloud run services update autofinance-bot \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --region us-central1
```

### Auto-scaling Settings

```bash
# Scale to zero when idle (save money)
gcloud run services update autofinance-bot \
  --min-instances 0 \
  --max-instances 10 \
  --region us-central1

# Keep 1 instance warm (faster response)
gcloud run services update autofinance-bot \
  --min-instances 1 \
  --max-instances 10 \
  --region us-central1
```

---

## 🎉 Success Checklist

- [ ] Google Cloud SDK installed
- [ ] Project created with billing enabled
- [ ] `.env` file configured with all API keys
- [ ] `GOOGLE_CLIENT_ID` copied to `frontend/app.js`
- [ ] Deployment script ran successfully
- [ ] Cloud Run URL added to Google OAuth authorized origins
- [ ] Tested sign-in and asking questions
- [ ] (Optional) Custom domain configured
- [ ] (Optional) Monitoring set up

---

## 🔗 Useful Links

- **Google Cloud Run Docs:** https://cloud.google.com/run/docs
- **Cloud Run Pricing:** https://cloud.google.com/run/pricing
- **OAuth Setup:** https://console.cloud.google.com/apis/credentials
- **Your Deployments:** https://console.cloud.google.com/run

---

## 📞 Need Help?

**Common Issues:**
1. Check logs: `gcloud run services logs tail autofinance-bot`
2. Verify environment variables are set
3. Ensure OAuth origins match deployed URL
4. Confirm billing is enabled

**Still stuck?** Review the error messages in Cloud Build logs at:
https://console.cloud.google.com/cloud-build/builds

---

**You're all set!** 🎉

Your Auto Finance Bot is now running on Google Cloud, accessible to your team from anywhere!

