# OCS User Import System Setup Script
# PowerShell script for Windows environment

Write-Host "🚀 OCS User Import System Setup" -ForegroundColor Green
Write-Host "=================================================="

# Function to check if running in PowerShell
function Test-PowerShell {
    return $PSVersionTable.PSVersion.Major -ge 5
}

# Function to check Docker
function Test-Docker {
    try {
        docker --version | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to check Python
function Test-Python {
    try {
        python --version | Out-Null
        return $true
    } catch {
        return $false
    }
}

Write-Host "`n🔍 Checking prerequisites..." -ForegroundColor Yellow

# Check PowerShell
if (Test-PowerShell) {
    Write-Host "✅ PowerShell $($PSVersionTable.PSVersion.Major).$($PSVersionTable.PSVersion.Minor) detected" -ForegroundColor Green
} else {
    Write-Host "❌ PowerShell 5.0+ required" -ForegroundColor Red
    exit 1
}

# Check Docker
if (Test-Docker) {
    Write-Host "✅ Docker is available" -ForegroundColor Green
} else {
    Write-Host "❌ Docker is not available - please install Docker Desktop" -ForegroundColor Red
    exit 1
}

# Check for docker-compose.yml
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ docker-compose.yml not found. Please run this script from the root Tracker directory" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites check passed" -ForegroundColor Green

# Step 1: Start OCS services
Write-Host "`n📦 Step 1: Starting OCS services..." -ForegroundColor Yellow
try {
    docker-compose up -d
    Write-Host "✅ Services started successfully" -ForegroundColor Green
    
    # Wait for services to be ready
    Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
} catch {
    Write-Host "❌ Failed to start services: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 2: Run database migration
Write-Host "`n🗄️ Step 2: Running database migration..." -ForegroundColor Yellow
try {
    docker-compose exec ocs-portal-py python migrate_user_tables.py
    Write-Host "✅ Database migration completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Database migration failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "📝 You may need to run the migration manually:" -ForegroundColor Yellow
    Write-Host "   docker-compose exec ocs-portal-py python migrate_user_tables.py" -ForegroundColor White
}

# Step 3: Check service health
Write-Host "`n🏥 Step 3: Checking service health..." -ForegroundColor Yellow

$services = @(
    @{Name="ocs-portal-py"; Url="http://localhost:8080/health"},
    @{Name="ocs-forms-api"; Url="http://localhost:8081/health"},
    @{Name="ocs-manage"; Url="http://localhost:8082/health"},
    @{Name="ocs-purchasing-api"; Url="http://localhost:8083/health"},
    @{Name="ocs-tickets-api"; Url="http://localhost:8084/health"}
)

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.Name) is healthy" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $($service.Name) returned status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($service.Name) is not responding" -ForegroundColor Red
    }
}

# Step 4: Test user management interface
Write-Host "`n🌐 Step 4: Testing user management interface..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/admin/users" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ User management interface is accessible" -ForegroundColor Green
    } else {
        Write-Host "⚠️ User management interface returned status $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ User management interface is not accessible" -ForegroundColor Red
}

# Step 5: Test user import endpoints
Write-Host "`n🔗 Step 5: Testing user import endpoints..." -ForegroundColor Yellow

$endpoints = @(
    @{Name="Import Stats"; Url="http://localhost:8080/api/user-import/stats"},
    @{Name="Department List"; Url="http://localhost:8080/api/user-import/departments"}
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint.Url -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($endpoint.Name) endpoint is working" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $($endpoint.Name) endpoint returned status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($endpoint.Name) endpoint is not accessible" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n📋 Setup Summary:" -ForegroundColor Green
Write-Host "   User Management: http://localhost:8080/admin/users" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8080/docs" -ForegroundColor White
Write-Host "   Import Stats: http://localhost:8080/api/user-import/stats" -ForegroundColor White

Write-Host "`n🎯 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Configure Azure AD credentials in environment variables" -ForegroundColor White
Write-Host "   2. Navigate to http://localhost:8080/admin/users" -ForegroundColor White
Write-Host "   3. Test the user import functionality" -ForegroundColor White
Write-Host "   4. Review imported users and departments" -ForegroundColor White

Write-Host "`n✅ Setup completed!" -ForegroundColor Green

# Optional: Open browser
$openBrowser = Read-Host "`nWould you like to open the user management interface in your browser? (y/n)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    try {
        Start-Process "http://localhost:8080/admin/users"
        Write-Host "🌐 Opening user management interface..." -ForegroundColor Green
    } catch {
        Write-Host "Could not open browser automatically. Please navigate to http://localhost:8080/admin/users" -ForegroundColor Yellow
    }
}
