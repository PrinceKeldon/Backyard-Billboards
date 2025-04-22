
"""
WSGI entry point for Replit deployment
This is the file that gunicorn uses as its entry point
"""
import os
import sys

# Import the Flask application
try:
    from app import app as application
except ImportError as e:
    print(f"ERROR: Failed to import app: {e}", file=sys.stderr)
    raise

# For direct execution during development
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run(host="0.0.0.0", port=port, debug=True)
