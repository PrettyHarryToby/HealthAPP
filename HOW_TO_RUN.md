# How to Run Avenara - Developer Guide

This guide will help you set up, run, and develop Avenara.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Running the Application](#running-the-application)
5. [Project Structure](#project-structure)
6. [Development Guide](#development-guide)
7. [Database Management](#database-management)
8. [Adding New Features](#adding-new-features)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Copy .env.example to .env and configure MongoDB and an admin password

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start MongoDB locally, or use a MongoDB Atlas URI, then run:
python app_web.py

# 4. Open http://localhost:5000 and sign in
```

Clinical workspace routes require staff sign-in; the patient portal has a separate,
read-only, patient-scoped account flow. `/admin` shows MongoDB storage status and counts.
Patient self-registration checks the chart ID, date of birth, and registered email, then
verifies ownership with a Brevo SMTP one-time code. Configure the Brevo SMTP login, SMTP
key, and verified sender in `.env` or Render. Do not commit `.env`.

---

## Prerequisites

### Required Software

- **Python 3.7+** (Python 3.8+ recommended)
  - Check version: `python --version`
  - Download: https://www.python.org/downloads/

- **pip** (Python package installer)
  - Usually comes with Python
  - Check: `pip --version`

### Recommended Tools

- **Git** (for version control)
- **Code Editor** (VS Code, PyCharm, or any IDE)
- **Web Browser** (Chrome, Firefox, Edge)

---

## Installation

### Step 1: Clone or Download the Project

```bash
# If using Git
git clone <repository-url>
cd HealthAPP

# Or download and extract the ZIP file
```

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **Flask** - Web framework
- **PyMongo** - MongoDB client
- **SQLAlchemy** - Existing model definitions and SQLite import support

### Step 4: Verify Installation

```bash
python -c "import flask, sqlalchemy, pymongo; print('All dependencies installed!')"
```

### Step 5: Configure MongoDB and administrator access

Copy `.env.example` to `.env`. Set a MongoDB URI, database name, admin username,
and unique admin password. For patient self-signup, fill in the Brevo SMTP login,
SMTP key (not the API key), and a verified sender address. The checked-in example contains
placeholders and is not usable until configured. The Render blueprint prompts for the
secrets.

---

## Running the Application

### Option 1: Web Application (Recommended)

**Start the server:**
```bash
python app_web.py
```

**Output:**
```
============================================================
Avenara - Web Server
============================================================

Starting server...
Open your browser and navigate to: http://localhost:5000

Press Ctrl+C to stop the server
```

**Access the application:**
- Open your web browser
- Navigate to: `http://localhost:5000`
- The dashboard will load automatically

**Stop the server:**
- Press `Ctrl+C` in the terminal

### Option 2: Desktop GUI Application

```bash
python app.py
```

This opens a Tkinter-based desktop application window.

### Option 3: Using Batch/Script Files

**Windows:**
```bash
# Double-click or run:
RUN_SERVER.bat
# or
start_server.bat
```

**Linux/Mac:**
```bash
bash start_server.sh
```

---

## Project Structure

```
HealthAPP/
│
├── app_web.py                 # Main Flask web application
├── app.py                     # Desktop GUI application (Tkinter)
├── models.py                  # Database models (SQLAlchemy ORM)
├── database.py                # Database connection and initialization
├── migrate_sqlite_to_mongodb.py # Copy SQLite records into MongoDB
├── render.yaml                # Render's recognized deployment blueprint
├── .render.yaml               # Matching dotfile requested for this project
├── .env.example               # Local environment variable template
├── analysis.py                # Health analysis and insights functions
├── migrate_database.py        # Database migration script
├── verify_database.py         # Database schema verification
├── example_usage.py           # Example code for programmatic usage
│
├── requirements.txt           # Python dependencies
├── README.md                  # User documentation
├── HOW_TO_RUN.md             # This file - Developer guide
│
├── templates/                 # HTML templates (Jinja2)
│   ├── base.html             # Base template with navigation
│   ├── landing.html          # Staff and patient entry points
│   ├── portal_login.html     # Patient portal sign-in
│   ├── portal_register.html  # Verified patient self-registration
│   ├── portal_verify.html    # Email OTP verification
│   ├── portal_dashboard.html # Read-only patient-specific view
│   ├── admin_dashboard.html  # Protected MongoDB admin console
│   ├── dashboard.html         # Dashboard page
│   ├── patients.html         # Patient list page
│   ├── patient_form.html     # Add/edit patient form
│   ├── blood_parameters.html # Blood test entry form
│   ├── vitamin_levels.html   # Vitamin test entry form
│   ├── micronutrient_levels.html
│   ├── reproductive_health.html
│   ├── medications.html
│   ├── genetic_data.html
│   ├── patient_needs.html
│   ├── gynecological_risk.html
│   └── insights.html         # Health insights page
│
└── health_database.db        # Existing SQLite source for optional migration
```

---

## Development Guide

### Understanding the Codebase

#### 1. **Database Models** (`models.py`)

Defines all database tables using SQLAlchemy ORM:

```python
# Example: Patient model
class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50), unique=True)
    # ... more fields
```

**Key Models:**
- `Patient` - Patient demographics
- `BloodParameters` - Blood test results
- `VitaminLevels` - Vitamin test results
- `Medication` - Medication records
- `GynecologicalRiskIndicators` - Risk assessment data

#### 2. **Web Application** (`app_web.py`)

Flask routes handle HTTP requests:

```python
@app.route('/patients')
def patients():
    """List all patients"""
    session = get_session()
    try:
        all_patients = session.query(Patient).all()
        return render_template('patients.html', patients=all_patients)
    finally:
        close_session(session)
```

**Key Routes:**
- `/` - Redirects to dashboard
- `/dashboard` - Main dashboard with statistics
- `/patients` - Patient management
- `/blood/<patient_id>` - Blood parameters
- `/vitamins/<patient_id>` - Vitamin levels
- `/insights/<patient_id>` - Health insights

#### 3. **Analysis Functions** (`analysis.py`)

Health analysis and recommendations:

```python
def generate_health_insights(session, patient_id):
    """Generate comprehensive health insights"""
    # Analyzes vitamins, micronutrients, genetics
    # Returns recommendations
```

#### 4. **Templates** (`templates/`)

HTML templates using Jinja2:

```jinja2
{% extends "base.html" %}
{% block content %}
    <h1>{{ patient.first_name }} {{ patient.last_name }}</h1>
{% endblock %}
```

### Code Style Guidelines

1. **Use meaningful variable names:**
   ```python
   # Good
   patient_blood_results = session.query(BloodParameters).all()
   
   # Bad
   x = session.query(BP).all()
   ```

2. **Always close database sessions:**
   ```python
   session = get_session()
   try:
       # Your code here
   finally:
       close_session(session)
   ```

3. **Add docstrings to functions:**
   ```python
   def calculate_bmi(weight, height):
       """
       Calculate Body Mass Index
       
       Args:
           weight: Weight in kg
           height: Height in meters
       
       Returns:
           BMI value
       """
   ```

4. **Handle errors gracefully:**
   ```python
   try:
       # Risky operation
   except ValueError as e:
       flash('Invalid input', 'error')
   except Exception as e:
       flash(f'Error: {str(e)}', 'error')
   ```

---

## Database Management

### MongoDB

- The web application reads `MONGODB_URI` and `MONGODB_DATABASE` from the environment.
- Collections are created as records are written; patient IDs and record IDs are indexed.
- Back up the MongoDB database using MongoDB Atlas or `mongodump`.

### Importing existing SQLite records

The SQLite file is retained as the source. Copy its records to the configured MongoDB:

```bash
python migrate_sqlite_to_mongodb.py
```

The import is safe to rerun by record ID and does not delete or modify the SQLite file.
Set `SQLITE_DATABASE_URL` if the source file is not `health_database.db`.

The older `migrate_database.py`, `verify_database.py`, and `fix_database.py` scripts
are for inspecting or maintaining a legacy SQLite file only; they do not manage MongoDB.

### Database model changes

**To add a new field:**

1. **Update the model** in `models.py`:
   ```python
   class Patient(Base):
       # ... existing fields
       new_field = Column(String(100))  # Add new field
   ```

2. **Update forms** in templates if needed

3. **Update routes** in `app_web.py` to handle the new field

4. Add a focused test and deploy. MongoDB documents can contain the new field without a
   relational schema migration.

---

## Adding New Features

### Example: Adding a New Data Field

**Step 1: Update Model** (`models.py`)
```python
class Patient(Base):
    # ... existing fields
    emergency_contact = Column(String(200))
    emergency_phone = Column(String(20))
```

**Note:** MongoDB documents are schema-flexible, so adding a field does not require a
database migration. Register new model collections in `database.MODEL_TYPES`.

**Step 3: Update Form** (`templates/patient_form.html`)
```html
<div class="form-group">
    <label for="emergency_contact">Emergency Contact</label>
    <input type="text" id="emergency_contact" name="emergency_contact">
</div>
```

**Step 4: Update Route** (`app_web.py`)
```python
patient.emergency_contact = request.form.get('emergency_contact', '').strip() or None
```

**Step 5: Test**
- Restart server
- Add/edit a patient
- Verify data saves correctly

### Example: Adding a New Page

**Step 1: Create Route** (`app_web.py`)
```python
@app.route('/new-page')
def new_page():
    session = get_session()
    try:
        # Your logic here
        return render_template('new_page.html', data=data)
    finally:
        close_session(session)
```

**Step 2: Create Template** (`templates/new_page.html`)
```html
{% extends "base.html" %}
{% block title %}New Page{% endblock %}
{% block content %}
    <h1>New Page Content</h1>
{% endblock %}
```

**Step 3: Add Navigation** (`templates/base.html`)
```html
<nav>
    <a href="{{ url_for('new_page') }}">New Page</a>
</nav>
```

---

## Common Development Tasks

### Adding a New Patient Field

1. Edit `models.py` - Add column to `Patient` class
2. Edit `templates/patient_form.html` - Add input field
3. Edit `app_web.py` - Update `add_patient()` and `edit_patient()` routes
4. Test by adding/editing a patient

### Adding a New Test Type

1. Create new model in `models.py` (e.g., `NewTestType`)
2. Add relationship to `Patient` model
3. Create route in `app_web.py`
4. Create template in `templates/`
5. Add navigation link
6. Register the new collection and add focused tests

### Modifying Reference Ranges

Edit `analysis.py`:
```python
VITAMIN_REFERENCE_RANGES = {
    'vitamin_d': {'low': 30, 'high': 100, 'unit': 'ng/mL'},
    # Modify values as needed
}
```

### Customizing Dashboard

Edit `app_web.py` - `dashboard()` function:
- Modify statistics queries
- Add new stat cards
- Change date ranges

Edit `templates/dashboard.html`:
- Modify layout
- Add new sections
- Change styling

---

## Troubleshooting

### Common Issues

#### 1. **Port Already in Use**

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 5000
# Windows:
netstat -ano | findstr :5000

# Linux/Mac:
lsof -i :5000

# Kill the process or use a different port
# In app_web.py, change:
app.run(debug=True, host='0.0.0.0', port=5000)
# to:
app.run(debug=True, host='0.0.0.0', port=5001)
```

#### 2. **Database Locked**

**Error:** `database is locked`

**Solution:**
- Close all connections to the database
- Restart the application
- Check if another process is using the database

#### 3. **Module Not Found**

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install individually
pip install Flask SQLAlchemy
```

#### 4. **Template Not Found**

**Error:** `TemplateNotFound`

**Solution:**
- Ensure `templates/` folder exists
- Check template file names match exactly
- Verify Flask app can find templates folder

#### 5. **Legacy SQLite Schema Errors**

**Error:** `no such column: ...`

**Solution:** These commands apply only to an old SQLite source file. MongoDB does not
require relational schema migrations for new document fields.
```bash
# Legacy SQLite maintenance only
python migrate_database.py

# Or verify schema
python verify_database.py

# If needed, reset database (WARNING: loses data)
# Delete health_database.db and restart app
```

### Debug Mode

Enable Flask debug mode for detailed error messages:

Set `FLASK_DEBUG=true` in `.env` for local debugging. Do not enable it in production.

The local server binds to `127.0.0.1`; production runs with Gunicorn through Render.

**Benefits:**
- Auto-reload on code changes
- Detailed error pages
- Interactive debugger

**Warning:** Don't use in production!

---

## Performance Optimization

### Database Query Optimization

**Before (N+1 queries):**
```python
for patient in patients:
    meds = session.query(Medication).filter_by(patient_id=patient.id).all()
```

**After (Single query with join):**
```python
meds = session.query(Medication).join(Patient).all()
```

### Caching (Future Enhancement)

Consider adding caching for frequently accessed data:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_patient_stats(patient_id):
    # Expensive calculation
    pass
```

---

## Testing

### Manual Testing Checklist

- [ ] Add a new patient
- [ ] Edit patient information
- [ ] Add blood test results
- [ ] Add vitamin levels
- [ ] View insights
- [ ] Add medication
- [ ] Mark medication as inactive
- [ ] Add gynecological risk assessment
- [ ] View dashboard statistics

### Testing New Features

1. **Test with sample data:**
   ```bash
   python example_usage.py
   ```

2. **Test edge cases:**
   - Empty fields
   - Invalid dates
   - Missing patient
   - Duplicate patient IDs

3. **Test error handling:**
   - Invalid input formats
   - Database errors
   - Missing data

---

## Deployment Considerations

### Production Checklist

- [ ] Set a strong `FLASK_SECRET_KEY`
- [ ] Set unique administrator credentials
- [ ] Disable debug mode
- [ ] Set up proper database backups
- [ ] Configure HTTPS
- [x] Require administrator authentication for application routes
- [ ] Set up logging
- [ ] Configure proper error handling
- [ ] Use production WSGI server (Gunicorn, uWSGI)

### Environment Variables

Create `.env` file:
```
MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=healthapp
FLASK_SECRET_KEY=generate-a-long-random-secret
ADMIN_USERNAME=your-admin-name
ADMIN_PASSWORD=your-unique-strong-password
SESSION_COOKIE_SECURE=true
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=your-brevo-smtp-login
SMTP_PASSWORD=your-brevo-smtp-key
SMTP_FROM=your-verified-sender@example.com
SMTP_USE_TLS=true
```

---

## Contributing

### Code Contribution Guidelines

1. **Follow PEP 8** style guide
2. **Write clear commit messages**
3. **Test your changes**
4. **Update documentation**
5. **Handle errors gracefully**

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ... edit files ...

# Commit changes
git add .
git commit -m "Add new feature: description"

# Push to repository
git push origin feature/new-feature
```

---

## Additional Resources

### Documentation

- **Flask:** https://flask.palletsprojects.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Jinja2 Templates:** https://jinja.palletsprojects.com/

### Project Files Reference

- `models.py` - Database schema definitions
- `app_web.py` - Web application routes and logic
- `analysis.py` - Health analysis algorithms
- `database.py` - Database connection management
- `templates/` - HTML templates

---

## Support

For issues or questions:

1. Check this guide first
2. Review error messages carefully
3. Check database schema with `verify_database.py`
4. Review code comments in source files
5. Check Flask debug output in terminal

---

## Quick Reference

### Start Server
```bash
python app_web.py
```

### Run Migration
```bash
python migrate_database.py
```

### Verify Database
```bash
python verify_database.py
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Access Application
```
http://localhost:5000
```

---

**Happy Coding! 🚀**

