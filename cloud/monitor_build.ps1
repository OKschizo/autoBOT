# Monitor Google Cloud Build status
# Usage: .\monitor_build.ps1 [region] [max_checks]

param(
    [string]$Region = "us-central1",
    [int]$MaxChecks = 20,
    [int]$CheckInterval = 30
)

Write-Host ""
Write-Host "⏳ Monitoring Cloud Build status..." -ForegroundColor Yellow
Write-Host "   Region: $Region" -ForegroundColor White
Write-Host "   Check interval: $CheckInterval seconds" -ForegroundColor White
Write-Host "   Max checks: $MaxChecks ($([math]::Round($MaxChecks * $CheckInterval / 60, 1)) minutes)" -ForegroundColor White
Write-Host ""

# Get the latest build ID first
$buildId = gcloud builds list --limit 1 --region=$Region --format="value(id)" 2>$null

if (-not $buildId) {
    Write-Host "❌ No builds found. Make sure a build is in progress." -ForegroundColor Red
    Write-Host "   Start a build first, or check:" -ForegroundColor Yellow
    Write-Host "   gcloud builds list --region=$Region" -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "📍 Monitoring build: $buildId" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date

for ($i = 1; $i -le $MaxChecks; $i++) {
    # Get build status
    $buildInfo = gcloud builds describe $buildId --region=$Region --format="value(status,logUrl)" 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $buildInfo) {
        $status = ($buildInfo -split "`n")[0]
        $logUrl = ($buildInfo -split "`n")[1]
        
        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
        
        # Color code the status
        $statusColor = switch ($status) {
            "SUCCESS" { "Green" }
            "FAILURE" { "Red" }
            "CANCELLED" { "Yellow" }
            "WORKING" { "Cyan" }
            "QUEUED" { "Gray" }
            default { "White" }
        }
        
        Write-Host "[$i/$MaxChecks] Status: $status (${elapsed}m elapsed)" -ForegroundColor $statusColor
        
        # Check for completion
        if ($status -eq "SUCCESS") {
            Write-Host ""
            Write-Host "✅ BUILD COMPLETE!" -ForegroundColor Green
            Write-Host "   Build ID: $buildId" -ForegroundColor White
            if ($logUrl) {
                Write-Host "   Logs: $logUrl" -ForegroundColor Cyan
            }
            Write-Host ""
            Write-Host "Total build time: ${elapsed} minutes" -ForegroundColor Green
            Write-Host ""
            break
        } elseif ($status -eq "FAILURE" -or $status -eq "CANCELLED") {
            Write-Host ""
            Write-Host "❌ BUILD $status" -ForegroundColor Red
            Write-Host "   Build ID: $buildId" -ForegroundColor White
            if ($logUrl) {
                Write-Host "   Logs: $logUrl" -ForegroundColor Cyan
            }
            Write-Host ""
            Write-Host "View detailed logs:" -ForegroundColor Yellow
            Write-Host "   gcloud builds log $buildId --region=$Region" -ForegroundColor White
            Write-Host ""
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host "[$i/$MaxChecks] Checking build status..." -ForegroundColor Gray
    }
    
    # Don't sleep on the last iteration
    if ($i -lt $MaxChecks) {
        Start-Sleep -Seconds $CheckInterval
    }
}

if ($i -gt $MaxChecks) {
    Write-Host ""
    Write-Host "⏱️  Monitoring timeout reached. Build may still be in progress." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Check build status manually:" -ForegroundColor Yellow
    Write-Host "   gcloud builds describe $buildId --region=$Region" -ForegroundColor White
    Write-Host ""
    Write-Host "Or view all builds:" -ForegroundColor Yellow
    Write-Host "   gcloud builds list --region=$Region --limit 5" -ForegroundColor White
    Write-Host ""
}

Read-Host "Press Enter to exit"


