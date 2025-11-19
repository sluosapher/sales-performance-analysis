[CmdletBinding()]
param(
    [string]$ArchiveName = "sales-performance-analysis.zip",
    [switch]$Overwrite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "== Packaging Sales Performance Analysis project ==" -ForegroundColor Cyan

$root = $PSScriptRoot
if (-not $root) {
    $root = (Get-Location).Path
}

try {
    if (-not $ArchiveName) {
        throw "ArchiveName cannot be empty."
    }

    if ([System.IO.Path]::GetExtension($ArchiveName) -eq "") {
        $ArchiveName = "$ArchiveName.zip"
    }

    $archivePath = if ([System.IO.Path]::IsPathRooted($ArchiveName)) {
        $ArchiveName
    }
    else {
        Join-Path $root $ArchiveName
    }

    if (Test-Path $archivePath) {
        Write-Host "Archive '$archivePath' already exists. Overwriting..." -ForegroundColor Yellow
        Remove-Item $archivePath -Force
    }

    Write-Host "Collecting project files from '$root'..." -ForegroundColor Cyan

    $inputDir = Join-Path $root "input"
    $outputDir = Join-Path $root "output"

    if (-not (Test-Path $inputDir)) {
        New-Item -ItemType Directory -Path $inputDir -Force | Out-Null
    }

    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }

    # Ensure the packaged output folder has no user data.
    Get-ChildItem -LiteralPath $outputDir -Force -Recurse -ErrorAction SilentlyContinue |
        Remove-Item -Force -Recurse -ErrorAction SilentlyContinue

    # Add tiny placeholder files so that empty input/output folders are preserved in the archive.
    $inputPlaceholder = Join-Path $inputDir ".keep"
    if (-not (Test-Path $inputPlaceholder)) {
        New-Item -ItemType File -Path $inputPlaceholder -Force | Out-Null
    }

    $outputPlaceholder = Join-Path $outputDir ".keep"
    if (-not (Test-Path $outputPlaceholder)) {
        New-Item -ItemType File -Path $outputPlaceholder -Force | Out-Null
    }

    # Copy root-level raw_data_*.xlsx into the input folder so that
    # packaged consumers find them under input\ by default.
    $rootRawData = Get-ChildItem -LiteralPath $root -Filter "raw_data_*.xlsx" -File -ErrorAction SilentlyContinue
    foreach ($file in $rootRawData) {
        $dest = Join-Path $inputDir $file.Name
        if (-not (Test-Path $dest)) {
            Copy-Item -Path $file.FullName -Destination $dest -Force
        }
    }

    $excludeDirs = @(
        ".venv",
        ".git",
        "__pycache__",
        ".pytest_cache"
    )

    $items = Get-ChildItem -LiteralPath $root -Recurse -Force |
        Where-Object {
            if ($_.PSIsContainer) {
                return $false
            }

            foreach ($ex in $excludeDirs) {
                if ($_.FullName -like "*\$ex*") {
                    return $false
                }
            }

            # Exclude root-level raw_data_*.xlsx; those are copied into input\.
            if (($_.DirectoryName -eq $root) -and ($_.Name -like "raw_data_*.xlsx")) {
                return $false
            }

            return $true
        } |
        Select-Object -ExpandProperty FullName

    # Also include the input and output directories in the archive.
    $items += $inputDir
    $items += $outputDir

    if (-not $items -or $items.Count -eq 0) {
        throw "No files found to add to the archive."
    }

    Write-Host "Creating archive at '$archivePath'..." -ForegroundColor Cyan
    Compress-Archive -Path $items -DestinationPath $archivePath -Force

    # Clean up placeholder files in the working copy (they remain inside the archive).
    Remove-Item $inputPlaceholder -Force -ErrorAction SilentlyContinue
    Remove-Item $outputPlaceholder -Force -ErrorAction SilentlyContinue

    Write-Host "Archive created successfully." -ForegroundColor Green
    Write-Host "You can move '$archivePath' to a new folder and extract it," `
        "then run '.\install.ps1' there to set up the environment." -ForegroundColor Green
}
catch {
    Write-Host "Failed to create archive:" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

exit 0
