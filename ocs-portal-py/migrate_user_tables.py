"""
Database Migration Script for User Import System
Adds Azure AD integration fields to existing users table
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run database migration to add user import fields"""
      # Get database connection
    db_url = DATABASE_URL
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as session:
        try:
            logger.info("Starting user import system database migration...")
            
            # Check if columns already exist
            check_columns_sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name IN (
                    'azure_user_id', 'user_principal_name', 'given_name', 'surname',
                    'job_title', 'department', 'office_location', 'employee_id',
                    'employee_type', 'manager_id', 'building_assignment', 'grade_level',
                    'user_type', 'is_active', 'last_login', 'imported_at'
                );
            """
            
            result = session.execute(text(check_columns_sql))
            existing_columns = {row[0] for row in result.fetchall()}
            
            # Define new columns to add
            new_columns = {
                'azure_user_id': 'VARCHAR(255) UNIQUE',
                'user_principal_name': 'VARCHAR(255) UNIQUE',
                'given_name': 'VARCHAR(100)',
                'surname': 'VARCHAR(100)',
                'job_title': 'VARCHAR(255)',
                'department': 'VARCHAR(255)',
                'office_location': 'VARCHAR(255)',
                'employee_id': 'VARCHAR(50)',
                'employee_type': 'VARCHAR(50)',
                'manager_id': 'VARCHAR(255)',
                'building_assignment': 'VARCHAR(255)',
                'grade_level': 'VARCHAR(10)',
                'user_type': 'VARCHAR(20) DEFAULT \'staff\'',
                'is_active': 'BOOLEAN DEFAULT TRUE',
                'last_login': 'TIMESTAMP',
                'imported_at': 'TIMESTAMP'
            }
            
            # Add missing columns
            for column_name, column_definition in new_columns.items():
                if column_name not in existing_columns:
                    add_column_sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_definition};"
                    logger.info(f"Adding column: {column_name}")
                    session.execute(text(add_column_sql))
                else:
                    logger.info(f"Column {column_name} already exists, skipping")
            
            # Make username nullable for Azure AD users
            try:
                alter_username_sql = "ALTER TABLE users ALTER COLUMN username DROP NOT NULL;"
                session.execute(text(alter_username_sql))
                logger.info("Made username column nullable")
            except Exception as e:
                logger.warning(f"Could not make username nullable (may already be nullable): {e}")
            
            # Create user_departments table if it doesn't exist
            create_user_departments_sql = """
                CREATE TABLE IF NOT EXISTS user_departments (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    department_name VARCHAR(255) NOT NULL,
                    building_name VARCHAR(255),
                    is_primary BOOLEAN DEFAULT TRUE,
                    role_in_department VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            
            session.execute(text(create_user_departments_sql))
            logger.info("Created user_departments table (if not exists)")
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_azure_user_id ON users(azure_user_id);",
                "CREATE INDEX IF NOT EXISTS idx_users_user_principal_name ON users(user_principal_name);",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
                "CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);",
                "CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type);",
                "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
                "CREATE INDEX IF NOT EXISTS idx_user_departments_user_id ON user_departments(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_departments_department_name ON user_departments(department_name);"
            ]
            
            for index_sql in indexes:
                try:
                    session.execute(text(index_sql))
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")
            
            logger.info("Created performance indexes")
            
            # Commit all changes
            session.commit()
            logger.info("✅ User import system migration completed successfully!")
            
            # Display summary
            logger.info("\n📊 Migration Summary:")
            logger.info("- Added Azure AD integration fields to users table")
            logger.info("- Created user_departments table for department assignments")
            logger.info("- Added performance indexes")
            logger.info("- Made username column nullable for Azure AD users")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Migration failed: {e}")
            raise
        finally:
            session.close()

def verify_migration():
    """Verify the migration was successful"""
    db_url = DATABASE_URL
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as session:
        try:
            # Check users table structure
            users_columns_sql = """
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position;
            """
            
            result = session.execute(text(users_columns_sql))
            users_columns = result.fetchall()
            
            logger.info("\n📋 Users Table Structure:")
            for column in users_columns:
                logger.info(f"  - {column[0]} ({column[1]}) - Nullable: {column[2]}")
            
            # Check user_departments table
            departments_check_sql = """
                SELECT COUNT(*) as table_exists
                FROM information_schema.tables 
                WHERE table_name = 'user_departments';
            """
            
            result = session.execute(text(departments_check_sql))
            table_exists = result.fetchone()[0]
            
            if table_exists:
                logger.info("\n✅ user_departments table exists")
                
                # Get column info
                dept_columns_sql = """
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_departments' 
                    ORDER BY ordinal_position;
                """
                
                result = session.execute(text(dept_columns_sql))
                dept_columns = result.fetchall()
                
                logger.info("📋 user_departments Table Structure:")
                for column in dept_columns:
                    logger.info(f"  - {column[0]} ({column[1]})")
            else:
                logger.error("❌ user_departments table not found")
            
            # Check indexes
            indexes_sql = """
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename IN ('users', 'user_departments') 
                ORDER BY indexname;
            """
            
            result = session.execute(text(indexes_sql))
            indexes = result.fetchall()
            
            logger.info("\n📊 Created Indexes:")
            for index in indexes:
                logger.info(f"  - {index[0]}")
                
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            raise

if __name__ == "__main__":
    print("🚀 OCS User Import System - Database Migration")
    print("=" * 50)
    
    try:
        # Run migration
        run_migration()
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        verify_migration()
        
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Test the user import functionality")
        print("2. Import a small group of users first")
        print("3. Verify data integrity")
        print("4. Run full import when ready")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Please check the error logs and fix any issues before retrying.")
        sys.exit(1)
