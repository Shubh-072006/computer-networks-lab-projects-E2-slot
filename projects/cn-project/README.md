# CN Project — Network Traffic Simulation + Anomaly Detection

## What it does
- Generates a realistic synthetic dataset (default 20,000 rows) containing normal and anomalous traffic.
- Trains Isolation Forest (unsupervised) and Random Forest (supervised).
- Provides a small Flask web dashboard to generate data, train models, and run a real-time demo simulation.

## Setup (Windows, VS Code)
1. Open the `cn-project` folder in VS Code.
2. Create virtual environment:
   - `python -m venv .venv`
3. Activate:
   - Command Prompt: `.venv\Scripts\activate`
   - PowerShell: `.venv\Scripts\Activate.ps1` (or use cmd if you get policy errors)
4. Install dependencies:
   - `pip install -r requirements.txt`
5. Start the app:
   - `python app.py`
6. Open browser to `http://127.0.0.1:5000`

## Demo flow
1. Click **Generate Dataset**.
2. Click **Train Models**.
3. Click **Start Simulation** to see real-time streaming of traffic and predictions.
4. Use **Stop** to pause.

## Files
- `data_generation.py` — create the synthetic dataset
- `data_preprocessing.py` — feature creation and scaling
- `anomaly_detection.py` — train models & prediction helpers
- `output_reporting.py` — create plots for UI
- `app.py` — Flask app & endpoints
- `templates/index.html`, `static/css/style.css`, `static/js/main.js` — UI

