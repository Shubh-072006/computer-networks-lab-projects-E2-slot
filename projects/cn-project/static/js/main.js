document.addEventListener("DOMContentLoaded", () => {

  // Show main content after intro animation
  setTimeout(() => {
    const introEl = document.getElementById('intro');
    const mainEl = document.getElementById('main');
    if (introEl) introEl.style.display = 'none';
    if (mainEl) mainEl.classList.remove('hidden');
  }, 2500);

  const ctx = document.getElementById("trafficChart").getContext("2d");
  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Packets/sec",
          borderColor: "#00f7ff",
          backgroundColor: 'rgba(0,247,255,0.08)',
          data: [],
          fill: true,
          tension: 0.3,
          borderWidth: 2
        },
        {
          label: "Packet Size",
          borderColor: "#ff4d6d",
          backgroundColor: 'rgba(255,77,109,0.08)',
          data: [],
          fill: true,
          tension: 0.3,
          borderWidth: 2
        }
      ]
    },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      elements: {
        point: { radius: 0 }
      },
      scales: {
        x: { display: true, grid: { color: '#333' } },
        y: { beginAtZero: true, grid: { color: '#333' } }
      },
      plugins: {
        legend: { 
          labels: { color: '#fff', font: { size: 12 } }
        }
      }
    }
  });

  // Initialize mode from server
  fetch('/api/mode').then(r => r.json()).then(data => {
    updateStatus(`Mode: ${data.mode.toUpperCase()}`);
  });

  function updateStatus(text, color = '#0ff') {
    const el = document.getElementById('status');
    if (el) el.innerHTML = `<span style="color:${color}">${text}</span>`;
  }

  function formatConnection(source, dest, protocol, extra = '') {
    return `${source} → ${dest} ${protocol ? `(${protocol})` : ''} ${extra}`.trim();
  }

  function formatNumber(num) {
    return Number(num).toLocaleString();
  }

  function displayEventInfo(data) {
    // Format simulation mode data nicely
    const row = data.row;
    const pred_rf = data.preds ? data.preds.rf_pred : 'N/A';
    const pred_iso = data.preds ? data.preds.iso_pred : 'N/A';
    
    const connectionInfo = formatConnection(
      row.Source_IP,
      row.Destination_IP,
      row.Protocol
    );
    
    const txt = `
${connectionInfo}
──────────────────────────
Traffic Stats:
• Packets/sec: ${formatNumber(row.Packets_per_sec)}
• Packet Size: ${formatNumber(row.Packet_Size)} bytes
──────────────────────────
Predictions:
• Random Forest: ${pred_rf === 1 ? '⚠️ Anomaly' : '✅ Normal'}
• Isolation Forest: ${pred_iso === 1 ? '⚠️ Anomaly' : '✅ Normal'}
──────────────────────────
Analysis:
${data.reason || 'No specific reason provided'}
`;
    
    const el = document.getElementById('event-details');
    el.style.whiteSpace = 'pre-wrap';
    el.style.fontFamily = 'monospace';
    el.textContent = txt;
    
    // Update index/progress if available
    if (data.idx !== undefined) {
      const pos = `[${data.idx + 1}/∞]`;
      updateStatus(`Mode: SIMULATION ${pos}`);
    }
  }

  function displayLiveInfo(data) {
    const conns = data.top_connections || [];
    let top = "Live Network Activity:\n──────────────────────────\n";
    
    if (conns.length) {
      conns.forEach((conn, i) => {
        const procInfo = conn.proc_name ? ` - ${conn.proc_name}` : '';
        top += `${i+1}. ${formatConnection(conn.laddr, conn.raddr, '', conn.status)}${procInfo}\n`;
      });
    } else {
      top += "No active connections\n";
    }
    
    top += `\nTraffic Summary:
• Total packets/sec: ${formatNumber(data.total_packets_per_sec)}
• Total bytes/sec: ${formatNumber(data.total_bytes_per_sec)}
──────────────────────────
${data.reason ? `Analysis:\n${data.reason}` : ''}`;

    const el = document.getElementById('event-details');
    el.style.whiteSpace = 'pre-wrap';
    el.style.fontFamily = 'monospace';
    el.textContent = top;
    
  // Use explicit anomaly flag to color status if present
  const color = data.is_anomaly ? '#ff3366' : '#00ff99';
  updateStatus('Live mode active', color);
  }

  function pushRowToChart(row) {
    // Use current time as label to ensure consistent formatting
    const ts = new Date().toLocaleTimeString();
    chart.data.labels.push(ts);
    chart.data.datasets[0].data.push(row.Packets_per_sec);
    chart.data.datasets[1].data.push(row.Packet_Size);
    
    // Keep last 50 points
    if (chart.data.labels.length > 50) {
      chart.data.labels.shift();
      chart.data.datasets.forEach(ds => ds.data.shift());
    }
    chart.update('none'); // disable animation for smoother updates
  }

  let simulationTimer = null;
  let realtimeTimer = null;

  function startSimulation() {
    // Clear previous data
    resetChart();
    
    setMode('simulation');
    fetch('/api/simulate/start', {method:'POST'})
    .then(r => r.json())
    .then(() => {
      updateStatus("Simulation started...");
      if (simulationTimer) clearInterval(simulationTimer);
      // First immediate fetch to start data flow
      fetchSimNext();
      simulationTimer = setInterval(fetchSimNext, 1500);
    })
    .catch(err => {
      console.error('Failed to start simulation:', err);
      updateStatus('Simulation start failed ❌');
    });
  }

  function startRealtime() {
    // Clear previous data
    resetChart();
    
    // Ask backend to start live collection, then begin polling
    fetch('/start/live')
      .then(r => r.json())
      .then(() => {
          setMode('live');
          updateStatus("Live mode active");
          if (realtimeTimer) clearInterval(realtimeTimer);
          // First immediate fetch to prime the chart, then interval
          fetchLive();
          realtimeTimer = setInterval(fetchLive, 1000);
          // Seed recent server-side data and logs so UI reflects persisted live state
          fetch('/data')
            .then(r => r.json())
            .then(d => {
              if (d && d.logs && Array.isArray(d.logs)) {
                d.logs.forEach(log => {
                  addLogEntry({
                    timestamp: log.timestamp,
                    source: log.source || log.laddr || '',
                    destination: log.destination || log.raddr || '',
                    packets_per_sec: log.packets || log.packets_per_sec || 0,
                    packet_size: log.size || log.packet_size || 0,
                    reason: log.reason || '',
                    is_anomaly: !!log.is_anomaly || !!log.anomaly
                  });
                });
              }
              if (d && d.data && Array.isArray(d.data)) {
                d.data.forEach(pt => {
                  try {
                    const row = {
                      Packets_per_sec: pt.packets || pt.Packets_per_sec || 0,
                      Packet_Size: pt.size || pt.Packet_Size || 0
                    };
                    pushRowToChart(row);
                  } catch (e) { /* ignore malformed entries */ }
                });
              }
            })
            .catch(() => {});
        })
      .catch(err => {
        console.error('Failed to start live:', err);
        updateStatus('Live start failed ❌');
      });
  }

  function stopSimulation() {
    fetch('/api/simulate/stop', {method:'POST'});
    if (simulationTimer) {
      clearInterval(simulationTimer);
      simulationTimer = null;
    }
    if (realtimeTimer) {
      clearInterval(realtimeTimer);
      realtimeTimer = null;
    }
    updateStatus("Stopped ⏹");
  }

  function fetchSimNext() {
    fetch('/api/simulate/next')
    .then(r => r.json())
    .then(data => {
      if (data.done) {
        stopSimulation();
        updateStatus("Simulation complete ✅");
        return;
      }
      
      // Update chart with new data
      pushRowToChart(data.row);
      displayEventInfo(data);
      
      // Determine anomaly from preds if provided
      const isAnom = data.preds && (data.preds.rf_pred === 1 || data.preds.iso_pred === 1);
      const timestamp = data.row.Timestamp || new Date().toISOString();
      addLogEntry({
        timestamp: timestamp,
        source: data.row.Source_IP || '',
        destination: data.row.Destination_IP || '',
        packets_per_sec: data.row.Packets_per_sec || 0,
        packet_size: data.row.Packet_Size || 0,
        reason: data.reason || `Traffic: ${data.row.Packets_per_sec} packets/sec`,
        is_anomaly: !!isAnom
      });
      
      // Update status with simulation progress
      if (data.idx !== undefined) {
        updateStatus(`Simulating... [${data.idx + 1}]`);
      }
    })
    .catch(err => {
      console.error('Simulation error:', err);
      stopSimulation();
      updateStatus("Simulation error ❌");
    });
  }

  function fetchLive() {
    fetch('/api/live')
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        updateStatus("Live error ❌");
        console.error(data);
        return;
      }

      const pps = data.total_packets_per_sec ||
                 (data.packets_sent_per_sec + data.packets_recv_per_sec);
      const size = Math.round(
        (data.total_bytes_per_sec || 0) /
        Math.max(1, pps)
      );
      
      const row = {
        Timestamp: data.timestamp,
        Source_IP: data.top_connections.length ? data.top_connections[0].laddr : 'local',
        Destination_IP: data.top_connections.length ? data.top_connections[0].raddr : '',
        Protocol: data.top_connections.length ? (data.top_connections[0].proc_name || '') : '',
        Packets_per_sec: pps,
        Packet_Size: size,
        Connection_Duration: 0,
        Is_Anomaly: 0
      };

      pushRowToChart(row);
      displayLiveInfo(data);

      // Always attempt to log live data point for continuity
      const src = data.top_connections && data.top_connections.length ? data.top_connections[0].laddr : 'local';
      const dst = data.top_connections && data.top_connections.length ? data.top_connections[0].raddr : '';
      const timestamp = data.timestamp || new Date().toISOString();
      
      // If server signals anomaly or traffic exceeds thresholds, log with anomaly details
      const humanReason = data.reason || (data.is_anomaly ? 
        (pps > 800 ? 
          'High packet rate detected — possible network scan or DDoS attempt.' :
          size > 500000 ? 
            'Unusually large packets detected — possible data exfiltration.' :
            'Anomalous network behavior detected.'
        ) : 'Normal traffic');

      addLogEntry({
        timestamp: timestamp,
        source: src,
        destination: dst,
        packets_per_sec: pps,
        packet_size: size,
        reason: humanReason,
        is_anomaly: data.is_anomaly || false
      });
    })
    .catch(err => {
      console.error(err);
      updateStatus("Live fetch error ❌");
    });
  }

  function setMode(mode) {
    fetch('/api/mode', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({mode})
    })
    .then(r => r.json())
    .then(d => console.log('mode set:', d));
  }

  function downloadPredictions() {
    window.location.href = '/api/download';
  }

  function downloadReport() {
    window.location.href = '/api/report';
  }

  function generateDataset() {
    updateStatus("Generating dataset...");
    fetch('/generate')
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          updateStatus('Dataset generation failed ❌');
        } else {
          updateStatus(`Dataset generated: ${data.rows} rows ✅`);
        }
      })
      .catch(() => updateStatus('Dataset generation failed ❌'));
  }

  function trainModels() {
    updateStatus("Training models...");
    fetch('/train')
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          updateStatus('Training failed ❌');
        } else {
          updateStatus(`Model trained — accuracy ${data.accuracy} ✅`);
        }
      })
      .catch(() => updateStatus('Training failed ❌'));
  }

  // Chart reset functionality
  function resetChart() {
    chart.data.labels = [];
    chart.data.datasets.forEach(ds => ds.data = []);
    chart.update();
    document.getElementById('event-details').textContent = '';
    clearLogs();
    updateStatus("Ready to start ▶️");
  }

  // Log management functions
  let logs = [];

      function addLogEntry(entry) {
    if (!entry || !entry.timestamp) return;
    
    // Deduplicate logs based on timestamp to prevent duplicates from live mode
    if (logs.length > 0 && logs[logs.length - 1].timestamp === entry.timestamp) {
      return;
    }
    
    logs.push(entry);
    
    const logContainer = document.getElementById('log-container');
    if (!logContainer) return;

    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry' + (entry.is_anomaly ? ' anomaly' : '');
    
    const timestamp = new Date(entry.timestamp).toLocaleTimeString();
    const src = entry.source || entry.Source_IP || '';
    const dst = entry.destination || entry.Destination_IP || '';
    const packets = entry.packets_per_sec || entry.Packets_per_sec || entry.packets || 0;
    const size = entry.packet_size || entry.Packet_Size || entry.size || 0;

    logEntry.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span class="log-time">${timestamp}</span>
        <span style="font-size:12px;color:#8e9eab">${src} → ${dst}</span>
      </div>
      <div style="margin-top:6px;">${entry.reason || 'Normal traffic'}</div>
      <div style="margin-top:4px;font-size:12px;color:#8e9eab">Packets/sec: ${packets} • Size: ${size}</div>
    `;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    // Keep only last 100 entries in DOM
    while (logContainer.children.length > 100) {
      logContainer.removeChild(logContainer.firstChild);
    }

    // Update event details and explanation
    document.getElementById('event-details').textContent = entry.reason || '';
    if (entry.is_anomaly) {
      document.getElementById('explanation').innerHTML = `
        <div class="explanation-alert">⚠️ Anomaly Detected</div>
        <p>${entry.reason || 'Unusual network behavior detected'}</p>
        <p class="explanation-detail">Time: ${timestamp}</p>
      `;
    }
  }  function clearLogs() {
    logs = [];
    const logContainer = document.getElementById('log-container');
    if (logContainer) {
      logContainer.innerHTML = '';
    }
  }

  function downloadLogs() {
    // Prefer server-side export which contains canonical logs for the session
    window.location.href = '/api/download';
  }

  // Wire up buttons (guarded in case some buttons were removed)
  const el = id => document.getElementById(id);
  if (el('generate-btn')) el('generate-btn').onclick = generateDataset;
  if (el('train-btn')) el('train-btn').onclick = trainModels;
  if (el('start-sim-btn')) el('start-sim-btn').onclick = startSimulation;
  if (el('start-live-btn')) el('start-live-btn').onclick = startRealtime;
  if (el('stop-btn')) el('stop-btn').onclick = stopSimulation;
  if (el('reset-chart-btn')) el('reset-chart-btn').onclick = resetChart;
  if (el('download-pred-btn')) el('download-pred-btn').onclick = downloadPredictions;
  if (el('download-report-btn')) el('download-report-btn').onclick = downloadReport;
  // Download logs should call the backend CSV exporter
  if (el('download-logs-btn')) el('download-logs-btn').onclick = downloadLogs;
});
