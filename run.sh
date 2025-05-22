#!/bin/bash

# Display deployment information
echo "Starting Backyard Billboards application..."
echo "Environment: $(printenv | grep -E 'PORT|REPL_')"

# Set default port if not provided
export PORT=${PORT:-5000}

# Start the application using gunicorn
echo "Starting gunicorn on port $PORT..."
exec gunicorn main:app --bind 0.0.0.0:$PORT --access-logfile - --error-logfile - --log-level info