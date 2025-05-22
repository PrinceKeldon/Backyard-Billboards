"""
Unified entry point for Backyard Billboards
This file provides a consistent way to run the application in any environment
"""
# Import the application from wsgi.py for consistency
from wsgi import application

# This is used when running this file directly
if __name__ == "__main__":
    import os
    # Run the application directly
    port = int(os.environ.get("PORT", 5000))
    application.run(host="0.0.0.0", port=port, debug=True)