# Install script for OCS Tracker dependencies
# This script installs all required Python packages for the OCS Tracker application

$ErrorActionPreference = "Stop"

Write-Host "OCS Tracker Dependency Installer" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Detect Python version
try {
    $pythonVersion = (python --version 2>&1).ToString()
    Write-Host "Detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10 or higher" -ForegroundColor Red
    exit 1
}

# Check for pip
try {
    $pipVersion = (pip --version 2>&1).ToString()
    Write-Host "Detected: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "pip is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Function to install requirements from a file
function Install-Requirements {
    param (
        [string]$requirementsPath
    )
    
    if (Test-Path $requirementsPath) {
        Write-Host "Installing dependencies from: $requirementsPath" -ForegroundColor Yellow
        pip install -r $requirementsPath
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error installing dependencies from $requirementsPath" -ForegroundColor Red
            exit $LASTEXITCODE
        }
    } else {
        Write-Host "Requirements file not found: $requirementsPath" -ForegroundColor Yellow
    }
}

# Install shared models in development mode
Write-Host "Installing shared models package..." -ForegroundColor Yellow
pip install -e "$PSScriptRoot\ocs_shared_models"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing shared models package" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Install main project requirements
Install-Requirements "$PSScriptRoot\requirements.txt"

# Install service-specific requirements
$services = @(
    "ocs-portal-py",
    "ocs-forms-api",
    "ocs-inventory-api",
    "ocs-manage",
    "ocs-purchasing-api",
    "ocs-tickets-api"
)

foreach ($service in $services) {
    Install-Requirements "$PSScriptRoot\$service\requirements.txt"
}

Write-Host "All dependencies installed successfully!" -ForegroundColor Green
Write-Host "You can now run the OCS Tracker application" -ForegroundColor Cyan
