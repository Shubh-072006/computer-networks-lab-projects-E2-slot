// Global simulation state
let currentSlide = 1;
let simulationInterval;
let trafficInterval;
let packetRate = 10;
let networkCapacity = 15;
let sentPackets = 0;
let deliveredPackets = 0;
let droppedPackets = 0;
let currentProtocol = 'tcp';
let isSimulationRunning = false;
let tcpWindowSize = 1;
let activePackets = 0;
let trafficDensity = 3;

// Chart data
let throughputChart, lossChart;
let chartData = {
    time: [],
    throughput: [],
    loss: []
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    initializeEventListeners();
    showSlide(1);
});

// Event listeners
function initializeEventListeners() {
    document.getElementById('packetRate').addEventListener('input', function(e) {
        packetRate = parseInt(e.target.value);
        document.getElementById('packetRateValue').textContent = packetRate;
        updateProtocolDisplays();
    });

    document.getElementById('networkCapacity').addEventListener('input', function(e) {
        networkCapacity = parseInt(e.target.value);
        document.getElementById('capacityValue').textContent = networkCapacity;
    });
}

// Navigation
function showSlide(slideNumber) {
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.querySelectorAll('.nav-link')[slideNumber - 1].classList.add('active');
    
    // Update slides
    document.querySelectorAll('.slide').forEach(slide => slide.classList.remove('active'));
    document.getElementById(`slide${slideNumber}`).classList.add('active');
    currentSlide = slideNumber;
    
    // Stop simulations when changing slides
    if (slideNumber !== 2 && slideNumber !== 3) {
        stopTraffic();
        stopSimulation();
    }
    
    // Initialize charts when reaching analytics
    if (slideNumber === 5) {
        updateCharts();
        updateAnalytics();
    }
}

// Traffic Simulation (Right to Left)
function startTraffic() {
    resetTraffic();
    trafficInterval = setInterval(() => generateTraffic(), 800);
}

function increaseTraffic() {
    trafficDensity = 8;
    document.getElementById('trafficDensity').textContent = 'High';
    document.getElementById('trafficDensity').style.color = '#ef4444';
}

function resetTraffic() {
    clearInterval(trafficInterval);
    trafficDensity = 3;
    activePackets = 0;
    document.querySelectorAll('.car').forEach(car => car.remove());
    document.getElementById('activePackets').textContent = '0';
    document.getElementById('trafficDensity').textContent = 'Low';
    document.getElementById('trafficDensity').style.color = '#10b981';
}

function generateTraffic() {
    const lanes = ['fastLane', 'slowLane'];
    
    for (let i = 0; i < trafficDensity; i++) {
        const lane = lanes[Math.floor(Math.random() * lanes.length)];
        createCar(lane);
    }
}

function createCar(laneId) {
    const lane = document.getElementById(laneId);
    const car = document.createElement('div');
    car.className = `car ${laneId === 'fastLane' ? 'fast' : 'slow'}`;
    
    const carTypes = ['🚗', '🚙', '🚐', '🚛'];
    const carType = carTypes[Math.floor(Math.random() * carTypes.length)];
    car.textContent = carType;
    
    car.style.animationDelay = `${Math.random() * 2}s`;
    
    // Random speed variation
    const speedVariation = 0.8 + Math.random() * 0.4;
    if (laneId === 'fastLane') {
        car.style.animationDuration = `${3 / speedVariation}s`;
    } else {
        car.style.animationDuration = `${5 / speedVariation}s`;
    }
    
    lane.appendChild(car);
    activePackets++;
    document.getElementById('activePackets').textContent = activePackets;
    
    setTimeout(() => {
        if (car.parentNode) {
            car.parentNode.removeChild(car);
            activePackets--;
            document.getElementById('activePackets').textContent = activePackets;
        }
    }, 10000);
}

function stopTraffic() {
    clearInterval(trafficInterval);
}

// Network Simulation
function startSimulation() {
    if (isSimulationRunning) return;
    
    isSimulationRunning = true;
    resetNetworkStats();
    
    simulationInterval = setInterval(() => {
        simulateNetworkTraffic();
        updateNetworkVisualization();
        updateCharts();
        updateStats();
        updateProtocolAnalysis();
    }, 1000);
}

function pauseSimulation() {
    isSimulationRunning = false;
    clearInterval(simulationInterval);
}

function resetSimulation() {
    pauseSimulation();
    resetNetworkStats();
    updateStats();
    resetCharts();
    resetNetworkVisualization();
    updateProtocolAnalysis();
}

function resetNetworkStats() {
    sentPackets = 0;
    deliveredPackets = 0;
    droppedPackets = 0;
    tcpWindowSize = 1;
    chartData = { time: [], throughput: [], loss: [] };
}

