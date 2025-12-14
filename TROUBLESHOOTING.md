# Troubleshooting Guide - HealthAPP

## Server Won't Start / localhost:5000 Not Opening

### Quick Fixes

#### 1. **Port Already in Use**

**Symptoms:** Error message about port 5000 being in use

**Solution A - Use Different Port:**
Edit `app_web.py`, line 870:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```
Then access: http://localhost:5001

**Solution B - Find and Close Process:**
```bash
# Windows - Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

#### 2. **Dependencies Not Installed**

**Symptoms:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
pip install -r requirements.txt
```

#### 3. **Server Not Actually Running**

**Symptoms:** Browser shows "This site can't be reached"

**Solution:**
1. Open a new terminal/command prompt
2. Navigate to HealthAPP folder:
   ```bash
   cd C:\Users\panda\Downloads\HealthAPP
   ```
3. Run:
   ```bash
   python app_web.py
   ```
4. Wait for "Starting server..." message
5. Keep terminal open (don't close it)
6. Open browser to http://localhost:5000

#### 4. **Firewall Blocking**

**Symptoms:** Server starts but browser can't connect

**Solution:**
- Windows: Allow Python through Windows Firewall
- Or use: `host='127.0.0.1'` instead of `host='0.0.0.0'`

#### 5. **Database Errors**

**Symptoms:** Server crashes on startup with database errors

**Solution:**
```bash
# Run migration
python migrate_database.py

# Verify database
python verify_database.py
```

### Step-by-Step Diagnostic

Run this command to check everything:
```bash
python start_server.py
```

This will:
- ✓ Check if dependencies are installed
- ✓ Check if port 5000 is available
- ✓ Start the server with error messages

### Common Error Messages

#### "Address already in use"
- **Cause:** Another process is using port 5000
- **Fix:** Use different port or close the other process

#### "ModuleNotFoundError"
- **Cause:** Dependencies not installed
- **Fix:** `pip install -r requirements.txt`

#### "This site can't be reached"
- **Cause:** Server not running or wrong URL
- **Fix:** Make sure server is running and use http://localhost:5000

#### "Connection refused"
- **Cause:** Server crashed or not started
- **Fix:** Check terminal for error messages, restart server

### Using the Batch File (Windows)

Double-click `RUN_SERVER.bat` or `start_server.bat`

This will:
- Check dependencies
- Start the server
- Show clear messages

### Manual Server Start

1. **Open Command Prompt:**
   - Press `Win + R`
   - Type `cmd` and press Enter

2. **Navigate to Project:**
   ```bash
   cd C:\Users\panda\Downloads\HealthAPP
   ```

3. **Start Server:**
   ```bash
   python app_web.py
   ```

4. **Look for this message:**
   ```
   Starting server...
   Open your browser and navigate to: http://localhost:5000
   ```

5. **Keep terminal open** - Closing it stops the server

6. **Open browser** to http://localhost:5000

### Still Not Working?

1. **Check Python version:**
   ```bash
   python --version
   ```
   Should be 3.7 or higher

2. **Test Flask installation:**
   ```bash
   python -c "import flask; print(flask.__version__)"
   ```

3. **Check for syntax errors:**
   ```bash
   python -m py_compile app_web.py
   ```

4. **Try alternative port:**
   - Edit `app_web.py`
   - Change `port=5000` to `port=8080`
   - Access http://localhost:8080

### Getting Help

If none of these work:
1. Check terminal output for error messages
2. Copy the full error message
3. Check `HOW_TO_RUN.md` for more details
4. Verify all files are in the correct location

