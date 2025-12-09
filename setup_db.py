"""
Database initialization script with connection validation and automatic setup.

This script:
- Validates DATABASE_URL environment variable
- Waits for PostgreSQL to be ready (with retry mechanism)
- Tests database connection
- Creates all database tables defined in models
- Provides clear status messages and error handling
"""

import asyncio
import os
import sys
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from models import Base

# Load environment variables from .env file
load_dotenv()


def check_database_url():
    """Check if DATABASE_URL environment variable is set."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("[ERROR] DATABASE_URL environment variable is not set")
        print("Please set DATABASE_URL in your .env file or environment")
        return False
    print("[OK] DATABASE_URL is configured")
    return True


# Get database URL (will be validated in check_database_url)
database_url = os.getenv("DATABASE_URL")

# Create database engine (only if DATABASE_URL is set)
if database_url:
    engine = create_engine(database_url.replace('+asyncpg', ''), echo=True)
else:
    engine = None


def wait_for_database(max_wait_seconds=30):
    """
    Wait for PostgreSQL to be ready with retry mechanism.
    
    Args:
        max_wait_seconds: Maximum time to wait for database (default: 30 seconds)
    
    Returns:
        bool: True if database is ready, False otherwise
    """
    if not engine:
        print("[ERROR] Cannot wait for database: engine not initialized")
        return False
    
    print(f"[WAIT] Waiting for database to be ready (max {max_wait_seconds}s)...")
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < max_wait_seconds:
        attempt += 1
        try:
            # Test connection with a simple query
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                elapsed = time.time() - start_time
                print(f"[OK] Database is ready (connected after {elapsed:.1f}s, attempt #{attempt})")
                return True
        except OperationalError as e:
            elapsed = time.time() - start_time
            if elapsed >= max_wait_seconds:
                print(f"[ERROR] Database connection timeout after {max_wait_seconds}s")
                print(f"Last error: {str(e)}")
                return False
            
            # Wait before retrying
            time.sleep(1)
            if attempt % 5 == 0:
                print(f"  Still waiting... ({elapsed:.0f}s elapsed, attempt #{attempt})")
    
    return False


def test_database_connection():
    """Test database connection with a simple query."""
    if not engine:
        print("[ERROR] Cannot test connection: engine not initialized")
        return False
    
    print("[TEST] Testing database connection...")
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("[OK] Connected to PostgreSQL")
            print(f"  Database version: {version.split(',')[0]}")
            return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {str(e)}")
        return False


def create_tables():
    """Create all database tables defined in models."""
    if not engine:
        print("[ERROR] Cannot create tables: engine not initialized")
        return False
    
    print("[CREATE] Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables created successfully")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if tables:
            print(f"  Created tables: {', '.join(tables)}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create tables: {str(e)}")
        return False


def main():
    """Main execution flow."""
    print("=" * 60)
    print("DATABASE SETUP SCRIPT")
    print("=" * 60)
    
    # Step 1: Check DATABASE_URL
    if not check_database_url():
        sys.exit(1)
    
    # Step 2: Wait for database to be ready
    if not wait_for_database(max_wait_seconds=30):
        print("\n[INFO] Troubleshooting tips:")
        print("  - Check if PostgreSQL is running")
        print("  - Verify DATABASE_URL is correct")
        print("  - Check network connectivity")
        print("  - Review PostgreSQL logs for errors")
        sys.exit(1)
    
    # Step 3: Test connection
    if not test_database_connection():
        sys.exit(1)
    
    # Step 4: Create tables
    if not create_tables():
        sys.exit(1)
    
    # Success!
    print("\n" + "=" * 60)
    print("[SUCCESS] Database setup completed successfully!")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()