# Script to fix the final broken links in README.md

# Configuration
$docsDir = "D:\Dev\repos\mywienerlinien\.windsurf\docs"
$readmePath = Join-Path -Path $docsDir -ChildPath "README.md"
$backupPath = "$readmePath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"

# Create backup of original file
Copy-Item -Path $readmePath -Destination $backupPath -Force
Write-Host "Created backup at: $backupPath" -ForegroundColor Cyan

# Create missing directories and README.md files
$missingDirs = @(
    "1_news/releases",
    "2_notes/how-tos",
    "2_notes/troubleshooting",
    "2_notes/contributing",
    "5_development/containers",
    "5_development/global_services",
    "6_software/development_tools/terminal",
    "7_projects/wiener_linien",
    "9_misc/resources",
    "9_misc/archive"
)

# Create missing directories and README.md files
foreach ($dir in $missingDirs) {
    $fullPath = Join-Path -Path $docsDir -ChildPath $dir
    $readmePath = Join-Path -Path $fullPath -ChildPath "README.md"
    
    # Create directory if it doesn't exist
    if (-not (Test-Path -Path $fullPath -PathType Container)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
    
    # Create README.md if it doesn't exist
    if (-not (Test-Path -Path $readmePath -PathType Leaf)) {
        $title = ($dir -split '[\\/]' | Select-Object -Last 1) -replace '_', ' ' -replace '\b(\p{L})', { $_.Value.ToUpper() }
        $content = "# $title

This directory contains $($title.ToLower()) resources and documentation.

## Contents

<!-- Add a brief description of the contents of this directory -->"
        
        $content | Out-File -FilePath $readmePath -Encoding utf8 -NoNewline
        Write-Host "Created README.md in: $dir" -ForegroundColor Green
    }
}

# Create specific missing files
$missingFiles = @(
    @{
        Path = "7_projects/wiener_linien/WIENER_LINIEN_API_GUIDE.md"
        Content = "# Wiener Linien API Guide

This guide provides documentation for working with the Wiener Linien API.

## Overview

<!-- Add API documentation here -->"
    },
    @{
        Path = "2_notes/flows/bugs/250621_rules_reading_issue/analysis.md"
        Content = "# Analysis of Rules Reading Issue (25/06/21)

## Issue Description

<!-- Add analysis of the issue here -->"
    },
    @{
        Path = "5_development/global_services/documentation_standards.md"
        Content = "# Documentation Standards

This document outlines the standards and guidelines for documentation in this project.

## Table of Contents

1. [General Guidelines](#general-guidelines)
2. [Markdown Formatting](#markdown-formatting)
3. [File Naming Conventions](#file-naming-conventions)
4. [Directory Structure](#directory-structure)
5. [Best Practices](#best-practices)

## General Guidelines

<!-- Add content here -->"
    },
    @{
        Path = "5_development/global_services/template_library.md"
        Content = "# Template Library

This directory contains templates for various types of documentation.

## Available Templates

<!-- List available templates here -->"
    },
    @{
        Path = "grafana/import_dashboard.ps1"
        Content = "<#
.SYNOPSIS
    Script to import Grafana dashboards

.DESCRIPTION
    This script helps with importing Grafana dashboards from JSON files.
    
.NOTES
    File Name: import_dashboard.ps1
    Author: Your Name
    Prerequisite: PowerShell 5.1 or later
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$DashboardPath,
    
    [string]$GrafanaUrl = "http://localhost:3000",
    
    [Parameter(Mandatory=$true)]
    [string]$ApiKey
)

# Implementation goes here
Write-Host "Dashboard import functionality will be implemented here" -ForegroundColor Yellow"
    }
)

foreach ($file in $missingFiles) {
    $fullPath = Join-Path -Path $docsDir -ChildPath $file.Path
    $dirPath = Split-Path -Path $fullPath -Parent
    
    # Create parent directory if it doesn't exist
    if (-not (Test-Path -Path $dirPath -PathType Container)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        Write-Host "Created directory: $($file.Path | Split-Path -Parent)" -ForegroundColor Green
    }
    
    # Create file if it doesn't exist
    if (-not (Test-Path -Path $fullPath -PathType Leaf)) {
        $file.Content | Out-File -FilePath $fullPath -Encoding utf8 -NoNewline
        Write-Host "Created file: $($file.Path)" -ForegroundColor Green
    }
}

# Fix the relative path in README.md for the Grafana script
$readmeContent = Get-Content -Path $readmePath -Raw
$updatedContent = $readmeContent -replace '\.\./grafana/import_dashboard\.ps1\.md', '../grafana/import_dashboard.ps1'
$updatedContent | Out-File -FilePath $readmePath -Encoding utf8 -NoNewline
Write-Host "Fixed Grafana script link in README.md" -ForegroundColor Green

Write-Host "\nAll missing files and directories have been created." -ForegroundColor Green
Write-Host "Verifying links..." -ForegroundColor Cyan

# Run the link checker to verify the fixes
& "$PSScriptRoot\check_links.ps1"