function resetNetworkVisualization() {
    document.getElementById('packetContainer').innerHTML = '';
    document.querySelectorAll('.link-fill').forEach(link => {
        link.style.width = '0%';
        link.style.background = '#2563eb';
    });
    document.getElementById('networkStatus').textContent = 'Normal';
    document.getElementById('networkStatus').style.color = '#10b981';
    document.getElementById('utilization').textContent = '0%';
}

function simulateNetworkTraffic() {
    const currentTime = new Date().toLocaleTimeString();
    
    // Determine sending rate based on protocol
    let sendingRate = currentProtocol === 'tcp' ? 
        Math.min(packetRate, tcpWindowSize) : packetRate;
    
    sentPackets += sendingRate;
    
    // Calculate network capacity and congestion
    const overload = Math.max(0, sendingRate - networkCapacity);
    
    if (overload > 0) {
        // Congestion occurs
        const dropRate = overload / sendingRate;
        const delivered = Math.floor(sendingRate * (1 - dropRate));
        const dropped = sendingRate - delivered;
        
        deliveredPackets += delivered;
        droppedPackets += dropped;
        
        // TCP congestion control
        if (currentProtocol === 'tcp') {
            tcpWindowSize = Math.max(1, Math.floor(tcpWindowSize * 0.7));
        }
    } else {
        // Normal operation
        deliveredPackets += sendingRate;
        
        // TCP slow start
        if (currentProtocol === 'tcp') {
            tcpWindowSize = Math.min(packetRate, tcpWindowSize + 1);
        }
    }
    
    // Animate packets
    animatePackets(sendingRate);
    
    // Update chart data
    chartData.time.push(currentTime);
    chartData.throughput.push(deliveredPackets - (chartData.throughput[chartData.throughput.length - 1] || 0));
    chartData.loss.push(droppedPackets);
    
    // Keep data manageable
    if (chartData.time.length > 8) {
        chartData.time.shift();
        chartData.throughput.shift();
        chartData.loss.shift();
    }
}

function animatePackets(packetCount) {
    const container = document.getElementById('packetContainer');
    
    for (let i = 0; i < packetCount; i++) {
        const packet = document.createElement('div');
        packet.className = 'packet';
        packet.style.top = `${100 + Math.random() * 200}px`;
        packet.style.animationDuration = `${2 + Math.random() * 2}s`;
        container.appendChild(packet);
        
        setTimeout(() => {
            if (packet.parentNode) packet.parentNode.removeChild(packet);
        }, 4000);
    }
}

function updateNetworkVisualization() {
    const utilization = (packetRate / networkCapacity) * 100;
    
    // Update link colors and widths
    document.querySelectorAll('.link-fill').forEach(link => {
        link.style.width = `${utilization}%`;
        
        if (utilization < 60) {
            link.style.background = '#10b981';
        } else if (utilization < 85) {
            link.style.background = '#f59e0b';
        } else {
            link.style.background = '#ef4444';
        }
    });
    
    // Update status
    const statusElement = document.getElementById('networkStatus');
    if (utilization < 60) {
        statusElement.textContent = 'Normal';
        statusElement.style.color = '#10b981';
    } else if (utilization < 85) {
        statusElement.textContent = 'Warning';
        statusElement.style.color = '#f59e0b';
    } else {
        statusElement.textContent = 'Congested';
        statusElement.style.color = '#ef4444';
    }
    
    document.getElementById('utilization').textContent = `${Math.round(utilization)}%`;
    document.getElementById('currentProtocol').textContent = currentProtocol.toUpperCase();
}

