"""
Database migration script to add new columns to existing tables
Run this script to update your database schema without losing data
"""
from sqlalchemy import create_engine, text
from database import DATABASE_URL

def migrate_database():
    """Add new columns to existing tables"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        
        try:
            # Check and add columns to medications table
            print("Migrating medications table...")
            
            # Check if columns exist and add them if they don't
            try:
                conn.execute(text("SELECT discontinuation_reason FROM medications LIMIT 1"))
                print("  - discontinuation_reason column already exists")
            except Exception:
                print("  - Adding discontinuation_reason column...")
                conn.execute(text("ALTER TABLE medications ADD COLUMN discontinuation_reason TEXT"))
            
            try:
                conn.execute(text("SELECT discontinuation_date FROM medications LIMIT 1"))
                print("  - discontinuation_date column already exists")
            except Exception:
                print("  - Adding discontinuation_date column...")
                conn.execute(text("ALTER TABLE medications ADD COLUMN discontinuation_date DATE"))
            
            try:
                conn.execute(text("SELECT status FROM medications LIMIT 1"))
                print("  - status column already exists")
            except Exception:
                print("  - Adding status column...")
                conn.execute(text("ALTER TABLE medications ADD COLUMN status VARCHAR(50) DEFAULT 'Active'"))
                # Update existing records to have 'Active' status
                conn.execute(text("UPDATE medications SET status = 'Active' WHERE status IS NULL"))
            
            # Check and add columns to blood_parameters table
            print("\nMigrating blood_parameters table...")
            
            protein_fields = [
                ('total_protein', 'FLOAT'),
                ('albumin', 'FLOAT'),
                ('globulin', 'FLOAT'),
                ('a_g_ratio', 'FLOAT'),
                ('c_reactive_protein', 'FLOAT'),
                ('hemoglobin_a1c', 'FLOAT')
            ]
            
            # Get table info to check existing columns
            result = conn.execute(text("PRAGMA table_info(blood_parameters)"))
            existing_columns = [row[1] for row in result]
            
            for field_name, field_type in protein_fields:
                if field_name not in existing_columns:
                    print(f"  - Adding {field_name} column...")
                    conn.execute(text(f"ALTER TABLE blood_parameters ADD COLUMN {field_name} {field_type}"))
                else:
                    print(f"  - {field_name} column already exists")
            
            # Check if gynecological_risk_indicators table exists and add missing columns
            print("\nMigrating gynecological_risk_indicators table...")
            try:
                # Check if table exists
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='gynecological_risk_indicators'"))
                table_exists = result.fetchone() is not None
                
                if table_exists:
                    # Get existing columns
                    result = conn.execute(text("PRAGMA table_info(gynecological_risk_indicators)"))
                    existing_columns = [row[1] for row in result]
                    
                    # Define all columns that should exist (from the model)
                    columns_to_add = [
                        ('previous_gynecological_surgery', 'BOOLEAN DEFAULT 0'),
                        ('gynecological_surgery_type', 'VARCHAR(200)'),
                        ('abnormal_pap_smear_history', 'BOOLEAN DEFAULT 0'),
                        ('cervical_dysplasia_history', 'BOOLEAN DEFAULT 0'),
                    ]
                    
                    for col_name, col_type in columns_to_add:
                        if col_name not in existing_columns:
                            print(f"  - Adding {col_name} column...")
                            conn.execute(text(f"ALTER TABLE gynecological_risk_indicators ADD COLUMN {col_name} {col_type}"))
                        else:
                            print(f"  - {col_name} column already exists")
                    
                    # Verify all columns exist
                    result = conn.execute(text("PRAGMA table_info(gynecological_risk_indicators)"))
                    final_columns = [row[1] for row in result]
                    print(f"  - Total columns in table: {len(final_columns)}")
                else:
                    print("  - gynecological_risk_indicators table will be created automatically")
            except Exception as e:
                print(f"  - Note: {str(e)}")
                print("  - Table will be created automatically if it doesn't exist")
            
            # Commit the transaction
            trans.commit()
            print("\n[SUCCESS] Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n[ERROR] Migration failed: {str(e)}")
            raise

if __name__ == '__main__':
    print("="*60)
    print("Database Migration Script")
    print("="*60)
    print("\nThis script will add new columns to your existing database.")
    print("Your existing data will be preserved.\n")
    
    migrate_database()
    
    print("\n" + "="*60)
    print("[SUCCESS] Migration complete! You can now run the application.")
    print("="*60)
