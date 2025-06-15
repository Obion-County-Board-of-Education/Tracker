#!/bin/bash
# Health check script for database services
# Tests if the database is ready and all required databases exist

set -e

echo "🔍 Checking database health..."

# Check if PostgreSQL is responding
if ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; then
    echo "❌ PostgreSQL is not ready"
    exit 1
fi

# Extract database name from DATABASE_URL
DB_NAME=$(echo $DATABASE_URL | sed 's/.*\///')

# Check if specific database exists
if ! psql $DATABASE_URL -c '\q' 2>/dev/null; then
    echo "❌ Database $DB_NAME does not exist or is not accessible"
    exit 1
fi

echo "✅ Database $DB_NAME is healthy and accessible"
exit 0
