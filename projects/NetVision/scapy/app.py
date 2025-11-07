import os
import sys
import time
import threading
import argparse
from datetime import datetime
from collections import Counter, defaultdict, deque

# --- Library Imports ---
# Tries to import required libraries and provides installation instructions if they're missing.
try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, ARP, wrpcap, get_if_list
except ImportError:
    print("Scapy not installed or import failed. Install with: pip install scapy")
    raise

try:
    from flask import Flask, render_template_string, jsonify, request, send_file, Response
except ImportError:
    print("Flask not installed. Install with: pip install flask")
    raise

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("Matplotlib not installed. Install with: pip install matplotlib")
    raise

try:
    import pandas as pd
except ImportError:
    print("Pandas not installed. Install with: pip install pandas")
    raise

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except ImportError:
    # Dummy classes for colorama if it's not installed
    class Dummy:
        def __getattr__(self, name):
            return ""
    Fore = Style = Dummy()

# --- Global Configuration and State ---
app = Flask(__name__, static_folder=".")

# File names for data persistence and charts
PACKET_LOG_CSV = "packet_log.csv"
PCAP_SNAPSHOT = "captured_packets.pcap"
MATPLOTLIB_PIE = "protocol_pie.png"
MATPLOTLIB_SIZE = "size_hist.png"

# Threading lock for safe access to shared data
lock = threading.Lock()

# Capture control flags and threads
capture_running = False
capture_thread = None

# Packet counters and data structures
protocol_counter = Counter()
src_counter = Counter()
dst_counter = Counter()
port_counter = Counter()
size_bins = defaultdict(int)
packets_buffer = deque(maxlen=5000)
packets_pcap_buffer = deque(maxlen=20000)

# Real-time dashboard data series
pps_series = deque(maxlen=300)
bps_series = deque(maxlen=300)
time_labels = deque(maxlen=300)
proto_series = {
    "TCP": deque(maxlen=300),
    "UDP": deque(maxlen=300),
    "ICMP": deque(maxlen=300),
    "ARP": deque(maxlen=300),
    "Other": deque(maxlen=300)
}

# Metrics for rate calculation
prev_total_packets = 0
prev_total_bytes = 0
total_bytes = 0
start_time = time.time()

# Suspicious activity detection
suspicious_threshold = 120
suspicious_window = 10
ip_window_counter = defaultdict(int)
suspicious_ips = {}
last_window_reset = time.time()

# Packet flow tracking
flow_counter = Counter()
flow_bytes = Counter()
flow_details = {}

# Interface and BPF filter options
interface_name = None
bpf_filter = None

