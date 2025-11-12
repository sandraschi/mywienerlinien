#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automated repository backup using Windows native compression
    
.DESCRIPTION
    Creates a compressed ZIP backup of the repository and saves to:
    1. Desktop\repo backup\
    2. N:\backup\dev\repos\
    
    Excludes:
    - .venv/ (virtual environments)
    - __pycache__/ (Python cache)
    - .ruff_cache/, .mypy_cache/, .pytest_cache/
    - node_modules/ (if any)
    - dist/, build/ (build artifacts)
    - VirtualBox files (*.vdi, *.vmdk, *.vbox)
    - Test artifacts (MagicMock/, sandboxes/, quarantine/)
    - Logs (*.log)
    
.PARAMETER IncludeBuild
    Include dist/ and build/ folders (default: false)
.PARAMETER BackupTargets
    Optional list of destination directories. Defaults to Desktop, N: drive, and OneDrive paths.
.PARAMETER AdditionalExclusions
    Optional additional wildcard patterns to exclude from the backup.
.PARAMETER FullHistory
    Include the `.git` directory so the backup can be restored as a full repository clone. Default: false.
.PARAMETER ShowHelp
    Display usage information and exit.
.PARAMETER BackupData
    Include large GTFS/data artifacts (archives, SQLite dumps, generated markdown). Default skips them.
    
.EXAMPLE
    .\scripts\backup-repo.ps1
    # Creates backup in Desktop\repo backup and N:\backup\dev\repos
    
.EXAMPLE
    .\scripts\backup-repo.ps1 -IncludeBuild
    # Creates backup including build artifacts
#>

param(
    [string]$SourcePath,
    [switch]$IncludeBuild = $false,
    [string[]]$BackupTargets,
    [string[]]$AdditionalExclusions,
    [switch]$BackupData = $false,
    [switch]$FullHistory = $false,
    [switch]$ShowHelp = $false
)

if ($ShowHelp) {
    Write-Host @"
Repository Backup Script
Usage:
  pwsh -File scripts\backup\backup-repo.ps1 [options]

Options:
  -SourcePath <path>         Root directory to back up (default: current directory).
  -IncludeBuild              Include dist/ and build/ artifacts.
  -BackupTargets <paths[]>   Override default destinations (Desktop, N:, OneDrive).
  -AdditionalExclusions <patterns[]>  Extra wildcard exclusions.
  -BackupData                Include large GTFS/data artifacts (archives, SQLite, generated markdown).
  -FullHistory               Include .git history for full repository restoration.
  -ShowHelp                  Display this help text.
"@
    exit 0
}

