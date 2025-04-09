# Import all required modules first to ensure they're available
import os
import sys
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
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Now import Flask app and other components
try:
    from app import app
    from utils import get_time_ago
    
    # Register Jinja filter for time ago display
    app.jinja_env.filters['to_time_ago'] = get_time_ago
    
    logger.info("Successfully imported Flask app and registered filters")
except Exception as e:
    logger.error(f"Error importing app: {str(e)}", exc_info=True)
    # Create a minimal app as fallback if the import fails
    from flask import Flask, render_template_string
    app = Flask(__name__)
    
    @app.route('/')
    def error_page():
        error_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Application Error</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    background-color: #121212;
                    color: #e0e0e0;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                .error-container {
                    max-width: 800px;
                    margin: 2rem;
                    padding: 2rem;
                    background-color: #1e1e1e;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                }
                h1 {
                    color: #ec5f67;
                    margin-top: 0;
                }
                .action-btn {
                    display: inline-block;
                    margin-top: 1rem;
                    padding: 0.5rem 1rem;
                    background-color: #4caf50;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    transition: background-color 0.3s;
                }
                .action-btn:hover {
                    background-color: #45a049;
                }
                .error-details {
                    margin-top: 2rem;
                    padding: 1rem;
                    background-color: #2a2a2a;
                    border-radius: 4px;
                    overflow-x: auto;
                }
                code {
                    font-family: monospace;
                    white-space: pre-wrap;
                }
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>Application Error</h1>
                <p>Backyard Billboards encountered an error during startup.</p>
                <p>This is likely due to a configuration issue or missing dependencies.</p>
                <div class="error-details">
                    <p><strong>Error Details:</strong></p>
                    <code>{{ error }}</code>
                </div>
                <p>
                    <a href="/" class="action-btn">Try Again</a>
                </p>
            </div>
        </body>
        </html>
        """
        # Get detailed error information
        import traceback
        error_details = str(e) + "\n\n" + traceback.format_exc()
        
        return render_template_string(error_html, error=error_details)

# This makes the app available to gunicorn via "main:app"
# app is now explicitly exported and accessible by gunicorn

# Add health check endpoint for deployment
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # Set the port from the environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
