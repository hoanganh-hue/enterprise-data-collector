#!/bin/bash

# Enterprise Data Collector v2.0 - Mac Build Script
# Author: MiniMax Agent
# This script creates a portable version on Mac for later Windows packaging

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Enterprise Data Collector v2.0 - Mac Build   ${NC}"
echo -e "${BLUE}================================================${NC}"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This script is designed for macOS${NC}"
    exit 1
fi

PROJECT_ROOT="/workspace"
OUTPUT_DIR="$PROJECT_ROOT/mac_build_output"

echo -e "\n${YELLOW}🔧 Setting up Mac build environment${NC}"
echo "----------------------------------------"

cd "$PROJECT_ROOT"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}❌ Python 3 not found!${NC}"
    echo "Install with: brew install python"
    exit 1
fi

echo "✓ Python available: $($PYTHON_CMD --version)"

# Install dependencies
echo -e "\n${YELLOW}🔧 Installing dependencies${NC}"
echo "----------------------------------------"

$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install pyinstaller

if [ -f "requirements.txt" ]; then
    $PYTHON_CMD -m pip install -r requirements.txt
fi

echo "✓ Dependencies installed"

# Create Windows-compatible spec for later use
echo -e "\n${YELLOW}🔧 Creating Windows-compatible package${NC}"
echo "----------------------------------------"

# Clean previous builds
rm -rf build/ dist/

# Create a Windows-specific package structure
mkdir -p "$OUTPUT_DIR/windows_package"
mkdir -p "$OUTPUT_DIR/windows_package/src"

# Copy all source files
cp -r src/* "$OUTPUT_DIR/windows_package/src/"
cp main.py "$OUTPUT_DIR/windows_package/"
cp requirements.txt "$OUTPUT_DIR/windows_package/"
cp -r installer "$OUTPUT_DIR/windows_package/"

# Copy documentation
cp -r docs "$OUTPUT_DIR/windows_package/" 2>/dev/null || true
cp -r samples "$OUTPUT_DIR/windows_package/" 2>/dev/null || true

# Create Windows build instructions
cat > "$OUTPUT_DIR/windows_package/BUILD_ON_WINDOWS.md" << 'EOF'
# BUILD INSTRUCTIONS FOR WINDOWS

## Prerequisites
1. Install Python 3.8+ from python.org
2. Install NSIS from https://nsis.sourceforge.io/

## Build Steps
1. Open Command Prompt as Administrator
2. Navigate to this directory
3. Run: `installer\build_complete.bat`

## Expected Output
- `dist\EnterpriseDataCollector\EnterpriseDataCollector.exe`
- `installer\output\EnterpriseDataCollector_v2.0_setup.exe`

## Troubleshooting
- If PyInstaller fails: `pip install --upgrade pyinstaller`
- If NSIS fails: Add NSIS to PATH or reinstall
- If executable doesn't run: Check Windows Defender
EOF

# Create deployment package
echo -e "\n${YELLOW}🔧 Creating deployment package${NC}"
echo "----------------------------------------"

cd "$OUTPUT_DIR"

# Create ZIP for easy transfer to Windows
if command -v zip >/dev/null 2>&1; then
    zip -r "EnterpriseDataCollector_v2.0_source_for_windows.zip" windows_package/
    echo "✓ Windows deployment package created"
else
    tar -czf "EnterpriseDataCollector_v2.0_source_for_windows.tar.gz" windows_package/
    echo "✓ Windows deployment package created (tar.gz)"
fi

# Create Mac instructions
cat > "MAC_TO_WINDOWS_INSTRUCTIONS.md" << 'EOF'
# MAC TO WINDOWS BUILD INSTRUCTIONS

## What was created:
1. **windows_package/**: Complete source code ready for Windows build
2. **EnterpriseDataCollector_v2.0_source_for_windows.zip**: Transfer package

## Options to build Windows installer:

### Option 1: Use Windows Machine
1. Transfer ZIP file to Windows PC
2. Extract and run `installer\build_complete.bat`
3. Get `EnterpriseDataCollector_v2.0_setup.exe`

### Option 2: Use Windows VM on Mac
1. Install UTM or VirtualBox
2. Create Windows 11 VM
3. Transfer ZIP file to VM
4. Build as per Option 1

### Option 3: Use GitHub Actions
1. Push code to GitHub repository
2. GitHub automatically builds Windows installer
3. Download from Actions artifacts

### Option 4: Ask colleague with Windows PC
1. Send ZIP file to Windows user
2. They run build script
3. Get installer back via email/cloud

EOF

echo -e "\n${GREEN}✅ MAC BUILD COMPLETED!${NC}"
echo ""
echo "📦 Created files:"
echo "  • Windows source package: $OUTPUT_DIR/windows_package/"
echo "  • Transfer file: $OUTPUT_DIR/EnterpriseDataCollector_v2.0_source_for_windows.zip"
echo "  • Instructions: $OUTPUT_DIR/MAC_TO_WINDOWS_INSTRUCTIONS.md"
echo ""
echo "📋 Next steps:"
echo "  1. Choose one of the Windows build options in MAC_TO_WINDOWS_INSTRUCTIONS.md"
echo "  2. Transfer the ZIP file to Windows environment"
echo "  3. Run build script to get final installer"
echo ""
echo "🎉 Ready for Windows deployment!"