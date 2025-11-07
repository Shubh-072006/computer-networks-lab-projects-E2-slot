# utils/paths.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
PLOTS_DIR = BASE_DIR / "static" / "plots"

for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR, PLOTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
