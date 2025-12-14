"""
Flask Web Application for Health Database System
Run this file to start the web server: python app_web.py
Then open http://localhost:5000 in your browser
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date, timedelta
from database import init_database, get_session, close_session
from models import (
    Patient, BloodParameters, ReproductiveHealth, VitaminLevels,
    MicronutrientLevels, Medication, GeneticData, PatientNeeds,
    GynecologicalRiskIndicators
)
from analysis import generate_health_insights, analyze_vitamin_trends, analyze_micronutrient_trends
from sqlalchemy import desc, func, event
from database import engine

app = Flask(__name__)
app.secret_key = 'health-database-secret-key-change-in-production'

# Initialize database on startup
init_database()

# Run migrations to add new columns/tables
try:
    from migrate_database import migrate_database
    migrate_database()
except Exception as e:
    print(f"Note: Migration check completed (some columns may already exist): {e}")

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas for better compatibility"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@app.context_processor
def inject_today():
    """Make today's date available to all templates"""
    return dict(today=date.today())


@app.route('/')
def index():
    """Home page - redirect to dashboard"""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """
    Advanced dashboard with statistics and overview
    Optimized to reduce database queries using joins and bulk operations
    """
    session = get_session()
    try:
        # Get statistics (optimized single queries)
        total_patients = session.query(Patient).count()
        active_medications = session.query(Medication).filter_by(is_active=True).count()
        genetic_tests = session.query(GeneticData).count()
        
        # Recent patients
        recent_patients = session.query(Patient).order_by(desc(Patient.created_at)).limit(5).all()
        
        # Recent activity (last 7 days) - single query
        seven_days_ago = datetime.now().date() - timedelta(days=7)
        recent_vitamin_tests = session.query(VitaminLevels).filter(VitaminLevels.test_date >= seven_days_ago).count()
        recent_blood_tests = session.query(BloodParameters).filter(BloodParameters.test_date >= seven_days_ago).count()
        
        # Optimize: Get all patients with their latest test data in bulk
        # Use subqueries to get latest test dates per patient
        
        # Get latest vitamin test per patient
        latest_vitamin_subq = session.query(
            VitaminLevels.patient_id,
            func.max(VitaminLevels.test_date).label('max_date')
        ).group_by(VitaminLevels.patient_id).subquery()
        
        # Get latest blood test per patient
        latest_blood_subq = session.query(
            BloodParameters.patient_id,
            func.max(BloodParameters.test_date).label('max_date')
        ).group_by(BloodParameters.patient_id).subquery()
        
        # Join to get patients with recent tests
        patients_with_recent_tests_query = session.query(
            Patient,
            latest_vitamin_subq.c.max_date.label('last_vitamin_test'),
            latest_blood_subq.c.max_date.label('last_blood_test')
        ).outerjoin(
            latest_vitamin_subq, Patient.id == latest_vitamin_subq.c.patient_id
        ).outerjoin(
            latest_blood_subq, Patient.id == latest_blood_subq.c.patient_id
        ).filter(
            (latest_vitamin_subq.c.max_date != None) | (latest_blood_subq.c.max_date != None)
        ).limit(10).all()
        
        # Convert to dict format for template
        patients_with_recent_tests_list = []
        for result in patients_with_recent_tests_query:
            patients_with_recent_tests_list.append({
                'patient': result[0],  # Patient object
                'last_vitamin_test': result[1],  # last_vitamin_test date
                'last_blood_test': result[2]  # last_blood_test date
            })
        
        # Optimize: Get all patients needing attention in bulk
        # Get all vitamin levels with deficiencies
        all_vitamin_levels = session.query(VitaminLevels).join(Patient).all()
        patients_with_deficiencies = set()
        
        from analysis import get_vitamin_status, VITAMIN_REFERENCE_RANGES
        for vl in all_vitamin_levels:
            for vitamin_field in ['vitamin_d', 'vitamin_b12', 'vitamin_b9', 'vitamin_c']:
                value = getattr(vl, vitamin_field)
                if value and get_vitamin_status(value, vitamin_field) == "Low":
                    patients_with_deficiencies.add(vl.patient_id)
                    break
        
        patients_needing_attention = len(patients_with_deficiencies)
        
        # Optimize: Get patients with protein issues using bulk query
        # Get all recent blood tests (one per patient, latest)
        recent_blood_tests = session.query(
            BloodParameters.patient_id,
            func.max(BloodParameters.test_date).label('max_date')
        ).group_by(BloodParameters.patient_id).subquery()
        
        blood_with_protein = session.query(
            BloodParameters, Patient
        ).join(
            Patient, BloodParameters.patient_id == Patient.id
        ).join(
            recent_blood_tests,
            (BloodParameters.patient_id == recent_blood_tests.c.patient_id) &
            (BloodParameters.test_date == recent_blood_tests.c.max_date)
        ).all()
        
        patients_with_protein_issues = []
        for blood, patient in blood_with_protein:
            issues = []
            if blood.total_protein and (blood.total_protein < 6.0 or blood.total_protein > 8.3):
                issues.append(f"Total Protein: {blood.total_protein} g/dL")
            if blood.albumin and (blood.albumin < 3.5 or blood.albumin > 5.0):
                issues.append(f"Albumin: {blood.albumin} g/dL")
            if blood.c_reactive_protein and blood.c_reactive_protein > 3.0:
                issues.append(f"CRP elevated: {blood.c_reactive_protein} mg/L")
            if blood.hemoglobin_a1c and blood.hemoglobin_a1c > 5.7:
                issues.append(f"HbA1c elevated: {blood.hemoglobin_a1c}%")
            
            if issues:
                patients_with_protein_issues.append({
                    'patient': patient,
                    'issues': issues,
                    'test_date': blood.test_date
                })
        
        # Optimize: Get patients with inactive medications in bulk
        inactive_meds_by_patient = session.query(
            Medication.patient_id,
            func.count(Medication.id).label('med_count')
        ).filter_by(is_active=False).group_by(Medication.patient_id).all()
        
        patient_ids_with_inactive = {med[0]: med[1] for med in inactive_meds_by_patient}
        
        if patient_ids_with_inactive:
            patients_with_inactive_meds_data = session.query(
                Patient, Medication
            ).join(
                Medication, Patient.id == Medication.patient_id
            ).filter(
                Medication.patient_id.in_(patient_ids_with_inactive.keys()),
                Medication.is_active == False
            ).order_by(Medication.start_date.desc()).all()
            
            # Group medications by patient
            patients_with_inactive_meds_dict = {}
            for patient, med in patients_with_inactive_meds_data:
                if patient.id not in patients_with_inactive_meds_dict:
                    patients_with_inactive_meds_dict[patient.id] = {
                        'patient': patient,
                        'medications': [],
                        'count': patient_ids_with_inactive[patient.id]
                    }
                patients_with_inactive_meds_dict[patient.id]['medications'].append(med)
            
            patients_with_inactive_meds = list(patients_with_inactive_meds_dict.values())[:10]
        else:
            patients_with_inactive_meds = []
        
        # Optimize: Get gynecological risks in bulk
        patients_with_gyn_risks = []
        try:
            # Get latest risk assessment per patient
            latest_gyn_risks_subq = session.query(
                GynecologicalRiskIndicators.patient_id,
                func.max(GynecologicalRiskIndicators.record_date).label('max_date')
            ).group_by(GynecologicalRiskIndicators.patient_id).subquery()
            
            gyn_risks_data = session.query(
                GynecologicalRiskIndicators, Patient, GeneticData
            ).join(
                Patient, GynecologicalRiskIndicators.patient_id == Patient.id
            ).outerjoin(
                GeneticData, Patient.id == GeneticData.patient_id
            ).join(
                latest_gyn_risks_subq,
                (GynecologicalRiskIndicators.patient_id == latest_gyn_risks_subq.c.patient_id) &
                (GynecologicalRiskIndicators.record_date == latest_gyn_risks_subq.c.max_date)
            ).all()
            
            for risk, patient, genetic in gyn_risks_data:
                risk_factors = []
                
                if risk.family_history_breast_cancer or risk.family_history_ovarian_cancer:
                    risk_factors.append("Family History")
                if risk.personal_history_breast_cancer or risk.personal_history_ovarian_cancer:
                    risk_factors.append("Personal History")
                if genetic and (genetic.brca1_mutation or genetic.brca2_mutation):
                    risk_factors.append("BRCA Mutation")
                if risk.overall_risk_level in ['High', 'Very High']:
                    risk_factors.append(f"Risk Level: {risk.overall_risk_level}")
                if risk.ca125_level and risk.ca125_level > 35:
                    risk_factors.append(f"CA-125 elevated: {risk.ca125_level}")
                
                if risk_factors or risk.overall_risk_level:
                    patients_with_gyn_risks.append({
                        'patient': patient,
                        'risk_level': risk.overall_risk_level or 'Not Assessed',
                        'risk_factors': risk_factors,
                        'record_date': risk.record_date
                    })
        except Exception as e:
            print(f"Warning: Error loading gynecological risk indicators: {e}")
            patients_with_gyn_risks = []
        
        # Count statistics
        total_inactive_medications = session.query(Medication).filter_by(is_active=False).count()
        patients_with_gyn_risk_count = len(patients_with_gyn_risks)
        patients_with_protein_issues_count = len(patients_with_protein_issues)
        
        return render_template('dashboard.html',
                             total_patients=total_patients,
                             recent_patients=recent_patients,
                             patients_with_recent_tests=patients_with_recent_tests_list[:10],
                             patients_needing_attention=patients_needing_attention,
                             active_medications=active_medications,
                             genetic_tests=genetic_tests,
                             recent_vitamin_tests=recent_vitamin_tests,
                             recent_blood_tests=recent_blood_tests,
                             patients_with_protein_issues=patients_with_protein_issues[:10],
                             patients_with_inactive_meds=patients_with_inactive_meds[:10],
                             patients_with_gyn_risks=patients_with_gyn_risks[:10],
                             total_inactive_medications=sum(patient_ids_with_inactive.values()) if patient_ids_with_inactive else 0,
                             patients_with_gyn_risk_count=len(patients_with_gyn_risks),
                             patients_with_protein_issues_count=len(patients_with_protein_issues))
    finally:
        close_session(session)


