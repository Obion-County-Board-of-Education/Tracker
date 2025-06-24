# Quick Requirements Check for OCS Portal Fresh Build

Write-Host "🔍 Quick Requirements Check" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

$issues = 0

# Check Docker
Write-Host "`nChecking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✅ Docker found: $($dockerVersion.Trim())" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker not found" -ForegroundColor Red
        $issues++
    }
} catch {
    Write-Host "❌ Docker not installed" -ForegroundColor Red
    $issues++
}

# Check Docker Compose
Write-Host "`nChecking Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host "✅ Docker Compose found: $($composeVersion.Trim())" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker Compose not found" -ForegroundColor Red
        $issues++
    }
} catch {
    Write-Host "❌ Docker Compose not installed" -ForegroundColor Red
    $issues++
}

# Check key files
Write-Host "`nChecking project files..." -ForegroundColor Yellow
$files = @(
    "docker-compose.yml",
    "ocs_shared_models/models.py",
    "ocs-portal-py/main.py"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
        $issues++
    }
}

# Check environment
Write-Host "`nChecking environment..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ .env file exists" -ForegroundColor Green
} elseif (Test-Path ".env.template") {
    Write-Host "⚠️  .env template exists but .env file missing" -ForegroundColor Yellow
    Write-Host "   Copy .env.template to .env and configure" -ForegroundColor Gray
} else {
    Write-Host "❌ No environment configuration found" -ForegroundColor Red
    $issues++
}

# Summary
Write-Host "`n🎯 Summary:" -ForegroundColor Cyan
if ($issues -eq 0) {
    Write-Host "✅ All requirements met! Ready to build." -ForegroundColor Green
    Write-Host "`nNext step: .\fresh_build_complete.ps1" -ForegroundColor Yellow
} else {
    Write-Host "❌ $issues issues found. Fix these first:" -ForegroundColor Red
    Write-Host "   1. Install Docker Desktop" -ForegroundColor White
    Write-Host "   2. Ensure all project files are present" -ForegroundColor White
    Write-Host "   3. Configure environment variables" -ForegroundColor White
}
