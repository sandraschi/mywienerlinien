/**
 * About Page JavaScript
 * Handles interactive elements and dynamic content on the About page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the page
    initAboutPage();
    
    // Set current year in footer
    updateFooterYear();
    
    // Animate statistics
    if (document.getElementById('statLines')) {
        animateStatistics();
    }
    
    // Add smooth scrolling for anchor links
    setupSmoothScrolling();
});

/**
 * Initialize the About page
 */
function initAboutPage() {
    // Add any initialization code here
    console.log('About page initialized');
    
    // Add active class to current navigation item
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkHref = link.getAttribute('href');
        if (linkHref && currentPage.includes(linkHref.replace(/^\//, '').replace('.html', ''))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Update the current year in the footer
 */
function updateFooterYear() {
    const yearElement = document.getElementById('currentYear');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }
}

/**
 * Animate statistics on scroll into view
 */
function animateStatistics() {
    const statElements = {
        'statLines': 0,
        'statStations': 0,
        'statCoverage': 0
    };
    
    // Target values for the counters
    const targetValues = {
        'statLines': 150,      // Example value - should be updated with real data
        'statStations': 2000,  // Example value - should be updated with real data
        'statCoverage': 100    // Percentage
    };
    
    // Animation duration in milliseconds
    const duration = 2000;
    
    // Check if element is in viewport
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Animate a single value
    function animateValue(elementId, start, end, duration) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = Math.floor(progress * (end - start) + start);
            element.textContent = elementId === 'statCoverage' ? `${value}%` : value.toLocaleString();
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        
        window.requestAnimationFrame(step);
    }
    
    // Check if stats section is in view and animate
    function checkAndAnimate() {
        const statsSection = document.querySelector('.stats-section');
        if (statsSection && isInViewport(statsSection)) {
            // Only animate once
            window.removeEventListener('scroll', checkAndAnimate);
            
            // Animate each statistic
            for (const [id, startValue] of Object.entries(statElements)) {
                const target = targetValues[id] || 0;
                animateValue(id, startValue, target, duration);
            }
        }
    }
    
    // Initial check in case stats are already in view
    checkAndAnimate();
    
    // Add scroll event listener
    window.addEventListener('scroll', checkAndAnimate);
}

/**
 * Set up smooth scrolling for anchor links
 */
function setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 100, // Adjust for fixed header
                    behavior: 'smooth'
                });
                
                // Update URL without jumping
                history.pushState(null, null, targetId);
            }
        });
    });
}

/**
 * Fetch and update statistics from the API
 * This is a placeholder - implement with actual API calls when available
 */
async function updateStatistics() {
    try {
        // Example API call (replace with actual endpoint)
        // const response = await fetch('/api/statistics');
        // const data = await response.json();
        
        // For now, we'll use the target values from the animation
        const stats = {
            lines: 150,
            stations: 2000,
            dailyPassengers: 2600000,
            coverage: 100
        };
        
        // Update the DOM with the fetched data
        // document.getElementById('statLines').textContent = stats.lines.toLocaleString();
        // document.getElementById('statStations').textContent = stats.stations.toLocaleString();
        // document.getElementById('statDailyPassengers').textContent = (stats.dailyPassengers / 1000000).toFixed(1) + 'M';
        // document.getElementById('statCoverage').textContent = `${stats.coverage}%`;
        
    } catch (error) {
        console.error('Error fetching statistics:', error);
    }
}

// Make functions available globally if needed
window.animateStatistics = animateStatistics;
