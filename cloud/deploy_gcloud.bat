@echo off
REM Deploy Auto Finance Bot to Google Cloud Run

echo.
echo 🚀 Deploying Auto Finance Bot to Google Cloud Run
echo ==================================================
echo.

REM Check if gcloud is installed
where gcloud >nul 2>&1
if errorlevel 1 (
    echo ❌ gcloud CLI not found. Please install it:
    echo    https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

REM Get project ID
for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i
if "%PROJECT_ID%"=="" (
    echo ❌ No Google Cloud project set. Run:
    echo    gcloud config set project YOUR_PROJECT_ID
    pause
    exit /b 1
)

echo 📍 Project: %PROJECT_ID%
echo.

REM Check if .env exists
if not exist .env (
    echo ❌ .env file not found. Please create it with:
    echo    GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
    echo    ANTHROPIC_API_KEY=sk-ant-...
    echo    OPENAI_API_KEY=sk-proj-...
    echo    BOT_MODEL=claude-sonnet-4-20250514
    pause
    exit /b 1
)

REM Load environment variables
for /f "usebackq tokens=*" %%a in (.env) do (
    set "%%a"
)

REM Check if GOOGLE_CLIENT_ID is in frontend/app.js
findstr /C:"PASTE_YOUR_ACTUAL_CLIENT_ID_HERE" frontend\app.js >nul
if not errorlevel 1 (
    echo ❌ Please update frontend\app.js line 3 with your actual Google Client ID
    echo    Open cloud\frontend\app.js and replace:
    echo    'PASTE_YOUR_ACTUAL_CLIENT_ID_HERE'
    echo    with:
    echo    '%GOOGLE_CLIENT_ID%'
    pause
    exit /b 1
)

echo ✅ Environment variables loaded
echo.

REM Service settings
set SERVICE_NAME=autofinance-bot
set REGION=us-central1

echo 🏗️  Building and deploying to Cloud Run...
echo    Service: %SERVICE_NAME%
echo    Region: %REGION%
echo    Using E2_HIGHCPU_8 machine for faster builds (8x faster)
echo.

REM Verify frontend files exist
if not exist "frontend\index.html" (
    echo ❌ ERROR: frontend\index.html not found!
    echo    Make sure you're running this from the cloud\ directory
    pause
    exit /b 1
)

echo ✅ Frontend files verified
echo.

REM Deploy to Cloud Run with faster build machine
REM The cloudbuild.yaml will be used automatically if present
gcloud run deploy %SERVICE_NAME% ^
  --source . ^
  --platform managed ^
  --region %REGION% ^
  --allow-unauthenticated ^
  --set-env-vars "ANTHROPIC_API_KEY=%ANTHROPIC_API_KEY%,OPENAI_API_KEY=%OPENAI_API_KEY%,BOT_MODEL=%BOT_MODEL%,GOOGLE_CLIENT_ID=%GOOGLE_CLIENT_ID%" ^
  --memory 2Gi ^
  --cpu 1 ^
  --timeout 300 ^
  --max-instances 10

if errorlevel 1 (
    echo.
    echo ❌ Deployment failed. Check the errors above.
    pause
    exit /b 1
)

echo.
echo ✅ Deployment successful!
echo.
echo 📍 Getting service URL...
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region=%REGION% --format="value(status.url)"') do set SERVICE_URL=%%i
echo    %SERVICE_URL%
echo.
echo ⚠️  IMPORTANT: Update Google OAuth settings:
echo    1. Go to https://console.cloud.google.com/apis/credentials
echo    2. Edit your OAuth 2.0 Client ID
echo    3. Add to Authorized JavaScript origins:
echo       %SERVICE_URL%
echo.
echo 🎉 Done! Your bot is ready to use!
echo.
pause

