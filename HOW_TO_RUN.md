# How to Run HealthAPP - Developer Guide

This guide will help you set up, run, and develop the Health Database Application.

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
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the web application
python app_web.py

# 3. Open browser to http://localhost:5000
```

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
- **SQLAlchemy** (2.0.36+) - Database ORM
- **Flask** (3.0.0+) - Web framework

### Step 4: Verify Installation

```bash
python -c "import flask, sqlalchemy; print('All dependencies installed!')"
```

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
Health Database Application - Web Server
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
└── health_database.db        # SQLite database (created automatically)
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

### Database File

- **Location:** `health_database.db` (in project root)
- **Type:** SQLite (file-based database)
- **Backup:** Copy `health_database.db` to backup location

### Running Migrations

When you add new fields to models:

```bash
python migrate_database.py
```

This adds new columns without losing data.

### Verifying Database Schema

```bash
python verify_database.py
```

### Resetting Database (WARNING: Deletes all data)

```bash
# Delete the database file
rm health_database.db  # Linux/Mac
del health_database.db  # Windows

# Restart the app - it will recreate the database
python app_web.py
```

### Database Schema Changes

**To add a new field:**

1. **Update the model** in `models.py`:
   ```python
   class Patient(Base):
       # ... existing fields
       new_field = Column(String(100))  # Add new field
   ```

2. **Run migration:**
   ```bash
   python migrate_database.py
   ```

3. **Update forms** in templates if needed

4. **Update routes** in `app_web.py` to handle the new field

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

**Step 2: Run Migration**
```bash
python migrate_database.py
```

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
2. Run `python migrate_database.py`
3. Edit `templates/patient_form.html` - Add input field
4. Edit `app_web.py` - Update `add_patient()` and `edit_patient()` routes
5. Test by adding/editing a patient

### Adding a New Test Type

1. Create new model in `models.py` (e.g., `NewTestType`)
2. Add relationship to `Patient` model
3. Create route in `app_web.py`
4. Create template in `templates/`
5. Add navigation link
6. Run migration

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

#### 5. **Database Schema Errors**

**Error:** `no such column: ...`

**Solution:**
```bash
# Run migration
python migrate_database.py

# Or verify schema
python verify_database.py

# If needed, reset database (WARNING: loses data)
# Delete health_database.db and restart app
```

### Debug Mode

Enable Flask debug mode for detailed error messages:

In `app_web.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

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

- [ ] Change Flask secret key
- [ ] Disable debug mode
- [ ] Set up proper database backups
- [ ] Configure HTTPS
- [ ] Add authentication/authorization
- [ ] Set up logging
- [ ] Configure proper error handling
- [ ] Use production WSGI server (Gunicorn, uWSGI)

### Environment Variables

Create `.env` file:
```
FLASK_SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///health_database.db
FLASK_ENV=production
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

