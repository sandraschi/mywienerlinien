const fs = require('fs');
const path = require('path');

function generateSidebar(dir, basePath = '') {
  const files = fs.readdirSync(dir);
  let sidebar = [];
  
  // Sort files to ensure consistent ordering
  files.sort((a, b) => {
    // Directories first, then files
    const aIsDir = fs.statSync(path.join(dir, a)).isDirectory();
    const bIsDir = fs.statSync(path.join(dir, b)).isDirectory();
    
    if (aIsDir && !bIsDir) return -1;
    if (!aIsDir && bIsDir) return 1;
    
    // Alphabetical order
    return a.localeCompare(b);
  });
  
  files.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    
    // Skip hidden files/directories and specific files
    if (file.startsWith('.') || file === 'node_modules' || file === '_sidebar.md' || file === 'index.html' || file === 'README.md') {
      return;
    }
    
    if (stat.isDirectory()) {
      const children = generateSidebar(fullPath, path.join(basePath, file));
      if (children.length > 0) {
        sidebar.push({
          title: formatTitle(file),
          children: children,
          isDir: true
        });
      }
    } else if (file.endsWith('.md') && !file.startsWith('_')) {
      const name = path.basename(file, '.md');
      sidebar.push({
        title: formatTitle(name),
        path: path.join(basePath, name).replace(/\\/g, '/')
      });
    }
  });
  
  return sidebar;
}

function formatTitle(str) {
  return str
    .split(/[-_]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

// Generate sidebar content
const sidebar = generateSidebar(__dirname);
let sidebarContent = [];

function formatSidebar(items, level = 0) {
  items.forEach(item => {
    const indent = '  '.repeat(level);
    
    if (item.children) {
      // For directories, create a collapsible section
      const id = item.title.toLowerCase().replace(/\s+/g, '-');
      sidebarContent.push(`${indent}- <span class="folder" id="folder-${id}">${item.title}</span>`);
      sidebarContent.push(`${indent}  <ul class="folder-contents" id="${id}-contents" style="display: none;">`);
      formatSidebar(item.children, level + 2);
      sidebarContent.push(`${indent}  </ul>`);
    } else {
      // For files, create a normal link
      sidebarContent.push(`${indent}- [${item.title}](${item.path})`);
    }
  });
}

// Add a link to the home page at the top
sidebarContent.push('- [Home](/)');

// Add the collapsible folder JavaScript and CSS
sidebarContent.push(`<style>`);
sidebarContent.push(`.folder {`);
sidebarContent.push(`  cursor: pointer;`);
sidebarContent.push(`  font-weight: bold;`);
sidebarContent.push(`  user-select: none;`);
sidebarContent.push(`}`);
sidebarContent.push(`.folder:before {`);
sidebarContent.push(`  content: '▶ ';`);
sidebarContent.push(`  font-size: 0.8em;`);
sidebarContent.push(`}`);
sidebarContent.push(`.folder.open:before {`);
sidebarContent.push(`  content: '▼ ';`);
sidebarContent.push(`}`);
sidebarContent.push(`</style>`);
sidebarContent.push(``);
sidebarContent.push(`<script>`);
sidebarContent.push(`// Toggle folder visibility`);
sidebarContent.push(`function toggleFolder(folderId) {`);
sidebarContent.push(`  const folder = document.getElementById('folder-' + folderId);`);
sidebarContent.push(`  const contents = document.getElementById(folderId + '-contents');`);
sidebarContent.push(``);
sidebarContent.push(`  if (folder && contents) {`);
sidebarContent.push(`    folder.classList.toggle('open');`);
sidebarContent.push(`    contents.style.display = contents.style.display === 'none' ? 'block' : 'none';`);
sidebarContent.push(`  }`);
sidebarContent.push(`}`);
sidebarContent.push(``);
sidebarContent.push(`// Add click handlers to all folders`);
sidebarContent.push(`document.addEventListener('DOMContentLoaded', function() {`);
sidebarContent.push(`  document.querySelectorAll('.folder').forEach(folder => {`);
sidebarContent.push(`    const folderId = folder.id.replace('folder-', '');`);
sidebarContent.push(`    folder.addEventListener('click', () => toggleFolder(folderId));`);
sidebarContent.push(`  });`);
sidebarContent.push(``);
sidebarContent.push(`  // Open the current folder`);
sidebarContent.push(`  const currentPath = window.location.pathname.replace(/^\//, '');`);
sidebarContent.push(`  if (currentPath) {`);
sidebarContent.push(`    const pathParts = currentPath.split('/');`);
sidebarContent.push(`    pathParts.forEach((part, index) => {`);
sidebarContent.push(`      const folderId = part.toLowerCase();`);
sidebarContent.push(`      toggleFolder(folderId);`);
sidebarContent.push(`    });`);
sidebarContent.push(`  }`);
sidebarContent.push(`});`);
sidebarContent.push(`</script>`);
.folder {
  cursor: pointer;
  font-weight: bold;
  user-select: none;
}
.folder:before {
  content: '▶ ';
  font-size: 0.8em;
}
.folder.open:before {
  content: '▼ ';
}
</style>

<script>
// Toggle folder visibility
function toggleFolder(folderId) {
  const folder = document.getElementById('folder-' + folderId);
  const contents = document.getElementById(folderId + '-contents');
  
  if (folder && contents) {
    folder.classList.toggle('open');
    contents.style.display = contents.style.display === 'none' ? 'block' : 'none';
  }
}

// Add click handlers to all folders
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.folder').forEach(folder => {
    const folderId = folder.id.replace('folder-', '');
    folder.addEventListener('click', () => toggleFolder(folderId));
  });
  
  // Open the current folder
  const currentPath = window.location.pathname.replace(/^\//, '');
  if (currentPath) {
    const pathParts = currentPath.split('/');
    pathParts.forEach((part, index) => {
      const folderId = part.toLowerCase();
      toggleFolder(folderId);
    });
  }
});
</script>`);

formatSidebar(sidebar);

// Write to _sidebar.md
fs.writeFileSync(path.join(__dirname, '_sidebar.md'), sidebarContent.join('\n'));

console.log('Sidebar with collapsible nodes generated successfully!');
