"""
Development entry point for Backyard Billboards
For development use only - production deployment uses wsgi.py
"""
# Simply import the WSGI application from wsgi.py for consistency
# This ensures main.py and wsgi.py use exactly the same application object
from wsgi import application as app
import os

# This is only used when running this file directly for development
if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the app for development
    app.run(host="0.0.0.0", port=port, debug=True)
