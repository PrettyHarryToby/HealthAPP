---
layout : none
render_with_liquid: false
---
# Developer Guide - Avenara

## Architecture Overview

### Technology Stack

- **Backend:** Python 3.7+
- **Web Framework:** Flask 3.0+
- **Database:** SQLite (via SQLAlchemy ORM)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Templates:** Jinja2
- **Icons:** Font Awesome 6.4.0

### Application Flow

```
User Request → Flask Route → Database Query → Process Data → Render Template → Response
```

---

## Code Organization

### File Responsibilities

#### `models.py`
- **Purpose:** Database schema definitions
- **Contains:** SQLAlchemy model classes
- **Key Classes:**
  - `Patient` - Core patient information
  - `BloodParameters` - Blood test results
  - `VitaminLevels` - Vitamin test tracking
  - `Medication` - Medication records
  - `GynecologicalRiskIndicators` - Risk assessment data

**Example:**
```python
class Patient(Base):
    """Patient information model"""
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50), unique=True, nullable=False)
    # ... more fields
```

#### `database.py`
- **Purpose:** Database connection management
- **Functions:**
  - `init_database()` - Create tables
  - `get_session()` - Get database session
  - `close_session()` - Close session

**Usage Pattern:**
```python
session = get_session()
try:
    # Database operations
    patients = session.query(Patient).all()
finally:
    close_session(session)
```

#### `app_web.py`
- **Purpose:** Flask web application routes
- **Structure:**
  - Route decorators (`@app.route`)
  - Request handling
  - Template rendering
  - Form processing

**Route Pattern:**
```python
@app.route('/path/<int:id>', methods=['GET', 'POST'])
def route_function(id):
    session = get_session()
    try:
        if request.method == 'POST':
            # Handle form submission
            pass
        # Handle GET request
        return render_template('template.html', data=data)
    finally:
        close_session(session)
```

#### `analysis.py`
- **Purpose:** Health analysis and insights
- **Functions:**
  - `analyze_vitamin_trends()` - Track vitamin changes
  - `generate_health_insights()` - Comprehensive analysis
  - Reference range checking

#### `templates/`
- **Purpose:** HTML templates (Jinja2)
- **Base Template:** `base.html` - Common layout
- **Page Templates:** Individual pages extend base

---

## Database Schema

### Entity Relationship Diagram (Conceptual)

```
Patient (1) ──< (Many) BloodParameters
Patient (1) ──< (Many) VitaminLevels
Patient (1) ──< (Many) Medication
Patient (1) ──< (Many) GeneticData
Patient (1) ──< (Many) GynecologicalRiskIndicators
Patient (1) ──< (Many) ReproductiveHealth
Patient (1) ──< (Many) MicronutrientLevels
Patient (1) ──< (Many) PatientNeeds
```

### Key Relationships

All data tables have a foreign key to `patients.id`:
- Cascade delete: Deleting a patient removes all related records
- One-to-many: One patient can have many records of each type

---

## Adding New Features - Step by Step

### Example: Adding a "Lab Results" Feature

#### Step 1: Define Model

Edit `models.py`:
```python
class LabResults(Base):
    """Laboratory test results"""
    __tablename__ = 'lab_results'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    test_date = Column(Date, nullable=False, default=datetime.utcnow)
    test_name = Column(String(200), nullable=False)
    result_value = Column(Float)
    reference_range = Column(String(100))
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="lab_results")
```

#### Step 2: Add Relationship to Patient

Edit `models.py` - `Patient` class:
```python
lab_results = relationship("LabResults", back_populates="patient", cascade="all, delete-orphan")
```

#### Step 3: Create Route

