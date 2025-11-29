$containerName = "mcp-github-server"
$imageName = "ghcr.io/github/github-mcp-server:latest"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker CLI not found in PATH."
    exit 1
}

$token = $env:GITHUB_PERSONAL_ACCESS_TOKEN
if (-not $token) {
    Write-Error "Environment variable GITHUB_PERSONAL_ACCESS_TOKEN is not set."
    exit 1
}

$toolsets = $env:GITHUB_TOOLSETS
if ([string]::IsNullOrWhiteSpace($toolsets)) {
    $toolsets = "context,repos,issues,pull_requests,users"
}

$envVars = @(
    "--env", "GITHUB_PERSONAL_ACCESS_TOKEN=$token",
    "--env", "GITHUB_TOOLSETS=$toolsets"
)

$existingContainer = docker ps -aq --filter "name=^${containerName}$"

if (-not $existingContainer) {
    $createArgs = @("create", "--name", $containerName) + $envVars + @($imageName)
    $createResult = docker @createArgs

    if (-not $createResult) {
        Write-Error "Failed to create container $containerName using image $imageName."
        exit 1
    }
}

if ($toolsets) {
    docker update --env "GITHUB_TOOLSETS=$toolsets" $containerName | Out-Null
}

$startArgs = @("start", "--attach", "--interactive") + $envVars + @($containerName)
$startResult = docker @startArgs

if (-not $startResult) {
    Write-Error "Failed to start container $containerName."
    exit 1
}*** End Patch

