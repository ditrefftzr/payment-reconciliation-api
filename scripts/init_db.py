# scripts/init_db.py
"""
Script to initialize the database.
Run this once to create the database and all tables.
"""
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
import pymysql

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME")
    
    try:
        # Connect to MySQL server (without specifying database)
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            print(f"✓ Database '{DB_NAME}' ready")
        
        connection.close()
        
    except pymysql.Error as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

def init_tables():
    """Create all tables in the database"""
    from app.database import engine, Base
    from app.models.db_schema import Merchant, Order, Payment
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✓ Tables created successfully!")
    print("  - merchants")
    print("  - orders")
    print("  - payments")

if __name__ == "__main__":
    print("=== Payment Reconciliation API - Database Setup ===\n")
    
    # Step 1: Create database
    create_database_if_not_exists()
    
    # Step 2: Create tables
    init_tables()
    
    print("\n✓ Database initialization complete!")
    print("Run the server with: uvicorn app.main:app --reload")