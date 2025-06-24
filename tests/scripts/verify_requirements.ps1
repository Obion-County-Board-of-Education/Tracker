# OCS Portal - Requirements Verification Script
# Checks if all requirements are met for a fresh build

Write-Host "🔍 OCS Portal - Requirements Verification" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegWrite-Host "`n📖 Documentation:" -ForegroundColor Yellow
Write-Host "   • Full requirements: BUILD_REQUIREMENTS.md" -ForegroundColor White
Write-Host "   • Environment template: .env.template" -ForegroundColor White
Write-Host "   • Build script: fresh_build_complete.ps1" -ForegroundColor WhitedColor Cyan

$allGood = $true
$warnings = @()
$errors = @()

# Function to add issues
function Add-Error($message) {
    $script:errors += $message
    $script:allGood = $false
    Write-Host "❌ $message" -ForegroundColor Red
}

function Add-Warning($message) {
    $script:warnings += $message
    Write-Host "⚠️  $message" -ForegroundColor Yellow
}

function Add-Success($message) {
    Write-Host "✅ $message" -ForegroundColor Green
}

# Check 1: Docker
Write-Host "📦 Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Add-Success "Docker found: $($dockerVersion.Trim())"
    } else {
        Add-Error "Docker not found in PATH"
    }
} catch {
    Add-Error "Docker not installed or not accessible"
}

# Check 2: Docker Compose
Write-Host "`n🔧 Checking Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Add-Success "Docker Compose found: $($composeVersion.Trim())"
    } else {
        Add-Error "Docker Compose not found"
    }
} catch {
    Add-Error "Docker Compose not installed"
}

# Check 3: Python
Write-Host "`n🐍 Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.1[1-9]") {
        Add-Success "Python found: $($pythonVersion.Trim())"
    } elseif ($pythonVersion -match "Python 3\.[0-9]+") {
        $version = $pythonVersion -replace "Python ", ""
        Add-Warning "Python $version found - Python 3.11+ recommended"
    } else {
        Add-Warning "Python not found - migration scripts may not work locally"
    }
} catch {
    Add-Warning "Python not found - migration scripts may not work locally"
}

# Check 4: Project Structure
Write-Host "`n📁 Checking Project Structure..." -ForegroundColor Yellow

$requiredFiles = @{
    "docker-compose.yml" = "Docker Compose configuration"
    "ocs_shared_models/models.py" = "Shared models"
    "ocs-portal-py/main.py" = "Portal main application"
    "ocs-portal-py/requirements.txt" = "Portal requirements"
    "ocs-portal-py/create_scheduler_tables.py" = "Scheduler migration script"
    "ocs-tickets-api/main.py" = "Tickets API"
    "ocs-purchasing-api/main.py" = "Purchasing API"
    "ocs-manage/main.py" = "Manage API"
    "ocs-forms-api/main.py" = "Forms API"
}

foreach ($file in $requiredFiles.Keys) {
    if (Test-Path $file) {
        Add-Success "$($requiredFiles[$file]): $file"
    } else {
        Add-Error "Missing $($requiredFiles[$file]): $file"
    }
}

# Check 5: Requirements Files Content
Write-Host "`n📋 Checking Requirements Files..." -ForegroundColor Yellow

# Check portal requirements for APScheduler
$portalReqs = "ocs-portal-py/requirements.txt"
if (Test-Path $portalReqs) {
    $content = Get-Content $portalReqs -Raw
    if ($content -match "APScheduler") {
        Add-Success "APScheduler found in portal requirements"
    } else {
        Add-Error "APScheduler missing from portal requirements"
    }
    
    if ($content -match "fastapi") {
        Add-Success "FastAPI found in portal requirements"
    } else {
        Add-Error "FastAPI missing from portal requirements"
    }
} else {
    Add-Error "Portal requirements.txt not found"
}

# Check shared models doesn't have APScheduler
$sharedReqs = "ocs_shared_models/requirements.txt"
if (Test-Path $sharedReqs) {
    $content = Get-Content $sharedReqs -Raw
    if ($content -notmatch "APScheduler") {
        Add-Success "Shared models correctly excludes APScheduler"
    } else {
        Add-Warning "APScheduler found in shared models - should be portal-specific only"
    }
}

