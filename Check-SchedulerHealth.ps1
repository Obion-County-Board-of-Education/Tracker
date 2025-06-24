# Check-SchedulerHealth.ps1
Write-Host " Checking OCS Portal Scheduler Health..." -ForegroundColor Cyan

# 1. Check if portal is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8003/health" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host " Portal service is running" -ForegroundColor Green
    }
} catch {
    Write-Host " Portal service not responding" -ForegroundColor Red
    exit 1
}

# 2. Check scheduler logs
Write-Host "`n Recent scheduler activity:" -ForegroundColor Yellow
docker-compose logs --tail=20 ocs-portal-py | Select-String -Pattern "scheduler|import|job"

# 3. Check database tables
Write-Host "`n Scheduler database status:" -ForegroundColor Yellow
try {
    $dbResult = docker-compose exec db psql -U ocs_user -d ocs_portal -t -c "SELECT COUNT(*) FROM scheduled_tasks;"
    Write-Host "   Scheduled tasks in database: $($dbResult.Trim())" -ForegroundColor White
} catch {
    Write-Host "    Could not check database" -ForegroundColor Red
}

Write-Host "`n Scheduler health check complete!" -ForegroundColor Green
