# anomaly_detection.py
import joblib
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split
from utils.paths import MODELS_DIR
import numpy as np

def train_isolation_forest(X, contamination=0.15):
    iso = IsolationForest(n_estimators=100, contamination=contamination, random_state=42)
    iso.fit(X)
    joblib.dump(iso, MODELS_DIR / "isolation_forest.pkl")
    return iso

def train_random_forest(X, y, test_size=0.25):
    # Use train/test split for realistic metrics
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y if len(np.unique(y))>1 else None)
    rf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)
    rf.fit(X_train, y_train)

    preds = rf.predict(X_test)
    proba = rf.predict_proba(X_test)[:, 1] if hasattr(rf, "predict_proba") else None

    acc = accuracy_score(y_test, preds) if len(y_test)>0 else 0.0
    auc = roc_auc_score(y_test, proba) if proba is not None and len(np.unique(y_test))>1 else 0.0
    cm = confusion_matrix(y_test, preds) if len(y_test)>0 else np.array([[0,0],[0,0]])

    joblib.dump(rf, MODELS_DIR / "random_forest.pkl")
    return {"model": rf, "acc": float(acc), "auc": float(auc), "confusion_matrix": cm, "X_test": X_test, "y_test": y_test}

def load_models():
    iso = joblib.load(MODELS_DIR / "isolation_forest.pkl")
    rf = joblib.load(MODELS_DIR / "random_forest.pkl")
    scaler = joblib.load(MODELS_DIR / "scaler.pkl") if (MODELS_DIR / "scaler.pkl").exists() else None
    return {"iso": iso, "rf": rf, "scaler": scaler}

def predict_with_models(models, X_row):
    """
    X_row expected to be scaled already (1, n_features)
    Returns dict with iso_pred and rf_pred
    iso mapping: IsolationForest.predict() -> -1 (anomaly) or 1 (normal).
    We convert -1 -> 1 (anomaly), 1 -> 0 (normal)
    """
    out = {}
    if not models:
        return out
    if "iso" in models and models["iso"] is not None:
        try:
            v = models["iso"].predict(X_row)
            out["iso_pred"] = 1 if v[0] == -1 else 0
        except Exception:
            out["iso_pred"] = None
    if "rf" in models and models["rf"] is not None:
        try:
            v = models["rf"].predict(X_row)
            out["rf_pred"] = int(v[0])
        except Exception:
            out["rf_pred"] = None
    return out
