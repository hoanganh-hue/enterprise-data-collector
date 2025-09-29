# Enterprise Data Collector v2.0 - Build Script (PowerShell)
# Author: MiniMax Agent
# This script builds the complete installer package on Windows

param(
    [switch]$Clean = $false,
    [switch]$Test = $false
)

# Configuration
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$InstallerDir = Join-Path $ProjectRoot "installer"
$DistDir = Join-Path $ProjectRoot "dist"
$OutputDir = Join-Path $InstallerDir "output"

Write-Host "================================================" -ForegroundColor Blue
Write-Host "  Enterprise Data Collector v2.0 Build Script  " -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue

function Write-Step {
    param([string]$Message)
    Write-Host "`n🔧 $Message" -ForegroundColor Yellow
    Write-Host "----------------------------------------"
}

function Test-Command {
    param([string]$Command)
    return Get-Command $Command -ErrorAction SilentlyContinue
}

# Step 1: Environment Check
Write-Step "Kiểm tra môi trường"

Set-Location $ProjectRoot
Write-Host "✓ Project root: $ProjectRoot" -ForegroundColor Green
Write-Host "✓ Installer directory: $InstallerDir" -ForegroundColor Green

# Check Python
$pythonCmd = $null
if (Test-Command "python") {
    $pythonCmd = "python"
} elseif (Test-Command "py") {
    $pythonCmd = "py"
} else {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Python command: $pythonCmd" -ForegroundColor Green
& $pythonCmd --version

# Step 2: Install Dependencies
Write-Step "Cài đặt dependencies"

Write-Host "Installing PyInstaller..."
& $pythonCmd -m pip install --upgrade pip
& $pythonCmd -m pip install pyinstaller

Write-Host "Installing project dependencies..."
if (Test-Path "requirements.txt") {
    & $pythonCmd -m pip install -r requirements.txt
}

Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Step 3: Clean Previous Build
if ($Clean) {
    Write-Step "Dọn dẹp build cũ"
    
    if (Test-Path $DistDir) {
        Remove-Item $DistDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
    
    if (Test-Path $OutputDir) {
        Remove-Item $OutputDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    
    # Clean cache
    Get-ChildItem -Path . -Name "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force
    Get-ChildItem -Path . -Name "*.egg-info" -Recurse -Directory | Remove-Item -Recurse -Force
    if (Test-Path "build") {
        Remove-Item "build" -Recurse -Force
    }
    
    Write-Host "✓ Cleanup completed" -ForegroundColor Green
}

# Step 4: Build Executable
Write-Step "Build executable với PyInstaller"

$specFile = Join-Path $InstallerDir "build_exe.spec"
Write-Host "Running PyInstaller with spec file: $specFile"

& $pythonCmd -m PyInstaller $specFile --clean --noconfirm

$exePath = Join-Path $DistDir "EnterpriseDataCollector\EnterpriseDataCollector.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "❌ Build failed! Executable not found." -ForegroundColor Red
    exit 1
}

Write-Host "✓ Executable built successfully" -ForegroundColor Green
Write-Host "  Location: $(Join-Path $DistDir 'EnterpriseDataCollector\')" -ForegroundColor Gray

# Step 5: Test Executable
if ($Test) {
    Write-Step "Kiểm tra executable"
    
    $exeInfo = Get-Item $exePath
    Write-Host "✓ Executable file info:" -ForegroundColor Green
    Write-Host "  Size: $($exeInfo.Length) bytes"
    Write-Host "  Created: $($exeInfo.CreationTime)"
    
    if ($exeInfo.Length -gt 0) {
        Write-Host "✓ Executable file is valid" -ForegroundColor Green
    } else {
        Write-Host "❌ Executable file is empty or corrupted" -ForegroundColor Red
        exit 1
    }
}

# Step 6: Create Windows Installer
Write-Step "Tạo Windows Installer"

if (Test-Command "makensis") {
    Write-Host "NSIS found. Creating installer..."
    
    Set-Location $InstallerDir
    & makensis installer.nsi
    
    $installerPath = "EnterpriseDataCollector_v2.0_setup.exe"
    if (Test-Path $installerPath) {
        if (-not (Test-Path $OutputDir)) {
            New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
        }
        Move-Item $installerPath (Join-Path $OutputDir $installerPath) -Force
        Write-Host "✅ Installer created successfully!" -ForegroundColor Green
        Write-Host "  Location: $(Join-Path $OutputDir $installerPath)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Failed to create installer" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  NSIS not found. Creating installer script only." -ForegroundColor Yellow
    Write-Host "To create installer:"
    Write-Host "1. Install NSIS from https://nsis.sourceforge.io/"
    Write-Host "2. Add NSIS to PATH"
    Write-Host "3. Run: makensis installer.nsi"
}

# Step 7: Package Distribution
Write-Step "Đóng gói distribution"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Create ZIP archive instead of tar.gz for Windows
$distZip = Join-Path $OutputDir "EnterpriseDataCollector_v2.0_dist.zip"
if (Test-Path $distZip) {
    Remove-Item $distZip -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    (Join-Path $DistDir "EnterpriseDataCollector"),
    $distZip
)

Write-Host "✓ Distribution ZIP created: $distZip" -ForegroundColor Green

# Step 8: Build Summary
Write-Step "Tóm tắt kết quả build"

Write-Host "✅ BUILD COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Build Outputs:" -ForegroundColor Cyan
Write-Host "  • Executable: $(Join-Path $DistDir 'EnterpriseDataCollector\')"
Write-Host "  • Distribution ZIP: $distZip"

$installerExe = Join-Path $OutputDir "EnterpriseDataCollector_v2.0_setup.exe"
if (Test-Path $installerExe) {
    Write-Host "  • Windows Installer: $installerExe"
}

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Test the executable on target machines"
Write-Host "  2. Distribute the installer or portable ZIP"
Write-Host "  3. Verify installation process"
Write-Host ""
Write-Host "🎉 Enterprise Data Collector v2.0 is ready for deployment!" -ForegroundColor Green

# Create deployment info
$deploymentInfo = @"
Enterprise Data Collector v2.0 - Deployment Information
========================================================

Build Date: $(Get-Date)
Build Environment: $env:OS $env:PROCESSOR_ARCHITECTURE
Python Version: $(& $pythonCmd --version)
PowerShell Version: $($PSVersionTable.PSVersion)

Files Included:
- EnterpriseDataCollector.exe (Main executable)
- All Python dependencies bundled
- Required data files and configurations

Installation Requirements:
- Windows 10 or later
- No additional Python installation needed
- Internet connection for data collection

Distribution Files:
- EnterpriseDataCollector_v2.0_dist.zip (Portable version)
- EnterpriseDataCollector_v2.0_setup.exe (Installer - if created)

Support: support@minimax-agent.com
"@

$deploymentInfo | Out-File -FilePath (Join-Path $OutputDir "deployment_info.txt") -Encoding UTF8

Write-Host "📄 Deployment info saved: $(Join-Path $OutputDir 'deployment_info.txt')" -ForegroundColor Gray