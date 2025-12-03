/**
 * Analytics Dashboard
 * Phase 3C: Historical data visualization and ML predictions
 */

class AnalyticsDashboard {
    constructor() {
        this.charts = {};
        this.init();
    }

    async init() {
        await this.loadSummary();
        await this.loadReliability();
        await this.loadHeatmap('U1');
        await this.loadPredictions();
        this.setupEventListeners();
    }

    setupEventListeners() {
        const heatmapSelect = document.getElementById('heatmap-line-select');
        if (heatmapSelect) {
            heatmapSelect.addEventListener('change', (e) => {
                this.loadHeatmap(e.target.value);
            });
        }
    }

    async loadSummary() {
        try {
            const response = await fetch('/api/analytics/summary');
            const data = await response.json();

            document.getElementById('data-count').textContent = 
                (data.data_collection.vehicle_snapshots + data.data_collection.journey_records).toLocaleString();
            document.getElementById('models-count').textContent = data.ml_models.models_loaded;
            document.getElementById('reliable-line').textContent = data.reliability.most_reliable || 'N/A';
            document.getElementById('unreliable-line').textContent = data.reliability.least_reliable || 'N/A';

        } catch (error) {
            console.error('[Analytics] Error loading summary:', error);
        }
    }

    async loadReliability() {
        try {
            const response = await fetch('/api/analytics/line-reliability?days=30');
            const data = await response.json();

            const lines = Object.keys(data.stats);
            const scores = lines.map(line => data.stats[line].reliability_score);
            const avgDelays = lines.map(line => data.stats[line].average_delay);

            const ctx = document.getElementById('reliability-chart');
            this.charts.reliability = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: lines,
                    datasets: [{
                        label: 'Reliability Score',
                        data: scores,
                        backgroundColor: 'rgba(76, 175, 80, 0.7)',
                        borderColor: 'rgba(76, 175, 80, 1)',
                        borderWidth: 1
                    }, {
                        label: 'Average Delay (min)',
                        data: avgDelays,
                        backgroundColor: 'rgba(227, 6, 19, 0.7)',
                        borderColor: 'rgba(227, 6, 19, 1)',
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Reliability Score' }
                        },
                        y1: {
                            beginAtZero: true,
                            position: 'right',
                            title: { display: true, text: 'Average Delay (min)' }
                        }
                    }
                }
            });

        } catch (error) {
            console.error('[Analytics] Error loading reliability:', error);
        }
    }

    async loadHeatmap(line) {
        try {
            const response = await fetch(`/api/analytics/heatmap?line=${line}&days=30`);
            const data = await response.json();

            const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            const hours = Array.from({length: 24}, (_, i) => `${i}:00`);

            // Flatten heatmap data for Chart.js
            const chartData = [];
            for (let day = 0; day < 7; day++) {
                for (let hour = 0; hour < 24; hour++) {
                    chartData.push({
                        x: hour,
                        y: day,
                        v: data.heatmap[day][hour]
                    });
                }
            }

            const ctx = document.getElementById('heatmap-chart');
            if (this.charts.heatmap) {
                this.charts.heatmap.destroy();
            }

            this.charts.heatmap = new Chart(ctx, {
                type: 'bubble',
                data: {
                    datasets: [{
                        label: 'Average Delay (minutes)',
                        data: chartData.map(d => ({ x: d.x, y: d.y, r: Math.max(3, d.v * 2) })),
                        backgroundColor: chartData.map(d => this.getHeatColor(d.v)),
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: {
                            type: 'linear',
                            min: 0,
                            max: 23,
                            ticks: { stepSize: 1 },
                            title: { display: true, text: 'Hour of Day' }
                        },
                        y: {
                            type: 'linear',
                            min: 0,
                            max: 6,
                            ticks: {
                                stepSize: 1,
                                callback: (value) => days[value]
                            },
                            title: { display: true, text: 'Day of Week' }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const point = chartData[context.dataIndex];
                                    return `${point.v.toFixed(1)} min delay`;
                                }
                            }
                        }
                    }
                }
            });

        } catch (error) {
            console.error('[Analytics] Error loading heatmap:', error);
        }
    }

    getHeatColor(delay) {
        if (delay < 2) return 'rgba(76, 175, 80, 0.7)';   // Green
        if (delay < 5) return 'rgba(255, 193, 7, 0.7)';   // Yellow
        if (delay < 8) return 'rgba(255, 152, 0, 0.7)';   // Orange
        return 'rgba(244, 67, 54, 0.7)';                   // Red
    }

    async loadPredictions() {
        try {
            const lines = ['U1', 'U2', 'U3', 'U4', 'U6'];
            const container = document.getElementById('predictions-list');

            const predictions = await Promise.all(
                lines.map(line => this.fetchPrediction(line))
            );

            container.innerHTML = predictions.map(pred => {
                if (!pred) return '';
                
                const severity = this.getDelaySeverity(pred.predicted_delay_minutes);
                
                return `
                    <div class="prediction-card ${severity}">
                        <h3>${pred.line}</h3>
                        <div class="prediction-value">${pred.predicted_delay_minutes.toFixed(1)} min</div>
                        <div class="prediction-label">Predicted Delay</div>
                        <div class="prediction-confidence">
                            Confidence: ${(pred.confidence * 100).toFixed(0)}%
                        </div>
                    </div>
                `;
            }).join('');

        } catch (error) {
            console.error('[Analytics] Error loading predictions:', error);
        }
    }

    async fetchPrediction(line) {
        try {
            const response = await fetch(`/api/analytics/predictions/${line}`);
            if (!response.ok) return null;
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    getDelaySeverity(delay) {
        if (delay < 2) return 'severity-good';
        if (delay < 5) return 'severity-moderate';
        return 'severity-severe';
    }
}

// Initialize dashboard
const dashboard = new AnalyticsDashboard();
window.analyticsDashboard = dashboard;

