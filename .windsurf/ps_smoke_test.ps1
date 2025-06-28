# This is the simplest possible PowerShell script to test file I/O.
$LogFile = "d:\\Dev\\repos\\mywienerlinien\\.windsurf\\logs\\ps_smoke_test.log"
"PowerShell smoke test successful." | Out-File -FilePath $LogFile -Encoding utf8 -Force
