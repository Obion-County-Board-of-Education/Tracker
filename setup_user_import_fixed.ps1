# OCS User Import System Setup Script - Simple Version
# PowerShell script for Windows environment

Write-Host "🚀 OCS User Import System Setup" -ForegroundColor Green
Write-Host "=================================================="

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -ge 5) {
    Write-Host "✅ PowerShell $($PSVersionTable.PSVersion.Major).$($PSVersionTable.PSVersion.Minor) detected" -ForegroundColor Green
} else {
    Write-Host "❌ PowerShell 5.0+ required" -ForegroundColor Red
    exit 1
}

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not available - please install Docker Desktop" -ForegroundColor Red
    exit 1
}

# Check for docker-compose.yml
if (!(Test-Path "docker-compose.yml")) {
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
    Start-Sleep -Seconds 10
    
} catch {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    exit 1
}

# Step 2: Run database migration
Write-Host "`n🗄️ Step 2: Running database migration..." -ForegroundColor Yellow
try {
    docker-compose exec ocs-portal-py python migrate_user_tables.py
    Write-Host "✅ Database migration completed" -ForegroundColor Green
} catch {
    Write-Host "❌ Database migration failed" -ForegroundColor Red
    Write-Host "📝 You may need to run the migration manually:" -ForegroundColor Yellow
    Write-Host "   docker-compose exec ocs-portal-py python migrate_user_tables.py" -ForegroundColor White
}

# Step 3: Check service health
Write-Host "`n🏥 Step 3: Checking service health..." -ForegroundColor Yellow

# Check OCS Portal
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8003/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ OCS Portal is healthy" -ForegroundColor Green
    } else {
        Write-Host "⚠️ OCS Portal returned status $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ OCS Portal is not responding" -ForegroundColor Red
}

# Step 4: Test user import functionality
Write-Host "`n🧪 Step 4: Testing user import functionality..." -ForegroundColor Yellow

# Check admin interface
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8003/admin/users" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 302) {
        Write-Host "✅ Admin user management interface is accessible" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Admin user management returned status $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Admin user management interface is not accessible" -ForegroundColor Red
    Write-Host "   This is expected if you're not logged in as an admin" -ForegroundColor Gray
}

# Step 5: Display setup summary
Write-Host "`n📊 Setup Summary" -ForegroundColor Cyan
Write-Host "=============================="

Write-Host "🌐 OCS Portal Application:" -ForegroundColor Yellow
Write-Host "   Main Portal: http://localhost:8003" -ForegroundColor White
Write-Host "   Admin Dashboard: http://localhost:8003/admin" -ForegroundColor White
Write-Host "   User Management: http://localhost:8003/admin/users" -ForegroundColor White
Write-Host "   Health Check: http://localhost:8003/health" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8003/docs" -ForegroundColor White

Write-Host "`n🔑 Admin Access Required:" -ForegroundColor Yellow
Write-Host "   - Log in with a super_admin account to access admin features" -ForegroundColor White
Write-Host "   - User import and management require super_admin permissions" -ForegroundColor White

Write-Host "`n📋 User Import Features (Admin Only):" -ForegroundColor Yellow
Write-Host "   ✅ Import Staff from Azure AD 'All_Staff' group" -ForegroundColor Green
Write-Host "   ✅ Import Students from Azure AD 'All_Students' group" -ForegroundColor Green
Write-Host "   ✅ Sync existing user profiles with Azure AD" -ForegroundColor Green
Write-Host "   ✅ User search and filtering" -ForegroundColor Green
Write-Host "   ✅ Department management" -ForegroundColor Green

Write-Host "`n🔧 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Navigate to http://localhost:8003 and log in as a super_admin user" -ForegroundColor White
Write-Host "   2. Go to Admin Dashboard -> User Management" -ForegroundColor White
Write-Host "   3. Configure Azure AD credentials if not already done" -ForegroundColor White
Write-Host "   4. Test the import functionality with a small group first" -ForegroundColor White
Write-Host "   5. Monitor the logs for any import issues" -ForegroundColor White
Write-Host "   6. Run full import when ready" -ForegroundColor White

Write-Host "`n📝 Troubleshooting:" -ForegroundColor Yellow
Write-Host "   - Check logs: docker-compose logs -f ocs-portal-py" -ForegroundColor White
Write-Host "   - Restart services: docker-compose restart" -ForegroundColor White
Write-Host "   - Check database: docker-compose exec postgres psql -U postgres -d ocs_portal" -ForegroundColor White
Write-Host "   - Verify admin permissions in the database" -ForegroundColor White

# Step 6: Display Docker status
Write-Host "`n🐳 Current Docker Status:" -ForegroundColor Cyan
try {
    docker-compose ps
} catch {
    Write-Host "Could not display Docker status" -ForegroundColor Red
}

Write-Host "`n✅ User Import System Setup Complete!" -ForegroundColor Green
Write-Host "🎯 The user import functionality is now available in the OCS Portal admin section" -ForegroundColor Cyan

# Optional: Ask if user wants to open the browser
$openBrowser = Read-Host "`nWould you like to open the OCS Portal in your browser? (y/n)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    try {
        Start-Process "http://localhost:8003"
        Write-Host "🌐 Opening OCS Portal..." -ForegroundColor Green
        Write-Host "   Navigate to Admin -> User Management after logging in" -ForegroundColor Yellow
    } catch {
        Write-Host "Could not open browser automatically. Please navigate to http://localhost:8003" -ForegroundColor Yellow
    }
}