# --- Helper Functions ---
def human_bytes(n):
    """Converts a number of bytes into a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024.0:
            return f"{n:.2f}{unit}"
        n /= 1024.0
    return f"{n:.2f}PB"

def bin_size(n):
    """Categorizes a packet size into a predefined bin."""
    if n < 100:
        return "<100B"
    if n < 500:
        return "100-499B"
    if n < 1500:
        return "500B-1.4KB"
    return ">=1.5KB"

def flow_key(pkt):
    """Generates a unique key for a packet flow."""
    proto = "OTHER"
    sport = None
    dport = None

    if TCP in pkt:
        proto = "TCP"
        sport = getattr(pkt, "sport", None)
        dport = getattr(pkt, "dport", None)
    elif UDP in pkt:
        proto = "UDP"
        sport = getattr(pkt, "sport", None)
        dport = getattr(pkt, "dport", None)
    elif ICMP in pkt:
        proto = "ICMP"
    elif ARP in pkt:
        proto = "ARP"

    if IP in pkt:
        return (proto, pkt[IP].src, sport, pkt[IP].dst, dport)
    if ARP in pkt:
        sip = pkt[ARP].psrc if hasattr(pkt[ARP], "psrc") else "0.0.0.0"
        tip = pkt[ARP].pdst if hasattr(pkt[ARP], "pdst") else "0.0.0.0"
        return (proto, sip, None, tip, None)
    
    return (proto, "0.0.0.0", sport, "0.0.0.0", dport)

def parse_basic_info(pkt):
    """Extracts basic information from a packet."""
    src = dst = proto_name = ""
    sport = dport = None

    try:
        if IP in pkt:
            src = pkt[IP].src
            dst = pkt[IP].dst
            p = pkt[IP].proto
            if p == 6:
                proto_name = "TCP"
            elif p == 17:
                proto_name = "UDP"
            elif p == 1:
                proto_name = "ICMP"
            else:
                proto_name = str(p)
        elif ARP in pkt:
            proto_name = "ARP"
            src = pkt[ARP].psrc if hasattr(pkt[ARP], "psrc") else ""
            dst = pkt[ARP].pdst if hasattr(pkt[ARP], "pdst") else ""
        else:
            proto_name = pkt.__class__.__name__

        if TCP in pkt or UDP in pkt:
            sport = getattr(pkt, "sport", None)
            dport = getattr(pkt, "dport", None)
    except Exception:
        pass
    
    return src, dst, proto_name, sport, dport

def log_packet_csv(row):
    """Appends a packet row to the CSV log file."""
    df = pd.DataFrame([row], columns=["time", "src", "dst", "proto", "sport", "dport", "size"])
    if not os.path.exists(PACKET_LOG_CSV):
        df.to_csv(PACKET_LOG_CSV, index=False, mode="w")
    else:
        df.to_csv(PACKET_LOG_CSV, index=False, mode="a", header=False)

def save_matplotlib_charts():
    """Generates and saves Matplotlib charts as PNG files."""
    try:
        with lock:
            # Protocol Distribution Pie Chart
            labels = list(protocol_counter.keys())
            sizes = [protocol_counter[k] for k in labels]
            if not labels:
                labels = ["NoData"]
                sizes = [1]
            plt.figure(figsize=(6, 4))
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
            plt.title("Protocol Distribution")
            plt.tight_layout()
            plt.savefig(MATPLOTLIB_PIE)
            plt.close()

            # Packet Size Histogram
            bins = list(size_bins.keys())
            counts = [size_bins[b] for b in bins]
            plt.figure(figsize=(6, 4))
            plt.bar(bins, counts)
            plt.title("Packet Size Bins")
            plt.tight_layout()
            plt.savefig(MATPLOTLIB_SIZE)
            plt.close()
    except Exception:
        pass

# --- Core Logic Functions ---
def update_series_and_detection():
    """
    A background thread function that updates real-time charts data
    and performs suspicious IP detection.
    """
    global prev_total_packets, prev_total_bytes, last_window_reset
    
    while capture_running:
        with lock:
            # Update packet and byte rates
            total_packets = sum(protocol_counter.values())
            delta = total_packets - prev_total_packets
            prev_total_packets = total_packets
            pps_series.append(max(0, delta))
            
            # Use globals() to safely access variables
            prev_total_bytes_val = globals().get('prev_total_bytes', 0)
            globals()['prev_total_bytes'] = globals().get('total_bytes', 0)
            bps_series.append(max(0, globals().get('total_bytes', 0) - prev_total_bytes_val))

            time_labels.append(datetime.now().strftime("%H:%M:%S"))

            # Update protocol-specific rates
            for k in proto_series.keys():
                cur = protocol_counter.get(k, 0)
                last = globals().get('prev_proto_counts', {}).get(k, 0)
                proto_series[k].append(max(0, cur - last))
            globals()['prev_proto_counts'] = {k: protocol_counter.get(k, 0) for k in proto_series.keys()}

            # Suspicious IP detection
            now = time.time()
            if now - last_window_reset >= suspicious_window:
                for ip, cnt in list(ip_window_counter.items()):
                    if cnt >= suspicious_threshold:
                        suspicious_ips[ip] = suspicious_ips.get(ip, 0) + cnt
                ip_window_counter.clear()
                last_window_reset = now
        
        save_matplotlib_charts()
        time.sleep(1)

def packet_handler(pkt):
    """
    The main packet processing function for Scapy's sniff.
    Updates all counters and buffers with new packet information.
    """
    global total_bytes
    try:
        with lock:
            packets_pcap_buffer.append(pkt)
            ln = len(pkt)
            total_bytes += ln
            size_bins[bin_size(ln)] += 1
            src, dst, proto_name, sport, dport = parse_basic_info(pkt)

            protocol_counter[proto_name] += 1
            if src:
                src_counter[src] += 1
                ip_window_counter[src] += 1
            if dst:
                dst_counter[dst] += 1
            if sport:
                port_counter[sport] += 1
            if dport:
                port_counter[dport] += 1

            fk = flow_key(pkt)
            flow_counter[fk] += 1
            flow_bytes[fk] += ln
            flow_details[fk] = {"proto": fk[0], "src": fk[1], "sport": fk[2], "dst": fk[3], "dport": fk[4]}

            ts = datetime.now().strftime("%H:%M:%S")
            row = {"time": ts, "src": src, "dst": dst, "proto": proto_name, "sport": sport, "dport": dport, "size": ln}
            packets_buffer.append(row)

            try:
                log_packet_csv([ts, src, dst, proto_name, sport, dport, ln])
            except Exception:
                pass
    except Exception:
        pass

def capture_loop():
    """Starts the Scapy packet sniffing loop."""
    global capture_running
    kwargs = {}
    if interface_name:
        kwargs['iface'] = interface_name
    if bpf_filter:
        kwargs['filter'] = bpf_filter
    try:
        sniff(prn=packet_handler, store=False, **kwargs)
    except Exception:
        time.sleep(1)
        if capture_running:
            # Restart the loop if it fails but the capture is still active
            capture_loop()

# --- Capture Control Functions ---
def start_capture(iface=None, bpf=None):
    """Starts the packet capture threads."""
    global capture_running, capture_thread, interface_name, bpf_filter
    if iface is not None:
        interface_name = iface
    if bpf is not None:
        bpf_filter = bpf
    if capture_running:
        return False
    
    capture_running = True
    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    threading.Thread(target=update_series_and_detection, daemon=True).start()
    capture_thread.start()
    return True

def stop_capture():
    """Stops the packet capture."""
    global capture_running
    capture_running = False
    return True

# --- Flask Routes ---
@app.route("/")
def dashboard_index():
    """Serves the main HTML dashboard page."""
    html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <meta name="viewport" content="width=device-width,initial-scale=1"/>
      <title>Advanced Network Packet Analyzer - Dashboard</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"/>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <style>body{background:#0b0f14;color:#e9eef5} .card{background:#101720;border:1px solid #1e2a36}</style>
    </head>
    <body>
    <div class="container-fluid py-3">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h3>Advanced Network Packet Analyzer</h3>
        <div>
          <button class="btn btn-success btn-sm" onclick="startCapture()">Start</button>
          <button class="btn btn-danger btn-sm" onclick="stopCapture()">Stop</button>
          <a class="btn btn-info btn-sm" href="/save_pcap" target="_blank">Save PCAP</a>
          <a class="btn btn-secondary btn-sm" href="/export_csv" target="_blank">Export CSV</a>
        </div>
      </div>
      <div class="row g-3">
        <div class="col-md-4">
          <div class="card p-3">
            <h6>Protocol Distribution</h6>
            <img id="pieimg" src="/chart/pie?ts=0" style="width:100%"/>
          </div>
        </div>
        <div class="col-md-8">
          <div class="card p-3">
            <h6>Stats</h6>
            <div id="stats" class="small"></div>
            <canvas id="rateChart" height="120"></canvas>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card p-3">
            <h6>Packet Size Histogram</h6>
            <img id="sizeimg" src="/chart/size?ts=0" style="width:100%"/>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card p-3">
            <h6>Top Talkers</h6>
            <div id="toplist" class="small"></div>
          </div>
        </div>
        <div class="col-12">
          <div class="card p-3">
            <h6>Live Packet Table (last 100 entries)</h6>
            <div style="max-height:300px;overflow:auto;">
              <table class="table table-dark table-striped">
                <thead><tr><th>Time</th><th>Src</th><th>Dst</th><th>Proto</th><th>Sport</th><th>Dport</th><th>Size</th></tr></thead>
                <tbody id="pktbody"></tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="col-12">
          <div class="card p-3">
            <h6>Suspicious IPs</h6>
            <div id="susp" class="small text-danger"></div>
          </div>
        </div>
      </div>
    </div>
    <script>
      let rateChart;
      function setupCharts(){
        const ctx = document.getElementById('rateChart').getContext('2d');
        rateChart = new Chart(ctx, {
          type: 'line',
          data: { labels: [], datasets: [{ label: 'Packets/sec', data: [], borderColor: 'cyan', fill:false }, { label:'Bytes/sec', data: [], borderColor:'orange', fill:false }]},
          options: { scales: { y: { beginAtZero:true } } }
        });
      }
      function startCapture(){ fetch('/start', {method:'POST'}); }
      function stopCapture(){ fetch('/stop', {method:'POST'}); }
      function refresh(){
        fetch('/api/status').then(r=>r.json()).then(d=>{
          document.getElementById('stats').innerHTML = 
            '<b>Packets:</b> ' + d.total_packets + ' &nbsp; <b>Bytes:</b> ' + d.total_bytes_display + ' &nbsp; <b>Uptime:</b> ' + d.uptime_s + 's';
          document.getElementById('toplist').innerHTML = '<b>Top Src:</b><br>' + d.top_src.map(x=>x[0] + ' ('+x[1]+')').join('<br>');
          document.getElementById('susp').innerHTML = d.suspicious_list.map(x=>x[0] + ' => ' + x[1] + ' pkts').join('<br>');
          const tbody = document.getElementById('pktbody'); tbody.innerHTML = '';
          d.recent_packets.forEach(r=>{
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${r.time}</td><td>${r.src}</td><td>${r.dst}</td><td>${r.proto}</td><td>${r.sport||''}</td><td>${r.dport||''}</td><td>${r.size}</td>`;
            tbody.appendChild(tr);
          });
          if(rateChart){
            rateChart.data.labels = d.labels;
            rateChart.data.datasets[0].data = d.pps;
            rateChart.data.datasets[1].data = d.bps;
            rateChart.update();
          }
          document.getElementById('pieimg').src = '/chart/pie?ts=' + new Date().getTime();
          document.getElementById('sizeimg').src = '/chart/size?ts=' + new Date().getTime();
        });
      }
      setupCharts();
      refresh();
      setInterval(refresh, 2000);
    </script>
    </body>
    </html>
    """
    return html

