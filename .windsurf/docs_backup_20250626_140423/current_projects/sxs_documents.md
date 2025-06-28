# SxS Documents

## Overview
SxS (Side-by-Side) Documents is our integrated documentation system built on Docsify, providing a beautiful, searchable, and maintainable documentation solution for all Windsurf projects.

## Tech Stack

### Core Components
- **Frontend**: [Docsify.js](https://docsify.js.org/)
- **Styling**: Custom CSS with dark/light themes
- **Search**: Docsify Search Plugin
- **Deployment**: Tailscale for secure access
- **Backup**: Automated backup system

### Development Tools
- **Version Control**: Git
- **Package Manager**: npm
- **Automation**: PowerShell scripts
- **Containerization**: Docker (optional)

## Features

### Current Features
- [x] Markdown-based documentation
- [x] Dark/Light theme support
- [x] Full-text search
- [x] Responsive design
- [x] Automatic sidebar generation
- [x] Tailscale integration
- [x] Automated backups

### Planned Features
- [ ] AI-powered search
- [ ] Interactive examples
- [ ] User feedback system
- [ ] Documentation analytics
- [ ] Multi-language support

## Competitive Landscape

| Feature               | SxS Docs | GitBook | ReadTheDocs | Docusaurus |
|----------------------|-----------|---------|-------------|------------|
| Self-hosted         | ✅ Yes    | ❌ No   | ✅ Yes      | ✅ Yes     |
| Open Source         | ✅ Yes    | ❌ No   | ✅ Yes      | ✅ Yes     |
| Dark Mode           | ✅ Yes    | ✅ Yes  | ✅ Yes      | ✅ Yes     |
| Search              | ✅ Yes    | ✅ Yes  | ✅ Yes      | ✅ Yes     |
| Custom Domain       | ✅ Yes    | 💰 Pro | ✅ Yes      | ✅ Yes     |
| Versioning          | ✅ Git    | ✅ Git  | ✅ Git      | ✅ Git     |
| AI Integration      | ✅ Yes    | ❌ No   | ❌ No       | ❌ No      |
| Offline Access      | ✅ Yes    | ❌ No   | ✅ Yes      | ✅ Yes     |
| Cost                | 🆓 Free   | 💰💰💰  | 🆓 Free     | 🆓 Free    |


## Getting Started

### Prerequisites
- Node.js 16+
- npm or yarn
- Tailscale (for remote access)


### Local Development
```powershell
# Clone the repository
git clone https://github.com/your-org/your-repo.git
cd your-repo

# Install dependencies
npm install -g docsify-cli

# Start the development server
.\scripts\start-docsify-tailscale.ps1
```

### Directory Structure
```
.windsurf/
└── docs/
    ├── .nojekyll
    ├── index.html
    ├── README.md
    ├── _sidebar.md
    ├── assets/
    │   └── css/
    │       └── custom.css
    └── current_projects/
        └── sxs_documents.md
```

## Deployment

### Tailscale Deployment
1. Ensure Tailscale is running on your machine
2. Run the startup script:
   ```powershell
   .\scripts\start-docsify-tailscale.ps1
   ```
3. Access via Tailscale IP shown in the console

### Production Deployment (Optional)
For production deployment with Nginx, see our [Nginx Guide](./nginx_guide.md).

## Maintenance

### Backups
Automated backups run daily at 2 AM:
```powershell
# Manual backup
.\scripts\backup-docs.ps1
```

### Updating
1. Pull the latest changes
2. Restart the Docsify server
3. Clear browser cache if needed

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

## License
MIT License - See [LICENSE](../LICENSE) for details.
