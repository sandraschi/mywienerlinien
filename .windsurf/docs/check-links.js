#!/usr/bin/env node

/**
 * Docsify Link Checker
 * 
 * This script checks for broken links in your Docsify documentation.
 * It verifies both internal and external links.
 * 
 * Usage:
 *   node check-links.js [options]
 * 
 * Options:
 *   --serve     Start a local Docsify server for checking
 *   --external  Check external links (slower)
 */

const fs = require('fs');
const path = require('path');
const { promisify } = require('util');
const readFile = promisify(fs.readFile);
const readdir = promisify(fs.readdir);
const stat = promisify(fs.stat);
const { exec } = require('child_process');
const { promisify: p } = require('util');
const execAsync = p(exec);

// Configuration
const DOCS_DIR = __dirname;
const IGNORE_DIRS = ['node_modules', '.git', '.github', '.vscode', 'assets'];
const IGNORE_FILES = ['package.json', 'package-lock.json'];
const MARKDOWN_EXT = '.md';
const PORT = 3000;

// State
const checkedLinks = new Set();
const brokenLinks = [];
let checkExternal = false;
let useLocalServer = false;

// Parse command line arguments
process.argv.slice(2).forEach(arg => {
  if (arg === '--serve') useLocalServer = true;
  if (arg === '--external') checkExternal = true;
});

// Main function
async function main() {
  console.log('🔍 Starting Docsify link checker...');
  
  if (useLocalServer) {
    console.log('🚀 Starting local Docsify server...');
    const server = exec(`npx docsify serve -p ${PORT}`, { cwd: DOCS_DIR });
    server.stdout.pipe(process.stdout);
    server.stderr.pipe(process.stderr);
    
    // Give server time to start
    await new Promise(resolve => setTimeout(resolve, 3000));
  }
  
  console.log('📂 Scanning documentation files...');
  await checkDirectory(DOCS_DIR);
  
  console.log('\n📊 Link Check Results:');
  console.log(`✅ Checked ${checkedLinks.size} links`);
  
  if (brokenLinks.length > 0) {
    console.log(`❌ Found ${brokenLinks.length} broken links:`);
    brokenLinks.forEach(link => {
      console.log(`   - ${link.file}: ${link.link} (${link.status || 'Not found'})`);
    });
    process.exit(1);
  } else {
    console.log('🎉 No broken links found!');
    process.exit(0);
  }
}

// Recursively check a directory for markdown files
async function checkDirectory(dir) {
  const files = await readdir(dir);
  
  for (const file of files) {
    if (IGNORE_DIRS.includes(file) || IGNORE_FILES.includes(file)) continue;
    
    const fullPath = path.join(dir, file);
    const stats = await stat(fullPath);
    
    if (stats.isDirectory()) {
      await checkDirectory(fullPath);
    } else if (stats.isFile() && path.extname(file) === MARKDOWN_EXT) {
      await checkFile(fullPath);
    }
  }
}

// Check links in a markdown file
async function checkFile(filePath) {
  const content = await readFile(filePath, 'utf8');
  const relativePath = path.relative(DOCS_DIR, filePath);
  
  // Find all markdown links [text](url)
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  let match;
  
  while ((match = linkRegex.exec(content)) !== null) {
    const [_, text, url] = match;
    
    // Skip empty or special links
    if (!url || url.startsWith('#') || url.startsWith('mailto:')) continue;
    
    // Skip already checked links
    const linkKey = `${filePath}:${url}`;
    if (checkedLinks.has(linkKey)) continue;
    checkedLinks.add(linkKey);
    
    // Check link
    const result = await checkLink(url, filePath);
    if (!result.exists) {
      brokenLinks.push({
        file: relativePath,
        link: url,
        status: result.status,
        text: text
      });
    }
  }
}

// Check if a link is valid
async function checkLink(url, filePath) {
  // Handle relative paths
  if (!url.startsWith('http')) {
    const dir = path.dirname(filePath);
    const targetPath = path.resolve(dir, url.split('#')[0]);
    
    try {
      await stat(targetPath);
      return { exists: true };
    } catch (e) {
      return { exists: false, status: 'File not found' };
    }
  }
  
  // Check external links if enabled
  if (checkExternal && url.startsWith('http')) {
    try {
      const { statusCode } = await fetch(url, { method: 'HEAD' });
      return { 
        exists: statusCode >= 200 && statusCode < 400,
        status: statusCode
      };
    } catch (e) {
      return { 
        exists: false, 
        status: e.message 
      };
    }
  }
  
  return { exists: true };
}

// Start the link checker
main().catch(console.error);