@app.route('/patients')
def patients():
    """List all patients"""
    session = get_session()
    try:
        all_patients = session.query(Patient).order_by(Patient.last_name).all()
        return render_template('patients.html', patients=all_patients)
    finally:
        close_session(session)


@app.route('/patients/add', methods=['GET', 'POST'])
def add_patient():
    """Add a new patient"""
    if request.method == 'POST':
        session = get_session()
        try:
            patient_id = request.form.get('patient_id', '').strip()
            if not patient_id:
                flash('Patient ID is required', 'error')
                return redirect(url_for('add_patient'))
            
            # Check if patient ID already exists
            existing = session.query(Patient).filter_by(patient_id=patient_id).first()
            if existing:
                flash('Patient ID already exists', 'error')
                return redirect(url_for('add_patient'))
            
            dob_str = request.form.get('date_of_birth', '').strip()
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None
            
            patient = Patient(
                patient_id=patient_id,
                first_name=request.form.get('first_name', '').strip(),
                last_name=request.form.get('last_name', '').strip(),
                date_of_birth=dob,
                email=request.form.get('email', '').strip() or None,
                phone=request.form.get('phone', '').strip() or None,
                address=request.form.get('address', '').strip() or None
            )
            
            session.add(patient)
            session.commit()
            flash('Patient added successfully', 'success')
            return redirect(url_for('patients'))
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD', 'error')
        except Exception as e:
            flash(f'Error adding patient: {str(e)}', 'error')
        finally:
            close_session(session)
    
    return render_template('patient_form.html', patient=None)


@app.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
def edit_patient(patient_id):
    """Edit an existing patient"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        if request.method == 'POST':
            dob_str = request.form.get('date_of_birth', '').strip()
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None
            
            patient.first_name = request.form.get('first_name', '').strip()
            patient.last_name = request.form.get('last_name', '').strip()
            patient.date_of_birth = dob
            patient.email = request.form.get('email', '').strip() or None
            patient.phone = request.form.get('phone', '').strip() or None
            patient.address = request.form.get('address', '').strip() or None
            patient.updated_at = datetime.utcnow()
            
            session.commit()
            flash('Patient updated successfully', 'success')
            return redirect(url_for('patients'))
        
        return render_template('patient_form.html', patient=patient)
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD', 'error')
        return render_template('patient_form.html', patient=patient)
    except Exception as e:
        flash(f'Error updating patient: {str(e)}', 'error')
        return redirect(url_for('patients'))
    finally:
        close_session(session)


@app.route('/patients/<int:patient_id>/delete', methods=['POST'])
def delete_patient(patient_id):
    """Delete a patient"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if patient:
            session.delete(patient)
            session.commit()
            flash('Patient deleted successfully', 'success')
        else:
            flash('Patient not found', 'error')
    except Exception as e:
        flash(f'Error deleting patient: {str(e)}', 'error')
    finally:
        close_session(session)
    return redirect(url_for('patients'))


@app.route('/blood/<int:patient_id>', methods=['GET', 'POST'])
def blood_parameters(patient_id):
    """View and add blood parameters"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        if request.method == 'POST':
            test_date_str = request.form.get('test_date', '').strip()
            test_date = datetime.strptime(test_date_str, "%Y-%m-%d").date() if test_date_str else date.today()
            
            blood_params = BloodParameters(patient_id=patient_id, test_date=test_date)
            
            # Map form fields to model attributes
            float_fields = [
                'hemoglobin', 'hematocrit', 'white_blood_cells', 'red_blood_cells', 'platelets',
                'glucose', 'creatinine', 'bun', 'alt', 'ast',
                'total_cholesterol', 'hdl_cholesterol', 'ldl_cholesterol', 'triglycerides',
                'tsh', 't3', 't4', 'ferritin', 'iron', 'transferrin',
                'total_protein', 'albumin', 'globulin', 'a_g_ratio', 'c_reactive_protein', 'hemoglobin_a1c'
            ]
            
            for field in float_fields:
                value = request.form.get(field, '').strip()
                if value:
                    try:
                        setattr(blood_params, field, float(value))
                    except ValueError:
                        pass
            
            blood_params.notes = request.form.get('notes', '').strip() or None
            
            session.add(blood_params)
            session.commit()
            flash('Blood parameters saved successfully', 'success')
            return redirect(url_for('blood_parameters', patient_id=patient_id))
        
        # Get all blood parameter records
        records = session.query(BloodParameters).filter_by(patient_id=patient_id).order_by(desc(BloodParameters.test_date)).all()
        return render_template('blood_parameters.html', patient=patient, records=records)
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD', 'error')
        return redirect(url_for('blood_parameters', patient_id=patient_id))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('patients'))
    finally:
        close_session(session)


@app.route('/reproductive/<int:patient_id>', methods=['GET', 'POST'])
def reproductive_health(patient_id):
    """View and add reproductive health data"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        if request.method == 'POST':
            record_date_str = request.form.get('record_date', '').strip()
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date() if record_date_str else date.today()
            
            repro_health = ReproductiveHealth(
                patient_id=patient_id,
                record_date=record_date,
                pcos_diagnosis=request.form.get('pcos_diagnosis') == 'on',
                endometriosis=request.form.get('endometriosis') == 'on'
            )
            
            # Handle date fields
            lmp_str = request.form.get('last_menstrual_period', '').strip()
            if lmp_str:
                try:
                    repro_health.last_menstrual_period = datetime.strptime(lmp_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            due_date_str = request.form.get('due_date', '').strip()
            if due_date_str:
                try:
                    repro_health.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            # Handle integer fields
            int_fields = ['cycle_length', 'period_duration', 'weeks_pregnant']
            for field in int_fields:
                value = request.form.get(field, '').strip()
                if value:
                    try:
                        setattr(repro_health, field, int(value))
                    except ValueError:
                        pass
            
            # Handle float fields
            float_fields = ['fsh', 'lh', 'estradiol', 'progesterone', 'testosterone', 'prolactin']
            for field in float_fields:
                value = request.form.get(field, '').strip()
                if value:
                    try:
                        setattr(repro_health, field, float(value))
                    except ValueError:
                        pass
            
            # Handle string fields
            string_fields = ['menstrual_regularity', 'pregnancy_status', 'contraception_method']
            for field in string_fields:
                value = request.form.get(field, '').strip()
                if value:
                    setattr(repro_health, field, value)
            
            repro_health.notes = request.form.get('notes', '').strip() or None
            
            session.add(repro_health)
            session.commit()
            flash('Reproductive health data saved successfully', 'success')
            return redirect(url_for('reproductive_health', patient_id=patient_id))
        
        records = session.query(ReproductiveHealth).filter_by(patient_id=patient_id).order_by(desc(ReproductiveHealth.record_date)).all()
        return render_template('reproductive_health.html', patient=patient, records=records)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('patients'))
    finally:
        close_session(session)


@app.route('/vitamins/<int:patient_id>', methods=['GET', 'POST'])
def vitamin_levels(patient_id):
    """View and add vitamin levels"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        if request.method == 'POST':
            test_date_str = request.form.get('test_date', '').strip()
            test_date = datetime.strptime(test_date_str, "%Y-%m-%d").date() if test_date_str else date.today()
            
            vitamin_levels = VitaminLevels(patient_id=patient_id, test_date=test_date)
            
            vitamin_fields = [
                'vitamin_a', 'vitamin_d', 'vitamin_e', 'vitamin_k',
                'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b5',
                'vitamin_b6', 'vitamin_b7', 'vitamin_b9', 'vitamin_b12', 'vitamin_c'
            ]
            
            for field in vitamin_fields:
                value = request.form.get(field, '').strip()
                if value:
                    try:
                        setattr(vitamin_levels, field, float(value))
                    except ValueError:
                        pass
            
            vitamin_levels.notes = request.form.get('notes', '').strip() or None
            
            session.add(vitamin_levels)
            session.commit()
            flash('Vitamin levels saved successfully', 'success')
            return redirect(url_for('vitamin_levels', patient_id=patient_id))
        
        records = session.query(VitaminLevels).filter_by(patient_id=patient_id).order_by(desc(VitaminLevels.test_date)).all()
        return render_template('vitamin_levels.html', patient=patient, records=records)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('patients'))
    finally:
        close_session(session)


@app.route('/micronutrients/<int:patient_id>', methods=['GET', 'POST'])
def micronutrient_levels(patient_id):
    """View and add micronutrient levels"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        if request.method == 'POST':
            test_date_str = request.form.get('test_date', '').strip()
            test_date = datetime.strptime(test_date_str, "%Y-%m-%d").date() if test_date_str else date.today()
            
            micronutrient_levels = MicronutrientLevels(patient_id=patient_id, test_date=test_date)
            
            micronutrient_fields = [
                'calcium', 'magnesium', 'phosphorus', 'potassium', 'sodium',
                'zinc', 'selenium', 'copper', 'manganese', 'chromium',
                'molybdenum', 'omega_3', 'omega_6', 'coenzyme_q10'
            ]
            
            for field in micronutrient_fields:
                value = request.form.get(field, '').strip()
                if value:
                    try:
                        setattr(micronutrient_levels, field, float(value))
                    except ValueError:
                        pass
            
            micronutrient_levels.notes = request.form.get('notes', '').strip() or None
            
            session.add(micronutrient_levels)
            session.commit()
            flash('Micronutrient levels saved successfully', 'success')
            return redirect(url_for('micronutrient_levels', patient_id=patient_id))
        
        records = session.query(MicronutrientLevels).filter_by(patient_id=patient_id).order_by(desc(MicronutrientLevels.test_date)).all()
        return render_template('micronutrient_levels.html', patient=patient, records=records)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('patients'))
    finally:
        close_session(session)


@app.route('/medications/<int:patient_id>', methods=['GET', 'POST'])
def medications(patient_id):
    """View and add medications"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        if request.method == 'POST':
            medication_name = request.form.get('medication_name', '').strip()
            if not medication_name:
                flash('Medication name is required', 'error')
                return redirect(url_for('medications', patient_id=patient_id))
            
            start_date_str = request.form.get('start_date', '').strip()
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else date.today()
            
            end_date_str = request.form.get('end_date', '').strip()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
            
            status = request.form.get('status', 'Active').strip()
            discontinuation_date_str = request.form.get('discontinuation_date', '').strip()
            discontinuation_date = datetime.strptime(discontinuation_date_str, "%Y-%m-%d").date() if discontinuation_date_str else None
            
            medication = Medication(
                patient_id=patient_id,
                medication_name=medication_name,
                dosage=request.form.get('dosage', '').strip() or None,
                frequency=request.form.get('frequency', '').strip() or None,
                start_date=start_date,
                end_date=end_date,
                prescribing_physician=request.form.get('prescribing_physician', '').strip() or None,
                reason=request.form.get('reason', '').strip() or None,
                is_active=(status == 'Active'),
                status=status,
                discontinuation_reason=request.form.get('discontinuation_reason', '').strip() or None,
                discontinuation_date=discontinuation_date,
                notes=request.form.get('notes', '').strip() or None
            )
            
            session.add(medication)
            session.commit()
            flash('Medication saved successfully', 'success')
            return redirect(url_for('medications', patient_id=patient_id))
        
        # Separate active and inactive/discontinued medications
        active_meds = session.query(Medication).filter_by(patient_id=patient_id, is_active=True).order_by(desc(Medication.start_date)).all()
        inactive_meds = session.query(Medication).filter_by(patient_id=patient_id, is_active=False).order_by(desc(Medication.start_date)).all()
        return render_template('medications.html', patient=patient, active_medications=active_meds, inactive_medications=inactive_meds)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('patients'))
    finally:
        close_session(session)


@app.route('/genetic/<int:patient_id>', methods=['GET', 'POST'])
def genetic_data(patient_id):
    """View and add genetic data"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        if request.method == 'POST':
            test_date_str = request.form.get('test_date', '').strip()
            test_date = datetime.strptime(test_date_str, "%Y-%m-%d").date() if test_date_str else date.today()
            
            genetic_data = GeneticData(
                patient_id=patient_id,
                test_date=test_date,
                test_type=request.form.get('test_type', '').strip() or None,
                test_provider=request.form.get('test_provider', '').strip() or None,
                mthfr_c677t=request.form.get('mthfr_c677t', '').strip() or None,
                mthfr_a1298c=request.form.get('mthfr_a1298c', '').strip() or None,
                brca1_mutation=request.form.get('brca1_mutation') == 'on',
                brca2_mutation=request.form.get('brca2_mutation') == 'on',
                raw_data=request.form.get('raw_data', '').strip() or None,
                interpretation=request.form.get('interpretation', '').strip() or None,
                clinical_significance=request.form.get('clinical_significance', '').strip() or None,
                recommendations=request.form.get('recommendations', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None
            )
            
            session.add(genetic_data)
            session.commit()
            flash('Genetic data saved successfully', 'success')
            return redirect(url_for('genetic_data', patient_id=patient_id))
        
        records = session.query(GeneticData).filter_by(patient_id=patient_id).order_by(desc(GeneticData.test_date)).all()
        return render_template('genetic_data.html', patient=patient, records=records)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('patients'))
    finally:
        close_session(session)


@app.route('/needs/<int:patient_id>', methods=['GET', 'POST'])
def patient_needs(patient_id):
    """View and add patient needs"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        if request.method == 'POST':
            record_date_str = request.form.get('record_date', '').strip()
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date() if record_date_str else date.today()
            
            sleep_hours_str = request.form.get('sleep_hours', '').strip()
            sleep_hours = float(sleep_hours_str) if sleep_hours_str else None
            
            needs = PatientNeeds(
                patient_id=patient_id,
                record_date=record_date,
                dietary_restrictions=request.form.get('dietary_restrictions', '').strip() or None,
                special_diet=request.form.get('special_diet', '').strip() or None,
                activity_level=request.form.get('activity_level', '').strip() or None,
                smoking_status=request.form.get('smoking_status', '').strip() or None,
                alcohol_consumption=request.form.get('alcohol_consumption', '').strip() or None,
                sleep_hours=sleep_hours,
                health_goals=request.form.get('health_goals', '').strip() or None,
                special_requirements=request.form.get('special_requirements', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None
            )
            
            session.add(needs)
            session.commit()
            flash('Patient needs saved successfully', 'success')
            return redirect(url_for('patient_needs', patient_id=patient_id))
        
        records = session.query(PatientNeeds).filter_by(patient_id=patient_id).order_by(desc(PatientNeeds.record_date)).all()
        return render_template('patient_needs.html', patient=patient, records=records)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('patients'))
    finally:
        close_session(session)


@app.route('/gynecological-risk/<int:patient_id>', methods=['GET', 'POST'])
def gynecological_risk(patient_id):
    """View and add gynecological risk indicators"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        if request.method == 'POST':
            record_date_str = request.form.get('record_date', '').strip()
            record_date = datetime.strptime(record_date_str, "%Y-%m-%d").date() if record_date_str else date.today()
            
            risk_indicators = GynecologicalRiskIndicators(patient_id=patient_id, record_date=record_date)
            
            # Family history
            risk_indicators.family_history_ovarian_cancer = request.form.get('family_history_ovarian_cancer') == 'on'
            risk_indicators.family_history_breast_cancer = request.form.get('family_history_breast_cancer') == 'on'
            risk_indicators.family_history_cervical_cancer = request.form.get('family_history_cervical_cancer') == 'on'
            risk_indicators.family_history_endometrial_cancer = request.form.get('family_history_endometrial_cancer') == 'on'
            risk_indicators.family_history_details = request.form.get('family_history_details', '').strip() or None
            
            # Personal history
            risk_indicators.personal_history_breast_cancer = request.form.get('personal_history_breast_cancer') == 'on'
            risk_indicators.personal_history_ovarian_cancer = request.form.get('personal_history_ovarian_cancer') == 'on'
            risk_indicators.personal_history_cervical_cancer = request.form.get('personal_history_cervical_cancer') == 'on'
            risk_indicators.personal_history_endometrial_cancer = request.form.get('personal_history_endometrial_cancer') == 'on'
            
            # Risk factors - integer fields
            int_fields = ['age_at_menarche', 'age_at_menopause', 'first_pregnancy_age', 'number_of_pregnancies', 'breastfeeding_duration_months']
            for field in int_fields:
                value = request.form.get(field, '').strip()
                if value:
                    try:
                        setattr(risk_indicators, field, int(value))
                    except ValueError:
                        pass
            
            # Boolean fields
            risk_indicators.nulliparity = request.form.get('nulliparity') == 'on'
            risk_indicators.breastfeeding_history = request.form.get('breastfeeding_history') == 'on'
            risk_indicators.hormone_replacement_therapy = request.form.get('hormone_replacement_therapy') == 'on'
            risk_indicators.oral_contraceptive_use = request.form.get('oral_contraceptive_use') == 'on'
            risk_indicators.smoking_history = request.form.get('smoking_history') == 'on'
            risk_indicators.diabetes = request.form.get('diabetes') == 'on'
            risk_indicators.hypertension = request.form.get('hypertension') == 'on'
            risk_indicators.previous_gynecological_surgery = request.form.get('previous_gynecological_surgery') == 'on'
            risk_indicators.abnormal_pap_smear_history = request.form.get('abnormal_pap_smear_history') == 'on'
            risk_indicators.cervical_dysplasia_history = request.form.get('cervical_dysplasia_history') == 'on'
            
            # Float fields
            float_fields = ['hrt_duration_years', 'oc_duration_years', 'ca125_level', 'he4_level', 'roma_index', 
                          'smoking_pack_years', 'alcohol_consumption_weekly', 'bmi']
            for field in float_fields:
                value = request.form.get(field, '').strip()
                if value:
                    try:
                        setattr(risk_indicators, field, float(value))
                    except ValueError:
                        pass
            
            # Date fields
            date_fields = ['ca125_test_date', 'he4_test_date', 'roma_test_date', 'last_mammogram_date', 
                          'last_pap_smear_date', 'last_pelvic_ultrasound_date', 'next_screening_due_date']
            for field in date_fields:
                value = request.form.get(field, '').strip()
                if value:
                    try:
                        setattr(risk_indicators, field, datetime.strptime(value, "%Y-%m-%d").date())
                    except ValueError:
                        pass
            
            # String fields
            risk_indicators.physical_activity_level = request.form.get('physical_activity_level', '').strip() or None
            risk_indicators.mammogram_results = request.form.get('mammogram_results', '').strip() or None
            risk_indicators.pap_smear_results = request.form.get('pap_smear_results', '').strip() or None
            risk_indicators.overall_risk_level = request.form.get('overall_risk_level', '').strip() or None
            risk_indicators.autoimmune_diseases = request.form.get('autoimmune_diseases', '').strip() or None
            risk_indicators.pelvic_ultrasound_results = request.form.get('pelvic_ultrasound_results', '').strip() or None
            risk_indicators.gynecological_surgery_type = request.form.get('gynecological_surgery_type', '').strip() or None
            risk_indicators.risk_factors_summary = request.form.get('risk_factors_summary', '').strip() or None
            risk_indicators.recommended_screening_schedule = request.form.get('recommended_screening_schedule', '').strip() or None
            risk_indicators.notes = request.form.get('notes', '').strip() or None
            
            session.add(risk_indicators)
            session.commit()
            flash('Gynecological risk indicators saved successfully', 'success')
            return redirect(url_for('gynecological_risk', patient_id=patient_id))
        
        records = session.query(GynecologicalRiskIndicators).filter_by(patient_id=patient_id).order_by(desc(GynecologicalRiskIndicators.record_date)).all()
        return render_template('gynecological_risk.html', patient=patient, records=records)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('patients'))
    finally:
        close_session(session)


@app.route('/insights/<int:patient_id>')
def insights(patient_id):
    """Generate health insights for a patient"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        insights_data = generate_health_insights(session, patient_id)
        return render_template('insights.html', patient=patient, insights=insights_data, moment=datetime.now)
    except Exception as e:
        flash(f'Error generating insights: {str(e)}', 'error')
        return redirect(url_for('patients'))
    finally:
        close_session(session)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Health Database Application - Web Server")
    print("="*60)
    print("\nStarting server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

