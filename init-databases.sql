-- Initialize all required databases for OCS microservices
-- ocs_portal is the main database and is created by default via POSTGRES_DB
-- This script creates the additional databases that the other services expect

-- Create ocs_tickets database
SELECT 'CREATE DATABASE ocs_tickets' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ocs_tickets')\gexec

-- Create ocs_inventory database
SELECT 'CREATE DATABASE ocs_inventory' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ocs_inventory')\gexec

-- Create ocs_purchasing database
SELECT 'CREATE DATABASE ocs_purchasing' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ocs_purchasing')\gexec

-- Create ocs_manage database
SELECT 'CREATE DATABASE ocs_manage' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ocs_manage')\gexec

-- Create ocs_forms database
SELECT 'CREATE DATABASE ocs_forms' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ocs_forms')\gexec

-- Grant permissions to ocs_user on all databases
GRANT ALL PRIVILEGES ON DATABASE ocs_tickets TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_inventory TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_purchasing TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_portal TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_manage TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_forms TO ocs_user;
