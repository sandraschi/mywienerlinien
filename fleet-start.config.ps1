# Per-repo fleet start config for publictransport-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'publictransport-mcp'
    BackendPort  = 0
    FrontendPort = 0
    HealthPath   = '/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind         = 'none'
        UvicornTarget = 'server:app'
        SyncExtras    = @('dev')
        SyncOnStart  = $true
        Env           = @{ WEB_PORT = '11170' }
    }
    Frontend = @{
        Kind         = 'none'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
