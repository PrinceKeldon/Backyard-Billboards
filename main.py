# Import all required modules first to ensure they're available
import os
import logging
import time
import urllib.parse
import io
import random
import base64
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Now import Flask app and other components
try:
    from app import app
    from utils import get_time_ago
    
    # Register Jinja filter for time ago display
    app.jinja_env.filters['to_time_ago'] = get_time_ago
    
    logger.info("Successfully imported Flask app and registered filters")
except Exception as e:
    logger.error(f"Error importing app: {str(e)}")
    # Create a minimal app as fallback if the import fails
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def error_page():
        return "Application Error: Could not initialize properly. Please check the logs."

# This makes the app available to gunicorn via "main:app"
# app is now explicitly exported and accessible by gunicorn

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
