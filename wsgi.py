
"""
WSGI entry point for Replit deployment
This is the file that gunicorn uses as its entry point
"""
# Import the Flask application
try:
    from app import app as application
except ImportError as e:
    import sys
    print(f"ERROR: Failed to import app: {e}", file=sys.stderr)
    raise

# For direct execution during development
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)
