# OCS Tracker Development Commands
# PowerShell script for common development tasks

param(
    [Parameter(Position=0)]
    [string]$Command
)

function Show-Help {
    Write-Host "🚀 OCS Tracker Development Helper" -ForegroundColor Green
    Write-Host "=================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  setup       - Set up development environment and database"
    Write-Host "  start       - Start the portal server"
    Write-Host "  test        - Run all tests"
    Write-Host "  reset-db    - Reset database with fresh sample data"
    Write-Host "  check       - Check portal health and connectivity"
    Write-Host "  docker-up   - Start Docker development environment"
    Write-Host "  docker-down - Stop Docker development environment"
    Write-Host "  clean       - Clean up temporary files"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\dev.ps1 setup"
    Write-Host "  .\dev.ps1 start"
    Write-Host "  .\dev.ps1 reset-db"
}

function Setup-Environment {
    Write-Host "🔧 Setting up development environment..." -ForegroundColor Blue
    python setup_dev_environment.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Environment setup complete!" -ForegroundColor Green
    } else {
        Write-Host "❌ Environment setup failed!" -ForegroundColor Red
    }
}

function Start-Portal {
    Write-Host "🚀 Starting OCS Portal..." -ForegroundColor Blue
    Set-Location "ocs-portal-py"
    python main.py
    Set-Location ".."
}

function Run-Tests {
    Write-Host "🧪 Running tests..." -ForegroundColor Blue
    python run_all_tests.py
}

function Reset-Database {
    Write-Host "🗃️ Resetting database with sample data..." -ForegroundColor Blue
    python setup_dev_data.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database reset complete!" -ForegroundColor Green
    } else {
        Write-Host "❌ Database reset failed!" -ForegroundColor Red
    }
}

function Check-Health {
    Write-Host "🏥 Checking portal health..." -ForegroundColor Blue
    python test_portal_startup.py
}

function Docker-Up {
    Write-Host "🐳 Starting Docker development environment..." -ForegroundColor Blue
    docker-compose -f docker-compose.dev.yml up -d
}

function Docker-Down {
    Write-Host "🐳 Stopping Docker development environment..." -ForegroundColor Blue
    docker-compose -f docker-compose.dev.yml down
}

function Clean-Files {
    Write-Host "🧹 Cleaning temporary files..." -ForegroundColor Blue
    Remove-Item -Path "*.pyc" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "*.log" -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Cleanup complete!" -ForegroundColor Green
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "setup" { Setup-Environment }
    "start" { Start-Portal }
    "test" { Run-Tests }
    "reset-db" { Reset-Database }
    "check" { Check-Health }
    "docker-up" { Docker-Up }
    "docker-down" { Docker-Down }
    "clean" { Clean-Files }
    default { Show-Help }
}