@app.route("/chart/pie")
def chart_pie():
    """Serves the protocol distribution pie chart."""
    if os.path.exists(MATPLOTLIB_PIE):
        return send_file(MATPLOTLIB_PIE)
    else:
        save_matplotlib_charts()
        return send_file(MATPLOTLIB_PIE)

@app.route("/chart/size")
def chart_size():
    """Serves the packet size histogram."""
    if os.path.exists(MATPLOTLIB_SIZE):
        return send_file(MATPLOTLIB_SIZE)
    else:
        save_matplotlib_charts()
        return send_file(MATPLOTLIB_SIZE)

@app.route("/api/status")
def api_status():
    """Provides a JSON API for dashboard data."""
    with lock:
        uptime_s = int(time.time() - start_time)
        total_packets = sum(protocol_counter.values())
        recent_packets = list(packets_buffer)[-100:][::-1]
        top_src = src_counter.most_common(10)
        top_dst = dst_counter.most_common(10)
        labels = list(time_labels)
        pps = list(pps_series)
        bps = list(bps_series)
        suspicious_list = sorted(suspicious_ips.items(), key=lambda x: x[1], reverse=True)
        return jsonify({
            "uptime_s": uptime_s,
            "total_packets": total_packets,
            "total_bytes": total_bytes if 'total_bytes' in globals() else 0,
            "total_bytes_display": human_bytes(total_bytes if 'total_bytes' in globals() else 0),
            "recent_packets": recent_packets,
            "top_src": top_src,
            "top_dst": top_dst,
            "labels": labels,
            "pps": pps,
            "bps": bps,
            "suspicious_list": suspicious_list
        })

