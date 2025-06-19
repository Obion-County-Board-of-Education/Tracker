#!/bin/bash
# Health check script for OCS Portal service
# Tests if the portal service is responding to HTTP requests on the root endpoint

curl -f http://localhost:8000/ > /dev/null 2>&1 || exit 1
