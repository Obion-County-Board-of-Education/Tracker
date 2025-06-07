# PowerShell script to test OCS Portal routes
Write-Host "Testing OCS Portal Routes..." -ForegroundColor Green
Write-Host "=" * 50

$baseUrl = "http://localhost:8003"
$routes = @(
    @{Path="/"; Name="Homepage"},
    @{Path="/test-routing"; Name="Test Route"},
    @{Path="/users"; Name="Users Redirect"},
    @{Path="/users/list"; Name="Users List"},
    @{Path="/buildings"; Name="Buildings Redirect"},
    @{Path="/buildings/list"; Name="Buildings List"}
)

foreach ($route in $routes) {
    Write-Host "`nTesting $($route.Name) ($($route.Path))..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "$baseUrl$($route.Path)" -TimeoutSec 10 -MaximumRedirection 0 -ErrorAction SilentlyContinue
        Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
        
        if ($response.StatusCode -eq 302) {
            $location = $response.Headers.Location
            Write-Host "  Redirect to: $location" -ForegroundColor Cyan
        }
        elseif ($response.StatusCode -eq 200) {
            $contentLength = $response.Content.Length
            Write-Host "  Response length: $contentLength characters" -ForegroundColor Green
            
            if ($route.Path -like "*users*" -and $response.Content -like "*User Management*") {
                Write-Host "  ✅ Users page loaded successfully" -ForegroundColor Green
            }
            elseif ($route.Path -like "*buildings*" -and $response.Content -like "*Buildings Management*") {
                Write-Host "  ✅ Buildings page loaded successfully" -ForegroundColor Green
            }
        }
    }
    catch {
        Write-Host "  ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "  Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        }
    }
}

Write-Host "`nTesting complete!" -ForegroundColor Green
