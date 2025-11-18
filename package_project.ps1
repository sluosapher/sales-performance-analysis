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
        if ($Overwrite) {
            Write-Host "Archive '$archivePath' already exists. Overwriting..." -ForegroundColor Yellow
            Remove-Item $archivePath -Force
        }
        else {
            throw "Archive '$archivePath' already exists. Rerun with -Overwrite to replace it."
        }
    }

    Write-Host "Collecting project files from '$root'..." -ForegroundColor Cyan

    $excludeDirs = @(
        ".venv",
        "input",
        "output",
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

            return $true
        } |
        Select-Object -ExpandProperty FullName

    if (-not $items -or $items.Count -eq 0) {
        throw "No files found to add to the archive."
    }

    Write-Host "Creating archive at '$archivePath'..." -ForegroundColor Cyan
    Compress-Archive -Path $items -DestinationPath $archivePath -Force

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

