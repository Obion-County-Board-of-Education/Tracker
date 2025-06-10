# OCS Portal Test Suite Runner (PowerShell)
# =====================================
#
# This script provides a unified way to run all tests in the OCS Portal system.
# All testing scripts have been properly organized into the tests/ folder structure.
#
# Usage:
#     .\Run-AllTests.ps1 [-Category <category>] [-ShowOrganization]
#
# Test Categories:
#     - Unit: Run unit tests
#     - Portal: Run portal-specific tests  
#     - Api: Run API tests
#     - Integration: Run integration tests
#     - Csv: Run CSV import/export tests
#     - Utilities: Run utility verification scripts
#     - All: Run all tests (default)

param(
    [Parameter(Position=0)]
    [ValidateSet("Unit", "Portal", "Api", "Integration", "Csv", "Utilities", "All")]
    [string]$Category = "All",
    
    [switch]$ShowOrganization
)

# Test directory structure
$TestsDir = Join-Path $PSScriptRoot "tests"
$TestCategories = @{
    "Unit" = "tests\unit"
    "Portal" = "tests\portal"
    "Api" = "tests\api"
    "Integration" = "tests\integration"
    "Csv" = "tests\csv"
    "Utilities" = "tests\utilities"
}

function Run-PythonTests {
    param([string]$CategoryPath)
    
    $TestFiles = Get-ChildItem -Path $CategoryPath -Filter "test_*.py" -ErrorAction SilentlyContinue
    if (-not $TestFiles) {
        Write-Host "  No test files found in $CategoryPath" -ForegroundColor Yellow
        return $true
    }
    
    $Success = $true
    foreach ($TestFile in $TestFiles) {
        Write-Host "  Running $($TestFile.Name)..." -ForegroundColor Cyan
        try {
            $Result = Start-Process -FilePath "python" -ArgumentList $TestFile.FullName -Wait -PassThru -NoNewWindow -RedirectStandardError "error.txt" -RedirectStandardOutput "output.txt"
            if ($Result.ExitCode -eq 0) {
                Write-Host "    ✅ PASSED" -ForegroundColor Green
            } else {
                $ErrorContent = Get-Content "error.txt" -Raw -ErrorAction SilentlyContinue
                Write-Host "    ❌ FAILED: $ErrorContent" -ForegroundColor Red
                $Success = $false
            }
        } catch {
            Write-Host "    ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
            $Success = $false
        }
    }
    
    # Clean up temporary files
    Remove-Item "error.txt", "output.txt" -ErrorAction SilentlyContinue
    
    return $Success
}

function Run-VerificationScripts {
    param([string]$CategoryPath)
    
    $VerifyFiles = Get-ChildItem -Path $CategoryPath -Filter "verify_*.py" -ErrorAction SilentlyContinue
    if (-not $VerifyFiles) {
        return $true
    }
    
    $Success = $true
    foreach ($VerifyFile in $VerifyFiles) {
        Write-Host "  Running $($VerifyFile.Name)..." -ForegroundColor Cyan
        try {
            $Result = Start-Process -FilePath "python" -ArgumentList $VerifyFile.FullName -Wait -PassThru -NoNewWindow -RedirectStandardError "error.txt" -RedirectStandardOutput "output.txt"
            if ($Result.ExitCode -eq 0) {
                Write-Host "    ✅ VERIFIED" -ForegroundColor Green
            } else {
                $ErrorContent = Get-Content "error.txt" -Raw -ErrorAction SilentlyContinue
                Write-Host "    ❌ VERIFICATION FAILED: $ErrorContent" -ForegroundColor Red
                $Success = $false
            }
        } catch {
            Write-Host "    ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
            $Success = $false
        }
    }
    
    # Clean up temporary files
    Remove-Item "error.txt", "output.txt" -ErrorAction SilentlyContinue
    
    return $Success
}

function Run-CategoryTests {
    param([string]$Category)
    
    if (-not $TestCategories.ContainsKey($Category)) {
        Write-Host "❌ Unknown test category: $Category" -ForegroundColor Red
        return $false
    }
    
    $CategoryPath = $TestCategories[$Category]
    if (-not (Test-Path $CategoryPath)) {
        Write-Host "❌ Test directory not found: $CategoryPath" -ForegroundColor Red
        return $false
    }
    
    Write-Host "`n🧪 Running $($Category.ToUpper()) tests..." -ForegroundColor Magenta
    Write-Host ("=" * 50) -ForegroundColor Magenta
    
    $Success = $true
    
    # Run Python tests
    if (-not (Run-PythonTests -CategoryPath $CategoryPath)) {
        $Success = $false
    }
    
    # Run verification scripts
    if (-not (Run-VerificationScripts -CategoryPath $CategoryPath)) {
        $Success = $false
    }
    
    return $Success
}

function Show-TestOrganization {
    Write-Host "`n📁 Test Organization Summary" -ForegroundColor Magenta
    Write-Host ("=" * 50) -ForegroundColor Magenta
    
    foreach ($CategoryEntry in $TestCategories.GetEnumerator()) {
        $Category = $CategoryEntry.Key
        $Path = $CategoryEntry.Value
        
        if (Test-Path $Path) {
            $TestFiles = Get-ChildItem -Path $Path -Filter "*.py" -ErrorAction SilentlyContinue
            $Count = if ($TestFiles) { $TestFiles.Count } else { 0 }
            Write-Host "📁 $($Category.ToUpper()): $Count files" -ForegroundColor Cyan
        } else {
            Write-Host "📁 $($Category.ToUpper()): Directory not found" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n✅ All testing scripts are properly organized in the tests/ folder" -ForegroundColor Green
}

# Main execution
Write-Host "🚀 OCS Portal Test Suite Runner (PowerShell)" -ForegroundColor Green
Write-Host ("=" * 50) -ForegroundColor Green

if ($ShowOrganization) {
    Show-TestOrganization
    return
}

if ($Category -eq "All") {
    Write-Host "Running ALL test categories..." -ForegroundColor Yellow
    $OverallSuccess = $true
    
    foreach ($Cat in $TestCategories.Keys) {
        if (-not (Run-CategoryTests -Category $Cat)) {
            $OverallSuccess = $false
        }
    }
    
    if ($OverallSuccess) {
        Write-Host "`n🎉 ALL TESTS COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Some tests failed. Check output above." -ForegroundColor Red
        exit 1
    }
} else {
    $Success = Run-CategoryTests -Category $Category
    if (-not $Success) {
        exit 1
    }
}
