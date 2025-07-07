#!/bin/bash

# Railway deployment start script
cd backend

# Set default port if not provided
export PORT=${PORT:-8001}

echo "Starting AI Video Generation Platform on port $PORT..."
echo "Working directory: $(pwd)"
echo "Environment: $(printenv | grep -E '^(DATABASE_URL|GROQ_API_KEY|CLOUDFLARE_ACCOUNT_ID)=' | wc -l) environment variables loaded"

# Check if requirements are installed
if [ ! -f "server.py" ]; then
    echo "Error: server.py not found in $(pwd)"
    ls -la
    exit 1
fi

# Start the server with production settings
exec gunicorn server:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:$PORT \
  --timeout 120 \
  --keep-alive 2 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --preload