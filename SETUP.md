# Quick Setup Guide - HealthAPP

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Python
- Download Python 3.7+ from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

### Step 2: Install Dependencies
Open terminal/command prompt in the HealthAPP folder:
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python app_web.py
```

### Step 4: Open Browser
Navigate to: **http://localhost:5000**

That's it! 🎉

---

## 📋 Detailed Setup

### Windows Setup

1. **Install Python:**
   - Download from https://www.python.org/downloads/
   - Run installer
   - Check "Add Python to PATH"
   - Click "Install Now"

2. **Open Command Prompt:**
   - Press `Win + R`
   - Type `cmd` and press Enter
   - Navigate to HealthAPP folder:
     ```bash
     cd C:\Users\YourName\Downloads\HealthAPP
     ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Application:**
   ```bash
   python app_web.py
   ```

5. **Access Application:**
   - Open browser
   - Go to: http://localhost:5000

### Mac/Linux Setup

1. **Check Python:**
   ```bash
   python3 --version
   ```
   If not installed: `brew install python3` (Mac) or `sudo apt install python3` (Linux)

2. **Navigate to Project:**
   ```bash
   cd ~/Downloads/HealthAPP
   ```

3. **Install Dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Run Application:**
   ```bash
   python3 app_web.py
   ```

5. **Access Application:**
   - Open browser
   - Go to: http://localhost:5000

---

## 🔧 Troubleshooting

### "python is not recognized"
**Solution:** Use `python3` instead of `python`

### "pip is not recognized"
**Solution:** Use `python -m pip` instead of `pip`

### Port 5000 Already in Use
**Solution:** Change port in `app_web.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```

### Module Not Found Errors
**Solution:** Reinstall dependencies:
```bash
pip install --upgrade -r requirements.txt
```

---

## 📁 Project Files Explained

| File | Purpose |
|------|---------|
| `app_web.py` | Main web application (run this) |
| `models.py` | Database structure |
| `database.py` | Database connection |
| `analysis.py` | Health analysis functions |
| `requirements.txt` | Python packages needed |
| `health_database.db` | Database file (created automatically) |

---

## ✅ Verification

After setup, verify everything works:

1. **Check Python:**
   ```bash
   python --version
   ```
   Should show Python 3.7 or higher

2. **Check Dependencies:**
   ```bash
   python -c "import flask, sqlalchemy; print('OK')"
   ```
   Should print "OK"

3. **Run Application:**
   ```bash
   python app_web.py
   ```
   Should show "Starting server..." message

4. **Access Dashboard:**
   - Open http://localhost:5000
   - Should see dashboard page

---

## 🎯 Next Steps

1. Add your first patient
2. Enter test data
3. View insights
4. Explore the dashboard

For detailed development guide, see `HOW_TO_RUN.md` and `DEVELOPER_GUIDE.md`

