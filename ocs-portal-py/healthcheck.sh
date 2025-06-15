#!/bin/bash
# Health check script for OCS Portal service
# Tests if the service is responding to HTTP requests on port 8000
# Uses the root endpoint since portal might not have /health

curl -f http://localhost:8000/ || exit 1