Edit `app_web.py`:
```python
@app.route('/lab-results/<int:patient_id>', methods=['GET', 'POST'])
def lab_results(patient_id):
    """View and add lab results"""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            flash('Patient not found', 'error')
            return redirect(url_for('patients'))
        
        if request.method == 'POST':
            # Handle form submission
            test_date = datetime.strptime(request.form.get('test_date'), "%Y-%m-%d").date()
            lab_result = LabResults(
                patient_id=patient_id,
                test_date=test_date,
                test_name=request.form.get('test_name'),
                result_value=float(request.form.get('result_value')) if request.form.get('result_value') else None,
                notes=request.form.get('notes') or None
            )
            session.add(lab_result)
            session.commit()
            flash('Lab result saved successfully', 'success')
            return redirect(url_for('lab_results', patient_id=patient_id))
        
        # GET request - show form and existing results
        records = session.query(LabResults).filter_by(patient_id=patient_id).order_by(desc(LabResults.test_date)).all()
        return render_template('lab_results.html', patient=patient, records=records)
    finally:
        close_session(session)
```

#### Step 4: Create Template

Create `templates/lab_results.html`:
{% raw %}
```html
{% extends "base.html" %}

{% block title %}Lab Results - {{ patient.first_name }} {{ patient.last_name }}{% endblock %}

{% block content %}
<div class="patient-info">
    <h2>{{ patient.first_name }} {{ patient.last_name }} ({{ patient.patient_id }})</h2>
</div>

<h3>Add Lab Result</h3>
<form method="POST">
    <div class="form-group">
        <label for="test_date">Test Date (YYYY-MM-DD)</label>
        <input type="date" id="test_date" name="test_date" value="{{ today.isoformat() }}" required>
    </div>
    
    <div class="form-group">
        <label for="test_name">Test Name</label>
        <input type="text" id="test_name" name="test_name" required>
    </div>
    
    <div class="form-group">
        <label for="result_value">Result Value</label>
        <input type="number" step="0.1" id="result_value" name="result_value">
    </div>
    
    <button type="submit" class="btn btn-success">Save Lab Result</button>
</form>

<!-- Display existing results -->
{% if records %}
<h3>Previous Lab Results</h3>
<table>
    <!-- Table content -->
</table>
{% endif %}
{% endblock %}
```
{% endraw %}

#### Step 5: Run Migration

```bash
python migrate_database.py
```

#### Step 6: Add Navigation

Edit `templates/base.html` or patient info sections to add links to the new route.

---

## Code Patterns

### Database Session Pattern

**Always use try/finally:**
```python
session = get_session()
try:
    # Your code
    patient = session.query(Patient).first()
    # Process data
finally:
    close_session(session)
```

### Form Handling Pattern

```python
if request.method == 'POST':
    # Validate input
    if not required_field:
        flash('Field required', 'error')
        return redirect(url_for('form_page'))
    
    # Create/update object
    obj = Model(field=value)
    session.add(obj)
    session.commit()
    flash('Success message', 'success')
    return redirect(url_for('success_page'))

# GET request - show form
return render_template('form.html')
```

### Error Handling Pattern

```python
try:
    # Risky operation
    value = float(request.form.get('number'))
except ValueError:
    flash('Invalid number format', 'error')
except Exception as e:
    flash(f'Error: {str(e)}', 'error')
    # Log error for debugging
    print(f"Error: {e}")
```

---

## Best Practices

### 1. Database Queries

**✅ DO:**
- Use joins instead of multiple queries
- Limit results when possible
- Close sessions properly
- Use transactions for multiple operations

**❌ DON'T:**
- Query in loops (N+1 problem)
- Leave sessions open
- Query all records when you only need a few

### 2. Code Organization

**✅ DO:**
- Keep routes focused on one task
- Extract complex logic to separate functions
- Use meaningful variable names
- Add comments for complex logic

**❌ DON'T:**
- Put business logic in routes
- Use magic numbers (use constants)
- Write functions longer than 50 lines

### 3. Security

**✅ DO:**
- Validate all user input
- Use parameterized queries (SQLAlchemy does this)
- Sanitize output in templates
- Change secret key in production

**❌ DON'T:**
- Trust user input
- Expose sensitive data
- Use debug mode in production

### 4. Performance

**✅ DO:**
- Optimize database queries
- Use indexes on frequently queried fields
- Cache expensive calculations
- Limit dashboard data to recent records

