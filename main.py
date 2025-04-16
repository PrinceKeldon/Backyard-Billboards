"""
Development entry point for Backyard Billboards
For development use only - wsgi.py is used for deployment
"""
# Import Flask application - same import as wsgi.py for consistency
try:
    from app import app
except ImportError as e:
    import sys
    print(f"ERROR: Failed to import app: {e}", file=sys.stderr)
    raise

# For development execution only
if __name__ == "__main__":
    # Use consistent port with gunicorn_config.py
    app.run(host="0.0.0.0", port=5000, debug=True)
