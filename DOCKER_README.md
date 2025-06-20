# 🐳 Docker Setup for Wiener Linien Live Map

This guide will help you run the Wiener Linien Live Map application using Docker.

## 📋 Prerequisites

1. **Docker Desktop** installed and running
2. **Git** to clone the repository

## 🚀 Quick Start

### Option 1: Using the provided scripts (Recommended)

#### Windows Batch File:
```bash
start_docker.bat
```

#### PowerShell Script:
```powershell
.\start_docker.ps1
```

### Option 2: Manual Docker commands

1. **Build the Docker image:**
   ```bash
   docker build -t wiener-linien-app .
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - Web Interface: http://localhost:3080
   - API Status: http://localhost:3080/api/status

## 🛠️ Docker Commands

### Start the application:
```bash
docker-compose up -d
```

### Stop the application:
```bash
docker-compose down
```

### View logs:
```bash
docker-compose logs -f
```

### Rebuild and restart:
```bash
docker-compose up --build -d
```

### Check container status:
```bash
docker-compose ps
```

### Access container shell:
```bash
docker-compose exec wiener-linien-app bash
```

## 📁 Project Structure

```
mywienerlinien/
├── Dockerfile                 # Docker image configuration
├── docker-compose.yml         # Docker Compose configuration
├── .dockerignore             # Files to exclude from Docker build
├── start_docker.bat          # Windows batch file to start Docker
├── start_docker.ps1          # PowerShell script to start Docker
├── frontend/
│   ├── app.py                # Main Flask application
│   ├── requirements.txt      # Python dependencies
│   ├── data/                 # Static data files
│   └── logs/                 # Application logs
└── docs/                     # Documentation
```

## 🔧 Configuration

### Environment Variables

The application uses the following environment variables:

- `FLASK_APP=frontend/app.py` - Flask application entry point
- `FLASK_ENV=production` - Flask environment
- `PYTHONUNBUFFERED=1` - Python output buffering

### Port Configuration

- **Application Port**: 3080
- **Internal Port**: 3080
- **External Access**: http://localhost:3080

## 📊 Health Checks

The Docker container includes health checks that monitor:
- Application startup
- API endpoint availability
- Service responsiveness

## 🐛 Troubleshooting

### Docker Desktop not running
```
ERROR: Docker is not running. Please start Docker Desktop first.
```
**Solution**: Start Docker Desktop from the Start menu or system tray.

### Port already in use
```
ERROR: Port 3080 is already in use
```
**Solution**: 
1. Stop the existing application: `docker-compose down`
2. Or change the port in `docker-compose.yml`

### Build fails
```
ERROR: Failed to build Docker image
```
**Solution**:
1. Check Docker Desktop is running
2. Ensure you have sufficient disk space
3. Try rebuilding: `docker-compose up --build -d`

### Application not accessible
```
WARNING: Application might still be starting up
```
**Solution**:
1. Wait 30-60 seconds for full startup
2. Check logs: `docker-compose logs -f`
3. Verify health check: `docker-compose ps`

## 🔍 Monitoring

### View real-time logs:
```bash
docker-compose logs -f wiener-linien-app
```

### Check container health:
```bash
docker-compose ps
```

### Monitor resource usage:
```bash
docker stats wiener-linien-live-map
```

## 🧹 Cleanup

### Remove containers and networks:
```bash
docker-compose down
```

### Remove containers, networks, and volumes:
```bash
docker-compose down -v
```

### Remove all Docker resources:
```bash
docker system prune -a
```

## 📈 Production Deployment

For production deployment, consider:

1. **Environment Variables**: Use `.env` files for sensitive data
2. **Logging**: Configure external logging solutions
3. **Monitoring**: Add monitoring and alerting
4. **Security**: Use non-root user in container
5. **Backup**: Regular data backups

## 🤝 Contributing

When contributing to the Docker setup:

1. Test your changes locally
2. Update documentation
3. Ensure backward compatibility
4. Test on different platforms

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section
2. Review Docker logs
3. Verify system requirements
4. Check GitHub issues

---

**Happy mapping! 🗺️** 