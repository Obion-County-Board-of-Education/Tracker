#!/bin/bash

# Health check script for OCS microservices
# Tests if the service is responding to HTTP requests on port 8000

echo "Starting health check..."

# Wait a moment for the service to be ready
sleep 2

# Try health check with timeout and retry
curl -f --max-time 10 --retry 3 http://localhost:8000/health || exit 1

echo "Health check passed"