@app.route("/start", methods=["POST"])
def api_start():
    """API endpoint to start packet capture."""
    started = start_capture()
    return jsonify({"started": started})

@app.route("/stop", methods=["POST"])
def api_stop():
    """API endpoint to stop packet capture."""
    stopped = stop_capture()
    return jsonify({"stopped": stopped})

@app.route("/save_pcap")
def api_save_pcap():
    """API endpoint to save captured packets to a PCAP file."""
    try:
        with lock:
            wrpcap(PCAP_SNAPSHOT, list(packets_pcap_buffer))
        return send_file(PCAP_SNAPSHOT, as_attachment=True)
    except Exception as e:
        return Response("Error saving pcap: " + str(e), status=500)

@app.route("/export_csv")
def api_export_csv():
    """API endpoint to export the packet log to a CSV file."""
    if os.path.exists(PACKET_LOG_CSV):
        return send_file(PACKET_LOG_CSV, as_attachment=True)
    else:
        return Response("CSV not ready", status=404)

@app.route("/interfaces")
def api_interfaces():
    """API endpoint to list available network interfaces."""
    try:
        lst = get_if_list()
    except Exception:
        lst = []
    return jsonify({"interfaces": lst})

@app.route("/set_interface", methods=["POST"])
def api_set_interface():
    """API endpoint to set the capture interface."""
    global interface_name
    data = request.get_json(force=True)
    interface_name = data.get("iface")
    return jsonify({"ok": True, "iface": interface_name})

