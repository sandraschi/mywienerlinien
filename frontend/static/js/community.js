/**
 * Community Dashboard
 * Phase 5: Social features, weather, and user-generated content
 */

class CommunityDashboard {
    constructor() {
        this.init();
    }

    async init() {
        await this.loadWeather();
        await this.loadRecentReports();
        await this.loadLineRatings();
    }

    async loadWeather() {
        try {
            // Mock weather for now (integrate with OpenWeatherMap later)
            const weather = {
                temp: 15,
                condition: 'Clear',
                icon: '☀️',
                recommendations: [
                    '✅ All transit types running normally',
                    'ℹ️ Pleasant weather for waiting at stops'
                ]
            };

            document.getElementById('weather-temp').textContent = `${weather.temp}°C`;
            document.getElementById('weather-condition').textContent = weather.condition;
            document.getElementById('weather-icon').textContent = weather.icon;

            const recContainer = document.getElementById('weather-recommendations');
            recContainer.innerHTML = weather.recommendations
                .map(rec => `<div class="weather-rec">${rec}</div>`)
                .join('');

        } catch (error) {
            console.error('[Community] Error loading weather:', error);
        }
    }

    async loadRecentReports() {
        try {
            // Mock data (integrate with API later)
            const reports = [
                {
                    id: '1',
                    type: 'delay',
                    line: 'U3',
                    station: 'Stephansplatz',
                    description: '5 minute delay on platform 1',
                    timestamp: new Date().toISOString(),
                    votes_helpful: 12
                }
            ];

            const container = document.getElementById('reports-list');
            if (!reports.length) {
                container.innerHTML = '<p class="empty-state">No recent reports</p>';
                return;
            }

            container.innerHTML = reports.map(report => `
                <div class="report-card">
                    <div class="report-header">
                        <span class="report-badge badge-${report.type}">${report.type}</span>
                        <span class="report-line">${report.line} @ ${report.station}</span>
                    </div>
                    <p class="report-description">${report.description}</p>
                    <div class="report-footer">
                        <span class="report-time">${this.formatTime(report.timestamp)}</span>
                        <button class="vote-btn" onclick="communityDashboard.voteHelpful('${report.id}', 'report')">
                            <i class="fas fa-thumbs-up"></i> ${report.votes_helpful}
                        </button>
                    </div>
                </div>
            `).join('');

        } catch (error) {
            console.error('[Community] Error loading reports:', error);
        }
    }

    async loadLineRatings() {
        try {
            const lines = ['U1', 'U2', 'U3', 'U4', 'U6'];
            const container = document.getElementById('line-ratings');

            container.innerHTML = lines.map(line => `
                <div class="rating-card">
                    <h3>${line}</h3>
                    <div class="rating-stars">
                        ${this.renderStars(4.2)}
                    </div>
                    <div class="rating-meta">4.2/5 (128 ratings)</div>
                </div>
            `).join('');

        } catch (error) {
            console.error('[Community] Error loading ratings:', error);
        }
    }

    async submitReport() {
        const type = document.getElementById('report-type').value;
        const line = document.getElementById('report-line').value;
        const station = document.getElementById('report-station').value;
        const description = document.getElementById('report-description').value;

        if (!description.trim()) {
            alert('Please enter a description');
            return;
        }

        console.log('[Community] Submitting report:', { type, line, station, description });
        
        // Mock submission
        alert('Report submitted! Thank you for helping the community.');
        
        // Clear form
        document.getElementById('report-description').value = '';
        
        // Reload reports
        await this.loadRecentReports();
    }

    async searchTips() {
        const station = document.getElementById('tips-station-search').value;
        console.log('[Community] Searching tips for:', station);
        
        const container = document.getElementById('tips-list');
        container.innerHTML = '<p class="empty-state">Enter a station name to see tips</p>';
    }

    async voteHelpful(itemId, itemType) {
        console.log('[Community] Voting helpful:', itemId, itemType);
        alert('Thank you for your feedback!');
    }

    renderStars(rating) {
        const fullStars = Math.floor(rating);
        const halfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);

        let html = '';
        for (let i = 0; i < fullStars; i++) {
            html += '<i class="fas fa-star"></i>';
        }
        if (halfStar) {
            html += '<i class="fas fa-star-half-alt"></i>';
        }
        for (let i = 0; i < emptyStars; i++) {
            html += '<i class="far fa-star"></i>';
        }
        return html;
    }

    formatTime(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffMinutes = Math.floor((now - date) / 60000);

        if (diffMinutes < 1) return 'Just now';
        if (diffMinutes < 60) return `${diffMinutes} min ago`;
        if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)} hours ago`;
        return date.toLocaleDateString('de-AT');
    }
}

// Initialize
const communityDashboard = new CommunityDashboard();
window.communityDashboard = communityDashboard;

