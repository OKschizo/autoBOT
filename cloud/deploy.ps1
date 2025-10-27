# Simple deployment script for Google Cloud Run

$env:PATH = "$env:USERPROFILE\google-cloud-sdk\bin;$env:PATH"

# Read .env file
$envVars = @{}
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $envVars[$matches[1]] = $matches[2]
    }
}

# Build env-vars string
$envString = "ANTHROPIC_API_KEY=$($envVars['ANTHROPIC_API_KEY']),OPENAI_API_KEY=$($envVars['OPENAI_API_KEY']),BOT_MODEL=$($envVars['BOT_MODEL']),GOOGLE_CLIENT_ID=$($envVars['GOOGLE_CLIENT_ID'])"

Write-Host "Deploying to Google Cloud Run..."
Write-Host "Environment variables loaded from .env"
Write-Host ""

# Deploy with simple Dockerfile
gcloud run deploy autofinance-bot `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars $envString `
  --memory 2Gi `
  --cpu 1 `
  --timeout 300 `
  --dockerfile=Dockerfile.simple

