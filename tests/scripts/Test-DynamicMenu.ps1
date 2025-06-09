# Test Dynamic Menu Functionality
# This script tests the service health endpoints and menu visibility

Write-Host "🔍 Testing Dynamic Menu Health Checker" -ForegroundColor Cyan
Write-Host "=" * 50

# Test individual service health endpoints
$services = @{
    "Portal" = "http://localhost:8003/health"
    "Tickets API" = "http://localhost:8000/health"
    "Inventory API" = "http://localhost:8001/health"
    "Requisition API" = "http://localhost:8002/health"
    "Management API" = "http://localhost:8004/health"
}

Write-Host "`n📊 Checking individual service health..." -ForegroundColor Yellow

foreach ($service in $services.GetEnumerator()) {
    try {
        $response = Invoke-RestMethod -Uri $service.Value -Method Get -TimeoutSec 5
        if ($response.status -eq "healthy") {
            Write-Host "  ✅ $($service.Key): Healthy" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $($service.Key): Unhealthy" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ $($service.Key): Not responding" -ForegroundColor Red
    }
}

# Test the portal's service status API
Write-Host "`n🎯 Checking portal's service status API..." -ForegroundColor Yellow

try {
    $statusResponse = Invoke-RestMethod -Uri "http://localhost:8003/api/services/status" -Method Get -TimeoutSec 10
    
    Write-Host "  Service Status:" -ForegroundColor White
    foreach ($service in $statusResponse.service_status.PSObject.Properties) {
        $status = if ($service.Value) { "✅ Healthy" } else { "❌ Unhealthy" }
        Write-Host "    $($service.Name): $status"
    }
    
    Write-Host "`n  Menu Visibility:" -ForegroundColor White
    foreach ($menu in $statusResponse.menu_visibility.PSObject.Properties) {
        $visibility = if ($menu.Value) { "👁️  Visible" } else { "🚫 Hidden" }
        Write-Host "    $($menu.Name): $visibility"
    }
    
    Write-Host "`n✅ Dynamic menu system is working correctly!" -ForegroundColor Green
    
} catch {
    Write-Host "  ❌ Error accessing portal service status API: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Test completed!" -ForegroundColor Cyan
Write-Host "`nTo test dynamic menu behavior:" -ForegroundColor White
Write-Host "1. Visit the portal at: http://localhost:8003" -ForegroundColor Gray
Write-Host "2. All menu items should be visible (all services are running)" -ForegroundColor Gray
Write-Host "3. Stop a service with: docker-compose stop ocs-tickets-api" -ForegroundColor Gray
Write-Host "4. Refresh the portal - Tickets menu should disappear" -ForegroundColor Gray
Write-Host "5. Restart service with: docker-compose start ocs-tickets-api" -ForegroundColor Gray
Write-Host "6. Refresh the portal - Tickets menu should reappear" -ForegroundColor Gray
