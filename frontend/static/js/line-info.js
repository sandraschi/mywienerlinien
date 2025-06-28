/**
 * Line Information Page Functionality
 * Handles the display and interaction with public transport line information
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the page
    initLineInfoPage();
    
    // Set up tab switching
    setupLineTabs();
    
    // Load line data
    loadLines();
});

/**
 * Initialize the line information page
 */
function initLineInfoPage() {
    // Set current year in footer if it exists
    const yearElement = document.querySelector('footer p');
    if (yearElement) {
        const currentYear = new Date().getFullYear();
        yearElement.textContent = `© ${currentYear} Wiener Linien Live Map`;
    }
    
    // Close modal when clicking outside content
    const modal = document.getElementById('lineDetailModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
    
    // Close modal with escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

/**
 * Set up tab switching for line types
 */
function setupLineTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active tab
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter lines by type
            const type = this.getAttribute('data-type');
            filterLinesByType(type);
        });
    });
}

/**
 * Load line data from the API
 */
async function loadLines() {
    const linesGrid = document.getElementById('linesGrid');
    if (!linesGrid) return;
    
    try {
        // Show loading state
        linesGrid.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Loading line information...</p>
            </div>`;
        
        // Fetch line data from the API
        const response = await fetch('/api/lines');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const lines = await response.json();
        
        // Render lines
        renderLines(lines);
        
    } catch (error) {
        console.error('Error loading line data:', error);
        linesGrid.innerHTML = `
            <div class="error-message">
                <p>Failed to load line information. Please try again later.</p>
                <button onclick="loadLines()" class="retry-btn">Retry</button>
            </div>`;
    }
}

/**
 * Render lines in the grid
 * @param {Array} lines - Array of line objects
 */
function renderLines(lines) {
    const linesGrid = document.getElementById('linesGrid');
    if (!linesGrid) return;
    
    if (!lines || lines.length === 0) {
        linesGrid.innerHTML = '<p class="no-results">No line information available.</p>';
        return;
    }
    
    // Sort lines by type and then by name
    const sortedLines = [...lines].sort((a, b) => {
        const typeOrder = { 'Metro': 0, 'Tram': 1, 'Bus': 2, 'NightBus': 3 };
        const typeA = typeOrder[a.type] || 4;
        const typeB = typeOrder[b.type] || 4;
        
        if (typeA !== typeB) return typeA - typeB;
        return a.name.localeCompare(b.name, undefined, { numeric: true });
    });
    
    // Generate HTML for each line
    const linesHtml = sortedLines.map(line => createLineCard(line)).join('');
    
    // Update the grid
    linesGrid.innerHTML = linesHtml;
    
    // Add event listeners to line cards
    document.querySelectorAll('.line-card').forEach(card => {
        card.addEventListener('click', () => showLineDetails(card.dataset.lineId));
    });
    
    // Apply any active filters
    const activeTab = document.querySelector('.tab-btn.active');
    if (activeTab) {
        filterLinesByType(activeTab.getAttribute('data-type'));
    }
}

/**
 * Create HTML for a line card
 * @param {Object} line - Line object
 * @returns {string} HTML string for the line card
 */
function createLineCard(line) {
    const typeClass = line.type.toLowerCase().replace(' ', '-');
    
    return `
        <div class="line-card" data-line-id="${line.id || line.name}" data-type="${typeClass}">
            <div class="line-header" style="background-color: ${line.color || '#00796b'};">
                <div class="line-badge" style="background-color: ${line.color || '#00796b'};">
                    ${line.name}
                </div>
                <div>
                    <h2 class="line-title">${line.name} ${line.type}</h2>
                    <p class="line-subtitle">${line.description || ''}</p>
                </div>
            </div>
            <div class="line-details">
                <div class="detail-row">
                    <span class="detail-label">Stops:</span>
                    <span class="detail-value">${line.stations || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Frequency:</span>
                    <span class="detail-value">${line.frequency || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Operating Hours:</span>
                    <span class="detail-value">${line.operating_hours || 'N/A'}</span>
                </div>
            </div>
        </div>`;
}

/**
 * Filter lines by type
 * @param {string} type - Type of lines to show ('all', 'metro', 'tram', 'bus', 'nightbus')
 */
function filterLinesByType(type) {
    const lineCards = document.querySelectorAll('.line-card');
    
    lineCards.forEach(card => {
        if (type === 'all' || card.getAttribute('data-type') === type) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
    
    // Show message if no lines match the filter
    const visibleCards = document.querySelectorAll('.line-card[style="display: flex;"]');
    const noResultsMsg = document.querySelector('.no-results-msg');
    
    if (visibleCards.length === 0) {
        if (!noResultsMsg) {
            const msg = document.createElement('p');
            msg.className = 'no-results-msg';
            msg.textContent = 'No lines found for this category.';
            document.getElementById('linesGrid').appendChild(msg);
        } else {
            noResultsMsg.style.display = 'block';
        }
    } else if (noResultsMsg) {
        noResultsMsg.style.display = 'none';
    }
}

/**
 * Show detailed information for a specific line
 * @param {string} lineId - ID of the line to show details for
 */
async function showLineDetails(lineId) {
    const modal = document.getElementById('lineDetailModal');
    const content = document.getElementById('lineDetailContent');
    
    if (!modal || !content) return;
    
    try {
        // Show loading state
        content.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Loading line details...</p>
            </div>`;
        
        // Show modal
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Fetch detailed line data
        const response = await fetch(`/api/lines/${encodeURIComponent(lineId)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const line = await response.json();
        
        // Render line details
        content.innerHTML = renderLineDetails(line);
        
        // Add event listener to close button
        const closeBtn = document.querySelector('.close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }
        
    } catch (error) {
        console.error('Error loading line details:', error);
        content.innerHTML = `
            <div class="error-message">
                <p>Failed to load line details. Please try again later.</p>
                <button onclick="showLineDetails('${lineId}')" class="retry-btn">Retry</button>
            </div>`;
    }
}

/**
 * Render detailed line information
 * @param {Object} line - Line object with details
 * @returns {string} HTML string for the line details
 */
function renderLineDetails(line) {
    const typeClass = line.type.toLowerCase().replace(' ', '-');
    
    return `
        <div class="line-detail-header" style="background-color: ${line.color || '#00796b'};">
            <div class="line-detail-badge" style="background-color: ${line.color || '#00796b'};">
                ${line.name}
            </div>
            <div class="line-detail-titles">
                <h2>${line.name} ${line.type}</h2>
                <p>${line.description || ''}</p>
            </div>
        </div>
        <div class="line-detail-content">
            <div class="detail-section">
                <h3>Overview</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="detail-label">Type:</span>
                        <span class="detail-value">${line.type}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Stops:</span>
                        <span class="detail-value">${line.stations || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Frequency:</span>
                        <span class="detail-value">${line.frequency || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Operating Hours:</span>
                        <span class="detail-value">${line.operating_hours || 'N/A'}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>Route Map</h3>
                <div class="route-map-placeholder" id="routeMap">
                    <!-- Map will be rendered here -->
                    <p>Interactive map coming soon</p>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>Schedule</h3>
                <div class="schedule-placeholder">
                    <p>Schedule information coming soon</p>
                    <!-- Schedule will be added here -->
                </div>
            </div>
        </div>`;
}

/**
 * Close the modal dialog
 */
function closeModal() {
    const modal = document.getElementById('lineDetailModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Make functions available globally for HTML event handlers
window.loadLines = loadLines;
window.showLineDetails = showLineDetails;
window.closeModal = closeModal;
