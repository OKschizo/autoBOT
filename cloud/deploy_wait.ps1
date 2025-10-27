# Wait for build to complete, then deploy

$env:PATH = "$env:USERPROFILE\google-cloud-sdk\bin;$env:PATH"

Write-Host "Waiting for container build to complete..."
Write-Host ""

# Get the latest build ID
$buildId = gcloud builds list --limit=1 --region=us-central1 --format="value(id)"

# Wait for build to complete
do {
    Start-Sleep -Seconds 10
    $status = gcloud builds describe $buildId --region=us-central1 --format="value(status)"
    Write-Host "Build status: $status"
} while ($status -eq "WORKING" -or $status -eq "QUEUED")

if ($status -eq "SUCCESS") {
    Write-Host ""
    Write-Host "✅ Build completed successfully!"
    Write-Host "🚀 Deploying to Cloud Run..."
    Write-Host ""

    # Read .env file
    $envVars = @{}
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $envVars[$matches[1]] = $matches[2]
        }
    }

    # Build env-vars string
    $envString = "ANTHROPIC_API_KEY=$($envVars['ANTHROPIC_API_KEY']),OPENAI_API_KEY=$($envVars['OPENAI_API_KEY']),BOT_MODEL=$($envVars['BOT_MODEL']),GOOGLE_CLIENT_ID=$($envVars['GOOGLE_CLIENT_ID'])"

    # Deploy
    gcloud run deploy autofinance-bot `
      --image gcr.io/autobot-475622/autofinance-bot `
      --platform managed `
      --region us-central1 `
      --allow-unauthenticated `
      --set-env-vars $envString `
      --memory 2Gi `
      --cpu 1 `
      --timeout 300

} else {
    Write-Host ""
    Write-Host "❌ Build failed with status: $status"
    Write-Host "Check the build logs:"
    Write-Host "gcloud builds log $buildId --region=us-central1"
}


