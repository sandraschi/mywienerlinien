# Setup script for Docsify documentation
$docsDir = "d:\\Dev\\repos\\mywienerlinien\\.windsurf\\docs"
$devDir = "d:\\Dev\\repos\\mywienerlinien\\.windsurf\\docs-dev"

# Create dev directory if it doesn't exist
if (-not (Test-Path $devDir)) {
    New-Item -ItemType Directory -Path $devDir | Out-Null
    Write-Host "Created dev directory at $devDir" -ForegroundColor Green
}

# Install required npm packages if not already installed
if (-not (Test-Path "$docsDir\node_modules")) {
    npm install --prefix $docsDir docsify-cli@latest --save-dev
    npm install --prefix $docsDir docsify-sidebar-collapse@latest --save
    npm install --prefix $docsDir docsify-search@latest --save
    npm install --prefix $docsDir docsify-tabs@latest --save
}

# Create or update index.html for production
@"
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Windsurf AI Documentation</title>
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
  <meta name="description" content="Windsurf AI Documentation">
  <meta name="viewport" content="width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify-themeable@0/dist/css/theme-defaults/buble.css">
  <style>
    :root {
      --theme-color: #42b983;
      --content-max-width: 90%;
      --sidebar-width: 280px;
    }
    body {
      transition: background-color 0.3s ease;
    }
    .sidebar {
      background-color: #2f3136;
    }
    .sidebar ul li a {
      color: #e6e6e6;
    }
    .sidebar ul li.active>a {
      color: var(--theme-color);
    }
  </style>
</head>
<body>
  <div id="app"></div>
  <script>
    window.$docsify = {
      name: 'Windsurf AI',
      repo: '',
      loadSidebar: true,
      subMaxLevel: 5,
      search: {
        maxAge: 86400000,
        paths: 'auto',
        placeholder: 'Search...',
        noData: 'No results!',
        depth: 5
      },
      plugins: [
        function(hook, vm) {
          hook.beforeEach(function(html) {
            return html + '\n\n' + 
              '<div class="last-updated">' + 
              'Last updated: ' + new Date().toLocaleString() + 
              '</div>';
          });
        }
      ]
    }
  </script>
  <script src="//cdn.jsdelivr.net/npm/docsify@4"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify-sidebar-collapse/dist/docsify-sidebar-collapse.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/search.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify-tabs@1"></script>
</body>
</html>
"@ | Out-File -FilePath "$docsDir\index.html" -Encoding utf8

# Create dev version with hot-reload
@"
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Windsurf AI Dev</title>
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
  <meta name="description" content="Windsurf AI Development Documentation">
  <meta name="viewport" content="width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify-themeable@0/dist/css/theme-defaults/dark.css">
  <style>
    :root {
      --theme-color: #ff6b6b;
      --content-max-width: 90%;
      --sidebar-width: 300px;
    }
    .sidebar-toggle {
      background-color: var(--theme-color);
    }
    .sidebar-toggle span {
      background-color: white;
    }
  </style>
</head>
<body>
  <div id="app"></div>
  <script>
    window.$docsify = {
      name: 'Windsurf AI Dev',
      repo: '',
      loadSidebar: true,
      subMaxLevel: 5,
      auto2top: true,
      search: {
        maxAge: 0, // Always reindex
        paths: 'auto',
        placeholder: 'Search dev docs...',
        noData: 'No results!',
        depth: 5
      },
      plugins: [
        function(hook, vm) {
          hook.beforeEach(function(html) {
            return html + '\n\n' + 
              '<div class="last-updated" style="color: #ff6b6b; font-size: 0.8em;">' + 
              'DEV VERSION - Last updated: ' + new Date().toLocaleString() + 
              '</div>';
          });
        }
      ]
    }
  </script>
  <script src="//cdn.jsdelivr.net/npm/docsify@4"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify-sidebar-collapse/dist/docsify-sidebar-collapse.min.js"></script>
  <script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/search.min.js"></script>
  <script src="//unpkg.com/docsify-tabs@1"></script>
  <script>
    // Auto-refresh for development
    setInterval(() => {
      fetch(window.location.href, { method: 'HEAD' })
        .then(response => {
          if (response.headers.get('etag') !== document.querySelector('meta[http-equiv="etag"]')?.content) {
            window.location.reload();
          }
        });
    }, 5000);
  </script>
</body>
</html>
"@ | Out-File -FilePath "$devDir\index.html" -Encoding utf8

# Create start scripts
@"
@echo off
start "" "http://localhost:3300"
docsify serve docs -p 3300
"@ | Out-File -FilePath "$docsDir\start.bat" -Encoding ascii

@"
@echo off
start "" "http://localhost:3001"
docsify serve docs-dev -p 3001
"@ | Out-File -FilePath "$devDir\start-dev.bat" -Encoding ascii

# Copy sidebar and README to dev
Copy-Item "$docsDir\_sidebar.md" -Destination "$devDir\_sidebar.md" -Force
Copy-Item "$docsDir\README.md" -Destination "$devDir\README.md" -Force

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "- Production docs: cd docs && npm run start (port 3300)" -ForegroundColor Cyan
Write-Host "- Development docs: cd docs-dev && npm run start (port 3001)" -ForegroundColor Cyan
Write-Host "`nMake sure to run 'npm install -g docsify-cli' if you haven't already" -ForegroundColor Yellow
