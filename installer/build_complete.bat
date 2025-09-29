@echo off
REM Enterprise Data Collector v2.0 - Complete Build Script for Windows
REM Author: MiniMax Agent
REM Run this script on Windows with Python and NSIS installed

echo ================================================
echo   Enterprise Data Collector v2.0 Build Script
echo ================================================

REM Set variables
set PROJECT_ROOT=%~dp0..
set INSTALLER_DIR=%PROJECT_ROOT%\installer
set DIST_DIR=%PROJECT_ROOT%\dist
set OUTPUT_DIR=%INSTALLER_DIR%\output

echo.
echo 🔧 Step 1: Environment Check
echo ----------------------------------------

cd /d "%PROJECT_ROOT%"
echo ✓ Project root: %PROJECT_ROOT%
echo ✓ Installer directory: %INSTALLER_DIR%

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.8+ first.
    pause
    exit /b 1
)
echo ✓ Python is available

python --version

echo.
echo 🔧 Step 2: Install Dependencies
echo ----------------------------------------

echo Installing PyInstaller and dependencies...
python -m pip install --upgrade pip
python -m pip install pyinstaller

if exist "requirements.txt" (
    echo Installing project dependencies...
    python -m pip install -r requirements.txt
)

echo ✓ Dependencies installed

echo.
echo 🔧 Step 3: Clean Previous Build
echo ----------------------------------------

if exist "%DIST_DIR%" (
    echo Removing old dist directory...
    rmdir /s /q "%DIST_DIR%"
)
mkdir "%DIST_DIR%" 2>nul

if exist "%OUTPUT_DIR%" (
    echo Removing old output directory...
    rmdir /s /q "%OUTPUT_DIR%"
)
mkdir "%OUTPUT_DIR%" 2>nul

echo Cleaning Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
if exist "build" rmdir /s /q "build" 2>nul

echo ✓ Cleanup completed

echo.
echo 🔧 Step 4: Build Executable with PyInstaller
echo ----------------------------------------

echo Running PyInstaller with spec file...
python -m PyInstaller "%INSTALLER_DIR%\build_exe.spec" --clean --noconfirm

if not exist "%DIST_DIR%\EnterpriseDataCollector\EnterpriseDataCollector.exe" (
    echo ❌ Build failed! Executable not found.
    pause
    exit /b 1
)

echo ✓ Executable built successfully
echo   Location: %DIST_DIR%\EnterpriseDataCollector\

echo.
echo 🔧 Step 5: Test Executable
echo ----------------------------------------

cd /d "%DIST_DIR%\EnterpriseDataCollector"
dir EnterpriseDataCollector.exe

echo Testing executable...
REM Quick file size check
for %%A in (EnterpriseDataCollector.exe) do (
    if %%~zA GTR 0 (
        echo ✓ Executable file is valid ^(%%~zA bytes^)
    ) else (
        echo ❌ Executable file is empty or corrupted
        pause
        exit /b 1
    )
)

echo.
echo 🔧 Step 6: Create Windows Installer with NSIS
echo ----------------------------------------

cd /d "%INSTALLER_DIR%"

REM Check if NSIS is installed
where makensis >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  NSIS not found!
    echo Please install NSIS from: https://nsis.sourceforge.io/
    echo Then add it to your PATH and run this script again.
    echo.
    echo For now, creating installer source package...
    goto :create_package
)

echo NSIS found! Creating installer...
makensis installer.nsi

if exist "EnterpriseDataCollector_v2.0_setup.exe" (
    move "EnterpriseDataCollector_v2.0_setup.exe" "%OUTPUT_DIR%\"
    echo ✅ Installer created successfully!
    echo   Location: %OUTPUT_DIR%\EnterpriseDataCollector_v2.0_setup.exe
) else (
    echo ❌ Failed to create installer
    goto :create_package
)

echo.
echo 🔧 Step 7: Package Distribution
echo ----------------------------------------

:create_package
cd /d "%PROJECT_ROOT%"

echo Creating portable distribution...
powershell -Command "Compress-Archive -Path '%DIST_DIR%\EnterpriseDataCollector\*' -DestinationPath '%OUTPUT_DIR%\EnterpriseDataCollector_v2.0_portable.zip' -Force"

echo Creating installer source package...
cd /d "%INSTALLER_DIR%"
powershell -Command "Compress-Archive -Path '*.nsi','*.spec','resources','scripts' -DestinationPath '%OUTPUT_DIR%\installer_source.zip' -Force"

echo ✓ Distribution packages created

echo.
echo 🔧 Step 8: Build Summary
echo ----------------------------------------

echo.
echo ✅ BUILD COMPLETED SUCCESSFULLY!
echo.
echo 📦 Build Outputs:
echo   • Executable directory: %DIST_DIR%\EnterpriseDataCollector\
echo   • Portable ZIP: %OUTPUT_DIR%\EnterpriseDataCollector_v2.0_portable.zip

if exist "%OUTPUT_DIR%\EnterpriseDataCollector_v2.0_setup.exe" (
    echo   • Windows Installer: %OUTPUT_DIR%\EnterpriseDataCollector_v2.0_setup.exe
)

echo   • Installer source: %OUTPUT_DIR%\installer_source.zip
echo.
echo 📋 Next Steps:
echo   1. Test the executable: %DIST_DIR%\EnterpriseDataCollector\EnterpriseDataCollector.exe

if exist "%OUTPUT_DIR%\EnterpriseDataCollector_v2.0_setup.exe" (
    echo   2. Test the installer: %OUTPUT_DIR%\EnterpriseDataCollector_v2.0_setup.exe
    echo   3. Distribute the installer to end users
) else (
    echo   2. Install NSIS and re-run this script to create installer
    echo   3. Or distribute the portable ZIP file
)

echo.
echo 🎉 Enterprise Data Collector v2.0 is ready for deployment!

REM Create deployment info
echo Enterprise Data Collector v2.0 - Deployment Information > "%OUTPUT_DIR%\deployment_info.txt"
echo ======================================================== >> "%OUTPUT_DIR%\deployment_info.txt"
echo. >> "%OUTPUT_DIR%\deployment_info.txt"
echo Build Date: %DATE% %TIME% >> "%OUTPUT_DIR%\deployment_info.txt"
echo Build Environment: Windows >> "%OUTPUT_DIR%\deployment_info.txt"
python --version >> "%OUTPUT_DIR%\deployment_info.txt" 2>&1
echo. >> "%OUTPUT_DIR%\deployment_info.txt"
echo Files Included: >> "%OUTPUT_DIR%\deployment_info.txt"
echo - EnterpriseDataCollector.exe (Main executable) >> "%OUTPUT_DIR%\deployment_info.txt"
echo - All Python dependencies bundled >> "%OUTPUT_DIR%\deployment_info.txt"
echo - Required data files and configurations >> "%OUTPUT_DIR%\deployment_info.txt"
echo. >> "%OUTPUT_DIR%\deployment_info.txt"
echo Installation Requirements: >> "%OUTPUT_DIR%\deployment_info.txt"
echo - Windows 10 or later >> "%OUTPUT_DIR%\deployment_info.txt"
echo - No additional Python installation needed >> "%OUTPUT_DIR%\deployment_info.txt"
echo - Internet connection for data collection >> "%OUTPUT_DIR%\deployment_info.txt"
echo. >> "%OUTPUT_DIR%\deployment_info.txt"
echo Support: support@minimax-agent.com >> "%OUTPUT_DIR%\deployment_info.txt"

echo.
echo 📄 Deployment info saved: %OUTPUT_DIR%\deployment_info.txt

pause