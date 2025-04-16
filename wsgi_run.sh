#!/bin/bash
# This script is used to run the WSGI application with the correct settings
# It ensures consistent configuration between development and production

# Use gunicorn to serve the WSGI application
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload wsgi:application