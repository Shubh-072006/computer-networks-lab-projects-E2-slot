# data_preprocessing.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from utils.paths import DATA_DIR, MODELS_DIR
import joblib

def load_and_preprocess():
    """
    Loads DATA_DIR/network_traffic_data.csv and returns (df, X_scaled, y)
    Also saves a scaler to MODELS_DIR/scaler.pkl for consistent usage.
    """
    p = DATA_DIR / "network_traffic_data.csv"
    if not p.exists():
        raise FileNotFoundError(f"{p} not found")

    df = pd.read_csv(p)

    # Basic cleaning / ensure types
    df = df.fillna(0)

    le = LabelEncoder()
    if "Protocol" in df.columns:
        df["Protocol_enc"] = le.fit_transform(df["Protocol"].astype(str))
    else:
        df["Protocol_enc"] = 0

    features = ["Packets_per_sec", "Packet_Size", "Connection_Duration", "Protocol_enc"]
    X = df[features].astype(float).values
    y = df["Is_Anomaly"].astype(int).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # persist scaler for later (prediction etc.)
    joblib.dump(scaler, MODELS_DIR / "scaler.pkl")

    return df, X_scaled, y