**❌ DON'T:**
- Load all records unnecessarily
- Perform calculations in templates
- Make synchronous blocking calls

---

## Testing Your Changes

### Manual Testing Steps

1. **Start the server:**
    ```bash
    python app_web.py
    ```

2. **Test the new feature:**
    - Navigate to the page
    - Fill out forms
    - Submit data
    - Verify data saves
    - Check database directly if needed

3. **Test error cases:**
    - Invalid input
    - Missing required fields
    - Non-existent patient IDs

### Database Inspection

**Using Python:**
```python
from database import get_session, close_session
from models import Patient

session = get_session()
try:
    patients = session.query(Patient).all()
    for p in patients:
        print(f"{p.patient_id}: {p.first_name} {p.last_name}")
finally:
    close_session(session)
```

**Using SQLite CLI:**
```bash
sqlite3 health_database.db
.tables
SELECT * FROM patients;
```

---

## Common Modifications

### Changing Port

Edit `app_web.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Change 5000 to 8080
```

### Adding New Reference Ranges

Edit `analysis.py`:
```python
VITAMIN_REFERENCE_RANGES = {
    'vitamin_d': {'low': 30, 'high': 100, 'unit': 'ng/mL'},
    # Add or modify ranges
}
```

### Customizing Dashboard Statistics

Edit `app_web.py` - `dashboard()` function:
```python
# Modify date ranges
thirty_days_ago = datetime.now().date() - timedelta(days=30)

# Add new statistics
total_appointments = session.query(Appointment).count()
```

### Styling Changes

Edit `templates/base.html` - CSS in `<style>` tag:
```css
:root {
    --primary-color: #667eea;  /* Change colors */
    --secondary-color: #764ba2;
}
```

---

## Debugging Tips

### Enable Flask Debug Mode

In `app_web.py`:
```python
app.run(debug=True)  # Shows detailed errors
```

### Print Debugging

```python
print(f"DEBUG: Patient ID = {patient_id}")
print(f"DEBUG: Form data = {request.form}")
```

### Database Query Debugging

```python
# Enable SQL logging
from database import engine
engine.echo = True  # Prints all SQL queries
```

### Template Debugging

Use Jinja2 debug:
{% raw %}
```jinja2
{{ variable|pprint }}  <!-- Pretty print variable -->
{{ variable|debug }}  <!-- Debug output -->
```
{% endraw %}

---

## Version Control

### .gitignore Recommendations

Create `.gitignore`:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

---

## API Endpoints Reference

### Patient Management
- `GET /patients` - List all patients
- `GET /patients/add` - Show add patient form
- `POST /patients/add` - Create new patient
- `GET /patients/<id>/edit` - Show edit form
- `POST /patients/<id>/edit` - Update patient
- `POST /patients/<id>/delete` - Delete patient

### Clinical Data
- `GET /blood/<patient_id>` - View blood parameters
- `POST /blood/<patient_id>` - Add blood test
- `GET /vitamins/<patient_id>` - View vitamin levels
- `POST /vitamins/<patient_id>` - Add vitamin test
- Similar patterns for other data types

### Analysis
- `GET /insights/<patient_id>` - Generate health insights

---

## Performance Optimization Checklist

- [ ] Use database indexes on foreign keys
- [ ] Limit query results (use `.limit()`)
- [ ] Use joins instead of multiple queries
- [ ] Cache expensive calculations
- [ ] Optimize dashboard queries
- [ ] Use pagination for large lists
- [ ] Minimize template rendering time

---

## Security Checklist

- [ ] Change Flask secret key
- [ ] Validate all user input
- [ ] Sanitize output
- [ ] Use HTTPS in production
- [ ] Implement authentication
- [ ] Set proper file permissions
- [ ] Regular database backups
- [ ] Log security events

---

## Useful Commands

```bash
# Start development server
python app_web.py

# Run migrations
python migrate_database.py

# Verify database
python verify_database.py

# Check Python syntax
python -m py_compile app_web.py

# Install dependencies
pip install -r requirements.txt

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

---

**Remember:** Always test your changes thoroughly before deploying to production!

