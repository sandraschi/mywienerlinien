# Docker Setup for Windsurf Documentation

This directory contains Docker configuration forunning the Docsify documentation server with auto-restart and better management capabilities.

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- Docker Compose (usually included with Docker Desktop)

### Starthe Documentation Server

```powershell
# Navigate to the docs directory
cd .windsurf/docs

# Starthe server (builds and runs automatically)
.\docker-start.ps1
```

The server will be available at: **http://localhost:3301**

## Docker Management Commands

### PowerShell Script (Recommended)

```powershell
# Starthe server
.\docker-start.ps1

# Build the image (force rebuild)
.\docker-start.ps1 -Build

# Stop the server
.\docker-start.ps1 -Stop

# Restarthe server
.\docker-start.ps1 -Restart

# View logs
.\docker-start.ps1 -Logs

# Open shell in container
.\docker-start.ps1 -Shell

# Clean up all Dockeresources
.\docker-start.ps1 -Clean
```

### Docker Compose Commands

```bash
# Starthe server
docker-compose up -d

# Stop the server
docker-compose down

# View logs
docker-compose logs -f

# Rebuild and start
docker-compose up -d --build

# Clean up everything
docker-compose down --rmi all --volumes --remove-orphans
```

## Features

### Auto-Restart
- Container automatically restarts if it crashes
- Health checks ensure the server is running properly
- Graceful shutdown handling

### Live Reloading
- Volume mounting enables live reloading of documentation changes
- No need to restarthe container when editing files

### Resource Management
- Lightweight Alpine Linux base image
- Proper cleanup of resources
- Network isolation

### Monitoring
- Health checks every 30 seconds
- Comprehensive logging
- Easy access to container logs

## File Structure

```
.windsurf/docs/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── docker-entrypoint.sh    # Container startup script
├── docker-start.ps1        # PowerShell management script
├── docker-start.bat        # Windows batch management script
├── .dockerignore           # Files to exclude from build
└── README-Docker.md        # This file
```

## Configuration

### Porthe serveruns on port **3301** by default. To change this:

1. Update `docker-compose.yml`:
   ```yaml
   ports:
     - "YOUR_PORT:3300"
   ```

2. Update `docker-start.ps1`:
   ```powershell
   $Port = "YOUR_PORT"
   ```

3. Update `docker-start.bat`:
   ```batch
   set PORT=YOUR_PORT
   ```

### Environment Variables
You can add environment variables in `docker-compose.yml`:

```yaml
environment:
  - NODE_ENV=development
  - YOUR_VAR=value
```

## Troubleshooting

### Container Won't Start
1. Check if Docker Desktop is running
2. Check logs: `.\docker-start.ps1 -Logs`
3. Rebuild the image: `.\docker-start.ps1 -Build`

### Port Already in Use
1. Stop the container: `.\docker-start.ps1 -Stop`
2. Check what's using the port: `netstat -ano | findstr :3301`
3. Kill the process or change the port

### Permission Issues
1. Run PowerShell as Administrator
2. Check Docker Desktop settings
3. Ensure Docker has access to the directory

### Live Reload Not Working
1. Check volume mounting in `docker-compose.yml`
2. Ensure file permissions are correct
3. Restarthe container: `.\docker-start.ps1 -Restart`

## Benefits Over Local Installation

1. **Consistency**: Samenvironment across all machines
2. **Isolation**: No conflicts with local Node.js versions
3. **Auto-restart**: Automatic recovery from crashes
4. **Easy cleanup**: Simple commands to removeverything
5. **Portability**: Works on any machine with Docker
6. **Monitoring**: Built-in health checks and logging
7. **Resource management**: Controlled resource usage

## Migration from Local Installation

If you were previously running Docsify locally:

1. Stop any local Docsify processes
2. Run `.\docker-start.ps1 -Build` to build the Docker image
3. Run `.\docker-start.ps1` to starthe containerized version
4. Access your docs athe same URL: http://localhost:3301

The documentation will work exactly the same, but with better management and reliability. 