function Convert-ToAbsolutePath {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $null
    }
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $PathValue))
}

Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║       📦 Repository Backup (Windows Native ZIP) 📦      ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════════════╝`n" -ForegroundColor Magenta

# Resolve source path
if ($SourcePath) {
    $sourceDirectory = Convert-ToAbsolutePath $SourcePath
} else {
    $sourceDirectory = (Get-Location).Path
}

if (-not (Test-Path $sourceDirectory)) {
    Write-Host "❌ Error: Source path not found: $sourceDirectory" -ForegroundColor Red
    exit 1
}

# Sanity check: prevent running directly on root drives
$rootPath = [System.IO.Path]::GetPathRoot($sourceDirectory)
if ($rootPath -and [System.IO.Path]::GetFullPath($sourceDirectory).TrimEnd('\') -eq $rootPath.TrimEnd('\')) {
    Write-Host "❌ Refusing to back up root drive: $sourceDirectory" -ForegroundColor Red
    exit 1
}

# Check repo markers
$gitFolder = Join-Path $sourceDirectory ".git"
if (-not (Test-Path $gitFolder)) {
    Write-Host "❌ Error: Source path must be a git repository (.git folder not found)." -ForegroundColor Red
    exit 1
}

$repoInfo = Get-Item $sourceDirectory

# Get repo name and timestamp
$repoName = $repoInfo.Name
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupName = "${repoName}_backup_${timestamp}.zip"

# Determine backup targets
$desktopRoot = Join-Path ([Environment]::GetFolderPath("Desktop")) "repo backup"
$nDriveRoot = "N:\backup\dev\repos2"
$oneDriveRoot = $null
if ($env:OneDrive) {
    $oneDriveRoot = Join-Path $env:OneDrive "repo-backups"
}

$defaultTargets = @(
    [pscustomobject]@{ Label = "Desktop\repo backup"; Root = $desktopRoot },
    [pscustomobject]@{ Label = "N:\backup\dev\repos2"; Root = $nDriveRoot }
)
if ($oneDriveRoot) {
    $defaultTargets += [pscustomobject]@{ Label = "OneDrive\repo-backups"; Root = $oneDriveRoot }
}

$targetList = @()
if ($BackupTargets -and $BackupTargets.Count -gt 0) {
    foreach ($targetPath in $BackupTargets) {
        $absolute = Convert-ToAbsolutePath $targetPath
        if ($absolute) {
            $targetList += [pscustomobject]@{ Label = $targetPath; Root = $absolute }
        } else {
            Write-Host "⚠️  Skipping invalid target: $targetPath" -ForegroundColor Yellow
        }
    }
} else {
    foreach ($entry in $defaultTargets) {
        $absolute = Convert-ToAbsolutePath $entry.Root
        if ($absolute) {
            $targetList += [pscustomobject]@{ Label = $entry.Label; Root = $absolute }
        }
    }
}

if (-not $targetList -or $targetList.Count -eq 0) {
    Write-Host "❌ No valid backup targets defined." -ForegroundColor Red
    exit 1
}

$targetDetails = @()
foreach ($target in $targetList) {
    $rootPath = $target.Root
    $repoTargetDir = Join-Path $rootPath $repoName

    if (-not (Test-Path $rootPath)) {
        New-Item -ItemType Directory -Path $rootPath -Force | Out-Null
        Write-Host "✅ Created target root: $rootPath" -ForegroundColor Green
    }

    if (-not (Test-Path $repoTargetDir)) {
        New-Item -ItemType Directory -Path $repoTargetDir -Force | Out-Null
        Write-Host "✅ Created: $repoTargetDir" -ForegroundColor Green
    }

    $backupPath = Join-Path $repoTargetDir $backupName
    $targetDetails += [pscustomobject]@{
        Label = $target.Label
        Root = $rootPath
        RepoDir = $repoTargetDir
        BackupFile = $backupPath
    }
}

$repoRoot = $repoInfo.FullName

Write-Host "📋 Backup Configuration:" -ForegroundColor Cyan
Write-Host "  Repository:    $repoName" -ForegroundColor White
Write-Host "  Source path:   $repoRoot" -ForegroundColor White
Write-Host "  Timestamp:     $timestamp" -ForegroundColor White
Write-Host "  Include build: $(if($IncludeBuild){'Yes'}else{'No'})" -ForegroundColor White
Write-Host "  Full history:  $(if($FullHistory){'Yes'}else{'No'})" -ForegroundColor White
Write-Host "  Method:        .NET ZIP API (folder structure preserved)" -ForegroundColor Green
Write-Host "  Destinations:" -ForegroundColor Cyan
foreach ($detail in $targetDetails) {
    Write-Host "    - $($detail.Label): $($detail.BackupFile)" -ForegroundColor White
}
Write-Host ""

# Define exclusions
$exclusions = @(
    ".venv",
    "venv",
    "env",
    ".env",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "htmlcov",
    "node_modules",
    # ".git",  # INCLUDE .git - contains unpushed commits, local branches, history
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    "Thumbs.db",
    ".windsurf",
    ".cursor",
    "*.log",
    ".vbox",
    "*.vdi",
    "*.vmdk",
    "*.vhd",
    "*.vbox",
    "*.vbox-prev",
    "MagicMock",
    "sandboxes",
    "quarantine",
    "analysis",
    "backups",
    "*.dxt"
)

# Large test files that should be excluded (can be regenerated)
$excludeLargeTestFiles = @(
    "samples/metadata.db",
    "samples/test_library.db",
    "test_data/*.db"
)

# Data-heavy artifacts (GTFS archives, SQLite, generated markdown)
$dataExclusions = @(
    "gtfs_data",
    "gtfs_data\\*",
    "scripts\\gtfs_data*",
    "scripts\\gtfs_to_markdown.log",
    "scripts\\gtfs_processor.log",
    "scripts\\gtfs_data_backup_*",
    "scripts\\gtfs_data\\*",
    "scripts\\gtfs_data_backup_*\\*",
    "backup",
    "backup\\*",
    "data\\*routes.md",
    "gtfs_output.log",
    "*.sqlite",
    "*.zip"
)

# Combine exclusions
$exclusions += $excludeLargeTestFiles
if (-not $BackupData) {
    $exclusions += $dataExclusions
} else {
    Write-Host "💾 Including GTFS/data artifacts (--BackupData enabled)" -ForegroundColor Cyan
}

if (-not $FullHistory) {
    $exclusions += ".git"
} else {
    Write-Host "📚 Including .git history (--FullHistory enabled)" -ForegroundColor Cyan
}

if (-not $IncludeBuild) {
    $exclusions += @("dist", "build", "*.whl", "*.tar.gz")
}

# Normalize exclusions to work with wildcard matching
$normalizedExclusions = New-Object System.Collections.Generic.List[string]
function Add-NormalizedExclusion {
    param([string]$Pattern)
    if ([string]::IsNullOrWhiteSpace($Pattern)) { return }
    if ($Pattern -notmatch '[\*\?]') {
        $script:normalizedExclusions.Add("*$Pattern*")
    } else {
        $script:normalizedExclusions.Add($Pattern)
    }
}

foreach ($excl in $exclusions) {
    Add-NormalizedExclusion -Pattern $excl
}

if ($AdditionalExclusions) {
    foreach ($extra in $AdditionalExclusions) {
        Add-NormalizedExclusion -Pattern $extra
    }
}

$wildcardPatterns = $normalizedExclusions | ForEach-Object {
    [System.Management.Automation.WildcardPattern]::new($_, [System.Management.Automation.WildcardOptions]::IgnoreCase)
}

Write-Host "🚫 Excluding:" -ForegroundColor Yellow
foreach ($excl in $normalizedExclusions) {
    Write-Host "  - $excl" -ForegroundColor Gray
}
Write-Host ""

# Calculate sizes
Write-Host "📊 Analyzing repository size..." -ForegroundColor Cyan

$allFiles = Get-ChildItem -Path $sourceDirectory -Recurse -File -ErrorAction SilentlyContinue
$totalSize = ($allFiles | Measure-Object -Property Length -Sum).Sum / 1MB

# Filter files to backup
$backupFiles = $allFiles | Where-Object {
    $file = $_
    $shouldExclude = $false
    
    if ($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        return $false
    }
    
    foreach ($pattern in $wildcardPatterns) {
        if ($pattern.IsMatch($file.FullName)) {
            $shouldExclude = $true
            break
        }
    }
    
    -not $shouldExclude
}

$backupSize = ($backupFiles | Measure-Object -Property Length -Sum).Sum / 1MB
$excludedSize = $totalSize - $backupSize

Write-Host "  Total size:    $([math]::Round($totalSize, 2)) MB" -ForegroundColor White
Write-Host "  Excluded:      $([math]::Round($excludedSize, 2)) MB" -ForegroundColor Red
Write-Host "  Backup size:   $([math]::Round($backupSize, 2)) MB" -ForegroundColor Green
Write-Host "  Reduction:     $([math]::Round(($excludedSize / $totalSize) * 100, 1))%`n" -ForegroundColor Cyan

