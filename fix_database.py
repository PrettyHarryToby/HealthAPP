"""
Fix database schema by ensuring all columns exist
This will recreate tables if needed (WARNING: This will delete existing data!)
Only use if you're okay with losing data, or backup first.
"""
from sqlalchemy import create_engine, inspect, text
from database import DATABASE_URL, engine
from models import Base
import os

def fix_database():
    """Recreate all tables with correct schema"""
    print("="*60)
    print("Database Schema Fix")
    print("="*60)
    print("\nWARNING: This will recreate all tables!")
    print("All existing data will be lost!")
    print("\nIf you want to keep your data, use migrate_database.py instead.")
    
    response = input("\nDo you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Drop all tables and recreate them
    print("\nDropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Creating all tables with correct schema...")
    Base.metadata.create_all(bind=engine)
    
    print("\n[SUCCESS] Database schema fixed!")
    print("All tables have been recreated with the correct schema.")

if __name__ == '__main__':
    fix_database()

