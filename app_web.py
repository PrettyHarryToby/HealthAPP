"""
Flask web application for Avenara
Run this file to start the web server: python app_web.py
Then open http://localhost:5000 in your browser
"""
import hmac
import hashlib
import os
import secrets
import smtplib
import ssl
from email.message import EmailMessage
from flask import Flask, abort, current_app, render_template, request, redirect, url_for, flash, jsonify, session as web_session
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import desc
from pymongo.errors import DuplicateKeyError
from werkzeug.security import check_password_hash, generate_password_hash
from database import init_database, get_session, close_session, get_database, get_model_types
from models import (
    Patient, BloodParameters, ReproductiveHealth, VitaminLevels,
    MicronutrientLevels, Medication, GeneticData, PatientNeeds,
    GynecologicalRiskIndicators
)
from analysis import generate_health_insights

app = Flask(__name__)
configured_secret = os.getenv("FLASK_SECRET_KEY", "")
if not configured_secret or configured_secret in {
    "replace-this-with-a-long-random-secret",
    "generate-a-long-random-secret",
}:
    configured_secret = secrets.token_hex(32)
app.secret_key = configured_secret
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
)

# Verify the configured MongoDB instance before accepting requests.
init_database()


@app.before_request
def require_admin_login():
    endpoint = request.endpoint or ""
    public_endpoints = {
        "index", "admin_login", "portal_login", "portal_register",
        "portal_verify", "portal_logout", "faq", "terms", "privacy",
        "health", "static",
    }
    if endpoint in public_endpoints:
        if web_session.get("admin_authenticated") and endpoint.startswith("portal_"):
            return redirect(url_for("dashboard"))
        if web_session.get("portal_patient_id") and endpoint.startswith("portal_") and endpoint != "portal_logout":
            return redirect(url_for("portal_dashboard"))
        if web_session.get("portal_patient_id") and endpoint == "portal_logout":
            return None
        if web_session.get("portal_patient_id") and endpoint.startswith("admin_"):
            return redirect(url_for("portal_dashboard"))
        return None
    if web_session.get("admin_authenticated"):
        if endpoint.startswith("portal_"):
            return redirect(url_for("dashboard"))
        return None
    if web_session.get("portal_patient_id"):
        if endpoint in {"portal_dashboard", "portal_logout"}:
            return None
        return redirect(url_for("portal_dashboard"))
    if endpoint.startswith("portal_"):
        return redirect(url_for("portal_login"))
    return redirect(url_for("admin_login", next=request.full_path))


@app.after_request
def prevent_sensitive_page_caching(response):
    response.headers["Cache-Control"] = "no-store, private"
    return response


