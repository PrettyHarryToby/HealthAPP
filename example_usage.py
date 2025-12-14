"""
Example script demonstrating how to use the Health Database Application programmatically
This can be used for batch data import or automated analysis
"""
from database import init_database, get_session, close_session
from models import Patient, VitaminLevels, BloodParameters, ReproductiveHealth, Medication, GeneticData
from analysis import generate_health_insights, analyze_vitamin_trends
from datetime import date, datetime


def example_add_patient():
    """Example: Add a new patient"""
    session = get_session()
    try:
        patient = Patient(
            patient_id="PAT001",
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(1990, 5, 15),
            email="jane.doe@example.com",
            phone="555-0123"
        )
        session.add(patient)
        session.commit()
        print(f"Patient {patient.patient_id} added successfully")
    finally:
        close_session(session)


def example_add_vitamin_levels():
    """Example: Add vitamin level test results"""
    session = get_session()
    try:
        # Find patient
        patient = session.query(Patient).filter_by(patient_id="PAT001").first()
        if not patient:
            print("Patient not found. Please add patient first.")
            return
        
        # Add vitamin levels
        vitamin_levels = VitaminLevels(
            patient_id=patient.id,
            test_date=date.today(),
            vitamin_d=25.0,  # Low - below 30 ng/mL
            vitamin_b12=180.0,  # Low - below 200 pg/mL
            vitamin_b9=3.5,  # Low - below 4 ng/mL
            vitamin_c=1.2  # Normal
        )
        session.add(vitamin_levels)
        session.commit()
        print("Vitamin levels added successfully")
    finally:
        close_session(session)


def example_add_blood_parameters():
    """Example: Add blood test results"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(patient_id="PAT001").first()
        if not patient:
            print("Patient not found.")
            return
        
        blood_params = BloodParameters(
            patient_id=patient.id,
            test_date=date.today(),
            hemoglobin=12.5,
            hematocrit=38.0,
            ferritin=15.0,  # Low ferritin
            iron=45.0  # Low iron
        )
        session.add(blood_params)
        session.commit()
        print("Blood parameters added successfully")
    finally:
        close_session(session)


def example_add_genetic_data():
    """Example: Add genetic test results"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(patient_id="PAT001").first()
        if not patient:
            print("Patient not found.")
            return
        
        genetic_data = GeneticData(
            patient_id=patient.id,
            test_date=date.today(),
            test_type="MTHFR",
            test_provider="Genetic Testing Lab",
            mthfr_c677t="CT",  # Heterozygous variant
            mthfr_a1298c="AA",  # Normal
            interpretation="Heterozygous MTHFR C677T variant detected",
            clinical_significance="May affect folate metabolism. Consider methylated folate supplementation.",
            recommendations="Use methylated folate (5-MTHF) instead of folic acid for supplementation"
        )
        session.add(genetic_data)
        session.commit()
        print("Genetic data added successfully")
    finally:
        close_session(session)


def example_generate_insights():
    """Example: Generate health insights for a patient"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(patient_id="PAT001").first()
        if not patient:
            print("Patient not found.")
            return
        
        insights = generate_health_insights(session, patient.id)
        
        print("\n" + "="*80)
        print("HEALTH INSIGHTS")
        print("="*80)
        
        if insights['vitamin_analysis'] and insights['vitamin_analysis'].get('has_data'):
            va = insights['vitamin_analysis']
            print(f"\nVitamin Analysis: {va.get('total_records', 0)} records")
            
            if va.get('deficiencies'):
                print("\nDeficiencies Detected:")
                for def_item in va['deficiencies']:
                    print(f"  - {def_item['vitamin']}: {def_item['value']} {def_item['unit']}")
        
        if insights['genetic_insights']:
            print("\nGenetic Insights:")
            for gi in insights['genetic_insights']:
                print(f"  - {gi['type']}: {gi['implication']}")
        
        if insights['medication_recommendations']:
            print("\nMedication Recommendations:")
            for mr in insights['medication_recommendations']:
                print(f"  - {mr.get('vitamin', 'N/A')}: {mr['reason']}")
        
        print("\n" + "="*80)
    finally:
        close_session(session)


if __name__ == "__main__":
    # Initialize database
    init_database()
    
    print("Health Database Application - Example Usage")
    print("="*50)
    
    # Run examples
    print("\n1. Adding example patient...")
    example_add_patient()
    
    print("\n2. Adding vitamin levels...")
    example_add_vitamin_levels()
    
    print("\n3. Adding blood parameters...")
    example_add_blood_parameters()
    
    print("\n4. Adding genetic data...")
    example_add_genetic_data()
    
    print("\n5. Generating insights...")
    example_generate_insights()
    
    print("\nExample completed!")

