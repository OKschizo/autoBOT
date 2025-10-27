# Monitor Cloud Run deployment status

$env:PATH = "$env:USERPROFILE\google-cloud-sdk\bin;$env:PATH"

Write-Host "Monitoring deployment..." -ForegroundColor Cyan
Write-Host ""

$maxAttempts = 20
$attempt = 0

while ($attempt -lt $maxAttempts) {
    $attempt++
    
    # Get service status
    $status = gcloud run services describe autofinance-bot --region us-central1 --format="value(status.conditions[0].status,status.conditions[0].message)" 2>$null
    
    if ($status -match "True") {
        Write-Host "✅ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
        Write-Host ""
        
        # Get the URL
        $url = gcloud run services describe autofinance-bot --region us-central1 --format="value(status.url)"
        Write-Host "🌐 Your bot is live at:" -ForegroundColor Green
        Write-Host "   $url" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "📝 Next steps:" -ForegroundColor Cyan
        Write-Host "   1. Add this URL to Google OAuth authorized origins"
        Write-Host "   2. Share with your team!"
        break
    }
    elseif ($status -match "False") {
        Write-Host "❌ DEPLOYMENT FAILED" -ForegroundColor Red
        Write-Host ""
        Write-Host "Error: $status" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Check logs with:" -ForegroundColor Cyan
        Write-Host "gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=autofinance-bot' --limit 50"
        break
    }
    else {
        Write-Host "[$attempt/$maxAttempts] Still deploying... ($status)" -ForegroundColor Yellow
        Start-Sleep -Seconds 15
    }
}

if ($attempt -eq $maxAttempts) {
    Write-Host "⏱️ Deployment taking longer than expected" -ForegroundColor Yellow
    Write-Host "Check status manually with:" -ForegroundColor Cyan
    Write-Host "gcloud run services describe autofinance-bot --region us-central1"
}

