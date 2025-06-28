# SECURE LOCAL DEVELOPMENT SERVER
# Binds to 127.0.0.1 only - not accessible over Tailscale/network
# Using port 3310 for testing parallel access

# Configuration
$port = 3310  # Using port 3310 for testing
$bindAddress = "127.0.0.1"  # Explicitly bind to localhost only
$root = $PSScriptRoot
$url = "http://${bindAddress}:${port}/index.theme-v2.html"

# Function to test if port is available
function Test-PortAvailable {
    param([int]$port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse($bindAddress), $port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

# Check if port is available
if (-not (Test-PortAvailable -port $port)) {
    Write-Host "Port $port is not available. Another process may be using it."
    exit 1
}

# Start the server (bound to localhost only)
Write-Host "Starting secure local server on port $port (not accessible via Tailscale)..."
$server = Start-Process -FilePath "python" `
    -ArgumentList "-m", "http.server", "$port", "--bind", "$bindAddress", "--directory", "$root" `
    -PassThru -NoNewWindow

# Wait for server to start
Start-Sleep -Seconds 1

# Verify server is running
try {
    $request = [System.Net.WebRequest]::Create($url)
    $request.Timeout = 1000
    $response = $request.GetResponse()
    $response.Close()
    Write-Host "Server running locally at: $url"
    Write-Host "This server is ONLY accessible from this computer (localhost/127.0.0.1)"
    Write-Host "It is NOT accessible via Tailscale or any other network interface"
    Write-Host "Port: $port (secure localhost only)"
} catch {
    Write-Host "Warning: Server may not have started correctly"
    exit 1
}

# Open the browser
Start-Process $url

# Wait for key press
Write-Host "Press any key to stop the server..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Clean up
Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
Write-Host "Server stopped"
