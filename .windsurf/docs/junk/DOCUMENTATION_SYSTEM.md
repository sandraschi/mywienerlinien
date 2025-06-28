# SxS Documentation System

## Overview
The SxS (Side-by-Side) Documentation System provides a robust, maintainable way to manage and serve documentation for the Windsurf project. It features:

- **Markdown-based** - Easy to write and maintain
- **Version Controlled** - All documentation is stored in Git
- **Searchable** - Full-text search across all documents
- **Responsive** - Works on desktop and mobile
- **Themable** - Light and dark themes
- **Extensible** - Plugins for additional functionality

## Quick Start

### Prerequisites
- [Node.js](https://nodejs.org/) (LTS version recommended)
- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) (optional, for containerized deployment)
- [Tailscale](https://tailscale.com/) (for secure remote access)

### Local Development

1. **Start the development server**:
   ```powershell
   .\scripts\start-docs.ps1 -Mode local -Port 3000
   ```
   - Access at: http://localhost:3000

2. **With Tailscale** (for remote access):
   ```powershell
   .\scripts\start-docs.ps1 -Mode local -Port 3000 -Tailscale
   ```
   - Access via your Tailscale IP

### Production Deployment

#### Option 1: Docker Container
```powershell
# Build and run the container
.\scripts\start-docs.ps1 -Mode docker -Port 3000
```

#### Option 2: Docker Compose (with Nginx)
```powershell
# Start the full stack
.\scripts\start-docs.ps1 -Mode compose -Port 80
```

## Backup and Maintenance

### Manual Backup
```powershell
.\scripts\backup-docs.ps1 -BackupDir "D:\Backups\Docs"
```

### Schedule Automatic Backups
```powershell
# Run as Administrator
.\scripts\schedule-docs-backup.ps1
```

### Update Documentation
1. Edit the markdown files in `.windsurf/docs/`
2. The development server will automatically reload
3. Commit and push your changes to version control

## Features

### Last Modified Dates
Each page automatically shows when it was last modified at the top.

### Search
Full-text search is available in the top-right corner.

### Dark/Light Theme
Toggle using the sun/moon icon in the top-right corner.

### Code Copy
Code blocks have a copy button in the top-right corner.

## Directory Structure

```
.windsurf/
├── docs/                   # Documentation root
│   ├── assets/             # Images, CSS, JS
│   ├── current_projects/   # Active project documentation
│   ├── guides/             # How-to guides
│   ├── api/                # API documentation
│   └── index.html          # Main entry point
├── scripts/
│   ├── start-docs.ps1      # Main startup script
│   ├── backup-docs.ps1     # Backup utility
│   └── schedule-docs-backup.ps1  # Backup scheduler
└── docker/
    ├── Dockerfile.docsify  # Docker configuration
    └── nginx/             # Nginx configuration
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```powershell
# Find and stop the process
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

#### Docker Issues
```powershell
# Check container logs
docker logs windsurf-docs

# Rebuild the container
docker-compose -f docker-compose.docs.yml build --no-cache
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT - See [LICENSE](../LICENSE) for more information.

## Support
For help, please open an issue in the repository or contact the maintainers.
