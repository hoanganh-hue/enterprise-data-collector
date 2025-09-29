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
; Welcome Page Configuration
;=================================
!define MUI_WELCOMEPAGE_TITLE "Chào mừng đến với ${APP_NAME} ${APP_VERSION}"
!define MUI_WELCOMEPAGE_TEXT "Trình hướng dẫn này sẽ cài đặt ${APP_NAME} trên máy tính của bạn.$\r$\n$\r$\n${APP_DESCRIPTION}$\r$\n$\r$\nNhấn Tiếp tục để bắt đầu cài đặt."

;=================================
; Directory Page Configuration
;=================================
!define MUI_DIRECTORYPAGE_TEXT_TOP "Chọn thư mục cài đặt ${APP_NAME}."
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Thư mục đích"

;=================================
; Install Files Page Configuration
;=================================
!define MUI_INSTFILESPAGE_FINISHHEADER_TEXT "Cài đặt hoàn thành"
!define MUI_INSTFILESPAGE_FINISHHEADER_SUBTEXT "${APP_NAME} đã được cài đặt thành công."

;=================================
; Finish Page Configuration
;=================================
!define MUI_FINISHPAGE_TITLE "Hoàn thành cài đặt ${APP_NAME}"
!define MUI_FINISHPAGE_TEXT "${APP_NAME} đã được cài đặt thành công trên máy tính của bạn.$\r$\n$\r$\nNhấn Hoàn thành để đóng trình hướng dẫn."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE_NAME}"
!define MUI_FINISHPAGE_RUN_TEXT "Chạy ${APP_NAME}"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Xem hướng dẫn sử dụng"

;=================================
; Pages
;=================================
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "resources\license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;=================================
; Languages
;=================================
!insertmacro MUI_LANGUAGE "Vietnamese"
!insertmacro MUI_LANGUAGE "English"

;=================================
; Installation Section
;=================================
Section "Core Files" SecCore
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    
    ; Install main application files
    File /r "..\dist\EnterpriseDataCollector\*.*"
    
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
    
    done:
        Goto +2
    cancel:
        Abort
FunctionEnd

Function .onInstSuccess
    ; Open readme file option
    MessageBox MB_YESNO "Cài đặt hoàn thành! Bạn có muốn mở hướng dẫn sử dụng không?" IDNO end
    ExecShell "open" "$INSTDIR\README.txt"
    end:
FunctionEnd

;=================================
; Uninstaller Section
;=================================
Section "Uninstall"
    ; Remove application files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_DIR_NAME}"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_DIR_NAME}"
    DeleteRegKey HKLM "Software\${APP_DIR_NAME}"
    
    ; Ask user if they want to remove user data
    MessageBox MB_YESNO "Bạn có muốn xóa dữ liệu người dùng (Database, Logs, Outputs) không?" IDNO skip_userdata
    RMDir /r "$APPDATA\${APP_DIR_NAME}"
    skip_userdata:
SectionEnd

Function un.onInit
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 \
        "Bạn có chắc chắn muốn gỡ cài đặt ${APP_NAME} không?" \
        IDYES continue_uninstall
    Abort
    continue_uninstall:
FunctionEnd

Function un.onUninstSuccess
    MessageBox MB_ICONINFORMATION|MB_OK \
        "${APP_NAME} đã được gỡ cài đặt thành công khỏi máy tính của bạn."
FunctionEnd