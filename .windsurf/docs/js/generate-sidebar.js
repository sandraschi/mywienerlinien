// Generate sidebar content dynamically from folder structure
function generateSidebar() {
  // This function will be called after Docsify initializes
  console.log('Initializing dynamic sidebar generation...');
  
  // Ensure we don't override existing plugins
  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = (window.$docsify.plugins || []).concat([
    function(hook, vm) {
      hook.mounted(function() {
        // Get the sidebar element
        const sidebar = document.querySelector('.sidebar-nav');
        if (!sidebar) return;

        // Function to fetch directory structure
        async function fetchDirectory(path) {
          try {
            const response = await fetch(path);
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const links = Array.from(doc.querySelectorAll('a'));
            
            // Filter out parent directory and non-markdown files
            return links
              .filter(link => !link.href.includes('..'))
              .map(link => ({
                name: link.textContent.replace(/\.md$/, '').replace(/-/g, ' '),
                path: link.href.replace(window.location.origin, '')
              }));
          } catch (error) {
            console.error('Error fetching directory:', error);
            return [];
          }
        }

        // Function to generate sidebar HTML
        async function generateSidebarHTML(basePath = '') {
          const items = await fetchDirectory(basePath || '/');
          if (items.length === 0) return '';

          let html = '<ul class="app-sub-sidebar">';
          
          for (const item of items) {
            if (item.path.endsWith('/')) {
              // It's a directory
              const dirName = item.name.replace(/\/$/, '');
              const dirPath = item.path.endsWith('/') ? item.path : `${item.path}/`;
              
              html += `
                <li class="directory">
                  <div class="directory-title">
                    <span class="toggle-icon">▶</span>
                    <span class="directory-name">${dirName}</span>
                  </div>
                  <div class="directory-content">
                    ${await generateSidebarHTML(dirPath)}
                  </div>
                </li>
              `;
            } else if (item.path.endsWith('.md')) {
              // It's a markdown file
              const fileName = item.name.replace(/\.md$/, '');
              const isActive = window.location.pathname === item.path;
              
              html += `
                <li class="file ${isActive ? 'active' : ''}">
                  <a href="${item.path}">${fileName}</a>
                </li>
              `;
            }
          }
          
          html += '</ul>';
          return html;
        }

        // Initialize the sidebar
        async function initSidebar() {
          const sidebarHTML = await generateSidebarHTML();
          sidebar.innerHTML = sidebarHTML;
          
          // Add click handlers for directory toggling
          const dirTitles = sidebar.querySelectorAll('.directory-title');
          dirTitles.forEach(title => {
            title.addEventListener('click', function() {
              const content = this.nextElementSibling;
              const icon = this.querySelector('.toggle-icon');
              
              if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.textContent = '▼';
              } else {
                content.style.display = 'none';
                icon.textContent = '▶';
              }
            });
          });
        }

        // Initialize the sidebar
        initSidebar();
      });
    }
  ]);
  
  console.log('Sidebar generation plugin registered');
}

// Export for Node.js environment
if (typeof module !== 'undefined' && module.exports) {
  module.exports = generateSidebar;
}

// Initialize the sidebar generation when the script loads
if (typeof window !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing sidebar...');
    generateSidebar();
  });
}
