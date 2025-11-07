// static/js/dashboard.js
let trafficChart, attackChart;

// Helper to get data from our Flask API
async function fetchData(endpoint) {
    const response = await fetch(endpoint);
    if (!response.ok) {
        console.error(`Failed to fetch ${endpoint}: ${response.statusText}`);
        return null;
    }
    return await response.json();
}

// Initialize all charts on page load
function initCharts() {
    const trafficCtx = document.getElementById('trafficChart').getContext('2d');
    trafficChart = new Chart(trafficCtx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Threats Detected', data: [], borderColor: '#eab308', tension: 0.1 }] },
        options: { responsive: true, maintainAspectRatio: false }
    });

    const attackCtx = document.getElementById('attackChart').getContext('2d');
    attackChart = new Chart(attackCtx, {
        type: 'doughnut',
        data: { labels: [], datasets: [{ data: [], backgroundColor: ['#ef4444', '#f97316', '#3b82f6', '#10b981', '#6366f1'] }] },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

// Main function to update all dashboard elements
async function updateDashboard() {
    const stats = await fetchData("/api/stats");
    const alerts = await fetchData("/api/alerts");

    if (!stats || !alerts) return;

    // Update metric cards
    document.getElementById('totalThreats').textContent = stats.total_threats.toLocaleString();
    document.getElementById('threatsBlocked').textContent = stats.blocked_requests.toLocaleString();
    document.getElementById('activeConnections').textContent = stats.active_connections.toLocaleString();
    document.getElementById('topDomain').textContent = stats.top_domains.length > 0 ? stats.top_domains[0][0] : 'N/A';

    // Update live alerts table
    const alertsContainer = document.getElementById('liveAlerts');
    alertsContainer.innerHTML = alerts.map(alert => `
        <div class="alert-item ${alert.severity.toLowerCase()}">
            <div class="alert-header">
                <span class="alert-type">${alert.type}</span>
                <span class="alert-severity ${alert.severity.toLowerCase()}">${alert.severity}</span>
            </div>
            <div class="alert-details">
                <span>Source: ${alert.source_ip} | Time: ${alert.timestamp}</span>
            </div>
        </div>
    `).join('');

    // Update Traffic Chart
    const now = new Date().toLocaleTimeString();
    trafficChart.data.labels.push(now);
    trafficChart.data.datasets[0].data.push(stats.total_threats);
    if (trafficChart.data.labels.length > 20) { // Keep chart history clean
        trafficChart.data.labels.shift();
        trafficChart.data.datasets[0].data.shift();
    }
    trafficChart.update();

    // Update Attack Distribution Chart
    attackChart.data.labels = Object.keys(stats.attack_distribution);
    attackChart.data.datasets[0].data = Object.values(stats.attack_distribution);
    attackChart.update();
}

// Run the update cycle
document.addEventListener("DOMContentLoaded", () => {
    initCharts();
    updateDashboard(); // Initial load
    setInterval(updateDashboard, 3000); 
});