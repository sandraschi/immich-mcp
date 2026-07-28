# Per-repo fleet start config for immich-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'immich-mcp'
    BackendPort  = 10839
    FrontendPort = 10838
    HealthPath   = '/api/v1/health'
    WebRoot      = 'D:\Dev\repos\immich-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'immich_mcp.server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10839' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