# Create backup
Write-Host "🔄 Creating backups..." -ForegroundColor Cyan

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem

    foreach ($detail in $targetDetails) {
        Write-Host "  → $($detail.Label)..." -ForegroundColor Gray
        if (Test-Path $detail.BackupFile) {
            Remove-Item $detail.BackupFile -Force
        }

        $zipArchive = [System.IO.Compression.ZipFile]::Open($detail.BackupFile, [System.IO.Compression.ZipArchiveMode]::Create)

        foreach ($file in $backupFiles) {
            $relativePath = $file.FullName.Substring($repoRoot.Length + 1)
            $zipPath = $relativePath -replace '\\', '/'
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zipArchive, $file.FullName, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
        }

        $zipArchive.Dispose()
        Write-Host "  ✅ $($detail.Label) backup complete (folder structure preserved)" -ForegroundColor Green
    }

    Write-Host "`n✅ Backups created successfully with folder structure!`n" -ForegroundColor Green

} catch {
    Write-Host "❌ Error creating backup: $_" -ForegroundColor Red
    exit 1
}

$primaryBackup = $targetDetails[0].BackupFile
if (Test-Path $primaryBackup) {
    $finalSize = (Get-Item $primaryBackup).Length / 1MB
    $compressionRatio = if ($backupSize -gt 0) { ($finalSize / $backupSize) * 100 } else { 0 }

    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║              📦 Backup Complete! 📦                     ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Backup Statistics:" -ForegroundColor Cyan
    Write-Host "  File:           $backupName" -ForegroundColor White
    foreach ($detail in $targetDetails) {
        Write-Host "  Location:       $($detail.BackupFile)" -ForegroundColor White
    }
    Write-Host "  Size:           $([math]::Round($finalSize, 2)) MB" -ForegroundColor Cyan
    Write-Host "  Original:       $([math]::Round($backupSize, 2)) MB" -ForegroundColor Gray
    Write-Host "  Compression:    $([math]::Round($compressionRatio, 1))%" -ForegroundColor Green
    Write-Host "  Space saved:    $([math]::Round($totalSize - $finalSize, 2)) MB" -ForegroundColor Green
    Write-Host "  Method:         .NET ZIP API (folder structure preserved)" -ForegroundColor Green
    Write-Host ""

    Write-Host "💡 To restore:" -ForegroundColor Cyan
    Write-Host "  Expand-Archive -Path `"$primaryBackup`" -DestinationPath `"destination-folder`"" -ForegroundColor Gray
    Write-Host ""

} else {
    Write-Host "❌ Error: Primary backup file not created" -ForegroundColor Red
    foreach ($detail in $targetDetails) {
        Write-Host "  $($detail.Label): $(Test-Path $detail.BackupFile)" -ForegroundColor Gray
    }
    exit 1
}

Write-Host "✅ Done!`n" -ForegroundColor Green
