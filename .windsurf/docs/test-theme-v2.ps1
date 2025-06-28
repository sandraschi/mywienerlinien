$port = 8000
$root = "D:\Dev\repos\mywienerlinien\.windsurf\docs"
$url = "http://localhost:$port/index.theme-v2.html"

# Start the server
$server = Start-Process -FilePath "python" -ArgumentList "-m", "http.server", "$port", "--directory", "$root" -PassThru -NoNewWindow

# Open the browser
Start-Process $url

Write-Host "Server running at $url"
Write-Host "Press any key to stop..."

# Wait for a key press
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Stop the server
Stop-Process -Id $server.Id -Force
Write-Host "Server stopped"
