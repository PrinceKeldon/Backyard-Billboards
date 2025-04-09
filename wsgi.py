"""
WSGI entry point for Replit deployment
This is the file that should be specified in the Procfile
"""
import os
import logging
from datetime import datetime

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("wsgi")
logger.info(f"Starting WSGI application at {datetime.now().isoformat()}")

# Get the port from environment or use default
port = int(os.environ.get("PORT", 5000))
logger.info(f"Using port: {port}")

try:
    # Import the Flask app from app.py
    from app import app as application
    
    # Import Jinja filters from utils
    from utils import get_time_ago
    
    # Register custom filters
    application.jinja_env.filters['to_time_ago'] = get_time_ago
    logger.info("Successfully imported Flask app and registered filters")
    
except Exception as e:
    logger.error(f"Error importing application: {str(e)}", exc_info=True)
    # Create a minimal emergency application
    from flask import Flask, jsonify
    application = Flask(__name__)
    
    @application.route('/')
    def error_home():
        return jsonify({
            "error": "Application failed to initialize",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# This allows running the application directly
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=port)