# --- Main Execution ---
def ensure_csv_header():
    """Ensures the CSV file exists with the correct header."""
    if not os.path.exists(PACKET_LOG_CSV):
        df = pd.DataFrame([], columns=["time", "src", "dst", "proto", "sport", "dport", "size"])
        df.to_csv(PACKET_LOG_CSV, index=False)

def start_background_threads():
    """Initializes persistent background threads."""
    t = threading.Thread(target=ensure_csv_header, daemon=True)
    t.start()
    t2 = threading.Thread(target=periodic_persist_and_maintenance, daemon=True)
    t2.start()

def periodic_persist_and_maintenance():
    """A background thread for periodic tasks like saving charts."""
    while True:
        try:
            save_matplotlib_charts()
        except Exception:
            pass
        time.sleep(5)

def parse_args():
    """Parses command-line arguments."""
    p = argparse.ArgumentParser()
    p.add_argument("--iface", help="Interface to capture on (optional)")
    p.add_argument("--filter", help="BPF filter string (optional)")
    p.add_argument("--threshold", type=int, help="Suspicious packet threshold per window", default=120)
    p.add_argument("--window", type=int, help="Window seconds for suspicious detection", default=10)
    p.add_argument("--no-web", action="store_true", help="Do not start web dashboard, run capture only")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.iface:
        interface_name = args.iface
    if args.filter:
        bpf_filter = args.filter
    suspicious_threshold = args.threshold
    suspicious_window = args.window
    
    ensure_csv_header()
    capture_running = True
    threading.Thread(target=capture_loop, daemon=True).start()
    threading.Thread(target=update_series_and_detection, daemon=True).start()
    threading.Thread(target=periodic_persist_and_maintenance, daemon=True).start()

    if args.no_web:
        print(Fore.CYAN + "Capture-only mode. Press Ctrl+C to stop." + Style.RESET_ALL)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            capture_running = False
            print("Stopping...")
            sys.exit(0)
    else:
        print(Fore.GREEN + "Starting web dashboard on http://127.0.0.1:5000" + Style.RESET_ALL)
        app.run(host="127.0.0.1", port=5000)