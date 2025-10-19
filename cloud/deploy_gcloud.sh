#!/bin/bash
# Deploy Auto Finance Bot to Google Cloud Run

echo "🚀 Deploying Auto Finance Bot to Google Cloud Run"
echo "=================================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No Google Cloud project set. Run:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📍 Project: $PROJECT_ID"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it with:"
    echo "   GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com"
    echo "   ANTHROPIC_API_KEY=sk-ant-..."
    echo "   OPENAI_API_KEY=sk-proj-..."
    echo "   BOT_MODEL=claude-sonnet-4-20250514"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if GOOGLE_CLIENT_ID is in frontend/app.js
if grep -q "PASTE_YOUR_ACTUAL_CLIENT_ID_HERE" frontend/app.js; then
    echo "❌ Please update frontend/app.js line 3 with your actual Google Client ID"
    echo "   Open cloud/frontend/app.js and replace:"
    echo "   'PASTE_YOUR_ACTUAL_CLIENT_ID_HERE'"
    echo "   with:"
    echo "   '$GOOGLE_CLIENT_ID'"
    exit 1
fi

echo "✅ Environment variables loaded"
echo ""

# Service name
SERVICE_NAME="autofinance-bot"
REGION="us-central1"

echo "🏗️  Building and deploying to Cloud Run..."
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo ""

# Build from parent directory (to include scraped_data)
cd ..

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --source ./cloud \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY,OPENAI_API_KEY=$OPENAI_API_KEY,BOT_MODEL=$BOT_MODEL,GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "📍 Your app is live at:"
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
    echo "   $SERVICE_URL"
    echo ""
    echo "⚠️  IMPORTANT: Update Google OAuth settings:"
    echo "   1. Go to https://console.cloud.google.com/apis/credentials"
    echo "   2. Edit your OAuth 2.0 Client ID"
    echo "   3. Add to Authorized JavaScript origins:"
    echo "      $SERVICE_URL"
    echo ""
    echo "🎉 Done! Your bot is ready to use!"
else
    echo ""
    echo "❌ Deployment failed. Check the errors above."
    exit 1
fi

