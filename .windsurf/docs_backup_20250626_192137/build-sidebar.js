const fs = require('fs');
const path = require('path');

/**
 * Format a filename into a title
 */
function formatTitle(str) {
  return str
    .split(/[-_]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Generate sidebar items from directory structure
 */
function generateSidebarItems(dir, basePath = '') {
  const items = [];
  
  try {
    const files = fs.readdirSync(dir);
    
    // Sort files: directories first, then files, both alphabetically
    files.sort((a, b) => {
      const aPath = path.join(dir, a);
      const bPath = path.join(dir, b);
      const aIsDir = fs.statSync(aPath).isDirectory();
      const bIsDir = fs.statSync(bPath).isDirectory();
      
      if (aIsDir && !bIsDir) return -1;
      if (!aIsDir && bIsDir) return 1;
      return a.localeCompare(b);
    });
    
    for (const file of files) {
      // Skip hidden files and specific files
      if (file.startsWith('.') || 
          file === 'node_modules' || 
          file === '_sidebar.md' || 
          file === 'index.html' || 
          file === 'README.md') {
        continue;
      }
      
      const fullPath = path.join(dir, file);
      const stat = fs.statSync(fullPath);
      const relPath = path.join(basePath, file);
      
      if (stat.isDirectory()) {
        // For directories, recursively get children
        const children = generateSidebarItems(fullPath, relPath);
        if (children.length > 0) {
          items.push({
            title: formatTitle(file),
            path: relPath.replace(/\\/g, '/'),
            children: children
          });
        }
      } else if (file.endsWith('.md') && !file.startsWith('_')) {
        // For markdown files, add as a link
        const name = path.basename(file, '.md');
        items.push({
          title: formatTitle(name),
          path: path.join(basePath, name).replace(/\\/g, '/')
        });
      }
    }
  } catch (error) {
    console.error(`Error processing directory ${dir}:`, error);
  }
  
  return items;
}

/**
 * Generate the sidebar markdown content
 */
function generateSidebarMarkdown(items, level = 0) {
  const lines = [];
  const indent = '  '.repeat(level);
  
  for (const item of items) {
    // Create a proper path for both files and directories
    let path = item.path;
    let displayText = item.title;
    
    // For directories, link to index.md if it exists, otherwise just the path
    if (item.children) {
      path = path.endsWith('/') ? path : `${path}/`;
      // Check if this directory has an index.md
      const indexPath = `${path}index.md`;
      try {
        if (fs.existsSync(path.join(__dirname, indexPath))) {
          // Directory has an index.md, link to it with bold text
          lines.push(`${indent}- [**${displayText}**](${indexPath})`);
        } else {
          // No index.md, just link to the directory with bold text
          lines.push(`${indent}- [**${displayText}**](${path})`);
        }
      } catch (e) {
        // On error, just use the path as is with bold text
        lines.push(`${indent}- [**${displayText}**](${path})`);
      }
      
      // Add children with increased indentation
      const childLines = generateSidebarMarkdown(item.children, level + 1);
      lines.push(...childLines);
    } else {
      // For files, create a markdown link
      lines.push(`${indent}- [${displayText}](${path})`);
    }
  }
  
  return lines;
}

// Main execution
function main() {
  try {
    const items = generateSidebarItems(__dirname);
    const markdownLines = [
      '- [Home](/)',  // Home link at the top
      ...generateSidebarMarkdown(items)
    ];
    
    // Write to _sidebar.md
    fs.writeFileSync(
      path.join(__dirname, '_sidebar.md'),
      markdownLines.join('\n')
    );
    
    console.log('Sidebar generated successfully!');
  } catch (error) {
    console.error('Error generating sidebar:', error);
    process.exit(1);
  }
}

// Run the main function
main();
