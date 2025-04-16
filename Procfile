
web: gunicorn --config gunicorn_config.py --bind 0.0.0.0:$PORT --timeout 300 --workers 2 --worker-class sync wsgi:application