def admin_credentials_configured():
    username = os.getenv("ADMIN_USERNAME", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    placeholders = {
        "change-this-before-use",
        "choose-a-unique-strong-password",
    }
    return bool(username and password and password not in placeholders)


def secure_compare(first, second):
    return hmac.compare_digest(first.encode("utf-8"), second.encode("utf-8"))


def valid_csrf_token():
    expected = web_session.get("csrf_token", "")
    provided = request.form.get("csrf_token", "")
    return bool(expected) and secure_compare(expected, provided)


def smtp_configured():
    configured = all(os.getenv(key, "").strip() for key in (
        "SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM",
    )) and (
        os.getenv("SMTP_PASSWORD") != "your-brevo-smtp-key"
        and os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    )
    try:
        port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        return False
    return configured and 1 <= port <= 65535


def send_portal_verification(email, code):
    message = EmailMessage()
    message["Subject"] = "Your Avenara verification code"
    message["From"] = os.environ["SMTP_FROM"]
    message["To"] = email
    message.set_content(
        f"Your verification code is {code}. It expires in 10 minutes. "
        "If you did not request this, you can ignore this message."
    )
    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(message)


@app.context_processor
def inject_today():
    """Make today's date available to all templates"""
    return dict(today=date.today(), csrf_token=web_session.get("csrf_token"))


@app.route("/health")
def health():
    """Render health check endpoint."""
    get_database().client.admin.command("ping")
    return jsonify(status="ok")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if web_session.get("admin_authenticated"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = os.getenv("ADMIN_USERNAME", "")
        password = os.getenv("ADMIN_PASSWORD", "")
        if not admin_credentials_configured():
            abort(503, description="Set ADMIN_USERNAME and ADMIN_PASSWORD in the environment.")
        if not valid_csrf_token():
            abort(400, description="Invalid form token. Reload the page and try again.")
        submitted_username = request.form.get("username", "")
        submitted_password = request.form.get("password", "")
        username_matches = secure_compare(submitted_username, username)
        password_matches = len(submitted_password) <= 256 and secure_compare(submitted_password, password)
        if username_matches and password_matches:
            web_session.clear()
            web_session["admin_authenticated"] = True
            web_session["admin_username"] = username
            web_session["csrf_token"] = secrets.token_urlsafe(32)
            get_database()["admin_events"].insert_one({
                "event": "login",
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
            })
            return redirect(url_for("dashboard"))
        flash("The username or password was not accepted.", "error")
    if not web_session.get("csrf_token"):
        web_session["csrf_token"] = secrets.token_urlsafe(32)
    return render_template(
        "admin_login.html",
        login_configured=admin_credentials_configured(),
    )


@app.route("/admin/logout")
def admin_logout():
    web_session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
def admin_dashboard():
    database = get_database()
    collection_names = [model.__tablename__ for model in get_model_types()]
    collections = [
        {"name": name, "count": database[name].count_documents({})}
        for name in collection_names
    ]
    events = list(database["admin_events"].find({}, {"_id": 0}).sort("created_at", -1).limit(8))
    return render_template(
        "admin_dashboard.html",
        collections=collections,
        total_documents=sum(item["count"] for item in collections),
        portal_users=database["portal_users"].count_documents({}),
        admin_events_count=database["admin_events"].count_documents({}),
        database_name=database.name,
        events=events,
    )


@app.route("/portal/login", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def portal_login():
    if request.method == "POST":
        if not valid_csrf_token():
            abort(400, description="Invalid form token. Reload the page and try again.")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        account = get_database()["portal_users"].find_one({"email": email}) if len(email) <= 254 else None
        if account and len(password) <= 256 and check_password_hash(account["password_hash"], password):
            web_session.clear()
            web_session["portal_patient_id"] = account["patient_ref"]
            web_session["csrf_token"] = secrets.token_urlsafe(32)
            get_database()["admin_events"].insert_one({
                "event": "patient_portal_login",
                "patient_ref": account["patient_ref"],
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None),
            })
            return redirect(url_for("portal_dashboard"))
        flash("The email or password was not accepted.", "error")
    if not web_session.get("csrf_token"):
        web_session["csrf_token"] = secrets.token_urlsafe(32)
    return render_template("portal_login.html")


@app.route("/portal/register", methods=["GET", "POST"])
def portal_register():
    if request.method == "POST":
        if not valid_csrf_token():
            abort(400, description="Invalid form token. Reload the page and try again.")
        if not smtp_configured():
            abort(503, description="Patient email verification is not configured. Contact the administrator.")

        patient_code = request.form.get("patient_id", "").strip()
        email = request.form.get("email", "").strip().lower()
        date_of_birth = request.form.get("date_of_birth", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not email or len(email) > 254 or "@" not in email:
            flash("Enter the email address registered with the clinic.", "error")
            return render_template("portal_register.html", signup_enabled=True)
        if not password or len(password) < 12 or len(password) > 256:
            flash("Use a password between 12 and 256 characters.", "error")
            return render_template("portal_register.html", signup_enabled=True)
        if password != confirm_password:
            flash("The passwords do not match.", "error")
            return render_template("portal_register.html", signup_enabled=True)
        try:
            supplied_dob = date.fromisoformat(date_of_birth)
        except ValueError:
            supplied_dob = None

        challenge_id = secrets.token_urlsafe(32)
        web_session["portal_challenge_id"] = challenge_id
        pending_collection = get_database()["portal_pending"]
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        email_hash = hashlib.sha256(email.encode("utf-8")).hexdigest()
        rate_collection = get_database()["portal_rate_limits"]
        recent_requests = rate_collection.count_documents({
            "email_hash": email_hash,
            "expires_at": {"$gt": now},
        })
        if recent_requests < 3:
            rate_collection.insert_one({
                "email_hash": email_hash,
                "expires_at": now + timedelta(hours=1),
            })
        db_session = get_session()
        try:
            patient = db_session.query(Patient).filter_by(patient_id=patient_code).first()
        finally:
            close_session(db_session)
        account_exists = get_database()["portal_users"].find_one({
            "$or": [
                {"email": email},
                {"patient_ref": patient.id if patient else -1},
            ]
        })
        details_match = bool(
            patient
            and supplied_dob == patient.date_of_birth
            and email == (patient.email or "").strip().lower()
        )

        if details_match and not account_exists and recent_requests < 3:
            code = f"{secrets.randbelow(1_000_000):06d}"
            pending_collection.delete_many({"patient_ref": patient.id})
            pending_collection.insert_one({
                "_id": challenge_id,
                "patient_ref": patient.id,
                "email": email,
                "password_hash": generate_password_hash(password),
                "code_hash": generate_password_hash(code),
                "attempts": 0,
                "created_at": now,
                "expires_at": now + timedelta(minutes=10),
            })
            try:
                send_portal_verification(email, code)
            except (OSError, smtplib.SMTPException, ValueError):
                current_app.logger.exception("Patient portal verification email could not be sent")
                pending_collection.delete_one({"_id": challenge_id})
                abort(503, description="Email delivery is temporarily unavailable. Try again later.")
        flash("If the details match a registered patient record, a verification code has been sent to its email.", "success")
        return redirect(url_for("portal_verify"))

    if not web_session.get("csrf_token"):
        web_session["csrf_token"] = secrets.token_urlsafe(32)
    return render_template("portal_register.html", signup_enabled=smtp_configured())


@app.route("/portal/verify", methods=["GET", "POST"])
def portal_verify():
    if request.method == "POST":
        if not valid_csrf_token():
            abort(400, description="Invalid form token. Reload the page and try again.")
        challenge_id = web_session.get("portal_challenge_id")
        collection = get_database()["portal_pending"]
        pending = collection.find_one({"_id": challenge_id}) if challenge_id else None
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not pending or pending["expires_at"] <= now or pending["attempts"] >= 5:
            if challenge_id:
                collection.delete_one({"_id": challenge_id})
            web_session.pop("portal_challenge_id", None)
            flash("The verification request is invalid or expired. Please register again.", "error")
            return redirect(url_for("portal_register"))

        code = request.form.get("code", "").strip()
        code_matches = len(code) == 6 and code.isdecimal() and check_password_hash(pending["code_hash"], code)
        if not code_matches:
            collection.update_one({"_id": challenge_id}, {"$inc": {"attempts": 1}})
            flash("The verification code was not accepted.", "error")
            return render_template("portal_verify.html", challenge_available=True)

        try:
            get_database()["portal_users"].insert_one({
                "patient_ref": pending["patient_ref"],
                "email": pending["email"],
                "password_hash": pending["password_hash"],
                "created_at": now,
            })
        except DuplicateKeyError:
            collection.delete_one({"_id": challenge_id})
            web_session.pop("portal_challenge_id", None)
            flash("An account already exists for these patient details. Sign in or contact the clinic.", "error")
            return redirect(url_for("portal_login"))

        collection.delete_one({"_id": challenge_id})
        web_session.clear()
        web_session["portal_patient_id"] = pending["patient_ref"]
        web_session["csrf_token"] = secrets.token_urlsafe(32)
        flash("Your patient portal is ready.", "success")
        return redirect(url_for("portal_dashboard"))

    if not web_session.get("csrf_token"):
        web_session["csrf_token"] = secrets.token_urlsafe(32)
    challenge_id = web_session.get("portal_challenge_id")
    pending = get_database()["portal_pending"].find_one({"_id": challenge_id}) if challenge_id else None
    return render_template("portal_verify.html", challenge_available=bool(pending))


@app.route("/portal")
def portal_dashboard():
    patient_id = web_session.get("portal_patient_id")
    account = get_database()["portal_users"].find_one({"patient_ref": patient_id})
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first() if account else None
        if not patient:
            web_session.clear()
            flash("This portal account is no longer available. Contact the clinic.", "error")
            return redirect(url_for("portal_login"))
        blood_records = session.query(BloodParameters).filter_by(patient_id=patient.id).order_by(
            desc(BloodParameters.test_date)
        ).limit(5).all()
        vitamin_records = session.query(VitaminLevels).filter_by(patient_id=patient.id).order_by(
            desc(VitaminLevels.test_date)
        ).limit(5).all()
        micronutrient_records = session.query(MicronutrientLevels).filter_by(patient_id=patient.id).order_by(
            desc(MicronutrientLevels.test_date)
        ).limit(5).all()
        active_medications = session.query(Medication).filter_by(
            patient_id=patient.id, is_active=True
        ).order_by(desc(Medication.start_date)).all()
        reproductive_records = session.query(ReproductiveHealth).filter_by(
            patient_id=patient.id
        ).order_by(desc(ReproductiveHealth.record_date)).limit(3).all()
        genetic_records = session.query(GeneticData).filter_by(
            patient_id=patient.id
        ).order_by(desc(GeneticData.test_date)).limit(3).all()
        risk_records = session.query(GynecologicalRiskIndicators).filter_by(
            patient_id=patient.id
        ).order_by(desc(GynecologicalRiskIndicators.record_date)).limit(3).all()
        needs_records = session.query(PatientNeeds).filter_by(
            patient_id=patient.id
        ).order_by(desc(PatientNeeds.record_date)).limit(3).all()
        return render_template(
            "portal_dashboard.html",
            patient=patient,
            blood_records=blood_records,
            vitamin_records=vitamin_records,
            micronutrient_records=micronutrient_records,
            active_medications=active_medications,
            reproductive_records=reproductive_records,
            genetic_records=genetic_records,
            risk_records=risk_records,
            needs_records=needs_records,
        )
    finally:
        close_session(session)


@app.route("/portal/logout")
def portal_logout():
    web_session.clear()
    return redirect(url_for("portal_login"))


@app.route('/')
def index():
    if web_session.get("admin_authenticated"):
        return redirect(url_for("dashboard"))
    if web_session.get("portal_patient_id"):
        return redirect(url_for("portal_dashboard"))
    return render_template("landing.html")


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route('/dashboard')
def dashboard():
    session = get_session()
    try:
        patients = session.query(Patient).all()
        medications = session.query(Medication).all()
        genetic_records = session.query(GeneticData).all()
        vitamin_records = session.query(VitaminLevels).all()
        blood_records = session.query(BloodParameters).all()
        risk_records = session.query(GynecologicalRiskIndicators).all()
        patient_by_id = {patient.id: patient for patient in patients}
        def latest_by_patient(records, date_field):
            latest = {}
            for record in records:
                previous = latest.get(record.patient_id)
                current_date = getattr(record, date_field) or date.min
                previous_date = getattr(previous, date_field) or date.min if previous else date.min
                if previous is None or current_date > previous_date:
                    latest[record.patient_id] = record
            return latest

        recent_patients = sorted(
            patients, key=lambda patient: patient.created_at or datetime.min, reverse=True
        )[:5]
        seven_days_ago = datetime.now().date() - timedelta(days=7)
        recent_vitamin_tests = sum(
            1 for record in vitamin_records if record.test_date and record.test_date >= seven_days_ago
        )
        recent_blood_test_count = sum(
            1 for record in blood_records if record.test_date and record.test_date >= seven_days_ago
        )
        latest_vitamins = latest_by_patient(vitamin_records, "test_date")
        latest_blood = latest_by_patient(blood_records, "test_date")
        patients_with_recent_tests_list = [
            {
                "patient": patient,
                "last_vitamin_test": latest_vitamins.get(patient.id).test_date if patient.id in latest_vitamins else None,
                "last_blood_test": latest_blood.get(patient.id).test_date if patient.id in latest_blood else None,
            }
            for patient in patients
            if patient.id in latest_vitamins or patient.id in latest_blood
        ][:10]

        patients_with_deficiencies = set()
        from analysis import get_vitamin_status
        for vl in vitamin_records:
            for vitamin_field in ['vitamin_d', 'vitamin_b12', 'vitamin_b9', 'vitamin_c']:
                value = getattr(vl, vitamin_field)
                if value and get_vitamin_status(value, vitamin_field) == "Low":
                    patients_with_deficiencies.add(vl.patient_id)
                    break
        patients_needing_attention = len(patients_with_deficiencies)

        patients_with_protein_issues = []
        for patient_id, blood in latest_blood.items():
            patient = patient_by_id.get(patient_id)
            if not patient:
                continue
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

        inactive_by_patient = {}
        for medication in medications:
            if not medication.is_active:
                inactive_by_patient.setdefault(medication.patient_id, []).append(medication)
        patients_with_inactive_meds = [
            {
                "patient": patient_by_id[patient_id],
                "medications": sorted(records, key=lambda med: med.start_date or date.min, reverse=True),
                "count": len(records),
            }
            for patient_id, records in inactive_by_patient.items()
            if patient_id in patient_by_id
        ][:10]

        patients_with_gyn_risks = []
        latest_risks = latest_by_patient(risk_records, "record_date")
        latest_genetics = latest_by_patient(genetic_records, "test_date")
        for patient_id, risk in latest_risks.items():
            patient = patient_by_id.get(patient_id)
            if not patient:
                continue
            genetic = latest_genetics.get(patient_id)
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
                    "patient": patient,
                    "risk_level": risk.overall_risk_level or "Not Assessed",
                    "risk_factors": risk_factors,
                    "record_date": risk.record_date,
                })
        
        return render_template('dashboard.html',
                             total_patients=len(patients),
                             recent_patients=recent_patients,
                             patients_with_recent_tests=patients_with_recent_tests_list,
                             patients_needing_attention=patients_needing_attention,
                             active_medications=sum(1 for med in medications if med.is_active),
                             genetic_tests=len(genetic_records),
                             recent_vitamin_tests=recent_vitamin_tests,
                             recent_blood_tests=recent_blood_test_count,
                             patients_with_protein_issues=patients_with_protein_issues[:10],
                             patients_with_inactive_meds=patients_with_inactive_meds,
                             patients_with_gyn_risks=patients_with_gyn_risks[:10],
                             total_inactive_medications=sum(len(records) for records in inactive_by_patient.values()),
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
            patient.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            
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
    port = int(os.getenv("PORT", "5000"))
    print("\n" + "="*60)
    print("Avenara - Web Server")
    print("="*60)
    print("\nStarting server...")
    print(f"Open your browser and navigate to: http://localhost:{port}")
    print("\nPress Ctrl+C to stop the server\n")
    app.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        host="127.0.0.1",
        port=port,
    )

