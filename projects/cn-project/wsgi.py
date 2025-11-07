# wsgi.py - Production WSGI entry point with proper imports
import os
import sys
from pathlib import Path

# Add project root to Python path for absolute imports
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import Flask app after path setup
from app import app

if __name__ == '__main__':
    app.run()