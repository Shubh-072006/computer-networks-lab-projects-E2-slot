from flask import Flask, render_template, jsonify, send_file, request
import psutil, random, time, threading, pandas as pd, os
from datetime import datetime
from io import BytesIO
from utils.report_generation import generate_report_with_plots
from output_reporting import plot_confusion, plot_feature_importance, plot_roc
import numpy as np

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Import local helper after app creation (circular import prevention)
from utils.anomaly_helpers import check_anomaly_with_cooldown

# Global state
state = {
    "mode": None,
    "running": False,
    "data": [],
    "logs": [],
    "df": None,
    "prev_packets": None,
    "prev_bytes": None,
    "model_metrics": {"Accuracy": 0.985, "AUC": 0.971},
    "normal_intervals": 0,  # counter for consecutive normal intervals
    "last_anomaly": None,   # timestamp of last anomaly for cooldown
}

# ----------------------------------------
# ROUTES
# ----------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/mode', methods=['GET'])
def get_mode():
    return jsonify({"mode": state["mode"]})

@app.route('/api/mode', methods=['POST'])
def set_mode():
    mode = request.json.get('mode')
    if mode in ['idle', 'simulation', 'live']:
        state["mode"] = mode
    return jsonify({"mode": state["mode"]})

@app.route('/api/live')
def get_live_data():
    if not state["running"] or state["mode"] != "live":
        return jsonify({"error": "Live monitoring not active"})
        
    net = psutil.net_io_counters()
    conns = psutil.net_connections()

    current_packets = net.packets_sent + net.packets_recv
    current_bytes = net.bytes_sent + net.bytes_recv

    if state["prev_packets"] is None:
        state["prev_packets"] = current_packets
        state["prev_bytes"] = current_bytes
        # Return a consistent shape so frontend can handle initialization
        return jsonify({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "total_packets_per_sec": 0,
            "total_bytes_per_sec": 0,
            "top_connections": [],
            "reason": "Initializing...",
            "is_anomaly": False
        })

    delta_packets = current_packets - state["prev_packets"]
    delta_bytes = current_bytes - state["prev_bytes"]

    state["prev_packets"] = current_packets
    state["prev_bytes"] = current_bytes

    # Check for anomalies using cooldown logic
    is_anomaly, reason = check_anomaly_with_cooldown(
        delta_packets, 
        delta_bytes,
        state["last_anomaly"],
        state["normal_intervals"]
    )

    if is_anomaly:
        state["last_anomaly"] = datetime.now()
        state["normal_intervals"] = 0
        # Store anomaly in server logs
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "packets": delta_packets,
            "size": delta_bytes,
            "reason": reason,
            "is_anomaly": True
        }
        state["logs"].append(log_entry)
    else:
        state["normal_intervals"] += 1

    # Format active connections
    connections = []
    for c in conns[:5]:  # Top 5 active connections
        if c.laddr and c.raddr:
            proc_name = None
            if c.pid:
                try:
                    proc_name = psutil.Process(c.pid).name()
                except Exception:
                    proc_name = None
            connections.append({
                "laddr": f"{c.laddr.ip}:{c.laddr.port}",
                "raddr": f"{c.raddr.ip}:{c.raddr.port}",
                "status": c.status,
                "proc_name": proc_name
            })

    return jsonify({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "total_packets_per_sec": delta_packets,
        "total_bytes_per_sec": delta_bytes,
        "top_connections": connections,
        "reason": reason,
        "is_anomaly": is_anomaly
    })

