; NSIS Script for Enterprise Data Collector v2.0
; Author: MiniMax Agent
; This script creates a Windows installer for Enterprise Data Collector

;=================================
; General Settings
;=================================
!define APP_NAME "Enterprise Data Collector"
!define APP_VERSION "2.0"
!define APP_PUBLISHER "MiniMax Agent"
!define APP_URL "https://github.com/minimax-agent/enterprise-data-collector"
!define APP_DESCRIPTION "Thu thập dữ liệu doanh nghiệp từ nhiều nguồn"

!define APP_EXE_NAME "EnterpriseDataCollector.exe"
!define APP_DIR_NAME "EnterpriseDataCollector"
!define APP_UNINSTALLER "uninstall.exe"

;=================================
; Include Modern UI
;=================================
!include "MUI2.nsh"
!include "FileFunc.nsh"

;=================================
; General Configuration
;=================================
Name "${APP_NAME} ${APP_VERSION}"
OutFile "EnterpriseDataCollector_v${APP_VERSION}_setup.exe"
InstallDir "$PROGRAMFILES64\${APP_DIR_NAME}"
InstallDirRegKey HKLM "Software\${APP_DIR_NAME}" "InstallDir"
RequestExecutionLevel admin
ShowInstDetails show
ShowUnInstDetails show

;=================================
; Version Information
;=================================
VIProductVersion "${APP_VERSION}.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_DESCRIPTION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "Copyright © 2024 ${APP_PUBLISHER}"

;=================================
; Interface Settings
;=================================
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

;=================================
; Language & Pages
;=================================
!define MUI_LANGDLL_REGISTRY_ROOT "HKLM"
!define MUI_LANGDLL_REGISTRY_KEY "Software\${APP_DIR_NAME}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

; Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "resources\license.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Vietnamese"

;=================================
; Custom Language Strings
;=================================
LangString PAGE_TITLE ${LANG_ENGLISH} "Enterprise Data Collector Setup"
LangString PAGE_TITLE ${LANG_VIETNAMESE} "Cài đặt Enterprise Data Collector"

LangString PAGE_SUBTITLE ${LANG_ENGLISH} "Install Enterprise Data Collector v${APP_VERSION}"
LangString PAGE_SUBTITLE ${LANG_VIETNAMESE} "Cài đặt Enterprise Data Collector v${APP_VERSION}"

LangString WELCOME_TEXT ${LANG_ENGLISH} "This wizard will guide you through the installation of ${APP_NAME}.$\r$\n$\r$\nIt is recommended that you close all other applications before starting Setup."
LangString WELCOME_TEXT ${LANG_VIETNAMESE} "Trình hướng dẫn này sẽ giúp bạn cài đặt ${APP_NAME}.$\r$\n$\r$\nKhuyến nghị bạn nên đóng tất cả ứng dụng khác trước khi bắt đầu cài đặt."

;=================================
; Installer Sections
;=================================
Section "!Core Application" SecCore
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    
    ; Install main application executable (from PyInstaller --onefile)
    File "..\dist\EnterpriseDataCollector.exe"
    
    ; Create application data directories
    CreateDirectory "$APPDATA\${APP_DIR_NAME}"
    CreateDirectory "$APPDATA\${APP_DIR_NAME}\Database"
    CreateDirectory "$APPDATA\${APP_DIR_NAME}\Outputs"
    CreateDirectory "$APPDATA\${APP_DIR_NAME}\Logs"
    
    ; Install documentation and resources
    File "resources\README.txt"
    File "resources\license.txt"
    
    ; Write registry keys
    WriteRegStr HKLM "Software\${APP_DIR_NAME}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${APP_DIR_NAME}" "Version" "${APP_VERSION}"
    WriteRegStr HKLM "Software\${APP_DIR_NAME}" "Publisher" "${APP_PUBLISHER}"
    
    ; Write uninstall information
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}" "UninstallString" "$INSTDIR\${APP_UNINSTALLER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}" "HelpLink" "${APP_URL}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}" "NoRepair" 1
    
    ; Calculate and write install size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}" "EstimatedSize" "$0"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\${APP_UNINSTALLER}"
SectionEnd

Section "Desktop Shortcut" SecDesktop
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE_NAME}" "" "$INSTDIR\${APP_EXE_NAME}" 0
SectionEnd

Section "Start Menu Shortcut" SecStartMenu
    CreateDirectory "$SMPROGRAMS\${APP_DIR_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_DIR_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE_NAME}" "" "$INSTDIR\${APP_EXE_NAME}" 0
    CreateShortCut "$SMPROGRAMS\${APP_DIR_NAME}\Gỡ cài đặt.lnk" "$INSTDIR\${APP_UNINSTALLER}" "" "$INSTDIR\${APP_UNINSTALLER}" 0
    WriteINIStr "$SMPROGRAMS\${APP_DIR_NAME}\Website.url" "InternetShortcut" "URL" "${APP_URL}"
SectionEnd

;=================================
; Section Descriptions
;=================================
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Các file chính của ứng dụng (bắt buộc)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Tạo shortcut trên Desktop"
  !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Tạo shortcut trong Start Menu"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;=================================
; Installer Functions
;=================================
Function .onInit
    ; Check if application is already installed
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}" "UninstallString"
    StrCmp $0 "" done
    
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "${APP_NAME} đã được cài đặt trước đó. $\n$\nNhấn 'OK' để gỡ cài đặt phiên bản cũ và tiếp tục, hoặc 'Cancel' để hủy." \
        IDCANCEL cancel
    
    ; Uninstall previous version
    ExecWait '$0 /S _?=$INSTDIR'
    
cancel:
    Abort
    
done:
    ; Display language selection dialog
    !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

;=================================
; Uninstaller Section
;=================================
Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\${APP_EXE_NAME}"
    Delete "$INSTDIR\README.txt"
    Delete "$INSTDIR\license.txt"
    Delete "$INSTDIR\${APP_UNINSTALLER}"
    
    ; Remove directories
    RMDir "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_DIR_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_DIR_NAME}\Gỡ cài đặt.lnk"
    Delete "$SMPROGRAMS\${APP_DIR_NAME}\Website.url"
    RMDir "$SMPROGRAMS\${APP_DIR_NAME}"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}"
    DeleteRegKey HKLM "Software\${APP_DIR_NAME}"
    
    ; Note: User data in $APPDATA is preserved unless user specifically requests removal
    MessageBox MB_YESNO "Bạn có muốn xóa dữ liệu người dùng (Database, Outputs, Logs) không?" IDNO skip_userdata
    RMDir /r "$APPDATA\${APP_DIR_NAME}"
    
skip_userdata:
SectionEnd

Function un.onInit
    !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd