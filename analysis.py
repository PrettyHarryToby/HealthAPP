"""
Analysis functions for tracking vitamin levels, identifying deficiencies/excesses,
and providing health insights
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import Patient, VitaminLevels, MicronutrientLevels, BloodParameters, Medication, GeneticData
from typing import List, Dict, Optional, Tuple


# Reference ranges for vitamins (in standard units)
VITAMIN_REFERENCE_RANGES = {
    'vitamin_a': {'low': 30, 'high': 100, 'unit': 'μg/dL'},  # Normal: 30-100
    'vitamin_d': {'low': 30, 'high': 100, 'unit': 'ng/mL'},  # Optimal: 30-100
    'vitamin_e': {'low': 5, 'high': 20, 'unit': 'mg/dL'},  # Normal: 5-20
    'vitamin_k': {'low': 0.1, 'high': 2.2, 'unit': 'ng/mL'},  # Normal: 0.1-2.2
    'vitamin_b1': {'low': 2.5, 'high': 7.5, 'unit': 'ng/mL'},  # Normal: 2.5-7.5
    'vitamin_b2': {'low': 4, 'high': 24, 'unit': 'ng/mL'},  # Normal: 4-24
    'vitamin_b3': {'low': 0.5, 'high': 8.4, 'unit': 'ng/mL'},  # Normal: 0.5-8.4
    'vitamin_b5': {'low': 0.2, 'high': 1.8, 'unit': 'μg/mL'},  # Normal: 0.2-1.8
    'vitamin_b6': {'low': 5, 'high': 30, 'unit': 'ng/mL'},  # Normal: 5-30
    'vitamin_b7': {'low': 0.2, 'high': 0.5, 'unit': 'ng/mL'},  # Normal: 0.2-0.5
    'vitamin_b9': {'low': 4, 'high': 20, 'unit': 'ng/mL'},  # Normal: 4-20
    'vitamin_b12': {'low': 200, 'high': 900, 'unit': 'pg/mL'},  # Normal: 200-900
    'vitamin_c': {'low': 0.6, 'high': 2.0, 'unit': 'mg/dL'},  # Normal: 0.6-2.0
}

# Reference ranges for micronutrients
MICRONUTRIENT_REFERENCE_RANGES = {
    'calcium': {'low': 8.5, 'high': 10.5, 'unit': 'mg/dL'},
    'magnesium': {'low': 1.7, 'high': 2.2, 'unit': 'mg/dL'},
    'phosphorus': {'low': 2.5, 'high': 4.5, 'unit': 'mg/dL'},
    'potassium': {'low': 3.5, 'high': 5.0, 'unit': 'mEq/L'},
    'sodium': {'low': 136, 'high': 145, 'unit': 'mEq/L'},
    'zinc': {'low': 70, 'high': 120, 'unit': 'μg/dL'},
    'selenium': {'low': 70, 'high': 150, 'unit': 'μg/L'},
    'copper': {'low': 70, 'high': 140, 'unit': 'μg/dL'},
    'manganese': {'low': 0.4, 'high': 1.8, 'unit': 'μg/L'},
    'chromium': {'low': 0.05, 'high': 0.5, 'unit': 'μg/L'},
    'molybdenum': {'low': 0.1, 'high': 3.0, 'unit': 'μg/L'},
    'omega_3': {'low': 50, 'high': 200, 'unit': 'mg/dL'},
    'omega_6': {'low': 100, 'high': 300, 'unit': 'mg/dL'},
    'coenzyme_q10': {'low': 0.5, 'high': 2.0, 'unit': 'μg/mL'},
}


def get_vitamin_status(value: Optional[float], vitamin_name: str) -> str:
    """Determine if a vitamin level is low, normal, or high"""
    if value is None:
        return "Not Tested"
    
    if vitamin_name not in VITAMIN_REFERENCE_RANGES:
        return "Unknown"
    
    ref_range = VITAMIN_REFERENCE_RANGES[vitamin_name]
    if value < ref_range['low']:
        return "Low"
    elif value > ref_range['high']:
        return "High"
    else:
        return "Normal"


def get_micronutrient_status(value: Optional[float], micronutrient_name: str) -> str:
    """Determine if a micronutrient level is low, normal, or high"""
    if value is None:
        return "Not Tested"
    
    if micronutrient_name not in MICRONUTRIENT_REFERENCE_RANGES:
        return "Unknown"
    
    ref_range = MICRONUTRIENT_REFERENCE_RANGES[micronutrient_name]
    if value < ref_range['low']:
        return "Low"
    elif value > ref_range['high']:
        return "High"
    else:
        return "Normal"


def analyze_vitamin_trends(session: Session, patient_id: int, days_back: int = 365) -> Dict:
    """
    Analyze vitamin level trends over time for a patient
    Returns a dictionary with trends, deficiencies, and excesses
    """
    cutoff_date = datetime.now().date() - timedelta(days=days_back)
    
    # Get all vitamin level records for the patient
    records = session.query(VitaminLevels).filter(
        VitaminLevels.patient_id == patient_id,
        VitaminLevels.test_date >= cutoff_date
    ).order_by(VitaminLevels.test_date).all()
    
    if not records:
        return {
            'has_data': False,
            'message': 'No vitamin level data found for the specified period'
        }
    
    analysis = {
        'has_data': True,
        'total_records': len(records),
        'deficiencies': [],
        'excesses': [],
        'trends': {},
        'recommendations': []
    }
    
    # Check each vitamin
    vitamin_fields = [
        'vitamin_a', 'vitamin_d', 'vitamin_e', 'vitamin_k',
        'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b5',
        'vitamin_b6', 'vitamin_b7', 'vitamin_b9', 'vitamin_b12', 'vitamin_c'
    ]
    
    for vitamin in vitamin_fields:
        values = []
        dates = []
        
        for record in records:
            value = getattr(record, vitamin)
            if value is not None:
                values.append(value)
                dates.append(record.test_date)
        
        if values:
            latest_value = values[-1]
            latest_date = dates[-1]
            status = get_vitamin_status(latest_value, vitamin)
            
            # Calculate trend
            if len(values) > 1:
                trend = "Increasing" if values[-1] > values[0] else "Decreasing" if values[-1] < values[0] else "Stable"
                avg_value = sum(values) / len(values)
            else:
                trend = "Single Reading"
                avg_value = latest_value
            
            analysis['trends'][vitamin] = {
                'latest_value': latest_value,
                'latest_date': latest_date,
                'status': status,
                'trend': trend,
                'average': avg_value,
                'readings': len(values)
            }
            
            # Identify deficiencies and excesses
            if status == "Low":
                ref_range = VITAMIN_REFERENCE_RANGES[vitamin]
                deficiency_level = ((ref_range['low'] - latest_value) / ref_range['low']) * 100
                analysis['deficiencies'].append({
                    'vitamin': vitamin.replace('_', ' ').title(),
                    'value': latest_value,
                    'unit': ref_range['unit'],
                    'reference_low': ref_range['low'],
                    'deficiency_percent': round(deficiency_level, 1),
                    'date': latest_date
                })
            elif status == "High":
                ref_range = VITAMIN_REFERENCE_RANGES[vitamin]
                excess_level = ((latest_value - ref_range['high']) / ref_range['high']) * 100
                analysis['excesses'].append({
                    'vitamin': vitamin.replace('_', ' ').title(),
                    'value': latest_value,
                    'unit': ref_range['unit'],
                    'reference_high': ref_range['high'],
                    'excess_percent': round(excess_level, 1),
                    'date': latest_date
                })
    
    # Generate recommendations
    if analysis['deficiencies']:
        analysis['recommendations'].append({
            'type': 'supplement',
            'priority': 'high',
            'message': f"Consider supplementation for {len(analysis['deficiencies'])} deficient vitamins"
        })
    
    if analysis['excesses']:
        analysis['recommendations'].append({
            'type': 'monitoring',
            'priority': 'medium',
            'message': f"Monitor {len(analysis['excesses'])} vitamins showing elevated levels"
        })
    
    return analysis


def analyze_micronutrient_trends(session: Session, patient_id: int, days_back: int = 365) -> Dict:
    """Analyze micronutrient level trends over time"""
    cutoff_date = datetime.now().date() - timedelta(days=days_back)
    
    records = session.query(MicronutrientLevels).filter(
        MicronutrientLevels.patient_id == patient_id,
        MicronutrientLevels.test_date >= cutoff_date
    ).order_by(MicronutrientLevels.test_date).all()
    
    if not records:
        return {'has_data': False, 'message': 'No micronutrient data found'}
    
    analysis = {
        'has_data': True,
        'total_records': len(records),
        'deficiencies': [],
        'excesses': [],
        'trends': {}
    }
    
    micronutrient_fields = [
        'calcium', 'magnesium', 'phosphorus', 'potassium', 'sodium',
        'zinc', 'selenium', 'copper', 'manganese', 'chromium',
        'molybdenum', 'omega_3', 'omega_6', 'coenzyme_q10'
    ]
    
    for micronutrient in micronutrient_fields:
        values = []
        dates = []
        
        for record in records:
            value = getattr(record, micronutrient)
            if value is not None:
                values.append(value)
                dates.append(record.test_date)
        
        if values:
            latest_value = values[-1]
            latest_date = dates[-1]
            status = get_micronutrient_status(latest_value, micronutrient)
            
            if len(values) > 1:
                trend = "Increasing" if values[-1] > values[0] else "Decreasing" if values[-1] < values[0] else "Stable"
            else:
                trend = "Single Reading"
            
            analysis['trends'][micronutrient] = {
                'latest_value': latest_value,
                'latest_date': latest_date,
                'status': status,
                'trend': trend
            }
            
            if status == "Low":
                ref_range = MICRONUTRIENT_REFERENCE_RANGES[micronutrient]
                analysis['deficiencies'].append({
                    'micronutrient': micronutrient.replace('_', ' ').title(),
                    'value': latest_value,
                    'unit': ref_range['unit'],
                    'reference_low': ref_range['low'],
                    'date': latest_date
                })
            elif status == "High":
                ref_range = MICRONUTRIENT_REFERENCE_RANGES[micronutrient]
                analysis['excesses'].append({
                    'micronutrient': micronutrient.replace('_', ' ').title(),
                    'value': latest_value,
                    'unit': ref_range['unit'],
                    'reference_high': ref_range['high'],
                    'date': latest_date
                })
    
    return analysis


def generate_health_insights(session: Session, patient_id: int) -> Dict:
    """
    Generate comprehensive health insights based on all available data
    """
    insights = {
        'patient_id': patient_id,
        'vitamin_analysis': None,
        'micronutrient_analysis': None,
        'genetic_insights': [],
        'medication_recommendations': [],
        'overall_recommendations': []
    }
    
    # Analyze vitamins
    vitamin_analysis = analyze_vitamin_trends(session, patient_id)
    insights['vitamin_analysis'] = vitamin_analysis
    
    # Analyze micronutrients
    micronutrient_analysis = analyze_micronutrient_trends(session, patient_id)
    insights['micronutrient_analysis'] = micronutrient_analysis
    
    # Check genetic data for relevant insights
    genetic_records = session.query(GeneticData).filter(
        GeneticData.patient_id == patient_id
    ).order_by(desc(GeneticData.test_date)).all()
    
    for genetic_record in genetic_records:
        # MTHFR mutations can affect folate metabolism
        if genetic_record.mthfr_c677t and genetic_record.mthfr_c677t in ['CT', 'TT']:
            insights['genetic_insights'].append({
                'type': 'MTHFR Variant',
                'variant': genetic_record.mthfr_c677t,
                'implication': 'May require methylated folate supplementation instead of folic acid',
                'priority': 'high'
            })
        
        if genetic_record.mthfr_a1298c and genetic_record.mthfr_a1298c in ['AC', 'CC']:
            insights['genetic_insights'].append({
                'type': 'MTHFR Variant',
                'variant': genetic_record.mthfr_a1298c,
                'implication': 'May affect folate metabolism',
                'priority': 'medium'
            })
        
        if genetic_record.brca1_mutation or genetic_record.brca2_mutation:
            insights['genetic_insights'].append({
                'type': 'BRCA Mutation',
                'implication': 'Increased risk for breast and ovarian cancer. Regular screening recommended.',
                'priority': 'high'
            })
    
    # Check current medications
    active_medications = session.query(Medication).filter(
        Medication.patient_id == patient_id,
        Medication.is_active == True
    ).all()
    
    # Generate medication-related recommendations
    if vitamin_analysis.get('deficiencies'):
        for deficiency in vitamin_analysis['deficiencies']:
            vitamin_name = deficiency['vitamin'].lower().replace(' ', '_')
            
            # Check if already on supplementation
            supplementing = any(
                med.medication_name.lower().find(vitamin_name.replace('_', ' ')) != -1
                for med in active_medications
            )
            
            if not supplementing:
                insights['medication_recommendations'].append({
                    'type': 'supplement',
                    'vitamin': deficiency['vitamin'],
                    'reason': f"Deficiency detected: {deficiency['value']} {deficiency['unit']} (Reference: {deficiency['reference_low']}+)",
                    'priority': 'high'
                })
    
    # Overall recommendations
    if vitamin_analysis.get('deficiencies'):
        insights['overall_recommendations'].append({
            'category': 'Nutrition',
            'recommendation': f"Address {len(vitamin_analysis['deficiencies'])} vitamin deficiencies",
            'priority': 'high'
        })
    
    if micronutrient_analysis.get('deficiencies'):
        insights['overall_recommendations'].append({
            'category': 'Nutrition',
            'recommendation': f"Address {len(micronutrient_analysis['deficiencies'])} micronutrient deficiencies",
            'priority': 'medium'
        })
    
    if insights['genetic_insights']:
        insights['overall_recommendations'].append({
            'category': 'Genetics',
            'recommendation': 'Review genetic test results and consider personalized treatment approaches',
            'priority': 'high'
        })
    
    return insights