# Check 6: Environment Configuration
Write-Host "`n🔐 Checking Environment Configuration..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Add-Success "Environment file exists: .env"
    
    $envContent = Get-Content ".env" -Raw
    $requiredVars = @("AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID", "JWT_SECRET")
    
    foreach ($var in $requiredVars) {
        if ($envContent -match "$var=.+") {
            Add-Success "$var is configured"
        } elseif ($envContent -match "$var=") {
            Add-Warning "$var is present but appears empty"
        } else {
            Add-Warning "$var is missing from .env file"
        }
    }
} else {
    if (Test-Path ".env.template") {
        Add-Warning "No .env file found, but template exists"
        Add-Warning "Copy .env.template to .env and configure values"
    } else {
        Add-Error "No .env file or template found"
    }
}

# Check 7: Docker Files
Write-Host "`n🐳 Checking Docker Files..." -ForegroundColor Yellow

$dockerFiles = @(
    "ocs-portal-py/Dockerfile",
    "ocs-tickets-api/Dockerfile", 
    "ocs-purchasing-api/Dockerfile",
    "ocs-manage/Dockerfile",
    "ocs-forms-api/Dockerfile"
)

foreach ($dockerfile in $dockerFiles) {
    if (Test-Path $dockerfile) {
        Add-Success "Dockerfile exists: $dockerfile"
    } else {
        Add-Error "Missing Dockerfile: $dockerfile"
    }
}

# Check 8: Database Init Script
Write-Host "`n🗄️  Checking Database Configuration..." -ForegroundColor Yellow

if (Test-Path "init-databases.sql") {
    Add-Success "Database initialization script found"
    
    $initContent = Get-Content "init-databases.sql" -Raw
    $databases = @("ocs_portal", "ocs_tickets", "ocs_purchasing", "ocs_manage", "ocs_forms")
    
    foreach ($db in $databases) {
        if ($initContent -match "CREATE DATABASE $db") {
            Add-Success "Database creation found: $db"
        } else {
            Add-Warning "Database creation missing: $db"
        }
    }
} else {
    Add-Error "Database initialization script not found: init-databases.sql"
}

# Check 9: Scheduler Files
Write-Host "`n⏰ Checking Scheduler Files..." -ForegroundColor Yellow

$schedulerFiles = @(
    "ocs-portal-py/scheduler_models.py",
    "ocs-portal-py/scheduler_service.py", 
    "ocs-portal-py/scheduler_routes.py",
    "ocs-portal-py/create_scheduler_tables.py"
)

foreach ($file in $schedulerFiles) {
    if (Test-Path $file) {
        Add-Success "Scheduler file exists: $file"
    } else {
        Add-Warning "Scheduler file missing: $file (may be optional)"
    }
}

# Summary
Write-Host "`n🎯 Verification Summary" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

if ($allGood -and $warnings.Count -eq 0) {
    Write-Host "✅ All requirements met! Ready for fresh build." -ForegroundColor Green
} elseif ($allGood) {
    Write-Host "✅ Core requirements met, but there are warnings." -ForegroundColor Yellow
    Write-Host "   You can proceed but should address warnings for optimal experience." -ForegroundColor Yellow
} else {
    Write-Host "❌ Missing critical requirements. Cannot proceed with build." -ForegroundColor Red
}

if ($errors.Count -gt 0) {
    Write-Host "`n🚨 Critical Issues ($($errors.Count)):" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "   • $error" -ForegroundColor Red
    }
}

if ($warnings.Count -gt 0) {
    Write-Host "`n⚠️  Warnings ($($warnings.Count)):" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "   • $warning" -ForegroundColor Yellow
    }
}

Write-Host "`n📚 Next Steps:" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "   1. Run: .\fresh_build_complete.ps1" -ForegroundColor White
    Write-Host "   2. Configure .env file with your Azure AD credentials" -ForegroundColor White
    Write-Host "   3. Test the system at http://localhost:8003" -ForegroundColor White
} else {
    Write-Host "   1. Install missing prerequisites (Docker, Docker Compose)" -ForegroundColor White
    Write-Host "   2. Fix missing files and configuration" -ForegroundColor White
    Write-Host "   3. Run this verification script again" -ForegroundColor White
    Write-Host "   4. Then run: .\fresh_build_complete.ps1" -ForegroundColor White
}

Write-Host "`n📖 Documentation:" -ForegroundColor Yellow
Write-Host "   • Full requirements: BUILD_REQUIREMENTS.md" -ForegroundColor White
Write-Host "   • Environment template: .env.template" -ForegroundColor White
Write-Host "   • Build script: fresh_build_complete.ps1" -ForegroundColor White
