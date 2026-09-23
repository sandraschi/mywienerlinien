; Kill UI + backend before install/uninstall (backend locks resources/*.exe).
!macro KillMywienerlinienFleetProcesses
  DetailPrint "Stopping mywienerlinien processes..."
  ExecWait 'taskkill /F /IM mywienerlinien-backend.exe /T' $0
  ExecWait 'taskkill /F /IM mywienerlinien-native.exe /T' $0
  !if "${INSTALLMODE}" == "currentUser"
    nsis_tauri_utils::KillProcessCurrentUser "mywienerlinien-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcessCurrentUser "mywienerlinien-native.exe"
    Pop $0
  !else
    nsis_tauri_utils::KillProcess "mywienerlinien-backend.exe"
    Pop $0
    nsis_tauri_utils::KillProcess "mywienerlinien-native.exe"
    Pop $0
  !endif
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillMywienerlinienFleetProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillMywienerlinienFleetProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  IfFileExists "$INSTDIR\resources\install-mcp-clients.ps1" 0 mcp_hook_done
    DetailPrint "Optional: register mywienerlinien in Cursor / Claude Desktop"
    ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\resources\install-mcp-clients.ps1" -Interactive'
  mcp_hook_done:
!macroend