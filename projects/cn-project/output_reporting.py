# output_reporting.py
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc
from utils.paths import PLOTS_DIR, REPORTS_DIR
import numpy as np
import os

# Ensure PLOTS_DIR exists
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

def plot_confusion(cm, name="rf_confusion.png"):
    plt.figure(figsize=(4,3))
    sns.heatmap(cm, annot=True, fmt='d', cmap='rocket', xticklabels=["Normal","Anomaly"], yticklabels=["Normal","Anomaly"])
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    path = PLOTS_DIR / name
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path

def plot_feature_importance(model, features, name="rf_fi.png"):
    if not hasattr(model, "feature_importances_"):
        return None
    importance = model.feature_importances_
    sorted_idx = np.argsort(importance)
    plt.figure(figsize=(4,3))
    plt.barh(np.array(features)[sorted_idx], importance[sorted_idx], color="#00b4d8")
    plt.title("Feature Importance")
    plt.tight_layout()
    path = PLOTS_DIR / name
    plt.savefig(path)
    plt.close()
    return path

def plot_roc(y_true, y_proba, name="rf_roc.png"):
    if y_proba is None or len(y_true)==0:
        return None
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(4,3))
    plt.plot(fpr, tpr, color="#00ffcc", lw=2, label=f"AUC = {roc_auc:.2f}")
    plt.plot([0,1],[0,1], linestyle="--", color="#888")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend(loc="lower right")
    plt.tight_layout()
    path = PLOTS_DIR / name
    plt.savefig(path)
    plt.close()
    return path
