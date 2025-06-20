#!/bin/bash

# Health check script for OCS microservices
# Tests if the service is responding to HTTP requests on port 8000

curl -f http://localhost:8000/health || exit 1