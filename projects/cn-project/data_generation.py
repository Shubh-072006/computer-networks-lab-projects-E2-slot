# data_generation.py
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from utils.paths import DATA_DIR

def generate_dataset(n=20000, anomaly_fraction=0.1, save_csv=True):
    np.random.seed(42)
    # timestamps (newest first)
    timestamps = [datetime.now() - timedelta(seconds=i) for i in range(n)][::-1]

    # Base distributions
    packets_per_sec = np.random.gamma(2.0, 200, n).astype(int) + 10
    packet_size = np.abs(np.random.normal(600, 150, n)).astype(int)
    conn_duration = np.round(np.random.exponential(0.5, n), 2)
    protocol = np.random.choice(["TCP", "UDP", "ICMP"], n, p=[0.7, 0.25, 0.05])

    # Inject anomalies
    labels = np.zeros(n, dtype=int)
    k = max(1, int(n * anomaly_fraction))
    idx_anom = np.random.choice(n, k, replace=False)
    # Increase packets and size for anomalies
    packets_per_sec[idx_anom] = packets_per_sec[idx_anom] * np.random.randint(3, 8, size=k)
    packet_size[idx_anom] = packet_size[idx_anom] * np.random.randint(2, 4, size=k)
    labels[idx_anom] = 1

    src_ips = [f"192.168.{np.random.randint(0,255)}.{np.random.randint(1,254)}" for _ in range(n)]
    dst_ips = [f"10.0.{np.random.randint(0,255)}.{np.random.randint(1,254)}" for _ in range(n)]

    df = pd.DataFrame({
        "Timestamp": timestamps,
        "Source_IP": src_ips,
        "Destination_IP": dst_ips,
        "Protocol": protocol,
        "Packets_per_sec": packets_per_sec,
        "Packet_Size": packet_size,
        "Connection_Duration": conn_duration,
        "Is_Anomaly": labels
    })

    if save_csv:
        path = DATA_DIR / "network_traffic_data.csv"
        df.to_csv(path, index=False)
        print(f"[data_generation] saved {path}")

    return df