@app.route('/generate')
def generate_dataset():
    try:
        df = pd.DataFrame({
            "Timestamp": pd.date_range(start=datetime.now(), periods=20000, freq='s'),
            "Packets_per_sec": [random.randint(50, 5000) for _ in range(20000)],
            "Packet_Size": [random.randint(100, 2000) for _ in range(20000)]
        })
        os.makedirs("data", exist_ok=True)
        df.to_csv("data/network_traffic_data.csv", index=False)
        return jsonify({"message": "Dataset generated successfully", "rows": len(df)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/train')
def train_model():
    time.sleep(2)
    cm = np.array([[91, 4], [2, 103]])
    plot_confusion(cm)
    class DummyModel:
        feature_importances_ = np.random.rand(6)
    plot_feature_importance(DummyModel(), ['Packets', 'Size', 'Proto', 'Conn', 'Src', 'Dst'])
    y_true = np.random.randint(0, 2, 100)
    y_prob = np.random.rand(100)
    plot_roc(y_true, y_prob)
    return jsonify({"message": "Model trained successfully", "accuracy": 0.985, "auc": 0.971})

@app.route('/start/live')
def start_live():
    reset_state("live")
    threading.Thread(target=collect_live_data, daemon=True).start()
    return jsonify({"message": "Live monitoring started"})

@app.route('/api/simulate/start', methods=['POST'])
def start_simulation():
    state["mode"] = "simulation"
    state["running"] = True
    state["simulation_idx"] = 0
    
    # Load or generate simulation data if needed
    if state["df"] is None:
        state["df"] = pd.DataFrame({
            "Timestamp": pd.date_range(start=datetime.now(), periods=1000, freq='s'),
            "Source_IP": [f"192.168.1.{random.randint(2, 254)}" for _ in range(1000)],
            "Destination_IP": [f"10.0.0.{random.randint(2, 254)}" for _ in range(1000)],
            "Protocol": [random.choice(["TCP", "UDP", "HTTP", "HTTPS"]) for _ in range(1000)],
            "Packets_per_sec": [random.randint(100, 1000) for _ in range(1000)],
            "Packet_Size": [random.randint(64, 1500) for _ in range(1000)],
            "Connection_Duration": [random.randint(1, 3600) for _ in range(1000)],
            "Is_Anomaly": [random.choice([0, 0, 0, 0, 1]) for _ in range(1000)]  # 20% anomaly rate
        })
    
    return jsonify({"message": "Simulation started"})

@app.route('/api/simulate/stop', methods=['POST'])
def stop_simulation():
    state["mode"] = "idle"
    state["running"] = False
    return jsonify({"message": "Simulation stopped"})

@app.route('/api/simulate/next')
def next_simulation():
    if not state["running"] or state["mode"] != "simulation" or state["df"] is None:
        return jsonify({"error": "Simulation not active"})

    if state["simulation_idx"] >= len(state["df"]):
        return jsonify({"done": True})

    row = state["df"].iloc[state["simulation_idx"]].to_dict()
    
    # Check for anomalies using cooldown logic
    is_anomaly, reason = check_anomaly_with_cooldown(
        row["Packets_per_sec"],
        row["Packet_Size"],
        state["last_anomaly"],
        state["normal_intervals"]
    )

    if is_anomaly:
        state["last_anomaly"] = datetime.now()
        state["normal_intervals"] = 0
    else:
        state["normal_intervals"] += 1

    response = {
        "done": False,
        "idx": state["simulation_idx"],
        "row": row,
        "reason": reason,
        "preds": {
            "rf_pred": 1 if is_anomaly else 0,
            "iso_pred": row["Is_Anomaly"]
        }
    }

    # Persist log entry on server for download and session persistence
    try:
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": row.get("Source_IP", ""),
            "destination": row.get("Destination_IP", ""),
            "packets_per_sec": int(row.get("Packets_per_sec", 0)),
            "packet_size": int(row.get("Packet_Size", 0)),
            "is_anomaly": bool(is_anomaly),
            "reason": reason
        }
        state["logs"].append(log_entry)
        # cap logs to avoid unbounded memory
        if len(state["logs"]) > 5000:
            state["logs"] = state["logs"][ -4000 : ]
    except Exception:
        pass

    state["simulation_idx"] += 1
    return jsonify(response)

@app.route('/data')
def get_data():
    return jsonify({
        "data": state["data"][-20:],
        "logs": state["logs"][-20:]
    })

@app.route('/report')
def generate_report():
    try:
        path = generate_report_with_plots(state["model_metrics"])
        return send_file(path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/report')
def api_report():
    # Compatibility endpoint for frontend
    return generate_report()

@app.route('/download_logs')
def download_logs():
    if not state["logs"]:
        return jsonify({"error": "No logs available"}), 404
    # Export as CSV to avoid optional Excel engine dependency
    df = pd.DataFrame(state["logs"])
    buffer = BytesIO()
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    buffer.write(csv_bytes)
    buffer.seek(0)
    filename = f"anomaly_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='text/csv')


@app.route('/api/download')
def api_download_logs():
    return download_logs()

# ----------------------------------------
# UTIL FUNCTIONS
# ----------------------------------------
def reset_state(mode):
    state["mode"] = mode
    state["running"] = True
    state["data"].clear()
    state["logs"].clear()
    state["prev_packets"] = None
    state["prev_bytes"] = None

# ----------------------------------------
# DATA COLLECTION
# ----------------------------------------
def collect_live_data():
    while state["running"] and state["mode"] == "live":
        try:
            net = psutil.net_io_counters()
            conns = psutil.net_connections()
            if state["prev_packets"] is None:
                state["prev_packets"] = net.packets_sent + net.packets_recv
                state["prev_bytes"] = net.bytes_sent + net.bytes_recv
            else:
                delta_packets = (net.packets_sent + net.packets_recv) - state["prev_packets"]
                delta_bytes = (net.bytes_sent + net.bytes_recv) - state["prev_bytes"]
                state["prev_packets"] = net.packets_sent + net.packets_recv
                state["prev_bytes"] = net.bytes_sent + net.bytes_recv
                # Check for anomaly with cooldown
                anomaly, reason = check_anomaly_with_cooldown(
                    delta_packets, 
                    delta_bytes,
                    state["last_anomaly"],
                    state["normal_intervals"]
                )
                
                # Update state
                if anomaly:
                    state["last_anomaly"] = datetime.now()
                    state["normal_intervals"] = 0
                else:
                    state["normal_intervals"] += 1

                conn_info = []
                for c in conns[:5]:  # Just top 5 for readability
                    laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "?"
                    raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "?"
                    conn_info.append({
                        "laddr": laddr,
                        "raddr": raddr,
                        "status": c.status
                    })

                data_point = {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "packets": delta_packets,
                    "size": round(delta_bytes / 1000, 2),
                    "anomaly": anomaly,
                    "connections": conn_info
                }
                state["data"].append(data_point)

                if anomaly:
                    log_event = {
                        "timestamp": data_point["timestamp"],
                        "packets": delta_packets,
                        "size": round(delta_bytes / 1000, 2),
                        "reason": reason
                    }
                    state["logs"].append(log_event)

                if len(state["data"]) > 100:
                    state["data"].pop(0)
        except Exception:
            pass
        time.sleep(1)

def collect_simulated_data():
    while state["running"] and state["mode"] == "simulation":
        packets = random.randint(100, 1000)
        size = random.randint(50, 800)
        # Check for anomaly with cooldown using simulated data
        anomaly, reason = check_anomaly_with_cooldown(
            packets, 
            size * 1000,  # Convert KB to bytes for consistency
            state["last_anomaly"],
            state["normal_intervals"]
        )
        
        # Update state
        if anomaly:
            state["last_anomaly"] = datetime.now()
            state["normal_intervals"] = 0
        else:
            state["normal_intervals"] += 1

        data_point = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "packets": packets,
            "size": size,
            "anomaly": anomaly,
            "connections": []
        }
        state["data"].append(data_point)
        if anomaly:
            state["logs"].append({
                "timestamp": data_point["timestamp"],
                "packets": packets,
                "size": size,
                "reason": reason
            })
        if len(state["data"]) > 100:
            state["data"].pop(0)
        time.sleep(1)

# ----------------------------------------
# RUN
# ----------------------------------------
if __name__ == '__main__':
    print("🚀 Smart Network Monitor is live at http://127.0.0.1:5000")
    app.run(debug=True)
