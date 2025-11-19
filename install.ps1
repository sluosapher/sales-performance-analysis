[CmdletBinding()]
param ()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "== Sales Performance Analysis setup ==" -ForegroundColor Cyan

$root = $PSScriptRoot
if (-not $root) {
    $root = (Get-Location).Path
}

$errors = @()

function Add-InstallError {
    param (
        [string]$Message
    )
    $script:errors += $Message
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

try {
    Write-Host "1) Checking for 'uv' on PATH..." -ForegroundColor Cyan
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Add-InstallError "The 'uv' tool is not installed or not available on PATH. Install uv and re-run this script."
        throw "Missing uv"
    }

    Write-Host "2) Syncing Python environment with uv..." -ForegroundColor Cyan
    Push-Location $root
    try {
        uv sync
    }
    finally {
        Pop-Location
    }

    Write-Host "3) Ensuring input/output folders exist..." -ForegroundColor Cyan
    $inputDir = Join-Path $root "input"
    $outputDir = Join-Path $root "output"

    if (-not (Test-Path $inputDir)) {
        New-Item -ItemType Directory -Path $inputDir -Force | Out-Null
    }

    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }

    Write-Host "4) Running test with raw_data_251103.xlsx..." -ForegroundColor Cyan
    $testInput = Join-Path $inputDir "raw_data_251103.xlsx"
    if (-not (Test-Path $testInput)) {
        Add-InstallError "Test input file 'raw_data_251103.xlsx' not found in $inputDir."
        throw "Missing test data"
    }

    $testOutput = Join-Path $outputDir "test_output_251103.xlsx"
    if (Test-Path $testOutput) {
        Remove-Item $testOutput -Force
    }

    $testExitCode = 0
    Push-Location $root
    try {
        uv run python main.py --input $testInput --output $testOutput
        $testExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    if ($testExitCode -ne 0) {
        Add-InstallError "Test run with raw_data_251103.xlsx failed (exit code $testExitCode). See output above for details."
        throw "Test run failed"
    }

    if (-not (Test-Path $testOutput)) {
        Add-InstallError "Test output file was not created at '$testOutput'."
        throw "Missing test output"
    }

    Write-Host "5) Validating expected worksheets in test output..." -ForegroundColor Cyan
    $validationScript = @'
import sys
from openpyxl import load_workbook

path = sys.argv[1]
wb = load_workbook(path, read_only=True)
expected = [
    "Top 10 Sales by Geo",
    "Top 10 ThinkShield by Geo",
    "Top 10% All",
    "Top 10% Security",
]
missing = [name for name in expected if name not in wb.sheetnames]
if missing:
    raise SystemExit("Missing expected sheets: " + ", ".join(missing))
'@

    $validatorPath = Join-Path $outputDir "validate_output_tmp.py"
    Set-Content -Path $validatorPath -Value $validationScript -Encoding utf8

    $validationExitCode = 0
    Push-Location $root
    try {
        uv run python $validatorPath $testOutput
        $validationExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    Remove-Item $validatorPath -Force -ErrorAction SilentlyContinue

    if ($validationExitCode -ne 0) {
        Add-InstallError "Validation of test output workbook failed (exit code $validationExitCode). See Python output above for details."
        throw "Validation failed"
    }
}
catch {
    if (-not $errors) {
        $errors += $_.Exception.Message
    }

    Write-Host ""
    Write-Host "Installation FAILED." -ForegroundColor Red
    Write-Host "Details:" -ForegroundColor Red
    foreach ($msg in $errors) {
        Write-Host " - $msg" -ForegroundColor Red
    }

    exit 1
}

Write-Host ""
Write-Host "6) Creating desktop shortcut..." -ForegroundColor Cyan
try {
    $desktopPath = [Environment]::GetFolderPath('Desktop')
    if ($desktopPath -and (Test-Path $desktopPath)) {
        $shortcutPath = Join-Path $desktopPath "Sales Performance Analysis.lnk"
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = "uv"
        $shortcut.Arguments = "run python main.py --output report.xlsx"
        $shortcut.WorkingDirectory = $root
        $shortcut.WindowStyle = 1
        $shortcut.Save()
        Write-Host "Desktop shortcut created at '$shortcutPath'." -ForegroundColor Green
    }
    else {
        Write-Host "Could not determine Desktop folder; skipping shortcut creation." -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Failed to create desktop shortcut: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Installation and test completed successfully." -ForegroundColor Green
Write-Host "You can now run the program with:" -ForegroundColor Green
Write-Host "  uv run python main.py --input input\<your_input.xlsx> --output output\<your_output.xlsx>" -ForegroundColor Green

exit 0
