# Per-repo fleet start config for mywienerlinien
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'mywienerlinien'
    BackendPort  = 11170
    FrontendPort = 10896
    HealthPath   = '/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '11170' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
