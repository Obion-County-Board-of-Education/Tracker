#!/bin/bash

# Health check script for OCS microservices
# Tests if the service is responding to HTTP requests on port 8000

echo "Starting health check for ocs-forms-api..."

# Wait for service to be ready
sleep 3

# Try health check with timeout and retry
if curl -f --max-time 10 --retry 2 http://localhost:8000/health > /dev/null 2>&1; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed"
    exit 1
fi