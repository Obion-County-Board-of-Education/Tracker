-- Initialize all required databases for OCS microservices
-- This script creates all databases that the services expect

-- Create all required databases
CREATE DATABASE ocs_tickets;
CREATE DATABASE ocs_inventory;
CREATE DATABASE ocs_purchasing;
CREATE DATABASE ocs_portal;
CREATE DATABASE ocs_manage;
CREATE DATABASE ocs_forms;

-- Grant permissions to ocs_user on all databases
GRANT ALL PRIVILEGES ON DATABASE ocs_tickets TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_inventory TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_purchasing TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_portal TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_manage TO ocs_user;
GRANT ALL PRIVILEGES ON DATABASE ocs_forms TO ocs_user;
