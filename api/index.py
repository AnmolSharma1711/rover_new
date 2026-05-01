import sys
import os
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the Flask app from app.py
from app import app

# Vercel expects the WSGI application
application = app
