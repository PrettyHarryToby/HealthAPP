"""
Quick script to verify database schema
"""
from database import get_session, engine
from sqlalchemy import inspect

def check_schema():
    inspector = inspect(engine)
    
    print("Checking database schema...")
    print("="*60)
    
    # Check blood_parameters columns
    if 'blood_parameters' in inspector.get_table_names():
        print("\nblood_parameters table columns:")
        columns = inspector.get_columns('blood_parameters')
        protein_cols = [c['name'] for c in columns if 'protein' in c['name'].lower() or 'albumin' in c['name'].lower() or 'globulin' in c['name'].lower() or 'a1c' in c['name'].lower() or 'crp' in c['name'].lower()]
        for col in protein_cols:
            print(f"  - {col}")
    
    # Check reproductive_health columns
    if 'reproductive_health' in inspector.get_table_names():
        print("\nreproductive_health table columns:")
        columns = inspector.get_columns('reproductive_health')
        gyn_cols = [c['name'] for c in columns if 'gynecological' in c['name'].lower() or 'pap' in c['name'].lower() or 'dysplasia' in c['name'].lower()]
        for col in gyn_cols:
            print(f"  - {col}")
    
    # Check if gynecological_risk_indicators exists
    if 'gynecological_risk_indicators' in inspector.get_table_names():
        print("\ngynecological_risk_indicators table: EXISTS")
        columns = inspector.get_columns('gynecological_risk_indicators')
        print(f"  Total columns: {len(columns)}")
    else:
        print("\ngynecological_risk_indicators table: NOT FOUND")
    
    print("\n" + "="*60)
    print("Schema check completed!")

if __name__ == '__main__':
    check_schema()

