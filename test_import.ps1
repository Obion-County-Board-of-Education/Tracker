# Test CSV import using PowerShell
$uri = "http://localhost:8000/api/tickets/tech/import"
$csvPath = "manual_test_import.csv"

# Read the CSV file content
$csvContent = Get-Content -Path $csvPath -Raw

# Create boundary for multipart form data
$boundary = [System.Guid]::NewGuid().ToString()

# Create multipart form data body
$LF = "`r`n"
$bodyLines = @(
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"manual_test_import.csv`"",
    "Content-Type: text/csv",
    "",
    $csvContent,
    "--$boundary",
    "Content-Disposition: form-data; name=`"operation`"",
    "",
    "append",
    "--$boundary--"
) -join $LF

# Set headers
$headers = @{
    "Content-Type" = "multipart/form-data; boundary=$boundary"
}

# Make the request
try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -Body $bodyLines -Headers $headers
    Write-Host "Import successful:"
    $response | ConvertTo-Json
} catch {
    Write-Host "Import failed:"
    Write-Host $_.Exception.Message
    Write-Host $_.Exception.Response
}
