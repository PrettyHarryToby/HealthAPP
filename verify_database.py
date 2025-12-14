"""
Verify database schema has all required columns
"""
from database import engine
from sqlalchemy import inspect, text

def verify_database():
    """Verify all required columns exist"""
    inspector = inspect(engine)
    
    print("="*60)
    print("Database Schema Verification")
    print("="*60)
    
    # Check medications table
    print("\nChecking medications table...")
    med_columns = [c['name'] for c in inspector.get_columns('medications')]
    required_med_columns = ['discontinuation_reason', 'discontinuation_date', 'status']
    
    for col in required_med_columns:
        if col in med_columns:
            print(f"  [OK] {col}")
        else:
            print(f"  [MISSING] {col}")
    
    # Check blood_parameters table
    print("\nChecking blood_parameters table...")
    bp_columns = [c['name'] for c in inspector.get_columns('blood_parameters')]
    required_bp_columns = ['total_protein', 'albumin', 'globulin', 'a_g_ratio', 'c_reactive_protein', 'hemoglobin_a1c']
    
    for col in required_bp_columns:
        if col in bp_columns:
            print(f"  [OK] {col}")
        else:
            print(f"  [MISSING] {col}")
    
    # Check if gynecological_risk_indicators table exists
    print("\nChecking tables...")
    tables = inspector.get_table_names()
    if 'gynecological_risk_indicators' in tables:
        print("  [OK] gynecological_risk_indicators table exists")
    else:
        print("  [MISSING] gynecological_risk_indicators table")
    
    print("\n" + "="*60)
    print("Verification complete!")
    print("="*60)

if __name__ == '__main__':
    verify_database()

