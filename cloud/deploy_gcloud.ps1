# Deploy Auto Finance Bot to Google Cloud Run (PowerShell version with build monitoring)

Write-Host ""
Write-Host "🚀 Deploying Auto Finance Bot to Google Cloud Run" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if gcloud is installed
$gcloudPath = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloudPath) {
    Write-Host "❌ gcloud CLI not found. Please install it:" -ForegroundColor Red
    Write-Host "   https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Get project ID
$PROJECT_ID = gcloud config get-value project 2>$null
if (-not $PROJECT_ID) {
    Write-Host "❌ No Google Cloud project set. Run:" -ForegroundColor Red
    Write-Host "   gcloud config set project YOUR_PROJECT_ID" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "📍 Project: $PROJECT_ID" -ForegroundColor Green
Write-Host ""

# Check if .env exists (try cloud/.env first, then ../.env)
$envPath = ".env"
if (-not (Test-Path $envPath)) {
    $envPath = "..\.env"
}
if (-not (Test-Path $envPath)) {
    Write-Host "❌ .env file not found. Please create it with:" -ForegroundColor Red
    Write-Host "   GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com" -ForegroundColor Yellow
    Write-Host "   ANTHROPIC_API_KEY=sk-ant-..." -ForegroundColor Yellow
    Write-Host "   OPENAI_API_KEY=sk-proj-..." -ForegroundColor Yellow
    Write-Host "   BOT_MODEL=claude-sonnet-4-20250514" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "📄 Loading environment variables from: $envPath" -ForegroundColor Cyan

# Load environment variables
$envVars = @{}
Get-Content $envPath | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $envVars[$matches[1]] = $matches[2]
    }
}

# Validate required keys
if (-not $envVars['ANTHROPIC_API_KEY'] -or $envVars['ANTHROPIC_API_KEY'] -match 'your-key-here|placeholder|sk-ant-your') {
    Write-Host "❌ WARNING: ANTHROPIC_API_KEY appears to be a placeholder!" -ForegroundColor Red
    Write-Host "   Please update $envPath with a real API key" -ForegroundColor Yellow
    Read-Host "Press Enter to continue anyway (or Ctrl+C to cancel)"
}

# Check if GOOGLE_CLIENT_ID is in frontend/app.js
$appJsContent = Get-Content "frontend\app.js" -Raw -ErrorAction SilentlyContinue
if ($appJsContent -match "PASTE_YOUR_ACTUAL_CLIENT_ID_HERE") {
    Write-Host "❌ Please update frontend\app.js with your actual Google Client ID" -ForegroundColor Red
    Write-Host "   Replace 'PASTE_YOUR_ACTUAL_CLIENT_ID_HERE' with: $($envVars['GOOGLE_CLIENT_ID'])" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Environment variables loaded" -ForegroundColor Green
Write-Host ""

# Service settings
$SERVICE_NAME = "autofinance-bot"
$REGION = "us-central1"

Write-Host "🏗️  Building and deploying to Cloud Run..." -ForegroundColor Cyan
Write-Host "   Service: $SERVICE_NAME" -ForegroundColor White
Write-Host "   Region: $REGION" -ForegroundColor White
Write-Host "   Using E2_HIGHCPU_8 machine for faster builds (8x faster)" -ForegroundColor Yellow
Write-Host ""

# Verify frontend files exist
if (-not (Test-Path "frontend\index.html")) {
    Write-Host "❌ ERROR: frontend\index.html not found!" -ForegroundColor Red
    Write-Host "   Make sure you're running this from the cloud\ directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Frontend files verified" -ForegroundColor Green
Write-Host ""

# Build env-vars string
$anthropicKey = $envVars['ANTHROPIC_API_KEY']
$openaiKey = $envVars['OPENAI_API_KEY']
$botModel = $envVars['BOT_MODEL']
$googleClientId = $envVars['GOOGLE_CLIENT_ID']
$remoteBrowserEndpoint = $envVars['PLAYWRIGHT_REMOTE_BROWSER_ENDPOINT']

# Warn if remote browser endpoint is not set
if (-not $remoteBrowserEndpoint) {
    Write-Host "⚠️  WARNING: PLAYWRIGHT_REMOTE_BROWSER_ENDPOINT not set in .env" -ForegroundColor Yellow
    Write-Host "   Playwright will try to launch browsers locally (may fail on Cloud Run)" -ForegroundColor Yellow
    Write-Host "   See cloud/REMOTE_BROWSER_SETUP.md for setup instructions" -ForegroundColor Yellow
    Write-Host ""
}

$envString = "ANTHROPIC_API_KEY=$anthropicKey,OPENAI_API_KEY=$openaiKey,BOT_MODEL=$botModel,GOOGLE_CLIENT_ID=$googleClientId"

# Start deployment using optimized cloudbuild.yaml with caching
Write-Host "🚀 Starting deployment with optimized caching (this will take a few minutes)..." -ForegroundColor Cyan
Write-Host "   Using cloudbuild.yaml with layer caching enabled" -ForegroundColor Yellow
Write-Host ""

# Build substitutions string
$substitutions = "_GOOGLE_CLIENT_ID=$googleClientId,_ANTHROPIC_API_KEY=$anthropicKey,_OPENAI_API_KEY=$openaiKey,_BOT_MODEL=$botModel"
if ($remoteBrowserEndpoint) {
    $substitutions += ",_PLAYWRIGHT_REMOTE_BROWSER_ENDPOINT=$remoteBrowserEndpoint"
}

# Build and deploy using cloudbuild.yaml (with optimized caching)
$deployOutput = gcloud builds submit `
  --config cloudbuild.yaml `
  --substitutions=$substitutions `
  --region $REGION `
  2>&1

# Check if deployment started successfully
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Deployment failed. Check the errors above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Deployment output:" -ForegroundColor Yellow
    Write-Host $deployOutput
    Read-Host "Press Enter to exit"
    exit 1
}

# Extract build ID from output if available
$buildId = $null
if ($deployOutput -match "ID:\s*([a-f0-9-]+)") {
    $buildId = $matches[1]
    Write-Host ""
    Write-Host "📋 Build ID: $buildId" -ForegroundColor Cyan
}

# Monitor build status
Write-Host ""
Write-Host "⏳ Build started with optimized caching. Monitoring status..." -ForegroundColor Yellow
Write-Host "   Expected build time: ~3-5 minutes (with caching)" -ForegroundColor Yellow
Write-Host ""

$maxChecks = 15  # 15 checks * 30 seconds = 7.5 minutes max (should be much faster with caching)
$checkInterval = 30  # Check every 30 seconds

for ($i = 1; $i -le $maxChecks; $i++) {
    Start-Sleep -Seconds $checkInterval
    
    # Get latest build status
    if ($buildId) {
        $buildStatus = gcloud builds describe $buildId --region=$REGION --format="value(status)" 2>&1
    } else {
        $buildStatus = gcloud builds list --limit 1 --format="value(status)" --region=$REGION 2>&1
    }
    
    if ($LASTEXITCODE -eq 0 -and $buildStatus) {
        $elapsed = [math]::Round($i * $checkInterval / 60, 1)
        Write-Host "[$i/$maxChecks] Status: $buildStatus (${elapsed}m elapsed)" -ForegroundColor Cyan
        
        if ($buildStatus -eq "SUCCESS") {
            Write-Host ""
            Write-Host "✅ BUILD COMPLETE!" -ForegroundColor Green
            Write-Host ""
            break
        } elseif ($buildStatus -eq "FAILURE") {
            Write-Host ""
            Write-Host "❌ BUILD FAILED!" -ForegroundColor Red
            Write-Host ""
            Write-Host "View build logs:" -ForegroundColor Yellow
            if ($buildId) {
                Write-Host "   gcloud builds log $buildId --region=$REGION" -ForegroundColor White
            } else {
                Write-Host "   gcloud builds list --limit 1 --region=$REGION" -ForegroundColor White
            }
            Write-Host ""
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host "[$i/$maxChecks] Checking build status..." -ForegroundColor Gray
    }
}

if ($i -gt $maxChecks) {
    Write-Host ""
    Write-Host "⏱️  Build is taking longer than expected. Check status manually:" -ForegroundColor Yellow
    if ($buildId) {
        Write-Host "   gcloud builds describe $buildId --region=$REGION" -ForegroundColor White
    } else {
        Write-Host "   gcloud builds list --limit 1 --region=$REGION" -ForegroundColor White
    }
    Write-Host ""
}

# Get service URL
Write-Host "📍 Getting service URL..." -ForegroundColor Cyan
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)" 2>$null

if ($SERVICE_URL) {
    Write-Host ""
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Your app is live at:" -ForegroundColor Cyan
    Write-Host "   $SERVICE_URL" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Update Google OAuth settings:" -ForegroundColor Yellow
    Write-Host "   1. Go to https://console.cloud.google.com/apis/credentials" -ForegroundColor White
    Write-Host "   2. Edit your OAuth 2.0 Client ID" -ForegroundColor White
    Write-Host "   3. Add to Authorized JavaScript origins:" -ForegroundColor White
    Write-Host "      $SERVICE_URL" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🎉 Done! Your bot is ready to use!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "⚠️  Deployment may have completed, but could not retrieve service URL." -ForegroundColor Yellow
    Write-Host "   Check manually: gcloud run services list --region=$REGION" -ForegroundColor White
    Write-Host ""
}

Read-Host "Press Enter to exit"

