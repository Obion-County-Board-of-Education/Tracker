"""
Database migration script to create authentication tables.
This script should be run once to initialize the authentication database structure.
"""

from sqlalchemy import create_engine, text
import os
import sys
import datetime

# Get database connection from environment or use default
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://ocs_user:ocs_pass@localhost:5433/ocs_tickets")

# SQL statements to create authentication tables
SQL_CREATE_TABLES = """
-- Create group_roles table for storing permission mappings
CREATE TABLE IF NOT EXISTS group_roles (
    id SERIAL PRIMARY KEY,
    azure_group_id VARCHAR(255) UNIQUE,
    group_name VARCHAR(255) NOT NULL,
    access_level VARCHAR(50) NOT NULL,
    tickets_access VARCHAR(50) NOT NULL DEFAULT 'none',
    inventory_access VARCHAR(50) NOT NULL DEFAULT 'none',
    purchasing_access VARCHAR(50) NOT NULL DEFAULT 'none',
    forms_access VARCHAR(50) NOT NULL DEFAULT 'none',
    allowed_departments JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create user_sessions table for storing session information
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    token VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    access_level VARCHAR(50) NOT NULL,
    azure_groups JSONB,
    effective_permissions JSONB,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create audit_log table for security and compliance tracking
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    action_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    details TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- Create user_preferences table for storing user-specific settings
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    preferences JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create system_messages table for displaying announcements
CREATE TABLE IF NOT EXISTS system_messages (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    level VARCHAR(50) NOT NULL DEFAULT 'info',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    expires_at TIMESTAMP
);
"""

# SQL to insert initial role definitions
SQL_INSERT_INITIAL_ROLES = """
-- Insert initial group mappings based on auth.md definitions
INSERT INTO group_roles (azure_group_id, group_name, access_level, tickets_access, inventory_access, purchasing_access, forms_access, allowed_departments)
VALUES 
    ('fb4e15be-e9ac-4072-adac-898c9697e4cc', 'Technology Department', 'super_admin', 'admin', 'admin', 'admin', 'admin', '["*"]'),
    ('630591da-b07e-4bce-8b3f-90b8f46dcdeb', 'Finance', 'super_admin', 'admin', 'admin', 'admin', 'admin', '["*"]'),
    ('1a5462fc-7e89-4517-be54-2ce79b44e12a', 'All_Staff', 'write', 'write', 'read', 'write', 'write', null),
    ('f4ee1bf4-901c-43bb-a380-935540b0832d', 'All_Students', 'read', 'write', 'none', 'none', 'none', null)
ON CONFLICT (azure_group_id) DO UPDATE SET
    access_level = EXCLUDED.access_level,
    tickets_access = EXCLUDED.tickets_access,
    inventory_access = EXCLUDED.inventory_access,
    purchasing_access = EXCLUDED.purchasing_access,
    forms_access = EXCLUDED.forms_access,
    updated_at = NOW();

-- Insert special role for Director of Schools (identified by extensionAttribute10)
INSERT INTO group_roles (azure_group_id, group_name, access_level, tickets_access, inventory_access, purchasing_access, forms_access, allowed_departments)
VALUES 
    ('special:director_of_schools', 'Director of Schools', 'super_admin', 'admin', 'admin', 'admin', 'admin', '["*"]')
ON CONFLICT (azure_group_id) DO UPDATE SET 
    access_level = EXCLUDED.access_level,
    tickets_access = EXCLUDED.tickets_access,
    inventory_access = EXCLUDED.inventory_access,
    purchasing_access = EXCLUDED.purchasing_access,
    forms_access = EXCLUDED.forms_access,
    updated_at = NOW();
"""


def main():
    """Initialize authentication database tables"""
    print("Creating authentication tables...")
    
    try:
        # Connect to database
        engine = create_engine(DATABASE_URL)
        connection = engine.connect()
        
        # Execute table creation SQL
        connection.execute(text(SQL_CREATE_TABLES))
        
        # Execute initial role definitions
        connection.execute(text(SQL_INSERT_INITIAL_ROLES))
        
        # Commit the changes
        connection.commit()
        
        print("Authentication database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing authentication database: {e}")
        sys.exit(1)
    finally:
        # Clean up connection
        if 'connection' in locals():
            connection.close()
    
    print("Authentication database setup completed.")


if __name__ == "__main__":
    main()
