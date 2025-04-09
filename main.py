"""
Main entry point for Backyard Billboards - Happy Hour Deals App
This file imports app.py and provides the 'app' object for gunicorn to run
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables (ensure this runs first)
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the Flask app
from app import app
from utils import get_time_ago

# Register filters for templates
app.jinja_env.filters['to_time_ago'] = get_time_ago
logger.info("Successfully registered Jinja filters")

# This is the standard way to run the Flask application
if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the app for development
    app.run(host="0.0.0.0", port=port, debug=True)
