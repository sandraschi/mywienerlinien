# Wiener Linien App - Docker Setup

This document explains how to run the Wiener Linien Live Map application using Docker.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (usually included with Docker Desktop)
- At least 2GB of available RAM

## Quick Start

### Using PowerShell (Recommended)

```powershell
# Start the application
.\start_wiener_linien.ps1

# Or with specific action
.\start_wiener_linien.ps1 start
```

### Using Batch File

```cmd
# Start the application
start_wiener_linien.bat

# Or with specific action
start_wiener_linien.bat start
```

### Using Docker Compose Directly

```bash
# Build and start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## Available Commands

### PowerShell Script (`start_wiener_linien.ps1`)

| Command | Description |
|---------|-------------|
| `start` | Start the Wiener Linien application |
| `stop` | Stop the Wiener Linien application |
| `restart` | Restart the Wiener Linien application |
| `logs` | Show application logs |
| `status` | Show application status and health |
| `build` | Build the Docker image |
| `clean` | Clean up containers and images |

### Batch File (`start_wiener_linien.bat`)

Same commands as PowerShell script.

## Accessing the Application

Once started, the application will be available at:

- **Main Application**: http://localhost:3080
- **API Status**: http://localhost:3080/api/status
- **API Endpoints**: http://localhost:3080/api/*

## Container Details

- **Container Name**: `wiener-linien-app`
- **Port**: 3080
- **Base Image**: Python 3.11-slim
- **Health Check**: Automatic health monitoring via `/api/status` endpoint

## Volumes

The following directories are mounted as volumes:

- `./logs` → `/app/logs` - Application logs
- `./data` → `/app/data` - Application data

## Environment Variables

- `FLASK_ENV=production` - Production environment
- `PYTHONUNBUFFERED=1` - Unbuffered Python output
- `FLASK_APP=app.py` - Flask application entry point

## Troubleshooting

### Container Won't Start

1. Check if port 3080 is available:
   ```bash
   netstat -an | findstr :3080
   ```

2. Check Docker logs:
   ```bash
   docker-compose logs
   ```

3. Ensure Docker Desktop is running

### Application Not Responding

1. Check container status:
   ```bash
   docker-compose ps
   ```

2. Check application logs:
   ```bash
   docker-compose logs -f
   ```

3. Verify the API endpoint:
   ```bash
   curl http://localhost:3080/api/status
   ```

### Build Issues

1. Clean and rebuild:
   ```bash
   .\start_wiener_linien.ps1 clean
   .\start_wiener_linien.ps1 build
   .\start_wiener_linien.ps1 start
   ```

2. Check Docker disk space:
   ```bash
   docker system df
   ```

## Development

### Making Changes

1. Stop the container:
   ```bash
   .\start_wiener_linien.ps1 stop
   ```

2. Make your changes to the code

3. Rebuild and start:
   ```bash
   .\start_wiener_linien.ps1 build
   .\start_wiener_linien.ps1 start
   ```

### Live Development

For live development, you can mount the source code as a volume by modifying `docker-compose.yml`:

```yaml
volumes:
  - ./logs:/app/logs
  - ./data:/app/data
  - .:/app  # Add this line for live code changes
```

## Security

- The application runs as a non-root user (`app`)
- Health checks are enabled
- Container restart policy is set to `unless-stopped`

## Performance

- Uses Python 3.11 slim image for smaller size
- Multi-stage build optimization
- Proper layer caching for faster rebuilds

## Monitoring

### Health Checks

The container includes automatic health checks that verify the application is responding:

```bash
# Check health status
docker ps --filter "name=wiener-linien-app"
```

### Logs

Application logs are available in multiple ways:

1. **Container logs**:
   ```bash
   docker-compose logs -f
   ```

2. **Host logs directory**:
   ```bash
   # Logs are saved to ./logs/ directory
   ```

## Cleanup

To completely remove the application and all associated resources:

```bash
.\start_wiener_linien.ps1 clean
```

This will:
- Stop the container
- Remove the container
- Remove the image
- Remove associated volumes
- Remove orphaned resources

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the application logs
3. Verify Docker Desktop is running properly
4. Ensure sufficient system resources are available 