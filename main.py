# Import the flask app from app.py
from app import app
from utils import get_time_ago

# Register Jinja filter for time ago display
app.jinja_env.filters['to_time_ago'] = get_time_ago

# This makes the app available to gunicorn via "main:app"
# app is now explicitly exported and accessible by gunicorn

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