// Protocol Functions
function setProtocol(protocol) {
    currentProtocol = protocol;
    
    // Update tabs
    document.querySelectorAll('.protocol-tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update displays
    updateProtocolDisplays();
    
    if (isSimulationRunning) {
        resetSimulation();
    }
    
    updateProtocolAnalysis();
}

function updateProtocolDisplays() {
    // TCP Window
    const tcpWindow = document.getElementById('tcpWindow');
    const tcpWindowSizeElement = document.getElementById('tcpWindowSize');
    const windowPercentage = (tcpWindowSize / packetRate) * 100;
    
    tcpWindow.style.width = `${windowPercentage}%`;
    tcpWindowSizeElement.textContent = tcpWindowSize;
    
    // Current rates
    const currentRate = currentProtocol === 'tcp' ? Math.min(packetRate, tcpWindowSize) : packetRate;
    document.getElementById('tcpCurrentRate').textContent = currentProtocol === 'tcp' ? currentRate : '0';
    document.getElementById('udpCurrentRate').textContent = currentProtocol === 'udp' ? packetRate : '0';
    
    // UDP Rate
    document.getElementById('udpRateValue').textContent = packetRate;
    
    // Loss percentages
    const tcpLoss = sentPackets > 0 ? ((droppedPackets / sentPackets) * 100).toFixed(1) : 0;
    const udpLoss = currentProtocol === 'udp' && sentPackets > 0 ? ((droppedPackets / sentPackets) * 100).toFixed(1) : 0;
    
    document.getElementById('tcpLoss').textContent = `${tcpLoss}%`;
    document.getElementById('udpLoss').textContent = `${udpLoss}%`;
    
    // TCP behavior
    const utilization = (packetRate / networkCapacity) * 100;
    let behavior = 'Normal';
    if (utilization > 85) behavior = 'Reducing Rate';
    else if (utilization > 70) behavior = 'Monitoring';
    else if (tcpWindowSize < packetRate) behavior = 'Increasing Rate';
    
    document.getElementById('tcpBehavior').textContent = behavior;
}

function updateProtocolAnalysis() {
    const analysisElement = document.getElementById('protocolAnalysis');
    const utilization = (packetRate / networkCapacity) * 100;
    const efficiency = sentPackets > 0 ? ((deliveredPackets / sentPackets) * 100).toFixed(1) : 100;
    
    if (!isSimulationRunning) {
        analysisElement.innerHTML = '<p>Start simulation to see real-time protocol behavior analysis...</p>';
        return;
    }
    
    if (currentProtocol === 'tcp') {
        analysisElement.innerHTML = `
            <p><strong>TCP Adaptive Behavior:</strong></p>
            <p>• Current window size: ${tcpWindowSize} packets</p>
            <p>• Network utilization: ${Math.round(utilization)}%</p>
            <p>• Packet delivery efficiency: ${efficiency}%</p>
            <p>• Behavior: ${utilization > 85 ? 'Congestion avoidance active' : 'Normal operation'}</p>
        `;
    } else {
        analysisElement.innerHTML = `
            <p><strong>UDP Constant Rate Behavior:</strong></p>
            <p>• Fixed transmission rate: ${packetRate} packets/sec</p>
            <p>• Network utilization: ${Math.round(utilization)}%</p>
            <p>• Packet delivery efficiency: ${efficiency}%</p>
            <p>• Behavior: ${utilization > 100 ? 'High packet loss occurring' : 'Constant rate maintained'}</p>
        `;
    }
}

// Charts
function initializeCharts() {
    const throughputCtx = document.getElementById('throughputChart').getContext('2d');
    const lossCtx = document.getElementById('lossChart').getContext('2d');

    throughputChart = new Chart(throughputCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Packets Delivered/sec',
                data: [],
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true } },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Packets/sec' } },
                x: { title: { display: true, text: 'Time' } }
            }
        }
    });

    lossChart = new Chart(lossCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Packets Lost',
                data: [],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 54, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true } },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Packets Lost' } },
                x: { title: { display: true, text: 'Time' } }
            }
        }
    });
}

function updateCharts() {
    if (throughputChart) {
        throughputChart.data.labels = chartData.time;
        throughputChart.data.datasets[0].data = chartData.throughput;
        throughputChart.update('none');
    }
    
    if (lossChart) {
        lossChart.data.labels = chartData.time;
        lossChart.data.datasets[0].data = chartData.loss;
        lossChart.update('none');
    }
}

function resetCharts() {
    chartData = { time: [], throughput: [], loss: [] };
    updateCharts();
}

// Stats and Analytics
function updateStats() {
    document.getElementById('sentCount').textContent = sentPackets;
    document.getElementById('deliveredCount').textContent = deliveredPackets;
    document.getElementById('droppedCount').textContent = droppedPackets;
    
    const efficiency = sentPackets > 0 ? ((deliveredPackets / sentPackets) * 100).toFixed(1) : 100;
    document.getElementById('efficiency').textContent = `${efficiency}%`;
    
    updateProtocolDisplays();
}

function updateAnalytics() {
    document.getElementById('totalSent').textContent = sentPackets;
    document.getElementById('totalDelivered').textContent = deliveredPackets;
    document.getElementById('totalDropped').textContent = droppedPackets;
    
    const efficiency = sentPackets > 0 ? ((deliveredPackets / sentPackets) * 100).toFixed(1) : 100;
    document.getElementById('avgEfficiency').textContent = `${efficiency}%`;
    
    // Update insights
    const insightsElement = document.getElementById('liveInsights');
    const utilization = (packetRate / networkCapacity) * 100;
    
    let insights = [];
    if (utilization < 60) {
        insights.push('• Network operating at optimal capacity');
        insights.push('• No congestion detected');
    } else if (utilization < 85) {
        insights.push('• Network approaching capacity limits');
        insights.push('• Monitor for potential congestion');
    } else {
        insights.push('• Network congestion detected');
        insights.push('• Packet loss occurring');
    }
    
    insights.push(`• Current protocol: ${currentProtocol.toUpperCase()}`);
    insights.push(`• Delivery efficiency: ${efficiency}%`);
    
    insightsElement.innerHTML = insights.map(insight => `<p>${insight}</p>`).join('');
}