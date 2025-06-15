#!/usr/bin/env pwsh
# Fresh Setup Script for OCS Tracker
# This script ensures proper database initialization on fresh builds

param(
    [switch]$Clean = $false,
    [switch]$SkipBuild = $false
)

Write-Host "🚀 OCS Tracker Fresh Setup Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

if ($Clean) {
    Write-Host "🧹 Cleaning up existing containers and volumes..." -ForegroundColor Yellow
    docker compose down -v
    docker system prune -f
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}

Write-Host "🔧 Making initialization scripts executable..." -ForegroundColor Blue
if (Test-Path "init-db.sh") {
    # On Windows, we don't need to set executable permissions, but we verify the file exists
    Write-Host "✅ Database initialization script found" -ForegroundColor Green
} else {
    Write-Host "❌ Database initialization script not found!" -ForegroundColor Red
    exit 1
}

if ($SkipBuild) {
    Write-Host "⏭️ Skipping build step as requested" -ForegroundColor Yellow
    docker compose up -d
} else {
    Write-Host "🏗️ Building and starting all services..." -ForegroundColor Blue
    docker compose up -d --build --force-recreate
}

Write-Host "⏳ Waiting for database to be ready..." -ForegroundColor Blue
$maxAttempts = 30
$attempt = 0

do {
    $attempt++
    Start-Sleep -Seconds 2
    
    try {
        $healthStatus = docker inspect tracker-db-1 --format='{{.State.Health.Status}}' 2>$null
        if ($healthStatus -eq "healthy") {
            Write-Host "✅ Database is healthy!" -ForegroundColor Green
            break
        }
    } catch {
        # Container might not exist yet
    }
    
    Write-Host "⏳ Attempt $attempt/$maxAttempts - Database not ready yet..." -ForegroundColor Yellow
} while ($attempt -lt $maxAttempts)

if ($attempt -ge $maxAttempts) {
    Write-Host "❌ Database failed to become healthy within timeout" -ForegroundColor Red
    Write-Host "📋 Showing database logs:" -ForegroundColor Yellow
    docker logs tracker-db-1 --tail 20
    exit 1
}

Write-Host "🔍 Verifying all databases were created..." -ForegroundColor Blue
Start-Sleep -Seconds 3

$databases = @("ocs_tickets", "ocs_inventory", "ocs_purchasing", "ocs_portal", "ocs_manage", "ocs_forms")
$missingDatabases = @()

foreach ($db in $databases) {
    try {
        $result = docker exec tracker-db-1 psql -U ocs_user -d $db -c "\q" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Database '$db' is accessible" -ForegroundColor Green
        } else {
            $missingDatabases += $db
            Write-Host "❌ Database '$db' is not accessible" -ForegroundColor Red
        }
    } catch {
        $missingDatabases += $db
        Write-Host "❌ Database '$db' is not accessible" -ForegroundColor Red
    }
}

if ($missingDatabases.Count -eq 0) {
    Write-Host "🎉 SUCCESS: All databases created successfully!" -ForegroundColor Green
    Write-Host "🌐 Services should be available at:" -ForegroundColor Cyan
    Write-Host "   • Portal: http://localhost:8003" -ForegroundColor White
    Write-Host "   • Tickets API: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   • Inventory API: http://localhost:8001/docs" -ForegroundColor White
    Write-Host "   • Purchasing API: http://localhost:8002/docs" -ForegroundColor White
    Write-Host "   • Management API: http://localhost:8004/docs" -ForegroundColor White
    Write-Host "   • Forms API: http://localhost:8005/docs" -ForegroundColor White
} else {
    Write-Host "⚠️ Some databases are missing: $($missingDatabases -join ', ')" -ForegroundColor Red
    Write-Host "📋 Database initialization logs:" -ForegroundColor Yellow
    docker logs tracker-db-1 --tail 30
    
    Write-Host "🔧 Attempting to create missing databases manually..." -ForegroundColor Blue
    foreach ($db in $missingDatabases) {
        try {
            docker exec tracker-db-1 psql -U ocs_user -d postgres -c "CREATE DATABASE $db;"
            docker exec tracker-db-1 psql -U ocs_user -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $db TO ocs_user;"
            Write-Host "✅ Created database '$db'" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to create database '$db'" -ForegroundColor Red
        }
    }
}

Write-Host "📊 Container status:" -ForegroundColor Blue
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
