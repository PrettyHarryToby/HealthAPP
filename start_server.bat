@echo off
echo ========================================
echo Health Database Application - Web Server
echo ========================================
echo.
echo Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Flask not found. Installing dependencies...
    pip install -r requirements.txt
)
echo.
echo Starting web server...
echo Open your browser and navigate to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python app_web.py
pause

