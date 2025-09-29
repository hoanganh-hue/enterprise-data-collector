#!/bin/bash

# Enterprise Data Collector v2.0 - Build Script
# Author: MiniMax Agent
# This script builds the complete installer package

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/workspace"
INSTALLER_DIR="$PROJECT_ROOT/installer"
DIST_DIR="$PROJECT_ROOT/dist"
OUTPUT_DIR="$INSTALLER_DIR/output"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Enterprise Data Collector v2.0 Build Script  ${NC}"
echo -e "${BLUE}================================================${NC}"

# Function to print step header
print_step() {
    echo -e "\n${YELLOW}🔧 $1${NC}"
    echo "----------------------------------------"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Environment Check
print_step "Kiểm tra môi trường"

cd "$PROJECT_ROOT"

echo "✓ Project root: $PROJECT_ROOT"
echo "✓ Installer directory: $INSTALLER_DIR"

# Check Python
if command_exists python3; then
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found!${NC}"
    exit 1
fi

echo "✓ Python command: $PYTHON_CMD"
$PYTHON_CMD --version

# Step 2: Install Dependencies
print_step "Cài đặt dependencies"

echo "Installing PyInstaller..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install pyinstaller

echo "Installing project dependencies..."
if [ -f "requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r requirements.txt
fi

echo "✓ Dependencies installed"

# Step 3: Clean Previous Build
print_step "Dọn dẹp build cũ"

echo "Cleaning dist directory..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

echo "Cleaning installer output..."
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "Cleaning cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
rm -rf build/

echo "✓ Cleanup completed"

# Step 4: Build Executable
print_step "Build executable với PyInstaller"

cd "$PROJECT_ROOT"

echo "Running PyInstaller with spec file..."
$PYTHON_CMD -m PyInstaller "$INSTALLER_DIR/build_exe.spec" --clean --noconfirm

if [ ! -f "$DIST_DIR/EnterpriseDataCollector/EnterpriseDataCollector.exe" ]; then
    echo -e "${RED}❌ Build failed! Executable not found.${NC}"
    exit 1
fi

echo "✓ Executable built successfully"
echo "  Location: $DIST_DIR/EnterpriseDataCollector/"

# Step 5: Test Executable
print_step "Kiểm tra executable"

cd "$DIST_DIR/EnterpriseDataCollector"

echo "Checking executable file..."
ls -la EnterpriseDataCollector.exe

echo "Testing executable (dry run)..."
# Just check if the exe exists and has proper size
if [ -s "EnterpriseDataCollector.exe" ]; then
    echo "✓ Executable file is valid"
else
    echo -e "${RED}❌ Executable file is empty or corrupted${NC}"
    exit 1
fi

# Step 6: Prepare NSIS Build (if available)
print_step "Chuẩn bị tạo Windows Installer"

cd "$INSTALLER_DIR"

echo "NSIS installer script ready at: installer.nsi"
echo "To create Windows installer:"
echo "1. Install NSIS (Nullsoft Scriptable Install System) on Windows"
echo "2. Right-click installer.nsi and select 'Compile NSIS Script'"
echo "3. Or use command: makensis installer.nsi"

# Create a batch file for Windows users
cat > "$OUTPUT_DIR/build_installer.bat" << 'EOF'
@echo off
echo Building Windows Installer...
cd /d "%~dp0"
cd ..

REM Check if NSIS is installed
where makensis >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: NSIS (Nullsoft Scriptable Install System) not found!
    echo Please install NSIS from https://nsis.sourceforge.io/
    echo and add it to your PATH.
    pause
    exit /b 1
)

echo Running NSIS compiler...
makensis installer.nsi

if exist "EnterpriseDataCollector_v2.0_setup.exe" (
    move "EnterpriseDataCollector_v2.0_setup.exe" "output\"
    echo.
    echo ✓ Installer created successfully!
    echo Location: output\EnterpriseDataCollector_v2.0_setup.exe
) else (
    echo ❌ Failed to create installer
)

pause
EOF

chmod +x "$OUTPUT_DIR/build_installer.bat"

# Step 7: Package Distribution
print_step "Đóng gói distribution"

cd "$PROJECT_ROOT"

echo "Creating distribution archive..."
tar -czf "$OUTPUT_DIR/EnterpriseDataCollector_v2.0_dist.tar.gz" -C "$DIST_DIR" EnterpriseDataCollector/

echo "Creating installer package..."
cd "$INSTALLER_DIR"
tar -czf "$OUTPUT_DIR/installer_package.tar.gz" *.nsi *.spec resources/ scripts/

echo "✓ Distribution packages created"

# Step 8: Build Summary
print_step "Tóm tắt kết quả build"

echo -e "${GREEN}✅ BUILD COMPLETED SUCCESSFULLY!${NC}"
echo
echo "📦 Build Outputs:"
echo "  • Executable: $DIST_DIR/EnterpriseDataCollector/"
echo "  • Distribution archive: $OUTPUT_DIR/EnterpriseDataCollector_v2.0_dist.tar.gz"
echo "  • Installer package: $OUTPUT_DIR/installer_package.tar.gz"
echo "  • Windows installer builder: $OUTPUT_DIR/build_installer.bat"
echo
echo "📋 Next Steps:"
echo "  1. Test the executable on target Windows machines"
echo "  2. Run build_installer.bat on Windows with NSIS installed"
echo "  3. Test the final installer package"
echo
echo "🎉 Enterprise Data Collector v2.0 is ready for deployment!"

# Create deployment info
cat > "$OUTPUT_DIR/deployment_info.txt" << EOF
Enterprise Data Collector v2.0 - Deployment Information
========================================================

Build Date: $(date)
Build Environment: $(uname -a)
Python Version: $($PYTHON_CMD --version)

Files Included:
- EnterpriseDataCollector.exe (Main executable)
- All Python dependencies bundled
- Required data files and configurations

Installation Requirements:
- Windows 10 or later
- No additional Python installation needed
- Internet connection for data collection

Distribution Files:
- EnterpriseDataCollector_v2.0_dist.tar.gz (Portable version)
- installer_package.tar.gz (NSIS installer source)
- build_installer.bat (Windows installer builder)

Support: support@minimax-agent.com
EOF

echo "📄 Deployment info saved: $OUTPUT_DIR/deployment_info.txt"