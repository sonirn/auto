#!/bin/bash

# Start script for Railway deployment
cd /app/backend

# Set default port if not provided
export PORT=${PORT:-8001}

# Initialize database
echo "Initializing database..."
python -c "from database import init_database; init_database()"

# Start the server
echo "Starting server on port $PORT..."
exec gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --host 0.0.0.0 --port $PORT --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 50 --preload