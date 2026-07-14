# Immich MCP Test Runner Script
# Comprehensive testing of all MCP tools with real photo data

param(
    [switch]$Quick,
    [switch]$Full,
    [switch]$MCPOnly,
    [switch]$FunctionsOnly,
    [switch]$Cleanup
)

Write-Host "Immich MCP Test Suite" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Check if Immich server is running
Write-Host "Checking Immich server connectivity..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:2283/api/server-info/ping" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "âœ“ Immich server is accessible" -ForegroundColor Green
} catch {
    Write-Host "âœ- Immich server not accessible at http://localhost:2283" -ForegroundColor Red
    Write-Host "Please ensure Immich is running before testing." -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "âœ- .env file not found" -ForegroundColor Red
    Write-Host "Please create .env file with IMMICH_API_KEY and IMMICH_URL" -ForegroundColor Yellow
    exit 1
}

# Ensure test photos exist
Write-Host "Preparing test photos..." -ForegroundColor Yellow
if (!(Test-Path "test_photos")) {
    New-Item -ItemType Directory -Path "test_photos" -Force | Out-Null
}

# Count existing photos
$photoCount = (Get-ChildItem "test_photos" -File | Measure-Object).Count
if ($photoCount -lt 5) {
    Write-Host "Downloading additional test photos..." -ForegroundColor Yellow
    & python create_test_images.py
}

$photoCount = (Get-ChildItem "test_photos" -File | Measure-Object).Count
Write-Host "âœ“ $photoCount test photos ready" -ForegroundColor Green

# Determine test type
$testArgs = @()

if ($Quick) {
    Write-Host "Running quick smoke test..." -ForegroundColor Cyan
    $testArgs += "--quick"
} elseif ($MCPOnly) {
    Write-Host "Running MCP protocol tests only..." -ForegroundColor Cyan
    $testArgs += "--mcp-only"
} elseif ($FunctionsOnly) {
    Write-Host "Running function tests only..." -ForegroundColor Cyan
    $testArgs += "--funcs-only"
} else {
    Write-Host "Running full test suite..." -ForegroundColor Cyan
    $testArgs += "--full"
}

if ($Cleanup) {
    $testArgs += "--cleanup"
    Write-Host "Cleanup enabled" -ForegroundColor Yellow
}

# Run the tests
Write-Host "Starting tests..." -ForegroundColor Green
Write-Host "Command: python run_all_tests.py $($testArgs -join ' ')" -ForegroundColor Gray

try {
    & python run_all_tests.py @testArgs
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "`nâœ“ Test suite completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`nâœ- Test suite completed with errors (exit code: $exitCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "`nâœ- Test execution failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTest results saved to latest_test_results.json" -ForegroundColor Cyan
Write-Host "Detailed logs available in test_report.json and mcp_test_report.json" -ForegroundColor Gray
